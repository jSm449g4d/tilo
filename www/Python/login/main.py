import json
import hashlib
import jwt
import time
import sys
import os
import re
import threading
import unicodedata

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

FUNC_NAME = "login"
RESERVED_NAME = ["GUEST", "HOST", "ANONYMOUS"]


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
        return HTMLResponse(html)
    return PlainTextResponse("404: nof found → main.html", status_code=404)


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


Base = declarative_base()


class Account(Base):
    __tablename__ = "account"
    __table_args__ = {"sqlite_autoincrement": True}
    id = Column(Integer, primary_key=True, autoincrement=True)
    user = Column(String, unique=True, nullable=False)
    passhash = Column(String, nullable=False)
    mail = Column(String, default="")
    timestamp = Column(Integer, nullable=False)
    lastlogin = Column(Integer, nullable=False)


Base.metadata.create_all(engine)


def safe_string(s, max_len=500, anti_directory_traversal=True):
    s = unicodedata.normalize("NFKC", str(s))
    if anti_directory_traversal:
        s = re.sub(r"\[.*\]|<.*>|/", "", s)
    s = re.sub(r"\\|;|\'|\"", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:max_len]


async def show(request: Request):
    if request.method == "GET":
        return get_response()
    if request.method != "POST":
        return PlainTextResponse("404: nof found → main.html", status_code=404)
    form = await request.form()
    if "info" not in form:
        return {"message": "notEnoughForm(info)"}
    _dataDict = json.loads(form["info"])
    token = ""
    if _dataDict["token"] != "":
        token = jwt.decode(_dataDict["token"], pyJWT_pass, algorithms=["HS256"])
        if token["timestamp"] + pyJWT_timeout < int(time.time()):
            return {"message": "tokenTimeout", "text": "JWT outDated"}
    passhash = ""
    if _dataDict["pass"] != "":
        passhash = hashlib.sha256(_dataDict["pass"].encode()).hexdigest()
    with SessionLocal() as session:
        if "login" in form:
            _dataDict.update(json.loads(form["login"]))
            _username = safe_string(_dataDict["user"])
            account = session.query(Account).filter_by(user=_username).first()
            if account is None:
                return {"message": "notExist", "text": "Account is not exist"}
            if account.passhash != passhash:
                return {"message": "wrongPass", "text": "Access Denied"}
            token = jwt.encode(
                {"id": account.id, "user": account.user, "timestamp": int(time.time())},
                pyJWT_pass,
                algorithm="HS256",
            )
            account.lastlogin = int(time.time())
            session.commit()
            return {
                "message": "processed",
                "user": account.user,
                "token": token,
                "id": account.id,
                "mail": account.mail,
            }

        if "signup" in form:
            _dataDict.update(json.loads(form["signup"]))
            _username = safe_string(_dataDict["user"])
            if session.query(Account).filter_by(user=_username).first() is not None:
                return {"message": "alreadyExist", "text": _username}
            if any(reserved in _username for reserved in RESERVED_NAME):
                return {"message": "reservedName", "text": str(RESERVED_NAME)}
            if _username == "guest":
                _username = "GUEST-" + str(int(time.time() * 1000))
                passhash = ""

            account = Account(
                user=_username,
                passhash=passhash,
                timestamp=int(time.time()),
                lastlogin=int(time.time()),
                mail="",
            )
            session.add(account)
            session.commit()
            token = jwt.encode(
                {"id": account.id, "user": account.user, "timestamp": int(time.time())},
                pyJWT_pass,
                algorithm="HS256",
            )
            return {
                "message": "processed",
                "user": _username,
                "token": token,
                "id": account.id,
                "mail": account.mail,
            }

        if token == "":
            return {"message": "tokenNothing", "text": "token is not exist"}

        if "account_change" in form:
            _dataDict.update(json.loads(form["account_change"]))
            _username = safe_string(_dataDict["user"])
            if (
                session.query(Account)
                .filter(Account.user == _username, Account.id != token["id"])
                .first()
                is not None
            ):
                return {"message": "alreadyExist", "text": "既存の名前"}
            account = session.get(Account, token["id"])
            if account is None:
                return {"message": "notExist", "text": "Account is not exist"}
            account.user = account.user if _username == "" else _username
            account.passhash = account.passhash if _dataDict["pass"] == "" else passhash
            account.mail = (
                account.mail if _dataDict["mail"] == "" else _dataDict["mail"]
            )
            account.lastlogin = int(time.time())
            session.commit()
            token = jwt.encode(
                {"id": account.id, "user": account.user, "timestamp": int(time.time())},
                pyJWT_pass,
                algorithm="HS256",
            )
            return {
                "message": "processed",
                "user": account.user,
                "token": token,
                "id": account.id,
                "mail": account.mail,
            }

        if "account_delete" in form:
            _dataDict.update(json.loads(form["account_delete"]))
            account = session.get(Account, token["id"])
            if account is None:
                return {"message": "notExist", "text": "アカウントが存在しない"}
            session.delete(account)
            session.commit()
            return {"message": "processed"}

        if "new_token" in form:
            _token = jwt.encode(
                {
                    "id": token["id"],
                    "user": token["user"],
                    "timestamp": int(time.time()),
                },
                pyJWT_pass,
                algorithm="HS256",
            )
            return {
                "message": "processed",
                "token": _token,
                "id": token["id"],
                "user": token["user"],
            }

    return PlainTextResponse("404: nof found → main.html", status_code=404)


class SalyRunner:
    def __init__(self):
        self._lock = threading.Lock()
        self._thread = None

    def start_once(self):
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()

    def _loop(self):
        while True:
            with SessionLocal() as session:
                cutoff = int(time.time()) - 86400
                session.query(Account).filter(
                    (Account.lastlogin < cutoff) & (Account.passhash == "")
                ).delete(synchronize_session=False)
                session.commit()
            time.sleep(43200)


saly = SalyRunner()
saly.start_once()

# isolation
if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(os.path.dirname(os.path.join("./", __file__)))

    app = FastAPI()
    os.makedirs("./tmp", exist_ok=True)

    @app.api_route("/", methods=["GET", "POST"])
    async def py_show(request: Request):
        try:
            return await show(request)
        except Exception as e:
            return PlainTextResponse("500 error→" + str(e), status_code=500)

    import uvicorn

    uvicorn.run("main:app")
