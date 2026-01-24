import sqlite3
import json
import os
import jwt
from PIL import Image
import unicodedata
import re
import flask
import sys
from contextlib import closing
import time
import glob

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

with closing(sqlite3.connect(db_dir)) as conn:
    cur = conn.cursor()
    "(id,name,tag,description,userid,user,passhash,timestamp,img,contents)"
    # contents={material_id:amount}
    # passhash="": public ,"0": private
    # img: reserved for the future
    cur.execute(
        "CREATE TABLE IF NOT EXISTS tskb_combination(id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "name TEXT UNIQUE NOT NULL,tag TEXT DEFAULT '',description TEXT DEFAULT '',"
        "userid INTEGER NOT NULL,user TEXT NOT NULL,passhash TEXT DEFAULT '',timestamp INTEGER NOT NULL,"
        "img TEXT DEFAULT '',"
        "contents TEXT NOT NULL)"
    )
    # passhash="": public ,"0": private
    # tag="Requirements": special
    # img: reserved for the future
    "(id,name,tag,description,userid,user,passhash,timestamp,img,"
    "unit,cost,carbo,fiber,protein,fat,saturated_fat,n3,DHA_EPA,n6,"
    "ca,cl,cr,cu,i,fe,mg,mn,mo,p,k,se,na,zn,va,vb1,vb2,vb3,vb5,vb6,vb7,vb9,vb12,vc,vd,ve,vk,colin,kcal)"
    cur.execute(
        "CREATE TABLE IF NOT EXISTS tskb_material(id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "name TEXT UNIQUE NOT NULL,tag TEXT DEFAULT '',description TEXT DEFAULT '',"
        "userid INTEGER NOT NULL,user TEXT NOT NULL,passhash TEXT DEFAULT '',timestamp INTEGER NOT NULL,"
        "img TEXT DEFAULT '',"
        "unit REAL DEFAULT 100,cost REAL DEFAULT 0,"
        "carbo REAL DEFAULT 0,fiber REAL DEFAULT 0,"
        "protein REAL DEFAULT 0,fat REAL DEFAULT 0,saturated_fat REAL DEFAULT 0,"
        "n3 REAL DEFAULT 0,DHA_EPA REAL DEFAULT 0,"
        "n6 REAL DEFAULT 0,ca REAL DEFAULT 0,cl REAL DEFAULT 0,cr REAL DEFAULT 0,"
        "cu REAL DEFAULT 0,i REAL DEFAULT 0,fe REAL DEFAULT 0,"
        "mg REAL DEFAULT 0,mn REAL DEFAULT 0,mo REAL DEFAULT 0,"
        "p REAL DEFAULT 0,k REAL DEFAULT 0,se REAL DEFAULT 0,"
        "na REAL DEFAULT 0,zn REAL DEFAULT 0,va REAL DEFAULT 0,"
        "vb1 REAL DEFAULT 0,vb2 REAL DEFAULT 0,vb3 REAL DEFAULT 0,"
        "vb5 REAL DEFAULT 0,vb6 REAL DEFAULT 0,vb7 REAL DEFAULT 0,"
        "vb9 REAL DEFAULT 0,vb12 REAL DEFAULT 0,vc REAL DEFAULT 0,"
        "vd REAL DEFAULT 0,ve REAL DEFAULT 0,vk REAL DEFAULT 0,"
        "colin REAL DEFAULT 0,kcal REAL DEFAULT 0)"
    )
    conn.commit()


