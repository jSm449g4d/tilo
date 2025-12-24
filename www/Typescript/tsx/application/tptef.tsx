import React, { useState, useEffect } from 'react';

import { jpclock, Unixtime2String } from "../components/util";
import { HIModal, CIModal } from "../components/imodals";
import { accountSetState } from '../components/slice'
import { useAppSelector, useAppDispatch } from '../components/store'
import "../stylecheets/style.sass";

export const AppMain = () => {
    const user = useAppSelector((state) => state.account.user)
    const userId = useAppSelector((state) => state.account.id)
    const token = useAppSelector((state) => state.account.token)
    const roomKey = useAppSelector((state) => state.account.roomKey)
    const dispatch = useAppDispatch()
    const xhrTimeout = 3000
    const fileSizeMax = 1024 * 1024 * 2

    const [room, setRoom] = useState({ "id": -1, "user": "", "userid": -1, "room": "", "timestamp": 0, "passhash": "" })
    const [tmpRoomKey, setTmpRoomKey] = useState("")
    const [tmpRoom, setTmpRoom] = useState("")
    const [tmpText, setTmpText] = useState("")
    const [tmpAttachment, setTmpAttachment] = useState(null)
    const [tmpTargetId, setTmpTargetId] = useState(-1)
    const [contents, setContents] = useState([])

    useEffect(() => {
        if (room["room"] == "") searchRoom()
        else fetchChat()
    }, [userId])
    useEffect(() => { searchRoom() }, [])

    // jpclock (decoration)
    const [jpclockNow, setJpclockNow] = useState("")
    useEffect(() => {
        const _intervalId = setInterval(() => setJpclockNow(jpclock()), 500);
        return () => clearInterval(_intervalId);
    }, []);
    // related to fetchAPI
    const roadDelay = (_callback = () => { }, _delay = 100) => {
        setTimeout(() => { _callback(); }, _delay);
    }
    const stringForSend = (_additionalDict: {} = {}) => {
        const _sendDict = Object.assign(
            {
                "token": token, "text": tmpText, "user": user, roomid: room["id"], roomKey: roomKey
            }, _additionalDict)
        return (JSON.stringify(_sendDict))
    }
    const enterRoom = (_setContentsInitialze = true) => {
        setTmpRoomKey(""); setTmpRoom(""); setTmpText(""); setTmpAttachment(null); setTmpTargetId(-1);
        if (_setContentsInitialze) setContents([])
        $('#inputConsoleAttachment').val(null)
    }
    const exitRoom = (_setContentsInitialze = true) => {
        setRoom({ "id": -1, "user": "", "userid": -1, "room": "", "timestamp": 0, "passhash": "" });
        setTmpRoomKey(""); setTmpRoom(""); setTmpText(""); setTmpAttachment(null); setTmpTargetId(-1);
        if (_setContentsInitialze) setContents([])
    }
    const satisfyDictKeys = (_targetDict: {}, _keys: any[]) => {
        for (let _i = 0; _i < _keys.length; _i++) if (_keys[_i] in _targetDict == false) return false
        return true
    }
    const fetchChat = (_roomid = room["id"], _roomKey = roomKey) => {
        const sortSetContents = (_contents: any = []) => {
            const _sortContents = (a: any, b: any) => { return a["timestamp"] - b["timestamp"] }
            setContents(_contents.sort(_sortContents))
        }
        enterRoom(false)
        const headers = new Headers();
        const formData = new FormData();
        formData.append("info", stringForSend())
        formData.append("fetch", JSON.stringify({ "roomid": _roomid, "roomKey": _roomKey }))
        const request = new Request("/tptef/main.py", {
            method: 'POST',
            headers: headers,
            body: formData,
            signal: AbortSignal.timeout(xhrTimeout)
        });
        fetch(request)
            .then(response => response.json())
            .then(resJ => {
                switch (resJ["message"]) {
                    case "processed": {
                        setRoom(resJ["room"]);
                        sortSetContents(resJ["chats"])
                        dispatch(accountSetState({ token: resJ["token"] })); break;
                    } break;
                    case "wrongPass": {
                        CIModal("部屋のパスワードが違います")
                        searchRoom(); break;
                    }
                    case "notExist": {
                        CIModal("部屋が存在しません")
                        searchRoom(); break;
                    }
                    case "tokenNothing": {
                        CIModal("JWTトークン未提出")
                        searchRoom(); break;
                    }
                    case "tokenTimeout": {
                        CIModal("JWTトークンタイムアウト");
                        break;
                    }
                    default: {
                        CIModal("その他のエラー")
                        searchRoom(); break;
                    }
                }
            })
            .catch(error => {
                CIModal("通信エラー")
                console.error(error.message)
            });
    }
    const remarkChat = () => {
        if (tmpText != "") {
            const headers = new Headers();
            const formData = new FormData();
            formData.append("info", stringForSend())
            formData.append("remark", JSON.stringify({}))
            const request = new Request("/tptef/main.py", {
                method: 'POST',
                headers: headers,
                body: formData,
                signal: AbortSignal.timeout(xhrTimeout)
            });
            fetch(request)
                .then(response => response.json())
                .then(resJ => {
                    switch (resJ["message"]) {
                        case "processed": roadDelay(fetchChat); break;
                        case "wrongPass": {
                            CIModal("部屋のパスワードが違います")
                            searchRoom(); break;
                        }
                        case "notExist": {
                            CIModal("部屋が存在しません")
                            searchRoom(); break;
                        }
                        case "tokenNothing": {
                            CIModal("JWTトークン未提出")
                            searchRoom(); break;
                        }
                        default: {
                            CIModal("その他のエラー")
                            searchRoom(); break;
                        }
                    }
                })
                .catch(error => {
                    CIModal("通信エラー")
                    console.error(error.message)
                });
        }
        // upload file
        if (tmpAttachment == null) return
        if (fileSizeMax <= tmpAttachment.size) {
            $('#cautionInfoModal').modal('show');
            $('#cautionInfoModalTitle').text(
                "ファイルサイズが大きすぎます(" + String(fileSizeMax) + " byte)未満")
            return
        }
        const headers = new Headers();
        const formData = new FormData();
        formData.append("info", stringForSend())
        formData.append("upload", tmpAttachment, tmpAttachment.name)
        const request = new Request("/tptef/main.py", {
            method: 'POST',
            headers: headers,
            body: formData,
            signal: AbortSignal.timeout(xhrTimeout)
        });
        fetch(request)
            .then(response => response.json())
            .then(resJ => {
                switch (resJ["message"]) {
                    case "processed": roadDelay(fetchChat); break;
                    case "wrongPass": {
                        CIModal("部屋のパスワードが違います")
                        searchRoom(); break;
                    }
                    case "notExist": {
                        CIModal("部屋が存在しません")
                        searchRoom(); break;
                    }
                    case "tokenNothing": {
                        CIModal("JWTトークン未提出")
                        searchRoom(); break;
                    }
                    default: {
                        CIModal("その他のエラー")
                        searchRoom(); break;
                    }
                }
            })
            .catch(error => {
                CIModal("通信エラー")
                console.error(error.message)
            });
    }
    const deleteChat = (_id: number) => {
        const headers = new Headers();
        const formData = new FormData();
        formData.append("info", stringForSend())
        formData.append("delete", JSON.stringify({ "chatid": _id }))
        const request = new Request("/tptef/main.py", {
            method: 'POST',
            headers: headers,
            body: formData,
            signal: AbortSignal.timeout(xhrTimeout)
        });
        fetch(request)
            .then(response => response.json())
            .then(resJ => {
                switch (resJ["message"]) {
                    case "processed": roadDelay(fetchChat); break;
                    case "wrongPass": {
                        CIModal("部屋のパスワードが違います")
                        searchRoom(); break;
                    }
                    case "notExist": {
                        CIModal("部屋が存在しません")
                        searchRoom(); break;
                    }
                    case "tokenNothing": {
                        CIModal("JWTトークン未提出")
                        searchRoom(); break;
                    }
                    default: {
                        CIModal("その他のエラー")
                        searchRoom(); break;
                    }
                }
            })
            .catch(error => {
                CIModal("通信エラー")
                console.error(error.message)
            });
    }
    const downloadChat = (_id: number, _fileName: string = "", _asAttachment = true) => {
        const headers = new Headers();
        const formData = new FormData();
        formData.append("info", stringForSend())
        formData.append("download", JSON.stringify({
            "chatid": _id, "filename": _fileName, "as_attachment": _asAttachment
        }))
        const request = new Request("/tptef/main.py", {
            method: 'POST',
            headers: headers,
            body: formData,
            signal: AbortSignal.timeout(xhrTimeout)
        });
        fetch(request)
            .then(response => response.blob())
            .then(blob => {
                var a = document.createElement("a");
                a.href = window.URL.createObjectURL(blob);
                document.body.appendChild(a);
                a.setAttribute("style", "display: none");
                a.setAttribute("download", _fileName);
                a.click();
                roadDelay(fetchChat)
            })
            .catch(error => {
                CIModal("通信エラー")
                console.error(error.message)
            });
    }
    const searchRoom = () => {
        const sortSetContentsRev = (_contents: any = []) => {
            const _sortContentsRev = (a: any, b: any) => { return b["timestamp"] - a["timestamp"] }
            setContents(_contents.sort(_sortContentsRev))
        }
        exitRoom(false)
        const headers = new Headers();
        const formData = new FormData();
        formData.append("info", stringForSend())
        formData.append("search", JSON.stringify({}))
        const request = new Request("/tptef/main.py", {
            method: 'POST',
            headers: headers,
            body: formData,
            signal: AbortSignal.timeout(xhrTimeout)
        });
        fetch(request)
            .then(response => response.json())
            .then(resJ => {
                switch (resJ["message"]) {
                    case "processed": {
                        sortSetContentsRev(resJ["rooms"]);
                        dispatch(accountSetState({ token: resJ["token"] })); break;
                    }
                    case "tokenTimeout": {
                        CIModal("JWTトークンタイムアウト");
                        break;
                    }
                    default: {
                        CIModal("その他のエラー")
                        break;
                    }
                }
            })
            .catch(error => {
                CIModal("通信エラー")
                console.error(error.message)
            });
    }
    const createRoom = () => {
        exitRoom()
        const headers = new Headers();
        const formData = new FormData();
        formData.append("info", stringForSend())
        formData.append("create", JSON.stringify({ "room": tmpRoom, "roomKey": tmpRoomKey }))
        const request = new Request("/tptef/main.py", {
            method: 'POST',
            headers: headers,
            body: formData,
            signal: AbortSignal.timeout(xhrTimeout)
        });
        fetch(request)
            .then(response => response.json())
            .then(resJ => {
                switch (resJ["message"]) {
                    case "processed": roadDelay(searchRoom); break;
                    case "alreadyExisted": {
                        CIModal("既にその名前の部屋が存在します")
                        searchRoom(); break;
                    }
                    case "tokenNothing": {
                        CIModal("JWTトークン未提出")
                        searchRoom(); break;
                    }
                    default: {
                        CIModal("その他のエラー")
                        searchRoom(); break;
                    }
                }
            })
            .catch(error => {
                CIModal("通信エラー")
                console.error(error.message)
            });
    }
    const destroyRoom = () => {
        const _roomid = room["room"] == "" ? tmpTargetId : room["id"]
        const headers = new Headers();
        const formData = new FormData();
        formData.append("info", stringForSend())
        formData.append("destroy", JSON.stringify({ "roomid": _roomid }))
        const request = new Request("/tptef/main.py", {
            method: 'POST',
            headers: headers,
            body: formData,
            signal: AbortSignal.timeout(xhrTimeout)
        });
        fetch(request)
            .then(response => response.json())
            .then(resJ => {
                switch (resJ["message"]) {
                    case "processed": roadDelay(searchRoom); break;
                    case "notExist": {
                        CIModal("部屋が存在しません")
                        searchRoom(); break;
                    }
                    case "tokenNothing": {
                        CIModal("JWTトークン未提出")
                        searchRoom(); break;
                    }
                    case "youerntOwner": {
                        CIModal("部屋の所有権がありません")
                        searchRoom(); break;
                    }
                    default: {
                        CIModal("その他のエラー")
                        searchRoom(); break;
                    }
                }
            })
            .catch(error => {
                CIModal("通信エラー")
                console.error(error.message)
            });
    }
    // ConsoleRender
    const roomTopForm = () => {
        const roomCreateModal = () => {
            return (
                <div>
                    <div className="modal fade" id="roomCreateModal" aria-labelledby="exampleModalLabel" aria-hidden="true">
                        <div className="modal-dialog">
                            <div className="modal-content">
                                <div className="modal-header">
                                    <h3 className="modal-title fs-5">
                                        <i className="fa-solid fa-hammer mx-1" />部屋作成
                                    </h3>
                                </div>
                                <div className="modal-body row">
                                    <div className="input-group m-1 col-12">
                                        <span className="input-group-text">部屋名</span>
                                        <input type="text" className="form-control" placeholder="Roomname" aria-label="user"
                                            value={tmpRoom} onChange={(evt) => { setTmpRoom(evt.target.value) }} />
                                    </div>
                                    <div className="input-group m-1 col-12">
                                        <span className="input-group-text">Pass</span>
                                        <input type="text" className="form-control" placeholder="Password" aria-label="pass"
                                            value={tmpRoomKey} onChange={(evt) => { setTmpRoomKey(evt.target.value) }} />
                                    </div>
                                </div>
                                <div className="modal-footer">
                                    <button type="button" className="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                                    {tmpRoom == "" || token == "" ?
                                        <button type="button" className="btn btn-outline-info"
                                            onClick={() => { HIModal("部屋名が入力されてません") }}>
                                            <i className="fa-solid fa-hammer mx-1" style={{ pointerEvents: "none" }} />作成
                                        </button> :
                                        <div>
                                            {tmpRoomKey == "" ?
                                                <button type="button" className="btn btn-outline-primary" data-bs-dismiss="modal"
                                                    onClick={() => createRoom()}>
                                                    <i className="fa-solid fa-hammer mx-1" style={{ pointerEvents: "none" }} />作成
                                                </button> :
                                                <button type="button" className="btn btn-outline-warning" data-bs-dismiss="modal"
                                                    onClick={() => {
                                                        dispatch(accountSetState({ "roomKey": tmpRoomKey }))
                                                        createRoom()
                                                    }}>
                                                    <i className="fa-solid fa-key mx-1" />作成
                                                </button>}
                                        </div>
                                    }
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )
        }
        return (
            <div>{roomCreateModal()}
                <div className="input-group d-flex justify-content-center align-items-center my-1">

                    <button className="btn btn-outline-success btn-lg" type="button"
                        onClick={() => { searchRoom() }}>
                        <i className="fa-solid fa-rotate-right mx-1" style={{ pointerEvents: "none" }} />
                    </button>
                    <input className="flex-fill form-control form-control-lg" type="text" placeholder="部屋名検索" value={tmpRoom}
                        onChange={(evt: any) => { setTmpRoom(evt.target.value) }} />
                    {token == "" ?
                        <button className="btn btn-outline-info btn-lg" type="button"
                            onClick={() => { HIModal("部屋作成にはログインが必要です") }}>
                            <i className="fa-solid fa-circle-info mx-1" style={{ pointerEvents: "none" }} />
                            部屋作成
                        </button> :
                        <button className="btn btn-outline-primary btn-lg" type="button"
                            onClick={() => { setTmpRoom(""); $('#roomCreateModal').modal('show'); }}>
                            <i className="fa-solid fa-hammer mx-1" style={{ pointerEvents: "none" }} />
                            部屋作成
                        </button>}
                </div>
            </div>)
    }
    const roomTable = () => {
        const roomInterModal = () => {
            return (
                <div className="modal fade" id="roomInterModal" aria-labelledby="exampleModalLabel" aria-hidden="true">
                    <div className="modal-dialog">
                        <div className="modal-content">
                            <div className="modal-header">
                                <h1 className="modal-title fs-5">
                                    <i className="fa-solid fa-lock mx-1" />パスワード入力
                                </h1>
                            </div>
                            <div className="modal-body row">
                                <div className="input-group m-1 col-12">
                                    <span className="input-group-text">Pass</span>
                                    <input type="text" className="form-control" placeholder="Password" aria-label="pass"
                                        value={tmpRoomKey} onChange={(evt) => { setTmpRoomKey(evt.target.value) }} />
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" value={-1} id="roomInterModalButton"
                                    className="btn btn-secondary" data-bs-dismiss="modal">
                                    Close
                                </button>
                                {tmpRoomKey != "" ?
                                    <button type="button" className="btn btn-outline-primary" data-bs-dismiss="modal"
                                        onClick={
                                            () => {
                                                // roomKey cannot be updated in time
                                                dispatch(accountSetState({ roomKey: tmpRoomKey }))
                                                fetchChat(Number(tmpTargetId), tmpRoomKey)
                                            }}>
                                        <i className="fa-solid fa-right-to-bracket mx-1" style={{ pointerEvents: "none" }} />入室
                                    </button> :
                                    <button type="button" className="btn btn-outline-primary" disabled>
                                        <i className="fa-solid fa-right-to-bracket mx-1" style={{ pointerEvents: "none" }} />入室
                                    </button>
                                }
                            </div>
                        </div>
                    </div>
                </div>
            )
        }
        const _tmpRecord = [];
        if (0 < contents.length)
            if (!satisfyDictKeys(contents[0], ["id", "user", "userid", "room", "timestamp", "passhash"]))
                return (<div className="row m-1">loading</div>)
        for (var i = 0; i < contents.length; i++) {
            if (contents[i]["room"].indexOf(tmpRoom) == -1) continue
            const _tmpData = [];
            var _style = { background: "linear-gradient(rgba(60,60,60,0), rgba(60,60,60,0.2))" }
            if (contents[i]["passhash"] != "")
                _style = { background: "linear-gradient(rgba(60,60,60,0), rgba(150,150,60,0.2))" }
            _tmpData.push(
                <div className="col-12 border d-flex" style={_style}>
                    <h5 className="me-auto">
                        <i className="far fa-user mx-1"></i>{contents[i]["user"]}
                    </h5>
                    {contents[i]["passhash"] == "" ?
                        <button className="btn btn-outline-primary rounded-pill"
                            onClick={(evt: any) => { fetchChat(evt.target.value) }} value={contents[i]["id"]}>
                            <i className="fa-solid fa-right-to-bracket mx-1" style={{ pointerEvents: "none" }}></i>入室
                        </button> :
                        <button className="btn btn-outline-dark rounded-pill"
                            onClick={(evt: any) => {
                                setTmpTargetId(evt.target.value)
                                $('#roomInterModal').modal('show')
                            }} value={contents[i]["id"]}>
                            <i className="fa-solid fa-lock mx-1" style={{ pointerEvents: "none" }}></i>入室
                        </button>
                    }
                    {contents[i]["userid"] == userId ?
                        <button className="btn btn-outline-danger rounded-pill"
                            onClick={(evt: any) => {
                                setTmpTargetId(evt.target.value)
                                $('#destroyRoomModal').modal('show');

                            }} value={contents[i]["id"]}>
                            <i className="far fa-trash-alt mx-1" style={{ pointerEvents: "none" }}></i>削除
                        </button> : <div></div>
                    }
                </div >)
            _tmpData.push(
                <div className="col-12 col-md-10 p-1 d-flex justify-content-center align-items-center border">
                    <h3>
                        {contents[i]["room"]}
                    </h3>
                </div>)
            _tmpData.push(
                <div className="col-12 col-md-2 p-1 border"><div className="text-center">
                    {Unixtime2String(Number(contents[i]["timestamp"]))}
                </div></div>)
            _tmpRecord.push(
                <div className="col-12 col-md-6" style={{
                    border: "1px inset silver", borderRadius: "5px", marginBottom: "3px", boxShadow: "2px 2px 1px rgba(60,60,60,0.2)"
                }}>
                    <div className="row p-1">{_tmpData}</div>
                </div>
            )
        }
        return (
            <div>
                {roomInterModal()}
                <div className="row m-1">{_tmpRecord}
                </div>
            </div>)
    }
    const chatTopForm = () => {
        return (
            <div>
                <div className="input-group d-flex justify-content-center align-items-center my-1">
                    <button className="btn btn-outline-success btn-lg" type="button"
                        onClick={() => { fetchChat() }}>
                        <i className="fa-solid fa-rotate-right mx-1" style={{ pointerEvents: "none" }} />
                    </button>
                    <button className="btn btn-outline-dark btn-lg" type="button"
                        disabled>
                        <i className="far fa-user mx-1"></i>{room["user"]}
                    </button>
                    <input className="flex-fill form-control form-control-lg" type="text" value={room["room"]}
                        disabled>
                    </input >
                    {room["userid"] == userId ?
                        <button className="btn btn-outline-danger btn-lg" type="button"
                            onClick={() => { $("#destroyRoomModal").modal('show') }}>
                            <i className="far fa-trash-alt mx-1 " style={{ pointerEvents: "none" }}></i>部屋削除
                        </button> :
                        <button className="btn btn-outline-info btn-lg" type="button"
                            onClick={() => { HIModal("部屋削除は部屋作成者にしかできません") }}>
                            <i className="fa-solid fa-circle-info mx-1" style={{ pointerEvents: "none" }} />部屋削除
                        </button>
                    }
                    <button className="btn btn-outline-dark btn-lg" type="button"
                        onClick={() => { searchRoom() }}>
                        <i className="fa-solid fa-right-from-bracket mx-1"></i>
                        部屋を出る
                    </button>
                </div></div>)
    }
    const chatTable = () => {
        // if contents dont have enough element for example contents hold chat_data ,table need break
        if (0 < contents.length)
            if (!satisfyDictKeys(contents[0], ["id", "user", "userid", "roomid", "text", "mode", "timestamp"]))
                return (<div className="row m-1">loading</div>)
        const _tmpRecord = [];
        for (var i = 0; i < contents.length; i++) {
            var _style = { background: "linear-gradient(rgba(60,60,60,0), rgba(60,60,60,0.2))" }
            if (contents[i]["mode"] == "attachment")
                _style = { background: "linear-gradient(rgba(60,60,60,0), rgba(60,60,150,0.2))" }
            const _tmpData = [];
            // text
            _tmpData.push(
                <div className="col-12 border d-flex" style={_style}>
                    <h5 className="me-auto">
                        <i className="far fa-user mx-1"></i>{contents[i]["user"]}
                    </h5>
                    {Unixtime2String(Number(contents[i]["timestamp"]))}
                </div>)
            if (contents[i]["mode"] == "text") {
                _tmpData.push(
                    <div className="col-12 col-md-9 border"><div className="text-center">
                        {contents[i]["text"]}
                    </div></div>)
                _tmpData.push(
                    <div className="col-12 col-md-3 border"><div className="text-center">
                        {
                            contents[i]["userid"] == userId ?
                                <button className="btn btn-outline-danger rounded-pill"
                                    onClick={(evt: any) => {
                                        deleteChat(evt.target.name);
                                    }} name={contents[i]["id"]}>
                                    <i className="far fa-trash-alt mx-1" style={{ pointerEvents: "none" }}></i>Delete
                                </button> : <div></div>}
                    </div></div>)
            }
            // file
            if (contents[i]["mode"] == "attachment") {
                _tmpData.push(
                    <div className="col-12 col-md-9 border"><div className="text-center">
                        {contents[i]["text"]}
                    </div></div>)
                _tmpData.push(
                    <div className="col-12 col-md-3 border d-flex justify-content-end">
                        <button className="btn btn-outline-primary rounded-pill"
                            onClick={(evt: any) => {
                                downloadChat(evt.target.value, evt.target.name);
                            }} value={contents[i]["id"]} name={contents[i]["text"]}>
                            <i className="fa-solid fa-download mx-1" style={{ pointerEvents: "none" }}></i>Download
                        </button>
                        {
                            contents[i]["userid"] == userId ?
                                <button className="btn btn-outline-danger rounded-pill"
                                    onClick={(evt: any) => {
                                        deleteChat(evt.target.name);
                                    }} name={contents[i]["id"]}>
                                    <i className="far fa-trash-alt mx-1" style={{ pointerEvents: "none" }}></i>Delete
                                </button> : <div></div>
                        }
                    </div>)
            }
            _tmpRecord.push(
                <div style={{
                    border: "1px inset silver", borderRadius: "5px", marginBottom: "3px", boxShadow: "2px 2px 1px rgba(60,60,60,0.2)"
                }}><div className="m-1 row">{_tmpData}</div></div>)
        }
        return (<div className="">{_tmpRecord}</div>)
    }
    const inputConsole = () => {
        const remarkButton = () => {
            if (tmpAttachment == null && tmpText == "")
                return (
                    <button className="btn btn-dark " disabled>
                        <i className="far fa-comment-dots mx-1" style={{ pointerEvents: "none" }}></i>要入力
                    </button>
                )
            return (
                <button className="btn btn-success"
                    onClick={() => { remarkChat(); }}>
                    <i className="far fa-comment-dots mx-1" style={{ pointerEvents: "none" }}></i>送信
                </button>
            )
        }
        if (token == "") return (
            <div className="m-1 p-2 row w-100"
                style={{ color: "#CCFFFF", border: "3px double silver", background: "#001111" }}>
                <div className="col-12 d-flex justify-content-center">
                    <h5><i className="far fa-clock "></i>{jpclockNow}</h5>
                </div>
                <div className="col-12 my-1">
                    <div className="input-group">
                        <input type="file" className="form-control" placeholder="attachment file"
                            disabled />
                        <button className="btn btn-outline-info"
                            onClick={() => { HIModal("発言機能にはログインが必要です"); }}>
                            <i className="fa-solid fa-circle-info mx-1" style={{ pointerEvents: "none" }} ></i>送信
                        </button>
                    </div>
                </div>
            </div>)
        return (
            <div className="m-1 p-2 row w-100"
                style={{ color: "#CCFFFF", border: "3px double silver", background: "#001111" }}>
                <div className="col-12 d-flex justify-content-center">
                    <h5><i className="far fa-clock "></i>{jpclockNow}</h5>
                </div>
                <textarea className="form-control col-12 w-80" rows={4} value={tmpText}
                    onChange={(evt) => { setTmpText(evt.target.value) }} style={{ resize: "none" }} />
                <div className="col-12 my-1">
                    <div className="input-group">
                        <input type="file" className="form-control" placeholder="attachment file"
                            id="inputConsoleAttachment"
                            onChange={(evt) => { setTmpAttachment(evt.target.files[0]) }} />
                        {remarkButton()}
                    </div>
                </div>
            </div>
        )
    }
    // applicationRender
    const destroyRoomModal = () => {
        return (
            <div className="modal fade" id="destroyRoomModal"
                aria-labelledby="exampleModalLabel" aria-hidden="true">
                <div className="modal-dialog">
                    <div className="modal-content">
                        <div className="modal-header">
                            <h4 className="modal-title">
                                <i className="fa-solid fa-circle-info mx-1" />部屋を削除しますか?
                            </h4>
                        </div>
                        <div className="modal-footer d-flex">
                            <button type="button" className="btn btn-secondary me-auto" data-bs-dismiss="modal">Close</button>
                            <button type="button" className="btn btn-danger" data-bs-dismiss="modal"
                                onClick={() => { destroyRoom() }}>
                                <i className="far fa-trash-alt mx-1" style={{ pointerEvents: "none" }} />削除
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        )
    }
    return (
        <div>
            {room["room"] == "" ?
                <div className="m-1">
                    {roomTopForm()}
                    {roomTable()}
                </div> :
                <div className="m-1">
                    {chatTopForm()}
                    {chatTable()}
                    {inputConsole()}
                </div>
            }
            {destroyRoomModal()}
        </div>
    )
};

// titleLogo
export const titleLogo = () => {
    return (<h2 className="rotxin-2" style={{ fontFamily: "Impact", color: "black" }}>
        <i className="far fa-comments mx-1" style={{ pointerEvents: "none" }}></i>チャットアプリ
    </h2>)
}