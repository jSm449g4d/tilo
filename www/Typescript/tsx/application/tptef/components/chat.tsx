import React, { MutableRefObject, useState, useEffect } from "react";

import { jpclock, Unixtime2String } from "../../../components/util";
import { HIModal, CIModal } from "../../../components/imodals";
import { tptefStartTable } from "../../../components/slice";
import { useAppSelector, useAppDispatch } from "../../../components/store";
import "../../../stylecheets/style.sass";


export const CTable = ({ wsRef, wsReady }: any) => {
    const [tmpText, setTmpText] = useState("")
    const [tmpAttachment, setTmpAttachment] = useState<File | null>(null)
    const [contents, setContents] = useState<any>([])
    const userId = useAppSelector((state) => state.account.id)
    const token = useAppSelector((state) => state.account.token)
    const roomKey = useAppSelector((state) => state.account.roomKey)
    const room = useAppSelector((state) => state.tptef.room)
    const reloadFlag = useAppSelector((state) => state.tptef.reloadFlag)
    const tableStatus = useAppSelector((state) => state.tptef.tableStatus)
    const dispatch = useAppDispatch()
    const xhrTimeout = 3000
    const fileSizeMax = 1024 * 1024 * 2

    // jpclock (decoration)
    const [jpclockNow, setJpclockNow] = useState("")
    useEffect(() => {
        const _intervalId = setInterval(() => setJpclockNow(jpclock()), 500)
        return () => clearInterval(_intervalId)
    }, [])

    useEffect(() => {
        setTmpText("")
        setTmpAttachment(null)
    }, [reloadFlag, userId])

    useEffect(() => {
        const sortSetContents = (_contents: any = []) => {
            const _sortContents = (a: any, b: any) => a["timestamp"] - b["timestamp"]
            setContents([..._contents].sort(_sortContents))
        }
        if (tableStatus != "CTable") return
        if (!wsRef.current || !wsReady) return
        if (wsRef.current.readyState !== WebSocket.OPEN) return
        const formData = { "token": token, roomKey: roomKey, "info": "", "fetch": "", "roomid": room["id"] }
        wsRef.current.send(JSON.stringify(formData))
        const onMessage = (e: MessageEvent) => {
            const msg = JSON.parse(e.data)
            if (!Array.isArray(msg["chats"])) return
            if (msg.message == "processed") { sortSetContents(msg["chats"]) }
        }
        wsRef.current.addEventListener("message", onMessage)
        return () => { wsRef.current?.removeEventListener("message", onMessage) }
    }, [wsReady, tableStatus, token, roomKey])

    // fetchAPI
    const postJson = (key: string, body: object, onProcessed?: (resJ: any) => void,) => {
        const formData = new FormData();
        formData.append("info", JSON.stringify({ "token": token, roomKey: roomKey, roomid: room["id"] }));
        formData.append(key, JSON.stringify(body));
        fetch(new Request("/tptef/main.py", {
            method: "POST",
            body: formData,
            signal: AbortSignal.timeout(xhrTimeout),
        }))
            .then(response => response.json())
            .then((resJ: any) => {
                switch (resJ["message"]) {
                    case "processed": { onProcessed?.(resJ); break; }
                    default: {
                        if ("text" in resJ) CIModal(resJ["text"]);
                        break;
                    }
                }
            })
            .catch((e) => CIModal("fetchAPI_Error", e.message));
    };

    const uploadChat = () => {
        if (tmpAttachment == null) return
        if (fileSizeMax <= tmpAttachment.size) {
            CIModal("Too huge filesize", "plz filesize < " + String(fileSizeMax) + " [byte]")
            return
        }
        const formData = new FormData()
        formData.append("info", JSON.stringify({ "token": token, roomKey: roomKey, roomid: room["id"] }))
        formData.append("upload", tmpAttachment, tmpAttachment.name)
        const request = new Request("/tptef/main.py", {
            method: "POST",
            body: formData,
            signal: AbortSignal.timeout(xhrTimeout)
        })
        fetch(request)
            .then(response => response.json())
            .then(resJ => {
                if (resJ["message"] != "processed") { if ("text" in resJ) CIModal("Exception", resJ["text"]) }
            })
            .catch(error => { CIModal("fetchAPI_Error", error.message) })
        setTmpAttachment(null)
    }

    const downloadChat = (_id: number, _fileName: string = "", _asAttachment = true) => {
        const formData = new FormData()
        formData.append("info", JSON.stringify({ "token": token, roomKey: roomKey, roomid: room["id"] }))
        formData.append("download", JSON.stringify({
            "chatid": _id, "filename": _fileName, "as_attachment": _asAttachment
        }))
        const request = new Request("/tptef/main.py", {
            method: "POST",
            body: formData,
            signal: AbortSignal.timeout(xhrTimeout)
        })
        fetch(request)
            .then(response => response.blob())
            .then(blob => {
                const _url = window.URL.createObjectURL(blob)
                const a = document.createElement("a")
                a.href = _url
                document.body.appendChild(a)
                a.setAttribute("style", "display: none")
                a.setAttribute("download", _fileName)
                a.click()
                a.remove()
                window.URL.revokeObjectURL(_url)
            })
            .catch(error => { CIModal("fetchAPI_Error", error.message) })
    }

    const remarkChat = () => { postJson("remark", { "text": tmpText }); setTmpText(""); }

    const deleteChat = (_id: number) => { postJson("delete", { "chatid": _id }) }

    const destroyRoom = () => {
        postJson("destroy", { "roomid": room["id"] }, () => { dispatch(tptefStartTable({ tableStatus: "RTable" })) })
    }

    const destroyRoomModal = () => {
        return (
            <div className="modal fade" id="destroyRoomModal" aria-hidden="true">
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

    const chatTopForm = () => {
        return (
            <div>
                <div className="input-group d-flex justify-content-center align-items-center my-1">
                    <button className="btn btn-outline-success btn-lg" type="button"
                        onClick={() => { }}>
                        <i className="fa-solid fa-rotate-right mx-1" style={{ pointerEvents: "none" }} />
                    </button>
                    <button className="btn btn-outline-dark btn-lg" type="button" disabled>
                        <i className="far fa-user mx-1"></i>{room["user"]}
                    </button>
                    <input className="flex-fill form-control form-control-lg" type="text" value={room["room"]} disabled />
                    {room["userid"] == userId ?
                        <button className="btn btn-outline-danger btn-lg" type="button"
                            onClick={() => { $("#destroyRoomModal").modal("show") }}>
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
        const _tmpRecord = []
        for (let i = 0; i < contents.length; i++) {
            let _style = { background: "linear-gradient(rgba(60,60,60,0), rgba(60,60,60,0.2))" }
            if (contents[i]["mode"] == "attachment") {
                _style = { background: "linear-gradient(rgba(60,60,60,0), rgba(60,60,150,0.2))" }
            }
            const _tmpData = []
            _tmpData.push(
                <div className="col-12 border d-flex" style={_style} key={`head-${contents[i]["id"]}`}>
                    <h5 className="me-auto">
                        <i className="far fa-user mx-1"></i>{contents[i]["user"]}
                    </h5>
                    {Unixtime2String(Number(contents[i]["timestamp"]))}
                </div>)
            if (contents[i]["mode"] == "text") {
                _tmpData.push(
                    <div className="col-12 col-md-9 border" key={`text-${contents[i]["id"]}`}><div className="text-center">
                        {contents[i]["text"]}
                    </div></div>)
                _tmpData.push(
                    <div className="col-12 col-md-3 border" key={`action-${contents[i]["id"]}`}><div className="text-center">
                        {contents[i]["userid"] == userId ?
                            <button className="btn btn-outline-danger rounded-pill"
                                onClick={() => { deleteChat(contents[i]["id"]) }}>
                                <i className="far fa-trash-alt mx-1" style={{ pointerEvents: "none" }}></i>Delete
                            </button> : <div></div>}
                    </div></div>)
            }
            if (contents[i]["mode"] == "attachment") {
                _tmpData.push(
                    <div className="col-12 col-md-9 border" key={`file-${contents[i]["id"]}`}><div className="text-center">
                        {contents[i]["text"]}
                    </div></div>)
                _tmpData.push(
                    <div className="col-12 col-md-3 border d-flex justify-content-end" key={`download-${contents[i]["id"]}`}>
                        <button className="btn btn-outline-primary rounded-pill"
                            onClick={() => { downloadChat(contents[i]["id"], contents[i]["text"]) }}>
                            <i className="fa-solid fa-download mx-1" style={{ pointerEvents: "none" }}></i>Download
                        </button>
                        {contents[i]["userid"] == userId ?
                            <button className="btn btn-outline-danger rounded-pill"
                                onClick={() => { deleteChat(contents[i]["id"]) }}>
                                <i className="far fa-trash-alt mx-1" style={{ pointerEvents: "none" }}></i>Delete
                            </button> : <div></div>}
                    </div>)
            }
            _tmpRecord.push(
                <div key={contents[i]["id"]} style={{
                    border: "1px inset silver", borderRadius: "5px", marginBottom: "3px", boxShadow: "2px 2px 1px rgba(60,60,60,0.2)"
                }}><div className="m-1 row">{_tmpData}</div></div>)
        }
        return (<div className="">{_tmpRecord}</div>)
    }

    const inputConsole = () => {
        const remarkButton = () => {
            if (tmpAttachment == null && tmpText == "") {
                return (
                    <button className="btn btn-dark " disabled>
                        <i className="far fa-comment-dots mx-1" style={{ pointerEvents: "none" }}></i>要入力
                    </button>
                )
            }
            return (
                <button className="btn btn-success"
                    onClick={() => {
                        if (tmpText != "") remarkChat()
                        if (tmpAttachment != null) uploadChat()
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
                        <input type="file" className="form-control" placeholder="attachment file" disabled />
                        <button className="btn btn-outline-info" onClick={() => { HIModal("発言機能にはログインが必要です") }}>
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
                            onChange={(evt) => { setTmpAttachment(evt.target.files?.[0] ?? null) }} />
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
