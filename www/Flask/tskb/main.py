import json
import os
import sys
import time
import glob
import unicodedata
import re
import flask
import jwt
from PIL import Image
from sqlalchemy import Column, Integer, Text, Float, create_engine, select, delete
from sqlalchemy.orm import declarative_base, sessionmaker

FUNC_NAME = "tskb"


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
os.makedirs(tmp_dir + "combination/", exist_ok=True)
os.makedirs(tmp_dir + "material/", exist_ok=True)
key_dir = "./keys/"
os.makedirs(key_dir + "tskb/", exist_ok=True)
db_dir = "./tmp/sqlite.db"
pyJWT_pass = "test"
pyJWT_timeout = 3600
keys = {}
if os.path.exists(key_dir + "keys.json"):
    with open(key_dir + "keys.json") as f:
        keys = json.load(f)
        if "db" in keys:
            db_dir = keys["db"]
        if "pyJWT_pass" in keys:
            pyJWT_pass = keys["pyJWT_pass"]
        if "pyJWT_timeout" in keys:
            pyJWT_timeout = keys["pyJWT_timeout"]

Base = declarative_base()


class TskbCombination(Base):
    __tablename__ = "tskb_combination"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, unique=True, nullable=False)
    tag = Column(Text, default="")
    description = Column(Text, default="")
    userid = Column(Integer, nullable=False)
    user = Column(Text, nullable=False)
    passhash = Column(Text, default="")
    timestamp = Column(Integer, nullable=False)
    img = Column(Text, default="")
    contents = Column(Text, nullable=False)


class TskbMaterial(Base):
    __tablename__ = "tskb_material"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Text, unique=True, nullable=False)
    tag = Column(Text, default="")
    description = Column(Text, default="")
    userid = Column(Integer, nullable=False)
    user = Column(Text, nullable=False)
    passhash = Column(Text, default="")
    timestamp = Column(Integer, nullable=False)
    img = Column(Text, default="")
    unit = Column(Float, default=100)
    cost = Column(Float, default=0)
    carbo = Column(Float, default=0)
    fiber = Column(Float, default=0)
    protein = Column(Float, default=0)
    fat = Column(Float, default=0)
    saturated_fat = Column(Float, default=0)
    n3 = Column(Float, default=0)
    DHA_EPA = Column(Float, default=0)
    n6 = Column(Float, default=0)
    ca = Column(Float, default=0)
    cl = Column(Float, default=0)
    cr = Column(Float, default=0)
    cu = Column(Float, default=0)
    i = Column(Float, default=0)
    fe = Column(Float, default=0)
    mg = Column(Float, default=0)
    mn = Column(Float, default=0)
    mo = Column(Float, default=0)
    p = Column(Float, default=0)
    k = Column(Float, default=0)
    se = Column(Float, default=0)
    na = Column(Float, default=0)
    zn = Column(Float, default=0)
    va = Column(Float, default=0)
    vb1 = Column(Float, default=0)
    vb2 = Column(Float, default=0)
    vb3 = Column(Float, default=0)
    vb5 = Column(Float, default=0)
    vb6 = Column(Float, default=0)
    vb7 = Column(Float, default=0)
    vb9 = Column(Float, default=0)
    vb12 = Column(Float, default=0)
    vc = Column(Float, default=0)
    vd = Column(Float, default=0)
    ve = Column(Float, default=0)
    vk = Column(Float, default=0)
    colin = Column(Float, default=0)
    kcal = Column(Float, default=0)


engine = create_engine(f"sqlite:///{db_dir}", future=True)
Session = sessionmaker(bind=engine, future=True)
Base.metadata.create_all(engine)


