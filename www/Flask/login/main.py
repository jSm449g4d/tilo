import json
import hashlib
import jwt
import time
import sys
import os
import re
import unicodedata
import flask

from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import DeclarativeBase

FUNC_NAME = "login"


def get_response(status={"STATUS": "VALUE"}):
    rows = "".join(f"<tr><th>{k}</th><th>{v}</th></tr>" for k, v in status.items())
    with open(
        os.path.join(os.path.dirname(__file__), "main.html"), "r", encoding="utf-8"
    ) as f:
        html = f.read()
    html = html.replace("{{FUNC_NAME}}", FUNC_NAME).replace(
        "{{STATUS_TABLE}}", f" <table border='1'>{rows} </table>"
    )
    return flask.render_template_string(html)


os.makedirs(f"./tmp/{FUNC_NAME}/", exist_ok=True)
key_dir = "./keys/keys.json"
db_dir = "./tmp/sqlite.db"
pyJWT_pass = "test"
pyJWT_timeout = 3600
if os.path.exists(key_dir):
    with open(key_dir) as f:
        keys = json.load(f)
    db_dir = keys.get("db", db_dir)
    pyJWT_pass = keys.get("pyJWT_pass", pyJWT_pass)
    pyJWT_timeout = keys.get("pyJWT_timeout", pyJWT_timeout)

engine = create_engine(f"sqlite:///{db_dir}", future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "account"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user = Column(String, unique=True, nullable=False)
    passhash = Column(String, nullable=False)
    mail = Column(String, default="")
    timestamp = Column(Integer, nullable=False)


Base.metadata.create_all(engine)


def safe_string(s, max_len=500, anti_directory_traversal=True):
    s = unicodedata.normalize("NFKC", str(s))
    if anti_directory_traversal:
        s = re.sub(r"\[.*\]|<.*>|/", "", s)
    s = re.sub(r"\\|;|\'|\"", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:max_len]


def show(request):
    if request.method == "GET":
        return get_response()
    if request.method != "POST":
        return "404: nof found → main.html", 404
    if "info" not in request.form:
        return json.dumps({"message": "notEnoughForm(info)", "text": "infoフォーム無"})
    data = json.loads(request.form["info"])
    token = ""
    encoded_new_token = token
    if data.get("token") != "":
        token = jwt.decode(data["token"], pyJWT_pass, algorithms=["HS256"])
        if token["timestamp"] + pyJWT_timeout < int(time.time()):
            return json.dumps({"message": "tokenTimeout", "text": "トークン期限切れ"})
        encoded_new_token = jwt.encode(
            {"id": token["id"], "timestamp": int(time.time())},
            pyJWT_pass,
            algorithm="HS256",
        )
    passhash = ""
    if data.get("pass") != "":
        passhash = hashlib.sha256(data["pass"].encode()).hexdigest()

    with SessionLocal() as session:
        if "login" in request.form:
            data.update(json.loads(request.form["login"]))
            _username = safe_string(data["user"])
            account = session.query(Account).filter_by(user=_username).first()
            if account is None:
                return json.dumps(
                    {"message": "notExist", "text": "アカウントが存在しない"}
                )
            if account.passhash != passhash:
                return json.dumps({"message": "wrongPass", "text": "アクセス拒否"})
            token = jwt.encode(
                {"id": account.id, "timestamp": int(time.time())},
                pyJWT_pass,
                algorithm="HS256",
            )
            return json.dumps(
                {
                    "message": "processed",
                    "user": account.user,
                    "token": token,
                    "id": account.id,
                    "mail": account.mail,
                }
            )

        if "signup" in request.form:
            data.update(json.loads(request.form["signup"]))
            _username = safe_string(data["user"])
            if session.query(Account).filter_by(user=_username).first() is not None:
                return json.dumps({"message": "alreadyExist", "text": "既存の名前"})
            account = Account(
                user=_username,
                passhash=passhash,
                timestamp=int(time.time()),
                mail="",
            )
            session.add(account)
            session.commit()
            token = jwt.encode(
                {"id": account.id, "timestamp": int(time.time())},
                pyJWT_pass,
                algorithm="HS256",
            )
            return json.dumps(
                {
                    "message": "processed",
                    "user": _username,
                    "token": token,
                    "id": account.id,
                    "mail": account.mail,
                }
            )

        if "signout" in request.form:
            return json.dumps({"message": "processed"})

        if "account_change" in request.form:
            data.update(json.loads(request.form["account_change"]))
            _username = safe_string(data["user"])
            if token == "":
                return json.dumps({"message": "tokenNothing", "text": "トークン未提出"})
            if _username != "":
                if (
                    session.query(Account)
                    .filter(Account.user == _username, Account.id != token["id"])
                    .first()
                    is not None
                ):
                    return json.dumps({"message": "alreadyExist", "text": "既存の名前"})
            account = session.get(Account, token["id"])
            if account is None:
                return json.dumps(
                    {"message": "notExist", "text": "アカウントが存在しない"}
                )
            account.user = account.user if _username == "" else _username
            account.passhash = account.passhash if data["pass"] == "" else passhash
            account.mail = account.mail if data["mail"] == "" else data["mail"]
            session.commit()
            return json.dumps(
                {
                    "message": "processed",
                    "user": account.user,
                    "mail": account.mail,
                    "token": encoded_new_token,
                }
            )

        if "account_delete" in request.form:
            data.update(json.loads(request.form["account_delete"]))
            if token == "":
                return json.dumps({"message": "tokenNothing", "text": "トークン無し"})
            account = session.get(Account, token["id"])
            if account is None:
                return json.dumps(
                    {"message": "notExist", "text": "アカウントが存在しない"}
                )
            session.delete(account)
            session.commit()
            return json.dumps({"message": "processed"})

    return "404: nof found → main.html", 404


if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(os.path.dirname(os.path.join("./", __file__)))
    app = flask.Flask(__name__, template_folder="./", static_folder="./static/")
    app.config["MAX_CONTENT_LENGTH"] = 100000000
    os.makedirs("./tmp", exist_ok=True)

    @app.route("/", methods=["GET", "POST"])
    def py_show():
        try:
            return show(flask.request)
        except Exception as e:
            return "500 error⇒" + str(e), 500

    app.run()
