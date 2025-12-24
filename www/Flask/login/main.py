import sqlite3
import json
import hashlib
import jwt
from contextlib import closing
import time
import sys
import os
import re
import unicodedata
import flask
import smtplib
from email.mime.text import MIMEText
from email.utils import formatdate

FUNC_NAME = "login"


# Processing when accessing directly with GET
def get_response(_statusDict={"STATUS": "VALUE"}):
    _statusLines: str = " <table border='1'>"
    for key, value in _statusDict.items():
        _statusLines += "<tr><th>" + key + "</th><th>" + value + "</th></tr>"
    _statusLines += " </table>"
    with open(
        os.path.join(os.path.dirname(__file__), "main.html"), "r", encoding="utf-8"
    ) as f:
        html = f.read()
        html = html.replace("{{FUNC_NAME}}", FUNC_NAME)
        html = html.replace("{{STATUS_TABLE}}", _statusLines)
        return flask.render_template_string(html)
    return "404: nof found → main.html", 404


# load setting
tmp_dir = "./tmp/" + FUNC_NAME + "/"
os.makedirs(tmp_dir, exist_ok=True)
key_dir = "./keys/keys.json"
db_dir = "./tmp/sqlite.db"
pyJWT_pass = "test"
pyJWT_timeout = 3600
keys = {}
if os.path.exists(key_dir):
    with open(key_dir) as f:
        keys = json.load(f)
        if "db" in keys:
            db_dir = keys["db"]
        if "pyJWT_pass" in keys:
            pyJWT_pass = keys["pyJWT_pass"]
        if "pyJWT_timeout" in keys:
            pyJWT_timeout = keys["pyJWT_timeout"]

with closing(sqlite3.connect(db_dir)) as conn:
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS account(id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "user TEXT UNIQUE NOT NULL,passhash TEXT NOT NULL,"
        "mail TEXT DEFAULT '',timestamp INTEGER NOT NULL)"
    )
    conn.commit()


def safe_string(_s, _max=500, _anti_directory_traversal=True):
    _s = unicodedata.normalize("NFKC", str(_s))
    if _anti_directory_traversal:
        _s = re.sub(r"\[.*\]|<.*>|/", "", _s)
    _s = re.sub(r"\\|;|\'|\"", "", _s)
    _s = re.sub(r"\s+", " ", _s).strip()
    return _s[:_max]


