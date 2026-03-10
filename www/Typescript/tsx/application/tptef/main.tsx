import React, { useState, useEffect, useRef } from "react";

import { Unixtime2String } from "../../components/util";
import { HIModal, CIModal } from "../../components/imodals";
import { tptefStartTable } from "../../components/slice";
import { useAppSelector, useAppDispatch } from "../../components/store";
import { CTable } from "./components/chat";
import "../../stylecheets/style.sass";

export const AppMain = () => {
    const token = useAppSelector((state) => state.account.token)
    const roomKey = useAppSelector((state) => state.account.roomKey)
    const tableStatus = useAppSelector((state) => state.tptef.tableStatus)
    const dispatch = useAppDispatch()

    const xhrTimeout = 3000
    const [tmpRoomKeyhole, setTmpRoomKeyhole] = useState("")
    const [tmpRoom, setTmpRoom] = useState("")
    const [tmpSearch, setTmpSearch] = useState("")
    const [contents, setContents] = useState<any>([])
    const wsRef = useRef<WebSocket | null>(null)
    const [wsReady, setWsReady] = useState(false)

    useEffect(() => {
        dispatch(tptefStartTable({ "tableStatus": "RTable" }))
        const ws = new WebSocket("/tptef/main.ws")
        wsRef.current = ws
        ws.onopen = () => setWsReady(true)
        ws.onerror = () => setWsReady(false)
        ws.onclose = () => setWsReady(false)
        return () => { ws.close(); if (wsRef.current === ws) wsRef.current = null; }
    }, [dispatch])

    useEffect(() => {
        const sortSetContentsRev = (_contents: any) => {
            const _sortContentsRev = (a: any, b: any) => b["timestamp"] - a["timestamp"]
            setContents([..._contents].sort(_sortContentsRev))
        }
        if (tableStatus != "RTable") return
        if (!wsRef.current || !wsReady) return
        if (wsRef.current.readyState !== WebSocket.OPEN) return

        const onMessage = (e: MessageEvent) => {
            const msg = JSON.parse(e.data)
            if (msg.message == "processed") { if (Array.isArray(msg["rooms"])) sortSetContentsRev(msg["rooms"]) }
        }
        wsRef.current.addEventListener("message", onMessage)
        sendSearch()
        setTmpRoomKeyhole(""); setTmpRoom(""); setTmpSearch("");
        return () => { wsRef.current?.removeEventListener("message", onMessage) }
    }, [wsReady, tableStatus, token])

    const sendSearch = () => { wsRef.current?.send(JSON.stringify({ "token": token, roomKey: roomKey, "search": tmpSearch })) }

    // fetchAPI
    const createRoom = () => {
        const formData = new FormData()
        formData.append("info", JSON.stringify({ "token": token, roomKey: roomKey }))
        formData.append("create", JSON.stringify({ "roomName": tmpRoom, "roomKeyhole": tmpRoomKeyhole }))
        fetch(new Request("/tptef/main.py", {
            method: "POST",
            body: formData,
            signal: AbortSignal.timeout(xhrTimeout)
        }))
            .then(response => response.json())
            .then(resJ => {
                switch (resJ["message"]) {
                    case "processed":
                        dispatch(tptefStartTable({ tableStatus: "CTable", room: resJ["room"] }))
                        break
                    default:
                        if ("text" in resJ) { CIModal(resJ["message"], resJ["text"]); break; }
                }
            })
            .catch(error => { CIModal("fetchAPI_Error", error.message) })
        setTmpRoomKeyhole("")
        setTmpRoom("")
    }

    const roomTopForm = () => {
        const roomCreateModal = () => {
            return (
                <div>
                    <div className="modal fade" id="roomCreateModal" aria-hidden="true">
                        <div className="modal-dialog">
                            <div className="modal-content">
                                <div className="modal-header">
                                    <h3 className="modal-title fs-5">
                                        <i className="fa-solid fa-hammer mx-1" />部屋作成
                                    </h3>
                                </div>
                                <div className="modal-body row">
                                    <div className="input-group m-1 col-12">
                                        <span className="input-group-text">Roomname</span>
                                        <input type="text" className="form-control" placeholder="Roomname" aria-label="room"
                                            value={tmpRoom} onChange={(evt) => { setTmpRoom(evt.target.value) }} />
                                    </div>
                                    <div className="input-group m-1 col-12">
                                        <span className="input-group-text">Pass</span>
                                        <input type="password" className="form-control" placeholder="Password" aria-label="pass"
                                            value={tmpRoomKeyhole} onChange={(evt) => { setTmpRoomKeyhole(evt.target.value) }} />
                                    </div>
                                    <div className="m-1 col-12">
                                        {tmpRoom == "" ?
                                            <div className="text-warning-emphasis">
                                                Plz Input Roomname
                                            </div> : <div />
                                        }
                                    </div>
                                </div>
                                <div className="modal-footer">
                                    <button type="button" className="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                                    {tmpRoom == "" ?
                                        <button type="button" className="btn btn-outline-primary" data-bs-dismiss="modal" disabled>
                                            <i className="fa-solid fa-hammer mx-1" style={{ pointerEvents: "none" }} />作成
                                        </button> :
                                        <div>
                                            {tmpRoomKeyhole == "" ?
                                                <button type="button" className="btn btn-outline-primary" data-bs-dismiss="modal"
                                                    onClick={() => createRoom()}>
                                                    <i className="fa-solid fa-hammer mx-1" style={{ pointerEvents: "none" }} />作成
                                                </button> :
                                                <button type="button" className="btn btn-outline-warning" data-bs-dismiss="modal"
                                                    onClick={() => { createRoom() }}>
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
                        onClick={() => { sendSearch() }}>
                        <i className="fa-solid fa-magnifying-glass mx-1" style={{ pointerEvents: "none" }} />
                    </button>
                    <input className="flex-fill form-control form-control-lg" type="text" placeholder="部屋名検索" value={tmpSearch}
                        onChange={(evt) => { setTmpSearch(evt.target.value) }}
                        onKeyDown={(evt) => { if (evt.key === "Enter") { evt.preventDefault(); sendSearch(); } }}
                    />
                    <button className="btn btn-outline-primary btn-lg" type="button"
                        onClick={() => { setTmpRoomKeyhole(""); setTmpRoom(""); $("#roomCreateModal").modal("show") }}>
                        <i className="fa-solid fa-hammer mx-1" style={{ pointerEvents: "none" }} />
                        部屋作成
                    </button>
                </div>
            </div>)
    }

    const roomTable = () => {
        const enterButton = (_room: any) => {
            const _locked = _room["passhash"] != ""
            return (
                <button
                    className={_locked ? "btn btn-outline-dark rounded-pill" : "btn btn-outline-primary rounded-pill"}
                    onClick={() => {
                        dispatch(tptefStartTable({ tableStatus: "CTable", room: _room }))
                    }}>
                    <i className={_locked ? "fa-solid fa-lock mx-1" : "fa-solid fa-right-to-bracket mx-1"}
                        style={{ pointerEvents: "none" }} />Enter
                </button>
            )
        }

        const _tmpRecord = []
        for (let i = 0; i < contents.length; i++) {
            if (contents[i]["name"].indexOf(tmpRoom) == -1) continue
            const _tmpData = []
            let _style = { background: "linear-gradient(rgba(60,60,60,0), rgba(60,60,60,0.2))" }
            if (contents[i]["passhash"] != "") {
                _style = { background: "linear-gradient(rgba(60,60,60,0), rgba(150,150,60,0.2))" }
            }
            _tmpData.push(
                <div className="col-12 border d-flex" style={_style} key={`user-${contents[i]["id"]}`}>
                    <h5 className="me-auto">
                        <i className="far fa-user mx-1"></i>{contents[i]["user"]}
                    </h5>
                    {enterButton(contents[i])}
                </div>)
            _tmpData.push(
                <div className="col-12 col-md-10 p-1 d-flex justify-content-center align-items-center border" key={`name-${contents[i]["id"]}`}>
                    <h3>{contents[i]["name"]}</h3>
                </div>)
            _tmpData.push(
                <div className="col-12 col-md-2 p-1 border" key={`ts-${contents[i]["id"]}`}><div className="text-center">
                    {Unixtime2String(Number(contents[i]["timestamp"]))}
                </div></div>)
            _tmpRecord.push(
                <div key={contents[i]["id"]} className="col-12 col-md-6" style={{
                    border: "1px inset silver", borderRadius: "5px", marginBottom: "3px", boxShadow: "2px 2px 1px rgba(60,60,60,0.2)"
                }}>
                    <div className="row p-1">{_tmpData}</div>
                </div>
            )
        }
        return (
            <div>
                {_tmpRecord.length > 0 ? <div className="row m-1">{_tmpRecord}</div> : <h4 className="text-center">Room is NOT exist</h4>}
            </div>)
    }

    return (
        <div>
            {tableStatus == "RTable" ?
                <div className="m-1">
                    {roomTopForm()}
                    {roomTable()}
                </div> : <div />}
            {tableStatus == "CTable" ?
                <div className="m-1">
                    <CTable wsRef={wsRef} wsReady={wsReady} />
                </div> : <div />}
        </div>
    )
}
// titleLogo
export const titleLogo = () => {
    return (<h2 className="rotxin-2" style={{ fontFamily: "Impact", color: "black" }}>
        <i className="far fa-comments mx-1" style={{ pointerEvents: "none" }}></i>チャットアプリ
    </h2>)
}
