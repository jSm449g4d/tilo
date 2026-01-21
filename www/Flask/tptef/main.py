import json
import os
import sys
import time
import hashlib
import re
import unicodedata
import flask
import jwt
from sqlalchemy import Column, Integer, String, Text, create_engine, select, delete
from sqlalchemy.orm import declarative_base, sessionmaker

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

Base = declarative_base()


class TptefChat(Base):
    __tablename__ = "tptef_chat"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user = Column(Text, nullable=False)
    userid = Column(Integer, nullable=False)
    roomid = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    mode = Column(Text, nullable=False)
    timestamp = Column(Integer, nullable=False)


class TptefRoom(Base):
    __tablename__ = "tptef_room"
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
        
        with Session() as session:

            if "fetch" in request.form:
                _dataDict.update(json.loads(request.form["fetch"]))
                _roompasshash = _dataDict["roomKey"]
                if _dataDict["roomKey"] not in ["", "0"]:
                    _roompasshash = hashlib.sha256(
                        _dataDict["roomKey"].encode()
                    ).hexdigest()
                room = session.get(TptefRoom, _dataDict["roomid"])
                if room is None:
                    return json.dumps(
                        {"message": "notExist", "text": "部屋が不明"},
                        ensure_ascii=False,
                    )
                if room.userid != user_id and room.passhash and room.passhash != _roompasshash:
                    return json.dumps(
                        {"message": "wrongPass", "text": "アクセス拒否"},
                        ensure_ascii=False,
                    )
                chats = (
                    session.execute(
                        select(TptefChat).where(TptefChat.roomid == room.id)
                    )
                    .scalars()
                    .all()
                )
                session.commit()
                return json.dumps(
                    {
                        "message": "processed",
                        "chats": [
                            {c.name: getattr(chat, c.name) for c in chat.__table__.columns}
                            for chat in chats
                        ],
                        "room": {c.name: getattr(room, c.name) for c in room.__table__.columns},
                        "userid": room.userid,
                        "token": encoded_new_token,
                    },
                    ensure_ascii=False,
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
                room = session.get(TptefRoom, _dataDict["roomid"])
                if room is None:
                    return json.dumps(
                        {"message": "notExist", "text": "存在不明"}, ensure_ascii=False
                    )
                if room.passhash and room.passhash != _roompasshash:
                    return json.dumps(
                        {"message": "wrongPass", "text": "アクセス拒否"},
                        ensure_ascii=False,
                    )
                session.add(
                    TptefChat(
                        user=_dataDict["user"],
                        userid=user_id,
                        roomid=room.id,
                        text=_dataDict["text"],
                        mode="text",
                        timestamp=int(time.time()),
                    )
                )
                session.commit()
                return json.dumps({"message": "processed"}, ensure_ascii=False)

            if "upload" in request.files:
                _roompasshash = _dataDict["roomKey"]
                if _dataDict["roomKey"] not in ["", "0"]:
                    _roompasshash = hashlib.sha256(
                        _dataDict["roomKey"].encode()
                    ).hexdigest()
                if token == "":
                    return json.dumps({"message": "tokenNothing"}, ensure_ascii=False)
                room = session.get(TptefRoom, _dataDict["roomid"])
                if room is None:
                    return json.dumps(
                        {"message": "notExist", "text": "存在不明"}, ensure_ascii=False
                    )
                if room.passhash and room.passhash != _roompasshash:
                    return json.dumps(
                        {"message": "wrongPass", "text": "アクセス拒否"},
                        ensure_ascii=False,
                    )
                chat = TptefChat(
                    user=_dataDict["user"],
                    userid=user_id,
                    roomid=room.id,
                    text=request.files["upload"].filename,
                    mode="attachment",
                    timestamp=int(time.time()),
                )
                session.add(chat)
                request.files["upload"].save(
                    os.path.normpath(os.path.join(tmp_dir, safe_string(chat.id)))
                )
                session.commit()
                return json.dumps({"message": "processed"}, ensure_ascii=False)

            if "download" in request.form:
                _dataDict.update(json.loads(request.form["download"]))
                _roompasshash = _dataDict["roomKey"]
                if _dataDict["roomKey"] not in ["", "0"]:
                    _roompasshash = hashlib.sha256(
                        _dataDict["roomKey"].encode()
                    ).hexdigest()
                    room = session.get(TptefRoom, _dataDict["roomid"])
                if room is None:
                    return json.dumps(
                        {"message": "notExist", "text": "ファイルが不明"},
                        ensure_ascii=False,
                    )
                if room.passhash and room.passhash != _roompasshash:
                    return json.dumps(
                        {"message": "wrongPass", "text": "アクセス拒否"},
                        ensure_ascii=False,
                    )
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

            if "delete" in request.form:
                _dataDict.update(json.loads(request.form["delete"]))
                _roompasshash = _dataDict["roomKey"]
                if _dataDict["roomKey"] not in ["", "0"]:
                    _roompasshash = hashlib.sha256(
                        _dataDict["roomKey"].encode()
                    ).hexdigest()
                if token == "":
                    return json.dumps({"message": "tokenNothing"}, ensure_ascii=False)
                room = session.get(TptefRoom, _dataDict["roomid"])
                if room is None:
                    return json.dumps(
                        {"message": "notExist", "text": "発言が不明"},
                        ensure_ascii=False,
                    )
                if room.passhash and room.passhash != _roompasshash:
                    return json.dumps(
                        {"message": "wrongPass", "text": "アクセス拒否"},
                        ensure_ascii=False,
                    )
                session.execute(
                    delete(TptefChat).where(
                        TptefChat.id == _dataDict["chatid"],
                        TptefChat.userid == user_id,
                    )
                )
                _remove_file = os.path.normpath(
                    os.path.join(tmp_dir, safe_string(_dataDict["chatid"]))
                )
                if os.path.exists(_remove_file):
                    os.remove(_remove_file)
                session.commit()
                return json.dumps({"message": "processed"}, ensure_ascii=False)

            if "search" in request.form:
                _dataDict.update(json.loads(request.form["search"]))
                rooms = session.execute(select(TptefRoom)).scalars().all()
                session.commit()
                return json.dumps(
                    {
                        "message": "processed",
                        "rooms": [
                            {c.name: getattr(room, c.name) for c in room.__table__.columns}
                            for room in rooms
                        ],
                        "token": encoded_new_token,
                    },
                    ensure_ascii=False,
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
                room = session.execute(
                    select(TptefRoom).where(TptefRoom.room == _room_name)
                ).scalar_one_or_none()
                if room is not None:
                    return json.dumps(
                        {"message": "alreadyExisted", "text": "既存の部屋名"},
                        ensure_ascii=False,
                    )
                room = TptefRoom(
                    user=_dataDict["user"],
                    userid=user_id,
                    room=_room_name,
                    passhash=_roompasshash,
                    timestamp=int(time.time()),
                )
                session.add(room)
                session.commit()
                return json.dumps(
                    {
                        "message": "processed",
                        "room": {c.name: getattr(room, c.name) for c in room.__table__.columns},
                    },
                    ensure_ascii=False,
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
                room = session.get(TptefRoom, _dataDict["roomid"])
                if room is None:
                    return json.dumps(
                        {"message": "notExist", "text": "存在無し"}, ensure_ascii=False
                    )
                if room.userid != user_id:
                    return json.dumps(
                        {"message": "youerntOwner", "text": "アクセス拒否"},
                        ensure_ascii=False,
                    )
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
                    _remove_file = os.path.normpath(
                        os.path.join(tmp_dir, str(chat.id))
                    )
                    if os.path.exists(_remove_file):
                        os.remove(_remove_file)
                session.execute(delete(TptefChat).where(TptefChat.roomid == room.id))
                session.execute(
                    delete(TptefRoom).where(
                        TptefRoom.userid == user_id, TptefRoom.id == _dataDict["roomid"]
                    )
                )
                session.commit()
                return json.dumps({"message": "processed"}, ensure_ascii=False)
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
