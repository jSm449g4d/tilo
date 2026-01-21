import sqlite3
import json
import os
import jwt
import hashlib
import re
import unicodedata
import flask
import sys
from contextlib import closing
import time

FUNC_NAME = "tptef"


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
        "CREATE TABLE IF NOT EXISTS tptef_chat(id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "user TEXT NOT NULL,userid INTEGER NOT NULL,roomid INTEGER NOT NULL,"
        "text TEXT NOT NULL,mode TEXT NOT NULL,timestamp INTEGER NOT NULL)"
    )
    cur.execute(
        "CREATE TABLE IF NOT EXISTS tptef_room(id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "user TEXT NOT NULL,userid INTEGER NOT NULL,room TEXT UNIQUE NOT NULL,"
        "passhash TEXT DEFAULT '',timestamp INTEGER NOT NULL)"
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
            return json.dumps({"message": "notEnoughForm(info)"}, ensure_ascii=False)
        _dataDict = json.loads(request.form["info"])
        token = ""
        user_id = ""
        encoded_new_token = token
        if _dataDict["token"] != "":
            token = jwt.decode(_dataDict["token"], pyJWT_pass, algorithms=["HS256"])
            if token["timestamp"] + pyJWT_timeout < int(time.time()):
                return json.dumps({"message": "tokenTimeout"}, ensure_ascii=False)
            user_id = token["id"]
            encoded_new_token = jwt.encode(
                {"id": user_id, "timestamp": int(time.time())},
                pyJWT_pass,
                algorithm="HS256",
            )

        if "fetch" in request.form:
            _dataDict.update(json.loads(request.form["fetch"]))
            _roompasshash = _dataDict["roomKey"]
            if _dataDict["roomKey"] not in ["", "0"]:
                _roompasshash = hashlib.sha256(
                    _dataDict["roomKey"].encode()
                ).hexdigest()
            with closing(sqlite3.connect(db_dir)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                # duplication and roomKey check
                cur.execute(
                    "SELECT * FROM tptef_room WHERE id = ?;", [_dataDict["roomid"]]
                )
                _room = cur.fetchone()
                if _room == None:
                    return json.dumps(
                        {"message": "notExist", "text": "部屋が不明"},
                        ensure_ascii=False,
                    )
                if _room["userid"] != user_id:
                    if _room["passhash"] != "" and _room["passhash"] != _roompasshash:
                        return json.dumps(
                            {"message": "wrongPass", "text": "アクセス拒否"},
                            ensure_ascii=False,
                        )
                # process start
                _userid = _room["userid"]
                _roomid = _room["id"]
                cur.execute("SELECT * FROM tptef_chat WHERE roomid = ?;", [_roomid])
                _chats = [
                    {key: value for key, value in dict(result).items()}
                    for result in cur.fetchall()
                ]
                return json.dumps(
                    {
                        "message": "processed",
                        "chats": _chats,
                        "room": dict(_room),
                        "userid": _userid,
                        "token": encoded_new_token,
                    },
                    ensure_ascii=False,
                )
            return json.dumps(
                {"message": "rejected", "text": "不明なエラー"}, ensure_ascii=False
            )

        if "remark" in request.form:
            _dataDict.update(json.loads(request.form["remark"]))
            _roompasshash = _dataDict["roomKey"]
            if _dataDict["roomKey"] not in ["", "0"]:
                _roompasshash = hashlib.sha256(
                    _dataDict["roomKey"].encode()
                ).hexdigest()
            if token == "":
                return json.dumps(
                    {"message": "tokenNothing", "text": "トークン未提出"},
                    ensure_ascii=False,
                )
            with closing(sqlite3.connect(db_dir)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                # duplication and roomKey check
                cur.execute(
                    "SELECT * FROM tptef_room WHERE id = ?;", [_dataDict["roomid"]]
                )
                _room = cur.fetchone()
                if _room == None:
                    return json.dumps(
                        {"message": "notExist", "text": "存在不明"}, ensure_ascii=False
                    )
                if _room["passhash"] != "" and _room["passhash"] != _roompasshash:
                    return json.dumps(
                        {"message": "wrongPass", "text": "アクセス拒否"},
                        ensure_ascii=False,
                    )
                # process start
                cur.execute(
                    "INSERT INTO tptef_chat(user,userid,roomid,text,mode,timestamp) values(?,?,?,?,?,?)",
                    [
                        _dataDict["user"],
                        user_id,
                        _room["id"],
                        _dataDict["text"],
                        "text",
                        int(time.time()),
                    ],
                )
                conn.commit()
                return json.dumps(
                    {"message": "processed"},
                    ensure_ascii=False,
                )
            return json.dumps(
                {"message": "rejected", "text": "不明なエラー"}, ensure_ascii=False
            )

        if "upload" in request.files:
            _roompasshash = _dataDict["roomKey"]
            if _dataDict["roomKey"] not in ["", "0"]:
                _roompasshash = hashlib.sha256(
                    _dataDict["roomKey"].encode()
                ).hexdigest()
            if token == "":
                return json.dumps({"message": "tokenNothing"}, ensure_ascii=False)
            with closing(sqlite3.connect(db_dir)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                # duplication and roomKey check
                cur.execute(
                    "SELECT * FROM tptef_room WHERE id = ?;", [_dataDict["roomid"]]
                )
                _room = cur.fetchone()
                if _room == None:
                    return json.dumps(
                        {"message": "notExist", "text": "存在不明"}, ensure_ascii=False
                    )
                if _room["passhash"] != "" and _room["passhash"] != _roompasshash:
                    return json.dumps(
                        {"message": "wrongPass", "text": "アクセス拒否"},
                        ensure_ascii=False,
                    )
                # process start
                _timestamp = int(time.time())
                cur.execute(
                    "INSERT INTO tptef_chat(user,userid,roomid,text,mode,timestamp) values(?,?,?,?,?,?)",
                    [
                        _dataDict["user"],
                        user_id,
                        _room["id"],
                        request.files["upload"].filename,
                        "attachment",
                        _timestamp,
                    ],
                )
                conn.commit()
                cur.execute(
                    "SELECT * FROM tptef_chat WHERE ROWID = last_insert_rowid();",
                    [],
                )
                _chat = cur.fetchone()
                request.files["upload"].save(
                    os.path.normpath(os.path.join(tmp_dir, safe_string(_chat["id"])))
                )
                return json.dumps(
                    {"message": "processed"},
                    ensure_ascii=False,
                )
            return json.dumps(
                {"message": "rejected", "text": "不明なエラー"}, ensure_ascii=False
            )

        if "download" in request.form:
            _dataDict.update(json.loads(request.form["download"]))
            _roompasshash = _dataDict["roomKey"]
            if _dataDict["roomKey"] not in ["", "0"]:
                _roompasshash = hashlib.sha256(
                    _dataDict["roomKey"].encode()
                ).hexdigest()
            with closing(sqlite3.connect(db_dir)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                # duplication and roomKey check
                cur.execute(
                    "SELECT * FROM tptef_room WHERE id = ?;", [_dataDict["roomid"]]
                )
                _room = cur.fetchone()
                if _room == None:
                    return json.dumps(
                        {"message": "notExist", "text": "ファイルが不明"},
                        ensure_ascii=False,
                    )
                if _room["passhash"] != "" and _room["passhash"] != _roompasshash:
                    return json.dumps(
                        {"message": "wrongPass", "text": "アクセス拒否"},
                        ensure_ascii=False,
                    )
                # process start
                _target_file = os.path.normpath(
                    os.path.join(tmp_dir, safe_string(_dataDict["chatid"]))
                )
                if os.path.exists(_target_file):
                    return flask.send_file(
                        _target_file,
                        as_attachment=_dataDict["as_attachment"],
                        download_name=_dataDict["filename"],
                    )
                return json.dumps(
                    {"message": "notExist", "text": "ファイル不明"},
                    ensure_ascii=False,
                )
            return json.dumps(
                {"message": "rejected", "text": "不明なエラー"}, ensure_ascii=False
            )

        if "delete" in request.form:
            _dataDict.update(json.loads(request.form["delete"]))
            _roompasshash = _dataDict["roomKey"]
            if _dataDict["roomKey"] not in ["", "0"]:
                _roompasshash = hashlib.sha256(
                    _dataDict["roomKey"].encode()
                ).hexdigest()
            if token == "":
                return json.dumps({"message": "tokenNothing"}, ensure_ascii=False)
            with closing(sqlite3.connect(db_dir)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                # duplication and roomKey check
                cur.execute(
                    "SELECT * FROM tptef_room WHERE id = ?;", [_dataDict["roomid"]]
                )
                _room = cur.fetchone()
                if _room == None:
                    return json.dumps(
                        {"message": "notExist", "text": "発言が不明"},
                        ensure_ascii=False,
                    )
                if _room["passhash"] != "" and _room["passhash"] != _roompasshash:
                    return json.dumps(
                        {"message": "wrongPass", "text": "アクセス拒否"},
                        ensure_ascii=False,
                    )
                # process start
                cur.execute(
                    "DELETE FROM tptef_chat WHERE id = ? AND userId = ? ;",
                    [_dataDict["chatid"], user_id],
                )
                conn.commit()
                _remove_file = os.path.normpath(
                    os.path.join(tmp_dir, safe_string(_dataDict["chatid"]))
                )
                if os.path.exists(_remove_file):
                    os.remove(_remove_file)
                return json.dumps(
                    {"message": "processed"},
                    ensure_ascii=False,
                )
            return json.dumps(
                {"message": "rejected", "text": "不明なエラー"}, ensure_ascii=False
            )

        if "search" in request.form:
            _dataDict.update(json.loads(request.form["search"]))
            _roompasshash = _dataDict["roomKey"]
            if _dataDict["roomKey"] not in ["", "0"]:
                _roompasshash = hashlib.sha256(
                    _dataDict["roomKey"].encode()
                ).hexdigest()
            with closing(sqlite3.connect(db_dir)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                cur.execute("SELECT * FROM tptef_room")
                _rooms = [
                    {key: value for key, value in dict(result).items()}
                    for result in cur.fetchall()
                ]
                return json.dumps(
                    {
                        "message": "processed",
                        "rooms": _rooms,
                        "token": encoded_new_token,
                    },
                    ensure_ascii=False,
                )
            return json.dumps(
                {"message": "rejected", "text": "不明なエラー"}, ensure_ascii=False
            )

        if "create" in request.form:
            _dataDict.update(json.loads(request.form["create"]))
            _room_name = safe_string(_dataDict["room"], _anti_directory_traversal=False)
            _roompasshash = _dataDict["roomKey"]
            if _dataDict["roomKey"] not in ["", "0"]:
                _roompasshash = hashlib.sha256(
                    _dataDict["roomKey"].encode()
                ).hexdigest()
            if token == "":
                return json.dumps({"message": "tokenNothing"}, ensure_ascii=False)
            with closing(sqlite3.connect(db_dir)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                # check duplication
                cur.execute("SELECT * FROM tptef_room WHERE room = ?;", [_room_name])
                _room = cur.fetchone()
                if _room != None:
                    return json.dumps(
                        {"message": "alreadyExisted", "text": "既存の部屋名"},
                        ensure_ascii=False,
                    )
                cur.execute(
                    "INSERT INTO tptef_room(user,userid,room,passhash,timestamp) values(?,?,?,?,?)",
                    [
                        _dataDict["user"],
                        user_id,
                        _room_name,
                        _roompasshash,
                        int(time.time()),
                    ],
                )
                conn.commit()
                cur.execute(
                    "SELECT * FROM tptef_room WHERE ROWID = last_insert_rowid();", []
                )
                _room = cur.fetchone()
                return json.dumps(
                    {
                        "message": "processed",
                        "room": dict(_room),
                    },
                    ensure_ascii=False,
                )
            return json.dumps(
                {"message": "rejected", "text": "不明なエラー"}, ensure_ascii=False
            )

        if "destroy" in request.form:
            _dataDict.update(json.loads(request.form["destroy"]))
            _roompasshash = _dataDict["roomKey"]
            if _dataDict["roomKey"] not in ["", "0"]:
                _roompasshash = hashlib.sha256(
                    _dataDict["roomKey"].encode()
                ).hexdigest()
            if token == "":
                return json.dumps({"message": "tokenNothing"}, ensure_ascii=False)
            with closing(sqlite3.connect(db_dir)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                # check duplication
                cur.execute(
                    "SELECT * FROM tptef_room WHERE id = ?;", [_dataDict["roomid"]]
                )
                _room = cur.fetchone()
                if _room == None:
                    return json.dumps(
                        {"message": "notExist", "text": "存在無し"}, ensure_ascii=False
                    )
                if _room["userid"] != user_id:
                    return json.dumps(
                        {"message": "youerntOwner", "text": "アクセス拒否"},
                        ensure_ascii=False,
                    )
                cur.execute(
                    "DELETE FROM tptef_room WHERE userid = ? AND id = ? ;",
                    [user_id, _dataDict["roomid"]],
                )
                cur.execute(
                    "SELECT * FROM tptef_chat WHERE roomid = ? AND mode=? ;",
                    [_room["id"], "attachment"],
                )
                _chats = cur.fetchall()
                for _chat in _chats:
                    _remove_file = os.path.normpath(
                        os.path.join(tmp_dir, str(_chat["id"]))
                    )
                    if os.path.exists(_remove_file):
                        os.remove(_remove_file)
                cur.execute(
                    "DELETE FROM tptef_chat WHERE roomid = ? ;",
                    [_room["id"]],
                )
                conn.commit()
                return json.dumps(
                    {"message": "processed"},
                    ensure_ascii=False,
                )
            return json.dumps(
                {"message": "rejected", "text": "不明なエラー"}, ensure_ascii=False
            )

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