def load_reference_file():
    _reference_files = glob.glob(key_dir + "tskb/" + "*.json")
    for _filename in _reference_files:
        with open(_filename, "r", encoding="utf-8") as _f:
            _updata_dicts = json.loads(_f.read())
            with Session() as session:
                for _updata_dict in _updata_dicts:
                    _material = session.execute(
                        select(TskbMaterial).where(
                            TskbMaterial.name == safe_string(_updata_dict["name"])
                        )
                    ).scalar_one_or_none()
                    if _material is None:
                        _material = TskbMaterial(
                            name=safe_string(_updata_dict["name"]),
                            userid=0,
                            user="admin",
                            passhash="",
                            timestamp=int(time.time()),
                        )
                        session.add(_material)
                        session.flush()
                    _material_dict = {c.name: getattr(_material, c.name) for c in _material.__table__.columns}
                    _material_dict.update(_updata_dict)
                    _material.name = safe_string(_material_dict["name"])
                    _material.tag = safe_string(_material_dict.get("tag", ""))
                    _material.description = safe_string(
                        _material_dict.get("description", ""),
                        _anti_directory_traversal=False,
                    )
                    _material.userid = 0
                    _material.user = "admin"
                    _material.passhash = _material_dict.get("passhash", "")
                    _material.timestamp = _material_dict.get("timestamp", _material.timestamp)
                    _material.unit = isfloat(_material_dict.get("unit", _material.unit))
                    if _material.unit < 1:
                        _material.unit = 1
                    _material.cost = isfloat(_material_dict.get("cost", _material.cost))
                    _material.carbo = isfloat(_material_dict.get("carbo", _material.carbo))
                    _material.fiber = isfloat(_material_dict.get("fiber", _material.fiber))
                    _material.protein = isfloat(_material_dict.get("protein", _material.protein))
                    _material.fat = isfloat(_material_dict.get("fat", _material.fat))
                    _material.saturated_fat = isfloat(
                        _material_dict.get("saturated_fat", _material.saturated_fat)
                    )
                    _material.n3 = isfloat(_material_dict.get("n3", _material.n3))
                    _material.DHA_EPA = isfloat(_material_dict.get("DHA_EPA", _material.DHA_EPA))
                    _material.n6 = isfloat(_material_dict.get("n6", _material.n6))
                    _material.ca = isfloat(_material_dict.get("ca", _material.ca))
                    _material.cl = isfloat(_material_dict.get("cl", _material.cl))
                    _material.cr = isfloat(_material_dict.get("cr", _material.cr))
                    _material.cu = isfloat(_material_dict.get("cu", _material.cu))
                    _material.i = isfloat(_material_dict.get("i", _material.i))
                    _material.fe = isfloat(_material_dict.get("fe", _material.fe))
                    _material.mg = isfloat(_material_dict.get("mg", _material.mg))
                    _material.mn = isfloat(_material_dict.get("mn", _material.mn))
                    _material.mo = isfloat(_material_dict.get("mo", _material.mo))
                    _material.p = isfloat(_material_dict.get("p", _material.p))
                    _material.k = isfloat(_material_dict.get("k", _material.k))
                    _material.se = isfloat(_material_dict.get("se", _material.se))
                    _material.na = isfloat(_material_dict.get("na", _material.na))
                    _material.zn = isfloat(_material_dict.get("zn", _material.zn))
                    _material.va = isfloat(_material_dict.get("va", _material.va))
                    _material.vb1 = isfloat(_material_dict.get("vb1", _material.vb1))
                    _material.vb2 = isfloat(_material_dict.get("vb2", _material.vb2))
                    _material.vb3 = isfloat(_material_dict.get("vb3", _material.vb3))
                    _material.vb5 = isfloat(_material_dict.get("vb5", _material.vb5))
                    _material.vb6 = isfloat(_material_dict.get("vb6", _material.vb6))
                    _material.vb7 = isfloat(_material_dict.get("vb7", _material.vb7))
                    _material.vb9 = isfloat(_material_dict.get("vb9", _material.vb9))
                    _material.vb12 = isfloat(_material_dict.get("vb12", _material.vb12))
                    _material.vc = isfloat(_material_dict.get("vc", _material.vc))
                    _material.vd = isfloat(_material_dict.get("vd", _material.vd))
                    _material.ve = isfloat(_material_dict.get("ve", _material.ve))
                    _material.vk = isfloat(_material_dict.get("vk", _material.vk))
                    _material.colin = isfloat(_material_dict.get("colin", _material.colin))
                    _material.kcal = isfloat(_material_dict.get("kcal", _material.kcal))
                session.commit()


