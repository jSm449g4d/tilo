from argon2 import PasswordHasher
import json
import os
import re
import shutil
import asyncio
import sys
import time
import unicodedata
import threading
from pathlib import Path
from urllib.parse import quote

import jwt
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse
from sqlalchemy import Column, Integer, Text, create_engine, delete, select, event
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.orm import Session as SASession

FUNC_NAME = "tptef"
ph = PasswordHasher()


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
    db_dir = keys.get("db", db_dir)
    pyJWT_pass = keys.get("pyJWT_pass", pyJWT_pass)
    pyJWT_timeout = keys.get("pyJWT_timeout", pyJWT_timeout)

Base = declarative_base()


class TptefChat(Base):
    __tablename__ = "tptef_chat"
    __table_args__ = {"sqlite_autoincrement": True}
    id = Column(Integer, primary_key=True, autoincrement=True)
    user = Column(Text, nullable=False)
    userid = Column(Integer, nullable=False)
    roomid = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    filename = Column(Text, nullable=False)
    timestamp = Column(Integer, nullable=False)


class TptefRoom(Base):
    __tablename__ = "tptef_room"
    __table_args__ = {"sqlite_autoincrement": True}
    id = Column(Integer, primary_key=True, autoincrement=True)
    user = Column(Text, nullable=False)
    userid = Column(Integer, nullable=False)
    name = Column(Text, unique=True, nullable=False)
    passhash = Column(Text, default="")
    timestamp = Column(Integer, nullable=False)


