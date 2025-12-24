import React, { useState, useEffect } from 'react';

import { jpclock, Unixtime2String } from "../../../components/util";
import { HIModal, CIModal } from "../../../components/imodals";
import { accountSetState, tptefSetState, tptefStartTable } from '../../../components/slice'
import { useAppSelector, useAppDispatch } from '../../../components/store'
import "../../../stylecheets/style.sass";



export const CTable = () => {
    const [tmpText, setTmpText] = useState("")
    const [tmpAttachment, setTmpAttachment] = useState(null)
    const [contents, setContents] = useState([])
    const user = useAppSelector((state) => state.account.user)
    const userId = useAppSelector((state) => state.account.id)
    const token = useAppSelector((state) => state.account.token)
    const roomKey = useAppSelector((state) => state.account.roomKey)
    const room = useAppSelector((state) => state.tptef.room)
    const reloadFlag = useAppSelector((state) => state.tptef.reloadFlag)
    const tableStatus = useAppSelector((state) => state.tptef.tableStatus)
    const dispatch = useAppDispatch()
    const xhrTimeout = 3000
    const fileSizeMax = 1024 * 1024 * 2
    const xhrDelay = 100

    // jpclock (decoration)
    const [jpclockNow, setJpclockNow] = useState("")
    useEffect(() => {
        const _intervalId = setInterval(() => setJpclockNow(jpclock()), 500);
        return () => clearInterval(_intervalId);
    }, []);

    useEffect(() => {
        if (tableStatus == "CTable") setTimeout(() => fetchChat(), xhrDelay)
        initSubmitForm()
    }, [reloadFlag, userId])
    const initSubmitForm = () => {
        setTmpText("")
        setTmpAttachment(null)
    }
    const stringForSend = (_additionalDict: {} = {}) => {
        const _sendDict = Object.assign(
            {
                "token": token, "user": user,
            }, _additionalDict)
        return (JSON.stringify(_sendDict))
    }

    // fetchAPI
    const fetchChat = (_roomid = room["id"], _roomKey = roomKey) => {
        const sortSetContents = (_contents: any = []) => {
            const _sortContents = (a: any, b: any) => { return a["timestamp"] - b["timestamp"] }
            setContents(_contents.sort(_sortContents))
        }
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
                    case "processed":
                        sortSetContents(resJ["chats"])
                        dispatch(accountSetState({ token: resJ["token"] }));
                        break;
                    default: {
                        if ("text" in resJ) CIModal(resJ["text"]);
                        break;
                    }
                }
            })
            .catch(error => {
                CIModal("通信エラー")
                console.error(error.message)
            });
    }
    const uploadChat = () => {
        if (fileSizeMax <= tmpAttachment.size) {
            CIModal("ファイルサイズが大きすぎます(" + String(fileSizeMax) + " byte)未満")
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
                    case "processed":
                        setTimeout(() => fetchChat(), xhrDelay)
                        break;
                    default: {
                        if ("text" in resJ) CIModal(resJ["text"]);
                        break;
                    }
                }
            })
            .catch(error => {
                CIModal("通信エラー")
                console.error(error.message)
            });
    }
    const remarkChat = () => {
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
                    case "processed":
                        setTimeout(() => fetchChat(), xhrDelay)
                        break;
                    default: {
                        if ("text" in resJ) CIModal(resJ["text"]);
                        break;
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
                    case "processed":
                        setTimeout(() => fetchChat(), xhrDelay)
                        break;
                    default: {
                        if ("text" in resJ) CIModal(resJ["text"]);
                        break;
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
                setTimeout(() => fetchChat(), xhrDelay)
            })
            .catch(error => {
                CIModal("通信エラー")
                console.error(error.message)
            });
    }
    const destroyRoom = () => {
        const headers = new Headers();
        const formData = new FormData();
        formData.append("info", stringForSend())
        formData.append("destroy", JSON.stringify({ "roomid": room["id"] }))
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
                    case "processed":
                        dispatch(tptefStartTable({ tableStatus: "RTable" }))
                        break;
                    default: {
                        if ("text" in resJ) CIModal(resJ["text"]);
                        break;
                    }
                }
            })
            .catch(error => {
                CIModal("通信エラー")
                console.error(error.message)
            });
    }
    //modal
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
    // app
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
                        </button> : <div />
                    }
                    <button className="btn btn-outline-dark btn-lg" type="button"
                        onClick={() => { dispatch(tptefStartTable({ tableStatus: "RTable" })) }}>
                        <i className="fa-solid fa-right-from-bracket mx-1"></i>
                        退出
                    </button>
                </div></div>)
    }
    const chatTable = () => {
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
                    onClick={() => {
                        if (tmpText != "") remarkChat()
                        if (tmpAttachment != null) uploadChat()
                        initSubmitForm()
                    }}>
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
    return (
        <div>
            {destroyRoomModal()}
            {chatTopForm()}
            {chatTable()}
            {inputConsole()}
        </div>
    )
}