def isfloat(_s):
    try:
        _f = round(float(_s), 4)
    except ValueError:
        return 0
    else:
        return _f


def safe_string(_s, _max=500, _anti_directory_traversal=True):
    _s = unicodedata.normalize("NFKC", str(_s))
    if _anti_directory_traversal:
        _s = re.sub(r"\[.*\]|<.*>|/", "", _s)
    _s = re.sub(r"\\|;|\'|\"", "", _s)
    _s = re.sub(r"\s+", " ", _s).strip()
    return _s[:_max]


RECORD_RETURN_MAX = 100
load_reference_file()


NUM_FIELDS = [
    "unit",
    "cost",
    "carbo",
    "fiber",
    "protein",
    "fat",
    "saturated_fat",
    "n3",
    "DHA_EPA",
    "n6",
    "ca",
    "cl",
    "cr",
    "cu",
    "i",
    "fe",
    "mg",
    "mn",
    "mo",
    "p",
    "k",
    "se",
    "na",
    "zn",
    "va",
    "vb1",
    "vb2",
    "vb3",
    "vb5",
    "vb6",
    "vb7",
    "vb9",
    "vb12",
    "vc",
    "vd",
    "ve",
    "vk",
    "colin",
    "kcal",
]


def show(request):
    if request.method == "GET":
        _query = request.args
        # fetch combination image
        if "combination_imgid" in _query:
            _target_file = os.path.normpath(
                os.path.join(
                    tmp_dir + "combination/",
                    safe_string(_query["combination_imgid"], 10) + ".png",
                )
            )
            if os.path.exists(_target_file):
                return flask.send_file(
                    _target_file,
                    mimetype="image/png",
                )
            return json.dumps(
                {"message": "notExist", "text": "ファイル無"}, ensure_ascii=False
            )
        return get_response()
    if request.method == "POST":
        if "info" not in request.form:
            return json.dumps(
                {"message": "notEnoughForm(info)", "text": "INFOフォーム無し"},
                ensure_ascii=False,
            )
        _dataDict = json.loads(request.form["info"])
        token = ""
        encoded_new_token = token
        if _dataDict["token"] != "":
            token = jwt.decode(_dataDict["token"], pyJWT_pass, algorithms=["HS256"])
            if token["timestamp"] + pyJWT_timeout < int(time.time()):
                return json.dumps(
                    {"message": "tokenTimeout", "text": "JWT期限切れ_要再ログイン"},
                    ensure_ascii=False,
                )
            encoded_new_token = jwt.encode(
                {"id": token["id"], "timestamp": int(time.time())},
                pyJWT_pass,
                algorithm="HS256",
            )

        with Session() as session:
            if "listtag" in request.form:
                _dataDict.update(json.loads(request.form["listtag"]))

                _tags = {}
                for result in session.execute(
                    select(TskbMaterial.tag).where(TskbMaterial.passhash == "")
                ).all():
                    _tag = result[0]
                    if _tag == "":
                        continue
                    if _tag not in _tags:
                        _tags[_tag] = 0
                    _tags[_tag] += 1
                _tags_list = sorted(_tags.items(), key=lambda x: x[1], reverse=True)
                _tags = [_dict[0] for _dict in _tags_list]
                return json.dumps(
                    {
                        "message": "processed",
                        "tags": _tags,
                    },
                    ensure_ascii=False,
                )

            if "explore" in request.form:
                _dataDict.update(json.loads(request.form["explore"]))
                _userid = -1
                if token != "":
                    _userid = token["id"]
                _material_offset = 0
                if "offset" in _dataDict:
                    _material_offset = int(_dataDict["offset"])
                match _dataDict["search_radio"]:
                    case "name":
                        _materials = (
                            session.execute(
                                select(TskbMaterial)
                                .where(
                                    TskbMaterial.name.like(
                                        "%" + _dataDict["keyword"] + "%"
                                    ),
                                    TskbMaterial.passhash == "",
                                )
                                .limit(RECORD_RETURN_MAX)
                                .offset(RECORD_RETURN_MAX * _material_offset)
                            )
                            .scalars()
                            .all()
                        )
                        return json.dumps(
                            {
                                "message": "processed",
                                "materials": [
                                    {c.name: getattr(m, c.name) for c in m.__table__.columns}
                                    for m in _materials
                                ],
                                "token": encoded_new_token,
                            },
                            ensure_ascii=False,
                        )
                    case "tag":
                        _materials = (
                            session.execute(
                                select(TskbMaterial)
                                .where(
                                    TskbMaterial.tag.like(
                                        "%" + _dataDict["keyword"] + "%"
                                    ),
                                    TskbMaterial.passhash == "",
                                )
                                .limit(RECORD_RETURN_MAX)
                                .offset(RECORD_RETURN_MAX * _material_offset)
                            )
                            .scalars()
                            .all()
                        )
                        return json.dumps(
                            {
                                "message": "processed",
                                "materials": [
                                    {c.name: getattr(m, c.name) for c in m.__table__.columns}
                                    for m in _materials
                                ],
                                "token": encoded_new_token,
                            },
                            ensure_ascii=False,
                        )
                    case "private":
                        _materials = (
                            session.execute(
                                select(TskbMaterial)
                                .where(
                                    TskbMaterial.name.like(
                                        "%" + _dataDict["keyword"] + "%"
                                    ),
                                    TskbMaterial.userid == _userid,
                                )
                                .limit(RECORD_RETURN_MAX)
                                .offset(RECORD_RETURN_MAX * _material_offset)
                            )
                            .scalars()
                            .all()
                        )
                        return json.dumps(
                            {
                                "message": "processed",
                                "materials": [
                                    {c.name: getattr(m, c.name) for c in m.__table__.columns}
                                    for m in _materials
                                ],
                                "token": encoded_new_token,
                            },
                            ensure_ascii=False,
                        )

            if "fetch" in request.form:
                _dataDict.update(json.loads(request.form["fetch"]))
                _userid = -1
                if token != "":
                    _userid = token["id"]
                _combination = session.get(TskbCombination, _dataDict["combinationid"])
                if _combination is None:
                    return json.dumps(
                        {"message": "notExist", "text": "レシピが不明"},
                        ensure_ascii=False,
                    )
                if _combination.passhash != "":
                    if _combination.userid != _userid:
                        return json.dumps(
                            {"message": "wrongPass", "text": "アクセス拒否"},
                            ensure_ascii=False,
                        )
                _contents = json.loads(_combination.contents)
                _materials = []
                for _key in _contents.keys():
                    _material = session.get(TskbMaterial, int(_key))
                    if _material is None:
                        continue
                    if _material.passhash != "":
                        if _material.userid != _userid:
                            continue
                    _materials.append(
                        {c.name: getattr(_material, c.name) for c in _material.__table__.columns}
                    )
                _requirements = (
                    session.execute(
                        select(TskbMaterial)
                        .where(
                            TskbMaterial.tag == "Requirements",
                            TskbMaterial.passhash == "",
                            TskbMaterial.userid == 0,
                        )
                        .limit(20)
                    )
                    .scalars()
                    .all()
                )
                return json.dumps(
                    {
                        "message": "processed",
                        "materials": _materials,
                        "combination": {
                            c.name: getattr(_combination, c.name)
                            for c in _combination.__table__.columns
                        },
                        "requirements": [
                            {c.name: getattr(r, c.name) for c in r.__table__.columns}
                            for r in _requirements
                        ],
                        "token": encoded_new_token,
                    },
                    ensure_ascii=False,
                )

            if "register" in request.form:
                _dataDict.update(json.loads(request.form["register"]))
                if token == "":
                    return json.dumps(
                        {"message": "tokenNothing", "text": "JWT未提出"}, ensure_ascii=False
                    )
                _passhash = ""
                if _dataDict["privateFlag"] is True:
                    _passhash = "0"
                _material = session.execute(
                    select(TskbMaterial).where(
                        TskbMaterial.name == safe_string(_dataDict["name"])
                    )
                ).scalar_one_or_none()
                if _material is not None:
                    return json.dumps(
                        {"message": "alreadyExisted", "text": "既存の名前"}
                    )
                _material = TskbMaterial(
                    name=safe_string(_dataDict["name"]),
                    tag=safe_string(_dataDict["tag"]),
                    description=safe_string(
                        _dataDict["description"], _anti_directory_traversal=False
                    ),
                    userid=token["id"],
                    user=_dataDict["user"],
                    passhash=_passhash,
                    timestamp=int(time.time()),
                )
                session.add(_material)
                session.commit()
                return json.dumps(
                    {
                        "message": "processed",
                        "material": {
                            c.name: getattr(_material, c.name)
                            for c in _material.__table__.columns
                        },
                    },
                    ensure_ascii=False,
                )

            if "design" in request.form:
                _dataDict.update(json.loads(request.form["design"]))
                if token == "":
                    return json.dumps(
                        {"message": "tokenNothing", "text": "JWT未提出"}, ensure_ascii=False
                    )
                with Session() as session:
                    _material = session.execute(
                        select(TskbMaterial).where(
                            TskbMaterial.name == safe_string(_dataDict["material"]["name"])
                        )
                    ).scalar_one_or_none()
                    if _material is None:
                        return json.dumps(
                            {"message": "notExist", "text": "素材不明"},
                            ensure_ascii=False,
                        )
                    if _material.userid != token["id"]:
                        return json.dumps(
                            {"message": "wrongPass", "text": "アクセス拒否"},
                            ensure_ascii=False,
                        )
                    _material_dict = {c.name: getattr(_material, c.name) for c in _material.__table__.columns}
                    _material_dict.update(_dataDict["material"])
                    _material.name = safe_string(_material_dict["name"])
                    _material.tag = safe_string(_material_dict.get("tag", ""))
                    _material.description = safe_string(
                        _material_dict.get("description", ""),
                        _anti_directory_traversal=False,
                    )
                    _material.userid = token["id"]
                    _material.user = _dataDict["user"]
                    _material.passhash = _material_dict.get("passhash", _material.passhash)
                    _material.timestamp = _material_dict.get("timestamp", _material.timestamp)
                    _material.unit = isfloat(_material_dict.get("unit", _material.unit))
                    if _material.unit < 1:
                        _material.unit = 1
                    for _field in NUM_FIELDS[1:]:
                        setattr(
                            _material,
                            _field,
                            isfloat(_material_dict.get(_field, getattr(_material, _field))),
                        )
                    session.commit()
                    session.refresh(_material)
                    return json.dumps(
                        {
                            "message": "processed",
                            "material": {
                                c.name: getattr(_material, c.name)
                                for c in _material.__table__.columns
                            },
                        },
                        ensure_ascii=False,
                    )
                return json.dumps({"message": "rejected", "text": "不明なエラー"})

            if "updata" in request.files:
                if token == "":
                    return json.dumps(
                        {"message": "tokenNothing", "text": "JWT未提出"}, ensure_ascii=False
                    )
                _updata = request.files["updata"]
                _updata_dicts = json.loads(_updata.read())
                for _updata_dict in _updata_dicts:
                    _material = session.execute(
                        select(TskbMaterial).where(
                            TskbMaterial.name == safe_string(_updata_dict["name"])
                        )
                    ).scalar_one_or_none()
                    if _material is None:
                        _material = TskbMaterial(
                            name=safe_string(_updata_dict["name"]),
                            userid=token["id"],
                            user=_dataDict["user"],
                            passhash="",
                            timestamp=int(time.time()),
                        )
                        session.add(_material)
                        session.flush()
                    if _material.userid != token["id"]:
                        continue
                    _material_dict = {c.name: getattr(_material, c.name) for c in _material.__table__.columns}
                    _material_dict.update(_updata_dict)
                    _material.name = safe_string(_material_dict["name"])
                    _material.tag = safe_string(_material_dict.get("tag", ""))
                    _material.description = safe_string(
                        _material_dict.get("description", ""),
                        _anti_directory_traversal=False,
                    )
                    _material.userid = token["id"]
                    _material.user = _dataDict["user"]
                    _material.passhash = _material_dict.get("passhash", _material.passhash)
                    _material.timestamp = _material_dict.get("timestamp", _material.timestamp)
                    _material.unit = isfloat(_material_dict.get("unit", _material.unit))
                    if _material.unit < 1:
                        _material.unit = 1
                    for _field in NUM_FIELDS[1:]:
                        setattr(
                            _material,
                            _field,
                            isfloat(_material_dict.get(_field, getattr(_material, _field))),
                        )
                session.commit()
                return json.dumps(
                    {"message": "processed"},
                    ensure_ascii=False,
                )

            if "delete" in request.form:
                _dataDict.update(json.loads(request.form["delete"]))
                if token == "":
                    return json.dumps(
                        {"message": "tokenNothing", "text": "JWT未提出"}, ensure_ascii=False
                    )
                with Session() as session:
                    session.execute(
                        delete(TskbMaterial).where(
                            TskbMaterial.id == _dataDict["materialid"],
                            TskbMaterial.userid == token["id"],
                        )
                    )
                    session.commit()
                    return json.dumps({"message": "processed"}, ensure_ascii=False)
                return json.dumps({"message": "rejected", "text": "不明なエラー"})

            if "gathertag" in request.form:
                _dataDict.update(json.loads(request.form["gathertag"]))
                _tags = {}
                for result in session.execute(
                    select(TskbCombination.tag).where(TskbCombination.passhash == "")
                ).all():
                    _tag = result[0]
                    if _tag == "":
                        continue
                    if _tag not in _tags:
                        _tags[_tag] = 0
                    _tags[_tag] += 1
                _tags_list = sorted(_tags.items(), key=lambda x: x[1], reverse=True)
                _tags = [_dict[0] for _dict in _tags_list]
                return json.dumps(
                    {
                        "message": "processed",
                        "tags": _tags,
                    },
                    ensure_ascii=False,
                )

            if "search" in request.form:
                _dataDict.update(json.loads(request.form["search"]))
                _userid = -1
                if token != "":
                    _userid = token["id"]
                _material_offset = 0
                if "offset" in _dataDict:
                    _material_offset = int(_dataDict["offset"])
                match _dataDict["search_radio"]:
                    case "name":
                        _tskb_combinations = (
                            session.execute(
                                select(TskbCombination)
                                .where(
                                    TskbCombination.name.like(
                                        "%" + _dataDict["keyword"] + "%"
                                    ),
                                    TskbCombination.passhash == "",
                                )
                                .limit(RECORD_RETURN_MAX)
                                .offset(RECORD_RETURN_MAX * _material_offset)
                            )
                            .scalars()
                            .all()
                        )
                        return json.dumps(
                            {
                                "message": "processed",
                                "combinations": [
                                    {c.name: getattr(r, c.name) for c in r.__table__.columns}
                                    for r in _tskb_combinations
                                ],
                                "token": encoded_new_token,
                            },
                            ensure_ascii=False,
                        )
                    case "tag":
                        _tskb_combinations = (
                            session.execute(
                                select(TskbCombination)
                                .where(
                                    TskbCombination.tag.like(
                                        "%" + _dataDict["keyword"] + "%"
                                    ),
                                    TskbCombination.passhash == "",
                                )
                                .limit(RECORD_RETURN_MAX)
                                .offset(RECORD_RETURN_MAX * _material_offset)
                            )
                            .scalars()
                            .all()
                        )
                        return json.dumps(
                            {
                                "message": "processed",
                                "combinations": [
                                    {c.name: getattr(r, c.name) for c in r.__table__.columns}
                                    for r in _tskb_combinations
                                ],
                                "token": encoded_new_token,
                            },
                            ensure_ascii=False,
                        )
                    case "private":
                        _tskb_combinations = (
                            session.execute(
                                select(TskbCombination)
                                .where(
                                    TskbCombination.name.like(
                                        "%" + _dataDict["keyword"] + "%"
                                    ),
                                    TskbCombination.userid == _userid,
                                )
                                .limit(RECORD_RETURN_MAX)
                                .offset(RECORD_RETURN_MAX * _material_offset)
                            )
                            .scalars()
                            .all()
                        )
                        return json.dumps(
                            {
                                "message": "processed",
                                "combinations": [
                                    {c.name: getattr(r, c.name) for c in r.__table__.columns}
                                    for r in _tskb_combinations
                                ],
                                "token": encoded_new_token,
                            },
                            ensure_ascii=False,
                        )

            if "create" in request.form:
                _dataDict.update(json.loads(request.form["create"]))
                if token == "":
                    return json.dumps(
                        {"message": "tokenNothing", "text": "JWT未提出"}, ensure_ascii=False
                    )
                _passhash = ""
                if _dataDict["privateFlag"] is True:
                    _passhash = "0"
                _room = session.execute(
                    select(TskbCombination).where(
                        TskbCombination.name == safe_string(_dataDict["name"])
                    )
                ).scalar_one_or_none()
                if _room is not None:
                    return json.dumps(
                        {"message": "alreadyExisted", "text": "既存の名前"},
                        ensure_ascii=False,
                    )
                _combination = TskbCombination(
                    name=safe_string(_dataDict["name"]),
                    tag=safe_string(_dataDict["tag"]),
                    description=safe_string(
                        _dataDict["description"], _anti_directory_traversal=False
                    ),
                    userid=token["id"],
                    user=_dataDict["user"],
                    passhash=_passhash,
                    timestamp=int(time.time()),
                    contents=json.dumps({}, ensure_ascii=False),
                )
                session.add(_combination)
                session.commit()
                return json.dumps(
                    {
                        "message": "processed",
                        "combination": {
                            c.name: getattr(_combination, c.name)
                            for c in _combination.__table__.columns
                        },
                    },
                    ensure_ascii=False,
                )
            
            if "combine" in request.form:
                _dataDict.update(json.loads(request.form["combine"]))
                if token == "":
                    return json.dumps(
                        {"message": "tokenNothing", "text": "JWT未提出"}, ensure_ascii=False
                    )
                _combination = _dataDict["combination"]
                _Ccombination = session.get(TskbCombination, _combination["id"])
                if _Ccombination is None:
                    return json.dumps(
                        {"message": "notExist", "text": "存在しません"},
                        ensure_ascii=False,
                    )
                if _Ccombination.userid != token["id"]:
                    return json.dumps(
                        {"message": "wrongPass", "text": "アクセス拒否"},
                        ensure_ascii=False,
                    )
                _contents = json.loads(_Ccombination.contents)
                if "add_material" in _dataDict:
                    if _dataDict["add_material"] in _contents:
                        return json.dumps(
                            {"message": "alreadyExisted", "text": "既存です"},
                            ensure_ascii=False,
                        )
                    _Cmaterial = session.get(TskbMaterial, _dataDict["add_material"])
                    if _Cmaterial is None:
                        return json.dumps(
                            {"message": "notExist", "text": "素材不明"},
                            ensure_ascii=False,
                        )
                    if _Ccombination.passhash != "":
                        if _Cmaterial.userid != token["id"]:
                            return json.dumps(
                                {"message": "wrongPass", "text": "アクセス拒否"},
                                ensure_ascii=False,
                            )
                    _contents.update({_dataDict["add_material"]: _Cmaterial.unit})
                if "del_material" in _dataDict:
                    _contents.pop(_dataDict["del_material"])
                _Ccombination.userid = token["id"]
                _Ccombination.user = _dataDict["user"]
                _Ccombination.contents = json.dumps(_contents, ensure_ascii=False)
                session.commit()
                return json.dumps(
                    {"message": "processed"},
                    ensure_ascii=False,
                )

            if "update" in request.form:
                _dataDict.update(json.loads(request.form["update"]))
                if token == "":
                    return json.dumps(
                        {"message": "tokenNothing", "text": "JWT未提出"}, ensure_ascii=False
                    )
                _combination = _dataDict["combination"]
                _Ccombination = session.get(TskbCombination, _combination["id"])
                if _Ccombination is None:
                    return json.dumps(
                        {"message": "alreadyExisted", "text": "存在しません"},
                        ensure_ascii=False,
                    )
                if _Ccombination.userid != token["id"]:
                    return json.dumps(
                        {"message": "wrongPass", "text": "アクセス拒否"},
                        ensure_ascii=False,
                    )
                _Ccombination.name = safe_string(_combination["name"])
                _Ccombination.tag = safe_string(_combination["tag"])
                _Ccombination.description = safe_string(
                    _combination["description"], _anti_directory_traversal=False
                )
                _Ccombination.userid = token["id"]
                _Ccombination.user = _dataDict["user"]
                _Ccombination.passhash = _combination["passhash"]
                _Ccombination.contents = _combination["contents"]
                session.commit()
                _target_dir = os.path.normpath(
                    os.path.join(
                        tmp_dir + "combination/",
                        safe_string(_Ccombination.id) + ".png",
                    )
                )
                if "delimage" in request.form:
                    if os.path.exists(_target_dir):
                        os.remove(_target_dir)
                if "upimage" in request.files:
                    request.files["upimage"].save(_target_dir)
                    _im = Image.open(_target_dir)
                    _im = _im.resize((round(300 * _im.width / _im.height), 300))
                    _im.save(_target_dir)
                return json.dumps(
                    {"message": "processed"},
                    ensure_ascii=False,
                )

            if "dlimage" in request.form:
                _dataDict.update(json.loads(request.form["dlimage"]))
                _combination = session.get(TskbCombination, _dataDict["combination_id"])
                if _combination is None:
                    return json.dumps(
                        {"message": "notExist", "text": "レシピ不明"},
                        ensure_ascii=False,
                    )
                if _combination.passhash != "":
                    if _combination.id != token["id"]:
                        return json.dumps(
                            {"message": "wrongPass", "text": "アクセス拒否"},
                            ensure_ascii=False,
                        )
                _target_file = os.path.normpath(
                    os.path.join(
                        tmp_dir + "combination/",
                        safe_string(_dataDict["combination_id"]) + ".png",
                    )
                )
                if os.path.exists(_target_file):
                    return flask.send_file(
                        _target_file,
                        mimetype="image/png",
                    )
                return json.dumps(
                    {"message": "notExist", "text": "ファイル無"}, ensure_ascii=False
                )

            if "destroy" in request.form:
                _dataDict.update(json.loads(request.form["destroy"]))
                if token == "":
                    return json.dumps(
                        {"message": "tokenNothing", "text": "JWT未提出"}, ensure_ascii=False
                    )
                _combination = session.get(
                    TskbCombination, _dataDict["combination_id"]
                )
                if _combination is None:
                    return json.dumps(
                        {"message": "notExist", "text": "レシピ不明"},
                        ensure_ascii=False,
                    )
                session.execute(
                    delete(TskbCombination).where(
                        TskbCombination.id == _dataDict["combination_id"],
                        TskbCombination.userid == token["id"],
                    )
                )
                _target_dir = os.path.normpath(
                    os.path.join(
                        tmp_dir + "combination/",
                        safe_string(_dataDict["combination_id"]) + ".png",
                    )
                )
                if os.path.exists(_target_dir):
                    os.remove(_target_dir)
                session.commit()
                return json.dumps({"message": "processed"}, ensure_ascii=False)

            return json.dumps({"message": "rejected", "text": "不明なエラー"})
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