def show(request):
    if request.method == "GET":
        return get_response()
    if request.method == "POST":
        if "info" not in request.form:
            return json.dumps(
                {"message": "notEnoughForm(info)", "text": "infoフォーム無"},
                ensure_ascii=False,
            )
        _dataDict = json.loads(request.form["info"])
        token = ""
        encoded_new_token = token
        if _dataDict["token"] != "":
            token = jwt.decode(_dataDict["token"], pyJWT_pass, algorithms=["HS256"])
            if token["timestamp"] + pyJWT_timeout < int(time.time()):
                return json.dumps(
                    {"message": "tokenTimeout", "text": "トークン期限切れ"},
                    ensure_ascii=False,
                )
            encoded_new_token = jwt.encode(
                {"id": token["id"], "timestamp": int(time.time())},
                pyJWT_pass,
                algorithm="HS256",
            )

        if "login" in request.form:
            _dataDict.update(json.loads(request.form["login"]))
            _username = safe_string(_dataDict["user"])
            passhash = hashlib.sha256(_dataDict["pass"].encode()).hexdigest()
            with closing(sqlite3.connect(db_dir)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute("SELECT * FROM account WHERE user = ?;", [_username])
                _data = cur.fetchone()
                if _data == None:
                    return json.dumps(
                        {"message": "notExist", "text": "アカウントが存在しない"}
                    )
                if _data["passhash"] != passhash:
                    return json.dumps({"message": "wrongPass", "text": "アクセス拒否"})
                token = jwt.encode(
                    {"id": _data["id"], "timestamp": int(time.time())},
                    pyJWT_pass,
                    algorithm="HS256",
                )
                return json.dumps(
                    {
                        "message": "processed",
                        "user": _data["user"],
                        "token": token,
                        "id": _data["id"],
                        "mail": _data["mail"],
                    },
                    ensure_ascii=False,
                )
            return json.dumps({"message": "rejected", "text": "不明なエラー"})

        if "signup" in request.form:
            _dataDict.update(json.loads(request.form["signup"]))
            passhash = hashlib.sha256(_dataDict["pass"].encode()).hexdigest()
            _username = safe_string(_dataDict["user"])
            with closing(sqlite3.connect(db_dir)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                # check duplication
                cur.execute("SELECT * FROM account WHERE user = ?;", [_username])
                if cur.fetchone() != None:
                    return json.dumps(
                        {"message": "alreadyExist", "text": "既存の名前"},
                        ensure_ascii=False,
                    )
                # process
                cur.execute(
                    "INSERT INTO account(user,passhash,timestamp,mail) values(?,?,?,?)",
                    [_username, passhash, int(time.time()), ""],
                )
                conn.commit()
                # create token
                cur.execute(
                    "SELECT * FROM account WHERE ROWID = last_insert_rowid();", []
                )
                _data = cur.fetchone()
                token = jwt.encode(
                    {"id": _data["id"], "timestamp": int(time.time())},
                    pyJWT_pass,
                    algorithm="HS256",
                )
            return json.dumps(
                {
                    "message": "processed",
                    "user": _username,
                    "token": token,
                    "id": _data["id"],
                    "mail": _data["mail"],
                },
                ensure_ascii=False,
            )

        if "signout" in request.form:
            return json.dumps({"message": "processed"}, ensure_ascii=False)

        if "account_change" in request.form:
            _dataDict.update(json.loads(request.form["account_change"]))
            _username = safe_string(_dataDict["user"])
            if token == "":
                return json.dumps(
                    {"message": "tokenNothing", "text": "トークン未提出"},
                    ensure_ascii=False,
                )
            _passhash = hashlib.sha256(_dataDict["pass"].encode()).hexdigest()
            with closing(sqlite3.connect(db_dir)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                # check duplication
                cur.execute(
                    "SELECT * FROM account WHERE user = ?;", [_username]
                )
                if cur.fetchone() != None:
                    return json.dumps(
                        {"message": "alreadyExist", "text": "既存の名前"},
                        ensure_ascii=False,
                    )
                cur.execute(
                    "SELECT * FROM account WHERE ROWID = last_insert_rowid();", []
                )
                _data = cur.fetchone()
                # process
                _user = _data["user"] if _username == "" else _username
                _passhash = _data["passhash"] if _dataDict["pass"] == "" else _passhash
                _mail = _data["mail"] if _dataDict["mail"] == "" else _dataDict["mail"]
                print(_user)
                cur.execute(
                    "UPDATE account SET user = ?, passhash = ?, mail = ? WHERE id = ?;",
                    [_user, _passhash, _mail, token["id"]],
                )
                conn.commit()
                return json.dumps(
                    {
                        "message": "processed",
                        "user": _user,
                        "mail": _mail,
                        "token": encoded_new_token,
                    },
                    ensure_ascii=False,
                )
            return json.dumps({"message": "rejected", "text": "不明なエラー"})

        if "account_delete" in request.form:
            _dataDict.update(json.loads(request.form["account_delete"]))
            if token == "":
                return json.dumps(
                    {"message": "tokenNothing", "text": "トークン無し"},
                    ensure_ascii=False,
                )
            with closing(sqlite3.connect(db_dir)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                # process
                cur.execute(
                    "DELETE FROM account WHERE id = ?;",
                    [token["id"]],
                )
                conn.commit()
                return json.dumps(
                    {"message": "processed"},
                    ensure_ascii=False,
                )
            return json.dumps({"message": "rejected", "text": "不明なエラー"})

        # under construction
        if "mailcertification" in request.form:
            _dataDict.update(json.loads(request.form["login"]))
            user = _dataDict["user"]
            passhash = hashlib.sha256(_dataDict["pass"].encode()).hexdigest()
            with closing(sqlite3.connect(db_dir)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute("SELECT * FROM account WHERE user = ?;", [user])
                _data = cur.fetchone()
                if _data == None:
                    return json.dumps({"message": "notExist", "text": "存在なし"})
                token = jwt.encode(
                    {"id": _data["id"], "timestamp": int(time.time())},
                    pyJWT_pass,
                    algorithm="HS256",
                )
                _BODY = "1. copy this JTWtoken [" + token + "]\n"
                +"2. plz paste the JWTtoken certification modal"
                mail = MIMEText(_BODY)
                mail["To"] = _data["mail"]
                mail["Date"] = formatdate()
                smtpobj = smtplib.SMTP("smtp.gmail.com", 587)
                smtpobj.ehlo()
                smtpobj.starttls()
                smtpobj.ehlo()
                return json.dumps(
                    {
                        "message": "processed",
                    },
                    ensure_ascii=False,
                )
            return json.dumps({"message": "rejected"})

    return "404: nof found → main.html", 404


# isolation
if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(os.path.dirname(os.path.join("./", __file__)))
    app = flask.Flask(__name__, template_folder="./", static_folder="./static/")
    app.config["MAX_CONTENT_LENGTH"] = 100000000
    os.makedirs("./tmp", exist_ok=True)

    # FaaS: root this
    @app.route("/", methods=["GET", "POST"])
    def py_show():
        try:
            return show(flask.request)
        except Exception as e:
            return "500 error⇒" + str(e), 500

    # run
    app.run()