def load_reference_file():
    _reference_files = glob.glob(key_dir + "tskb/" + "*.json")
    for _filename in _reference_files:
        with open(_filename, "r", encoding="utf-8") as _f:
            _updata_dicts = json.loads(_f.read())
            with closing(sqlite3.connect(db_dir)) as conn:
                for _updata_dict in _updata_dicts:
                    conn.row_factory = sqlite3.Row
                    cur = conn.cursor()
                    # make record
                    cur.execute(
                        "SELECT * FROM tskb_material WHERE name = ?;",
                        [safe_string(_updata_dict["name"])],
                    )
                    _material = cur.fetchone()
                    if _material == None:
                        cur.execute(
                            "INSERT INTO tskb_material "
                            "(name,userid,user,passhash,timestamp) "
                            "values(?,?,?,?,?)",
                            [
                                safe_string(_updata_dict["name"]),
                                0,
                                "admin",
                                "",
                                int(time.time()),
                            ],
                        )
                        cur.execute(
                            "SELECT * FROM tskb_material WHERE ROWID = last_insert_rowid();",
                            [],
                        )
                        _material = cur.fetchone()
                    _material = dict(_material)
                    # upgrade record
                    _material.update(_updata_dict)
                    if isfloat(_material["unit"]) < 1:
                        _material["unit"] = 1
                    cur.execute(
                        "UPDATE tskb_material SET name = ?,tag = ?,description = ?,"
                        "userid = ?,user = ?,passhash = ?,timestamp = ?,"
                        "unit = ?,cost = ?,carbo = ?,fiber= ? ,protein = ?,"
                        "fat = ?,saturated_fat = ?,n3 = ?,DHA_EPA = ?,n6 = ?,"
                        "ca = ?,cl = ?,cr = ?,cu = ?,i = ?,fe = ?,mg = ?,mn = ?,"
                        "mo = ?,p = ?,k = ?,se = ?,na = ?,zn = ?,va = ?,vb1 = ?,"
                        "vb2 = ?,vb3 = ?,vb5 = ?,vb6 = ?,vb7 = ?,"
                        "vb9 = ?,vb12 = ?,vc = ?,vd = ?,ve = ?,vk = ?,"
                        "colin = ?,kcal = ? WHERE id = ?;",
                        [
                            safe_string(_material["name"]),
                            safe_string(_material["tag"]),
                            safe_string(
                                _material["description"],
                                _anti_directory_traversal=False,
                            ),
                            0,
                            "admin",
                            _material["passhash"],
                            _material["timestamp"],
                            isfloat(_material["unit"]),
                            isfloat(_material["cost"]),
                            isfloat(_material["carbo"]),
                            isfloat(_material["fiber"]),
                            isfloat(_material["protein"]),
                            isfloat(_material["fat"]),
                            isfloat(_material["saturated_fat"]),
                            isfloat(_material["n3"]),
                            isfloat(_material["DHA_EPA"]),
                            isfloat(_material["n6"]),
                            isfloat(_material["ca"]),
                            isfloat(_material["cl"]),
                            isfloat(_material["cr"]),
                            isfloat(_material["cu"]),
                            isfloat(_material["i"]),
                            isfloat(_material["fe"]),
                            isfloat(_material["mg"]),
                            isfloat(_material["mn"]),
                            isfloat(_material["mo"]),
                            isfloat(_material["p"]),
                            isfloat(_material["k"]),
                            isfloat(_material["se"]),
                            isfloat(_material["na"]),
                            isfloat(_material["zn"]),
                            isfloat(_material["va"]),
                            isfloat(_material["vb1"]),
                            isfloat(_material["vb2"]),
                            isfloat(_material["vb3"]),
                            isfloat(_material["vb5"]),
                            isfloat(_material["vb6"]),
                            isfloat(_material["vb7"]),
                            isfloat(_material["vb9"]),
                            isfloat(_material["vb12"]),
                            isfloat(_material["vc"]),
                            isfloat(_material["vd"]),
                            isfloat(_material["ve"]),
                            isfloat(_material["vk"]),
                            isfloat(_material["colin"]),
                            isfloat(_material["kcal"]),
                            _material["id"],
                        ],
                    )
                conn.commit()


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
        if "listtag" in request.form:
            _dataDict.update(json.loads(request.form["listtag"]))
            with closing(sqlite3.connect(db_dir)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                # process start
                cur.execute(
                    "SELECT tag FROM tskb_material WHERE passhash = '' ",
                    [],
                )
                _tags = {}
                for result in cur.fetchall():
                    if result["tag"] == "":
                        continue
                    if result["tag"] not in _tags:
                        _tags[result["tag"]] = 0
                    _tags[result["tag"]] += 1
                _tags_list = sorted(_tags.items(), key=lambda x: x[1], reverse=True)
                _tags = []
                for _dict in _tags_list:
                    _tags.append(_dict[0])
                return json.dumps(
                    {
                        "message": "processed",
                        "tags": _tags,
                    },
                    ensure_ascii=False,
                )
            return json.dumps({"message": "rejected", "text": "不明なエラー"})

        if "explore" in request.form:
            _dataDict.update(json.loads(request.form["explore"]))
            with closing(sqlite3.connect(db_dir)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                _userid = -1
                if token != "":
                    _userid = token["id"]
                _material_offset = 0
                if "offset" in _dataDict:
                    _material_offset = int(_dataDict["offset"])
                # process start
                match _dataDict["search_radio"]:
                    case "name":
                        cur.execute(
                            "SELECT * FROM tskb_material WHERE name LIKE ? "
                            "AND passhash = '' LIMIT ? OFFSET ? ;",
                            [
                                "%" + _dataDict["keyword"] + "%",
                                RECORD_RETURN_MAX,
                                RECORD_RETURN_MAX * _material_offset,
                            ],
                        )
                        _materials = [
                            {key: value for key, value in dict(result).items()}
                            for result in cur.fetchall()
                        ]
                        return json.dumps(
                            {
                                "message": "processed",
                                "materials": _materials,
                                "token": encoded_new_token,
                            },
                            ensure_ascii=False,
                        )
                    case "tag":
                        cur.execute(
                            "SELECT * FROM tskb_material WHERE tag LIKE ? "
                            "AND passhash = '' LIMIT ? OFFSET ? ;",
                            [
                                "%" + _dataDict["keyword"] + "%",
                                RECORD_RETURN_MAX,
                                RECORD_RETURN_MAX * _material_offset,
                            ],
                        )
                        _materials = [
                            {key: value for key, value in dict(result).items()}
                            for result in cur.fetchall()
                        ]
                        return json.dumps(
                            {
                                "message": "processed",
                                "materials": _materials,
                                "token": encoded_new_token,
                            },
                            ensure_ascii=False,
                        )
                    case "private":
                        cur.execute(
                            "SELECT * FROM tskb_material WHERE name LIKE ? "
                            "AND userid = ? LIMIT ? OFFSET ? ;",
                            [
                                "%" + _dataDict["keyword"] + "%",
                                _userid,
                                RECORD_RETURN_MAX,
                                RECORD_RETURN_MAX * _material_offset,
                            ],
                        )
                        _materials = [
                            {key: value for key, value in dict(result).items()}
                            for result in cur.fetchall()
                        ]
                        return json.dumps(
                            {
                                "message": "processed",
                                "materials": _materials,
                                "token": encoded_new_token,
                            },
                            ensure_ascii=False,
                        )
            return json.dumps({"message": "rejected", "text": "不明なエラー"})

        if "fetch" in request.form:
            _dataDict.update(json.loads(request.form["fetch"]))
            with closing(sqlite3.connect(db_dir)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                # process start
                # select combination
                _userid = -1
                if token != "":
                    _userid = token["id"]
                cur.execute(
                    "SELECT * FROM tskb_combination WHERE id = ?;",
                    [_dataDict["combinationid"]],
                )
                _combination = cur.fetchone()
                if _combination == None:
                    return json.dumps(
                        {"message": "notExist", "text": "レシピが不明"},
                        ensure_ascii=False,
                    )
                if _combination["passhash"] != "":
                    if _combination["userid"] != _userid:
                        return json.dumps(
                            {"message": "wrongPass", "text": "アクセス拒否"},
                            ensure_ascii=False,
                        )
                # select material
                _contents = json.loads(_combination["contents"])
                _materials = []
                for _key, _val in _contents.items():
                    cur.execute("SELECT * FROM tskb_material WHERE id = ?;", [_key])
                    _material = cur.fetchone()
                    if _material == None:
                        continue
                    if _material["passhash"] != "":
                        if _material["userid"] != _userid:
                            continue
                    _materials.append(dict(_material))
                # requirements
                cur.execute(
                    "SELECT * FROM tskb_material WHERE tag = 'Requirements' "
                    "AND passhash = '' AND userid = 0 LIMIT 20;",
                    [],
                )
                _requirements = [
                    {key: value for key, value in dict(result).items()}
                    for result in cur.fetchall()
                ]
                return json.dumps(
                    {
                        "message": "processed",
                        "materials": _materials,
                        "combination": dict(_combination),
                        "requirements": _requirements,
                        "token": encoded_new_token,
                    },
                    ensure_ascii=False,
                )
            return json.dumps({"message": "rejected", "text": "不明なエラー"})

        if "register" in request.form:
            _dataDict.update(json.loads(request.form["register"]))
            if token == "":
                return json.dumps(
                    {"message": "tokenNothing", "text": "JWT未提出"}, ensure_ascii=False
                )
            _passhash = ""
            if _dataDict["privateFlag"] == True:
                _passhash = "0"
            with closing(sqlite3.connect(db_dir)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                # process start
                cur.execute(
                    "SELECT * FROM tskb_material WHERE name = ?;",
                    [safe_string(_dataDict["name"])],
                )
                _material = cur.fetchone()
                if _material != None:
                    return json.dumps(
                        {"message": "alreadyExisted", "text": "既存の名前"}
                    )
                cur.execute(
                    "INSERT INTO tskb_material "
                    "(name,tag,description,userid,user,passhash,timestamp) "
                    "values(?,?,?,?,?,?,?)",
                    [
                        safe_string(_dataDict["name"]),
                        safe_string(_dataDict["tag"]),
                        safe_string(
                            _dataDict["description"], _anti_directory_traversal=False
                        ),
                        token["id"],
                        _dataDict["user"],
                        _passhash,
                        int(time.time()),
                    ],
                )
                cur.execute(
                    "SELECT * FROM tskb_material WHERE ROWID = last_insert_rowid();",
                    [],
                )
                _material = cur.fetchone()
                conn.commit()
                return json.dumps(
                    {"message": "processed", "material": dict(_material)},
                    ensure_ascii=False,
                )
            return json.dumps({"message": "rejected", "text": "不明なエラー"})

        if "design" in request.form:
            _dataDict.update(json.loads(request.form["design"]))
            if token == "":
                return json.dumps(
                    {"message": "tokenNothing", "text": "JWT未提出"}, ensure_ascii=False
                )
            with closing(sqlite3.connect(db_dir)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                # process start
                cur.execute(
                    "SELECT * FROM tskb_material WHERE name = ?;",
                    [safe_string(_dataDict["material"]["name"])],
                )
                _material = cur.fetchone()
                if _material == None:
                    return json.dumps(
                        {"message": "notExist", "text": "素材不明"},
                        ensure_ascii=False,
                    )
                if _material["userid"] != token["id"]:
                    return json.dumps(
                        {"message": "wrongPass", "text": "アクセス拒否"},
                        ensure_ascii=False,
                    )
                _material = dict(_material)
                _material.update(_dataDict["material"])
                if isfloat(_material["unit"]) < 1:
                    _material["unit"] = 1
                cur.execute(
                    "UPDATE tskb_material SET name = ?,tag = ?,description = ?,"
                    "userid = ?,user = ?,passhash = ?,timestamp = ?,"
                    "unit = ?,cost = ?,carbo = ?,fiber= ? ,protein = ?,"
                    "fat = ?,saturated_fat = ?,n3 = ?,DHA_EPA = ?,n6 = ?,"
                    "ca = ?,cl = ?,cr = ?,cu = ?,i = ?,fe = ?,mg = ?,mn = ?,"
                    "mo = ?,p = ?,k = ?,se = ?,na = ?,zn = ?,va = ?,vb1 = ?,"
                    "vb2 = ?,vb3 = ?,vb5 = ?,vb6 = ?,vb7 = ?,"
                    "vb9 = ?,vb12 = ?,vc = ?,vd = ?,ve = ?,vk = ?,"
                    "colin = ?,kcal = ? WHERE id = ?;",
                    [
                        safe_string(_material["name"]),
                        safe_string(_material["tag"]),
                        safe_string(
                            _material["description"], _anti_directory_traversal=False
                        ),
                        token["id"],
                        _dataDict["user"],
                        _material["passhash"],
                        _material["timestamp"],
                        isfloat(_material["unit"]),
                        isfloat(_material["cost"]),
                        isfloat(_material["carbo"]),
                        isfloat(_material["fiber"]),
                        isfloat(_material["protein"]),
                        isfloat(_material["fat"]),
                        isfloat(_material["saturated_fat"]),
                        isfloat(_material["n3"]),
                        isfloat(_material["DHA_EPA"]),
                        isfloat(_material["n6"]),
                        isfloat(_material["ca"]),
                        isfloat(_material["cl"]),
                        isfloat(_material["cr"]),
                        isfloat(_material["cu"]),
                        isfloat(_material["i"]),
                        isfloat(_material["fe"]),
                        isfloat(_material["mg"]),
                        isfloat(_material["mn"]),
                        isfloat(_material["mo"]),
                        isfloat(_material["p"]),
                        isfloat(_material["k"]),
                        isfloat(_material["se"]),
                        isfloat(_material["na"]),
                        isfloat(_material["zn"]),
                        isfloat(_material["va"]),
                        isfloat(_material["vb1"]),
                        isfloat(_material["vb2"]),
                        isfloat(_material["vb3"]),
                        isfloat(_material["vb5"]),
                        isfloat(_material["vb6"]),
                        isfloat(_material["vb7"]),
                        isfloat(_material["vb9"]),
                        isfloat(_material["vb12"]),
                        isfloat(_material["vc"]),
                        isfloat(_material["vd"]),
                        isfloat(_material["ve"]),
                        isfloat(_material["vk"]),
                        isfloat(_material["colin"]),
                        isfloat(_material["kcal"]),
                        _material["id"],
                    ],
                )
                conn.commit()
                cur.execute(
                    "SELECT * FROM tskb_material WHERE id = ?;",
                    [_material["id"]],
                )
                _material = cur.fetchone()
                return json.dumps(
                    {"message": "processed", "material": dict(_material)},
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
            with closing(sqlite3.connect(db_dir)) as conn:
                for _updata_dict in _updata_dicts:
                    conn.row_factory = sqlite3.Row
                    cur = conn.cursor()
                    # make record
                    cur.execute(
                        "SELECT * FROM tskb_material WHERE name = ?;",
                        [safe_string(_updata_dict["name"])],
                    )
                    _material = cur.fetchone()
                    if _material == None:
                        cur.execute(
                            "INSERT INTO tskb_material "
                            "(name,userid,user,passhash,timestamp) "
                            "values(?,?,?,?,?)",
                            [
                                safe_string(_updata_dict["name"]),
                                token["id"],
                                _dataDict["user"],
                                "",
                                int(time.time()),
                            ],
                        )
                        cur.execute(
                            "SELECT * FROM tskb_material WHERE ROWID = last_insert_rowid();",
                            [],
                        )
                        _material = cur.fetchone()
                    if _material["userid"] != token["id"]:
                        continue
                    _material = dict(_material)
                    # upgrade record
                    _material.update(_updata_dict)
                    if isfloat(_material["unit"]) < 1:
                        _material["unit"] = 1
                    cur.execute(
                        "UPDATE tskb_material SET name = ?,tag = ?,description = ?,"
                        "userid = ?,user = ?,passhash = ?,timestamp = ?,"
                        "unit = ?,cost = ?,carbo = ?,fiber= ? ,protein = ?,"
                        "fat = ?,saturated_fat = ?,n3 = ?,DHA_EPA = ?,n6 = ?,"
                        "ca = ?,cl = ?,cr = ?,cu = ?,i = ?,fe = ?,mg = ?,mn = ?,"
                        "mo = ?,p = ?,k = ?,se = ?,na = ?,zn = ?,va = ?,vb1 = ?,"
                        "vb2 = ?,vb3 = ?,vb5 = ?,vb6 = ?,vb7 = ?,"
                        "vb9 = ?,vb12 = ?,vc = ?,vd = ?,ve = ?,vk = ?,"
                        "colin = ?,kcal = ? WHERE id = ?;",
                        [
                            safe_string(_material["name"]),
                            safe_string(_material["tag"]),
                            safe_string(
                                _material["description"],
                                _anti_directory_traversal=False,
                            ),
                            token["id"],
                            _dataDict["user"],
                            _material["passhash"],
                            _material["timestamp"],
                            isfloat(_material["unit"]),
                            isfloat(_material["cost"]),
                            isfloat(_material["carbo"]),
                            isfloat(_material["fiber"]),
                            isfloat(_material["protein"]),
                            isfloat(_material["fat"]),
                            isfloat(_material["saturated_fat"]),
                            isfloat(_material["n3"]),
                            isfloat(_material["DHA_EPA"]),
                            isfloat(_material["n6"]),
                            isfloat(_material["ca"]),
                            isfloat(_material["cl"]),
                            isfloat(_material["cr"]),
                            isfloat(_material["cu"]),
                            isfloat(_material["i"]),
                            isfloat(_material["fe"]),
                            isfloat(_material["mg"]),
                            isfloat(_material["mn"]),
                            isfloat(_material["mo"]),
                            isfloat(_material["p"]),
                            isfloat(_material["k"]),
                            isfloat(_material["se"]),
                            isfloat(_material["na"]),
                            isfloat(_material["zn"]),
                            isfloat(_material["va"]),
                            isfloat(_material["vb1"]),
                            isfloat(_material["vb2"]),
                            isfloat(_material["vb3"]),
                            isfloat(_material["vb5"]),
                            isfloat(_material["vb6"]),
                            isfloat(_material["vb7"]),
                            isfloat(_material["vb9"]),
                            isfloat(_material["vb12"]),
                            isfloat(_material["vc"]),
                            isfloat(_material["vd"]),
                            isfloat(_material["ve"]),
                            isfloat(_material["vk"]),
                            isfloat(_material["colin"]),
                            isfloat(_material["kcal"]),
                            _material["id"],
                        ],
                    )
                conn.commit()
                return json.dumps(
                    {"message": "processed"},
                    ensure_ascii=False,
                )
            return json.dumps({"message": "rejected", "text": "不明なエラー"})

        if "delete" in request.form:
            _dataDict.update(json.loads(request.form["delete"]))
            if token == "":
                return json.dumps(
                    {"message": "tokenNothing", "text": "JWT未提出"}, ensure_ascii=False
                )
            with closing(sqlite3.connect(db_dir)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                # duplication and roomKey check
                cur.execute(
                    "DELETE FROM tskb_material WHERE id = ? AND userid = ?;",
                    [_dataDict["materialid"], token["id"]],
                )
                conn.commit()
                return json.dumps({"message": "processed"}, ensure_ascii=False)
            return json.dumps({"message": "rejected", "text": "不明なエラー"})

        if "gathertag" in request.form:
            _dataDict.update(json.loads(request.form["gathertag"]))
            with closing(sqlite3.connect(db_dir)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                # process start
                cur.execute(
                    "SELECT tag FROM tskb_combination WHERE passhash = '' ",
                    [],
                )
                _tags = {}
                for result in cur.fetchall():
                    if result["tag"] == "":
                        continue
                    if result["tag"] not in _tags:
                        _tags[result["tag"]] = 0
                    _tags[result["tag"]] += 1
                _tags_list = sorted(_tags.items(), key=lambda x: x[1], reverse=True)
                _tags = []
                for _dict in _tags_list:
                    _tags.append(_dict[0])
                return json.dumps(
                    {
                        "message": "processed",
                        "tags": _tags,
                    },
                    ensure_ascii=False,
                )
            return json.dumps({"message": "rejected", "text": "不明なエラー"})

        if "search" in request.form:
            _dataDict.update(json.loads(request.form["search"]))
            _userid = -1
            if token != "":
                _userid = token["id"]
            _material_offset = 0
            if "offset" in _dataDict:
                _material_offset = int(_dataDict["offset"])
            with closing(sqlite3.connect(db_dir)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                # process start
                match _dataDict["search_radio"]:
                    case "name":
                        cur.execute(
                            "SELECT * FROM tskb_combination where name LIKE ? AND "
                            "passhash == '' LIMIT ? OFFSET ? ;",
                            [
                                "%" + _dataDict["keyword"] + "%",
                                RECORD_RETURN_MAX,
                                RECORD_RETURN_MAX * _material_offset,
                            ],
                        )
                        _tskb_combinations = [
                            {key: value for key, value in dict(result).items()}
                            for result in cur.fetchall()
                        ]
                        return json.dumps(
                            {
                                "message": "processed",
                                "combinations": _tskb_combinations,
                                "token": encoded_new_token,
                            },
                            ensure_ascii=False,
                        )
                    case "tag":
                        cur.execute(
                            "SELECT * FROM tskb_combination where tag LIKE ? AND "
                            "passhash == '' LIMIT ? OFFSET ? ;",
                            [
                                "%" + _dataDict["keyword"] + "%",
                                RECORD_RETURN_MAX,
                                RECORD_RETURN_MAX * _material_offset,
                            ],
                        )
                        _tskb_combinations = [
                            {key: value for key, value in dict(result).items()}
                            for result in cur.fetchall()
                        ]
                        return json.dumps(
                            {
                                "message": "processed",
                                "combinations": _tskb_combinations,
                                "token": encoded_new_token,
                            },
                            ensure_ascii=False,
                        )
                    case "private":
                        cur.execute(
                            "SELECT * FROM tskb_combination WHERE name LIKE ? "
                            "AND userid = ? LIMIT ? OFFSET ? ;",
                            [
                                "%" + _dataDict["keyword"] + "%",
                                _userid,
                                RECORD_RETURN_MAX,
                                RECORD_RETURN_MAX * _material_offset,
                            ],
                        )
                        _tskb_combinations = [
                            {key: value for key, value in dict(result).items()}
                            for result in cur.fetchall()
                        ]
                        return json.dumps(
                            {
                                "message": "processed",
                                "combinations": _tskb_combinations,
                                "token": encoded_new_token,
                            },
                            ensure_ascii=False,
                        )
            return json.dumps({"message": "rejected", "text": "不明なエラー"})

        if "create" in request.form:
            _dataDict.update(json.loads(request.form["create"]))
            if token == "":
                return json.dumps(
                    {"message": "tokenNothing", "text": "JWT未提出"}, ensure_ascii=False
                )
            _passhash = ""
            if _dataDict["privateFlag"] == True:
                _passhash = "0"
            with closing(sqlite3.connect(db_dir)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                # check duplication
                cur.execute(
                    "SELECT * FROM tskb_combination WHERE name = ?;",
                    [safe_string(_dataDict["name"])],
                )
                _room = cur.fetchone()
                if _room != None:
                    return json.dumps(
                        {"message": "alreadyExisted", "text": "既存の名前"},
                        ensure_ascii=False,
                    )
                cur.execute(
                    "INSERT INTO tskb_combination "
                    "(name,tag,description,userid,user,passhash,timestamp,contents) "
                    "values(?,?,?,?,?,?,?,?)",
                    [
                        safe_string(_dataDict["name"]),
                        safe_string(_dataDict["tag"]),
                        safe_string(
                            _dataDict["description"], _anti_directory_traversal=False
                        ),
                        token["id"],
                        _dataDict["user"],
                        _passhash,
                        int(time.time()),
                        json.dumps({}, ensure_ascii=False),
                    ],
                )
                cur.execute(
                    "SELECT * FROM tskb_combination WHERE ROWID = last_insert_rowid();",
                    [],
                )
                _combination = cur.fetchone()
                conn.commit()
                return json.dumps(
                    {"message": "processed", "combination": dict(_combination)},
                    ensure_ascii=False,
                )
            return json.dumps({"message": "rejected"})

        if "combine" in request.form:
            _dataDict.update(json.loads(request.form["combine"]))
            if token == "":
                return json.dumps(
                    {"message": "tokenNothing", "text": "JWT未提出"}, ensure_ascii=False
                )
            _combination = _dataDict["combination"]
            with closing(sqlite3.connect(db_dir)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                # check duplication
                cur.execute(
                    "SELECT * FROM tskb_combination WHERE id = ?;",
                    [_combination["id"]],
                )
                _Ccombination = cur.fetchone()
                if _Ccombination == None:
                    return json.dumps(
                        {"message": "notExist", "text": "存在しません"},
                        ensure_ascii=False,
                    )
                if _Ccombination["userid"] != token["id"]:
                    return json.dumps(
                        {"message": "wrongPass", "text": "アクセス拒否"},
                        ensure_ascii=False,
                    )
                _contents = json.loads(_Ccombination["contents"])
                if "add_material" in _dataDict:
                    if _dataDict["add_material"] in _contents:
                        return json.dumps(
                            {"message": "alreadyExisted", "text": "既存です"},
                            ensure_ascii=False,
                        )
                    cur.execute(
                        "SELECT * FROM tskb_material WHERE id = ?;",
                        [_dataDict["add_material"]],
                    )
                    _Cmaterial = cur.fetchone()
                    if _Cmaterial == None:
                        return json.dumps(
                            {"message": "notExist", "text": "素材不明"},
                            ensure_ascii=False,
                        )
                    if _Ccombination["passhash"] != "":
                        if _Cmaterial["userid"] != token["id"]:
                            return json.dumps(
                                {"message": "wrongPass", "text": "アクセス拒否"},
                                ensure_ascii=False,
                            )
                    _contents.update({_dataDict["add_material"]: _Cmaterial["unit"]})
                if "del_material" in _dataDict:
                    _contents.pop(_dataDict["del_material"])
                cur.execute(
                    "UPDATE tskb_combination SET userid = ?, user = ?,"
                    "contents = ? WHERE id = ?;",
                    [
                        token["id"],
                        _dataDict["user"],
                        json.dumps(
                            _contents,
                            ensure_ascii=False,
                        ),
                        _combination["id"],
                    ],
                )
                conn.commit()
                return json.dumps(
                    {"message": "processed"},
                    ensure_ascii=False,
                )
            return json.dumps({"message": "rejected"})

        if "update" in request.form:
            _dataDict.update(json.loads(request.form["update"]))
            if token == "":
                return json.dumps(
                    {"message": "tokenNothing", "text": "JWT未提出"}, ensure_ascii=False
                )
            _combination = _dataDict["combination"]
            with closing(sqlite3.connect(db_dir)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                # check duplication
                cur.execute(
                    "SELECT * FROM tskb_combination WHERE id = ?;",
                    [_combination["id"]],
                )
                _Ccombination = cur.fetchone()
                if _Ccombination == None:
                    return json.dumps(
                        {"message": "alreadyExisted", "text": "存在しません"},
                        ensure_ascii=False,
                    )
                if _Ccombination["userid"] != token["id"]:
                    return json.dumps(
                        {"message": "wrongPass", "text": "アクセス拒否"},
                        ensure_ascii=False,
                    )
                cur.execute(
                    "UPDATE tskb_combination SET name = ?, tag = ?, description = ?,"
                    " userid = ?, user = ?, passhash = ? ,contents = ? WHERE id = ?;",
                    [
                        safe_string(_combination["name"]),
                        safe_string(_combination["tag"]),
                        safe_string(
                            _combination["description"], _anti_directory_traversal=False
                        ),
                        token["id"],
                        _dataDict["user"],
                        _combination["passhash"],
                        _combination["contents"],
                        _combination["id"],
                    ],
                )
                conn.commit()
                cur.execute(
                    "SELECT * FROM tskb_combination WHERE id = ?;",
                    [_combination["id"]],
                )
                _Ccombination = cur.fetchone()
                _target_dir = os.path.normpath(
                    os.path.join(
                        tmp_dir + "combination/",
                        safe_string(_Ccombination["id"]) + ".png",
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
            return json.dumps({"message": "rejected"})

        if "dlimage" in request.form:
            _dataDict.update(json.loads(request.form["dlimage"]))
            with closing(sqlite3.connect(db_dir)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                # duplication and roomKey check
                cur.execute(
                    "SELECT * FROM tskb_combination WHERE id = ?;",
                    [_dataDict["combination_id"]],
                )
                _combination = cur.fetchone()
                if _combination == None:
                    return json.dumps(
                        {"message": "notExist", "text": "レシピ不明"},
                        ensure_ascii=False,
                    )
                if _combination["passhash"] != "":
                    if _combination["id"] != token["id"]:
                        return json.dumps(
                            {"message": "wrongPass", "text": "アクセス拒否"},
                            ensure_ascii=False,
                        )
                # process start
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
            return json.dumps({"message": "rejected"}, ensure_ascii=False)

        if "destroy" in request.form:
            _dataDict.update(json.loads(request.form["destroy"]))
            if token == "":
                return json.dumps(
                    {"message": "tokenNothing", "text": "JWT未提出"}, ensure_ascii=False
                )
            with closing(sqlite3.connect(db_dir)) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                # check duplication
                cur.execute(
                    "SELECT * FROM tskb_combination WHERE id = ?;",
                    [_dataDict["combination_id"]],
                )
                _combination = cur.fetchone()
                if _combination == None:
                    return json.dumps(
                        {"message": "notExist", "text": "レシピ不明"},
                        ensure_ascii=False,
                    )
                cur.execute(
                    "DELETE FROM tskb_combination WHERE id = ? AND userid = ?;",
                    [_dataDict["combination_id"], token["id"]],
                )
                _target_dir = os.path.normpath(
                    os.path.join(
                        tmp_dir + "combination/",
                        safe_string(_dataDict["combination_id"]) + ".png",
                    )
                )
                if os.path.exists(_target_dir):
                    os.remove(_target_dir)
                conn.commit()
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
