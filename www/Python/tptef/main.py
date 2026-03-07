import hashlib
import json
import os
import re
import shutil
import asyncio
import sys
import time
import unicodedata
from urllib.parse import quote

import jwt
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse
from sqlalchemy import Column, Integer, Text, create_engine, delete, select, event
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.orm import Session as SASession

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
        if "db" in keys:
            db_dir = keys["db"]
        if "pyJWT_pass" in keys:
            pyJWT_pass = keys["pyJWT_pass"]
        if "pyJWT_timeout" in keys:
            pyJWT_timeout = keys["pyJWT_timeout"]

Base = declarative_base()


class TptefChat(Base):
    __tablename__ = "tptef_chat"
    __table_args__ = {"sqlite_autoincrement": True}
    id = Column(Integer, primary_key=True, autoincrement=True)
    user = Column(Text, nullable=False)
    userid = Column(Integer, nullable=False)
    roomid = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    mode = Column(Text, nullable=False)
    timestamp = Column(Integer, nullable=False)


class TptefRoom(Base):
    __tablename__ = "tptef_room"
    __table_args__ = {"sqlite_autoincrement": True}
    id = Column(Integer, primary_key=True, autoincrement=True)
    user = Column(Text, nullable=False)
    userid = Column(Integer, nullable=False)
    room = Column(Text, unique=True, nullable=False)
    passhash = Column(Text, default="")
    timestamp = Column(Integer, nullable=False)


engine = create_engine(f"sqlite:///{db_dir}", future=True)
Session = sessionmaker(bind=engine, future=True)
Base.metadata.create_all(engine)


def safe_string(_s, _max=500, _anti_directory_traversal=True):
    _s = unicodedata.normalize("NFKC", str(_s))
    if _anti_directory_traversal:
        _s = re.sub(r"\[.*\]|<.*>|/", "", _s)
    _s = re.sub(r"\\|;|\'|\"", "", _s)
    _s = re.sub(r"\s+", " ", _s).strip()
    return _s[:_max]


def parse_auth_context(_token_i="", _room_key_i=""):
    if _token_i == "":
        return {}, ""
    try:
        _token = jwt.decode(_token_i, pyJWT_pass, algorithms=["HS256"])
        if _token["timestamp"] + pyJWT_timeout < int(time.time()):
            raise Exception("Timeout")
        _roompasshash = ""
        if _room_key_i != "":
            _roompasshash = hashlib.sha256(_room_key_i.encode()).hexdigest()
        return _token, _roompasshash
    except Exception as e:
        return {}, str(e)


def check_roomkey(_room: TptefRoom, _user_id: int, _roompasshash: str):
    if _room.userid == _user_id or _room.passhash == "":
        return True
    return _room.passhash == _roompasshash