engine = create_engine(f"sqlite:///{db_dir}", future=True)
Session = sessionmaker(bind=engine, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base.metadata.create_all(engine)


def safe_string(_s, _max=500, _anti_directory_traversal=True) -> str:
    _s = unicodedata.normalize("NFKC", str(_s))
    if _anti_directory_traversal:
        _s = re.sub(r"\[.*\]|<.*>|/", "", _s)
    _s = re.sub(r"\\|;|\'|\"", "", _s)
    _s = re.sub(r"\s+", " ", _s).strip()
    return _s[:_max]


def verify_pass(_hash, _pass) -> bool:
    if _hash == "":
        return True
    try:
        if ph.verify(_hash, _pass):
            return True
    except:
        return False
    return False


def pass2hash(_hash) -> str:
    if _hash == "":
        return ""
    return ph.hash(_hash)


def parse_auth_context(_token_i=""):
    try:
        if _token_i == "":
            raise Exception("noToken")
        _token = jwt.decode(_token_i, pyJWT_pass, algorithms=["HS256"])
        if _token["timestamp"] + pyJWT_timeout < int(time.time()):
            raise Exception("Timeout")
        return _token, ""
    except Exception as e:
        return {}, str(e)


def check_roomkey(_room: TptefRoom, _user_id: int, _room_key: str):
    if _room.userid == _user_id:
        return True
    return verify_pass(_room.passhash, _room_key)


async def show(request: Request):
    if request.method == "GET":
        return get_response()

    if request.method != "POST":
        return PlainTextResponse("404: nof found → main.html", status_code=404)

    form = await request.form()
    if "info" not in form:
        return {"message": "notEnoughForm(info)"}
    _dataDict = json.loads(form["info"])
    token, _token_error = parse_auth_context(_dataDict["token"])
    if _token_error != "":
        return {"message": "JWT_Error", "text": _token_error}
    with Session() as session:
        if "create" in form:
            _dataDict.update(json.loads(form["create"]))
            _room_name = safe_string(
                _dataDict["roomName"], _anti_directory_traversal=False
            )
            _room = session.execute(
                select(TptefRoom).where(TptefRoom.name == _room_name)
            ).scalar_one_or_none()
            if _room is not None:
                return {"message": "alreadyExisted", "text": "既存の部屋名"}
            _room = TptefRoom(
                user=token["user"],
                userid=token["id"],
                name=_room_name,
                passhash=pass2hash(_dataDict["roomKeyhole"]),
                timestamp=int(time.time()),
            )
            session.add(_room)
            session.info["search_plz"] = True
            session.commit()
            return {
                "message": "processed",
                "room": {
                    c.name: getattr(_room, c.name) for c in _room.__table__.columns
                },
            }

        room = session.get(TptefRoom, _dataDict["roomid"])
        if room is None:
            return {"message": "notExist", "text": "the room is not exist"}
        if not check_roomkey(room, token["id"], _dataDict["roomKey"]):
            return {"message": "wrongPass", "text": "Access Denied"}

        if "remark" in form:
            _dataDict.update(json.loads(form["remark"]))
            _fn = ""
            if "upload" in form:
                _fn = form["upload"].filename
            _chat = TptefChat(
                user=token["user"],
                userid=token["id"],
                roomid=room.id,
                text=_dataDict["text"],
                filename=safe_string(_fn),
                timestamp=int(time.time()),
            )
            session.add(_chat)
            session.flush()
            session.info["fetch_plz"] = True
            session.commit()
            if _fn == "":
                return {"message": "processed"}
            _target_file = os.path.normpath(os.path.join(tmp_dir, str(_chat.id)))
            with open(_target_file, "wb") as out_f:
                shutil.copyfileobj(form["upload"].file, out_f)
            return {"message": "processed"}

        if "download" in form:
            _dataDict.update(json.loads(form["download"]))
            _chat = session.get(TptefChat, _dataDict["chatid"])
            if _chat is None:
                return {"message": "notExist", "text": "Chat is not exist"}
            if _chat.roomid != room.id:
                return {"message": "Error", "text": "Access Denied"}
            _target_file = os.path.normpath(os.path.join(tmp_dir, str(_chat.id)))
            if os.path.exists(_target_file):
                return FileResponse(
                    _target_file,
                    headers={
                        "Content-Disposition": "attachment; filename*=UTF-8''"
                        + quote(_chat.filename)
                    },
                )
            return {"message": "notExist", "text": "ファイル不明"}

        if "delete" in form:
            _dataDict.update(json.loads(form["delete"]))
            _chat = session.get(TptefChat, _dataDict["chatid"])
            if _chat is None:
                return {"message": "notExist", "text": "Chat is not exist"}
            if _chat.roomid != room.id:
                return {"message": "Error", "text": "Access Denied"}
            if room.userid != token["id"] and _chat.userid != token["id"]:
                return {
                    "message": "noAuthority",
                    "text": "You don't have the right to delete",
                }
            _remove_file = os.path.normpath(os.path.join(tmp_dir, str(_chat.id)))
            if os.path.exists(_remove_file):
                os.remove(_remove_file)
            session.delete(_chat)
            session.info["fetch_plz"] = True
            session.commit()
            return {"message": "processed"}

        if "destroy" in form:
            _dataDict.update(json.loads(form["destroy"]))
            if room.userid != token["id"]:
                return {
                    "message": "noAuthority",
                    "text": "You don't have the right to delete",
                }
            chats = (
                session.execute(select(TptefChat).where(TptefChat.roomid == room.id))
                .scalars()
                .all()
            )
            for chat in chats:
                _remove_file = os.path.normpath(os.path.join(tmp_dir, str(chat.id)))
                if os.path.exists(_remove_file):
                    os.remove(_remove_file)
            session.execute(delete(TptefChat).where(TptefChat.roomid == room.id))
            session.delete(room)
            session.info["search_plz"] = True
            session.commit()
            return {"message": "processed"}

    return PlainTextResponse("404: nof found → main.html", status_code=404)


class ConnectionManager:
    def __init__(self):
        self.client: dict[WebSocket, dict] = {}

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.client[ws] = {}

    def disconnect(self, ws: WebSocket) -> None:
        self.client.pop(ws, None)

    async def set_form(self, ws: WebSocket) -> None:
        _form = await ws.receive_json()
        if not isinstance(_form, dict):
            raise ValueError("JSON object (dict) required")
        self.client[ws] = _form
        await self.response_fs(ws)

    async def response_fs(self, ws):
        _form = self.client[ws]
        token, _token_error = parse_auth_context(_form["token"])
        if _token_error != "":
            await ws.send_json({"message": "JWT_Error", "text": _token_error})
            return
        with Session() as session:
            if "fetch" in _form:
                room = session.get(TptefRoom, _form["roomid"])
                if room is None:
                    return
                if not check_roomkey(room, token["id"], _form["roomKey"]):
                    await ws.send_json(
                        {"message": "wrongPass", "text": "Access Denied"}
                    )
                    return
                stmt = select(TptefChat).where(TptefChat.roomid == room.id)
                chats = session.execute(stmt).scalars().all()
                _chats = [
                    {c.key: getattr(chat, c.key) for c in chat.__mapper__.column_attrs}
                    for chat in chats
                ]
                await ws.send_json({"message": "processed", "chats": _chats})
            if "search" in _form:
                _frest = (
                    (TptefRoom.userid == token["id"]) | (TptefRoom.passhash == "")
                ) & (TptefRoom.name.ilike(f"%{_form['search']}%"))
                stmt = (
                    select(TptefRoom)
                    .where(_frest | (TptefRoom.name == _form["search"]))
                    .order_by(TptefRoom.timestamp.desc())
                    .limit(100)
                )
                rooms = session.execute(stmt).scalars().all()
                _rooms = [
                    {c.key: getattr(room, c.key) for c in room.__mapper__.column_attrs}
                    for room in rooms
                ]
                await ws.send_json(
                    {
                        "message": "processed",
                        "rooms": _rooms,
                    }
                )

    async def distributes(self):
        for ws in list(self.client.keys()):
            try:
                await self.response_fs(ws)
            except Exception:
                self.disconnect(ws)


manager = ConnectionManager()


async def ws_endpoint(ws: WebSocket):
    try:
        await manager.connect(ws)
        while True:
            await manager.set_form(ws)
    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception:
        manager.disconnect(ws)
        try:
            await ws.close(code=1011)
        except Exception:
            pass


@event.listens_for(SASession, "after_commit")
def on_after_commit(session: SASession):
    if session.info.get("fetch_plz"):
        loop = asyncio.get_running_loop()
        loop.create_task(manager.distributes())
    if session.info.get("search_plz"):
        loop = asyncio.get_running_loop()
        loop.create_task(manager.distributes())


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
                session.query(TptefRoom).filter(
                    (TptefRoom.timestamp < cutoff) & (TptefRoom.user.ilike("%GUEST%"))
                ).delete(synchronize_session=False)
                session.commit()
                session.query(TptefChat).filter(
                    ~session.query(TptefRoom.id)
                    .filter(TptefRoom.id == TptefChat.roomid)
                    .exists()
                ).delete(synchronize_session=False)
                session.commit()
                files = [p.name for p in Path(tmp_dir).iterdir() if p.is_file()]
                for f in files:
                    if not f.isdigit():
                        continue
                    _fileparentchat = session.get(TptefChat, int(f))
                    if _fileparentchat is None:
                        _remove_file = os.path.normpath(os.path.join(tmp_dir, str(f)))
                        if os.path.exists(_remove_file):
                            os.remove(_remove_file)
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