async def show(request: Request):
    if request.method == "GET":
        return get_response()

    if request.method != "POST":
        return PlainTextResponse("404: nof found → main.html", status_code=404)

    form = await request.form()
    if "info" not in form:
        return {"message": "notEnoughForm(info)"}
    _dataDict = json.loads(form["info"])
    token, roompasshash = parse_auth_context(_dataDict["token"], _dataDict["roomKey"])
    if roompasshash == "Timeout":
        return {"message": "tokenTimeout", "text": "JWT outDated"}
    if token == {}:
        return {"message": "tokenNothing", "text": "JWT is not exist"}
    with Session() as session:
        if "create" in form:
            _dataDict.update(json.loads(form["create"]))
            _room_name = safe_string(_dataDict["room"], _anti_directory_traversal=False)
            room = session.execute(
                select(TptefRoom).where(TptefRoom.room == _room_name)
            ).scalar_one_or_none()
            if room is not None:
                return {"message": "alreadyExisted", "text": "既存の部屋名"}
            room = TptefRoom(
                user=token["user"],
                userid=token["id"],
                room=_room_name,
                passhash=roompasshash,
                timestamp=int(time.time()),
            )
            session.add(room)
            session.info["search_plz"] = True
            session.commit()
            return {
                "message": "processed",
                "room": {c.name: getattr(room, c.name) for c in room.__table__.columns},
            }

        room = session.get(TptefRoom, _dataDict["roomid"])
        if room is None:
            session.info["search_plz"] = True
            session.commit()
            return {"message": "notExist", "text": "the room is not exist"}
        if not check_roomkey(room, token["id"], roompasshash):
            return {"message": "wrongPass", "text": "Access Denied"}

        if "remark" in form:
            _dataDict.update(json.loads(form["remark"]))
            session.add(
                TptefChat(
                    user=token["user"],
                    userid=token["id"],
                    roomid=room.id,
                    text=_dataDict["text"],
                    mode="text",
                    timestamp=int(time.time()),
                )
            )
            session.info["fetch_plz"] = True
            session.commit()
            return {"message": "processed"}

        if upload := form.get("upload"):
            chat = TptefChat(
                user=token["user"],
                userid=token["id"],
                roomid=room.id,
                text=upload.filename,
                mode="attachment",
                timestamp=int(time.time()),
            )
            session.add(chat)
            session.flush()
            with open(
                os.path.normpath(os.path.join(tmp_dir, safe_string(chat.id))), "wb"
            ) as out_f:
                shutil.copyfileobj(upload.file, out_f)
            session.info["fetch_plz"] = True
            session.commit()
            return {"message": "processed"}

        if "download" in form:
            _dataDict.update(json.loads(form["download"]))
            _target_file = os.path.normpath(
                os.path.join(tmp_dir, safe_string(_dataDict["chatid"]))
            )
            if os.path.exists(_target_file):
                return FileResponse(
                    _target_file,
                    headers={
                        "Content-Disposition": f"{"attachment"}; filename*=UTF-8''{quote(_dataDict['filename'])}"
                    },
                )
            return {"message": "notExist", "text": "ファイル不明"}

        if "delete" in form:
            _dataDict.update(json.loads(form["delete"]))
            _chat = session.get(TptefChat, _dataDict["chatid"])
            if _chat is None:
                session.info["fetch_plz"] = True
                session.commit()
                return {"message": "notExist", "text": "Chat is not exist"}
            if room.userid != token["id"] and _chat.userid != token["id"]:
                return {
                    "message": "noAuthority",
                    "text": "You don't have the right to delete",
                }
            session.execute(
                delete(TptefChat).where(TptefChat.id == _dataDict["chatid"])
            )
            _remove_file = os.path.normpath(
                os.path.join(tmp_dir, safe_string(_dataDict["chatid"]))
            )
            if os.path.exists(_remove_file):
                os.remove(_remove_file)
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
                session.execute(
                    select(TptefChat).where(
                        TptefChat.roomid == room.id, TptefChat.mode == "attachment"
                    )
                )
                .scalars()
                .all()
            )
            for chat in chats:
                _remove_file = os.path.normpath(os.path.join(tmp_dir, str(chat.id)))
                if os.path.exists(_remove_file):
                    os.remove(_remove_file)
            session.execute(delete(TptefChat).where(TptefChat.roomid == room.id))
            session.execute(
                delete(TptefRoom).where(
                    TptefRoom.userid == token["id"],
                    TptefRoom.id == _dataDict["roomid"],
                )
            )
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

        token, roompasshash = parse_auth_context(_form["token"], _form["roomKey"])
        if roompasshash == "Timeout":
            return
        if token == {}:
            return
        with Session() as session:
            if "fetch" in _form:
                room = session.get(TptefRoom, _form["roomid"])
                if room is None:
                    return
                if not check_roomkey(room, token["id"], roompasshash):
                    return
                stmt = select(TptefChat).where(TptefChat.roomid == room.id)
                chats = session.execute(stmt).scalars().all()
                _chats = [
                    {c.key: getattr(chat, c.key) for c in chat.__mapper__.column_attrs}
                    for chat in chats
                ]
                _room = {c.name: getattr(room, c.name) for c in room.__table__.columns}
                await ws.send_json({"message": "processed", "chats": _chats})
            if "search" in _form:
                stmt = (
                    select(TptefRoom)
                    .where(
                        (TptefRoom.userid == token["id"])
                        | (TptefRoom.passhash == "")
                        | (TptefRoom.passhash == roompasshash)
                    )
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