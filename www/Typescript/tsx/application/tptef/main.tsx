import React, { useState, useEffect } from 'react';

import { Unixtime2String } from "../../components/util";
import { HIModal, CIModal } from "../../components/imodals";
import { accountSetState, tptefSetState, tptefStartTable } from '../../components/slice'
import { useAppSelector, useAppDispatch } from '../../components/store'
import { CTable } from "./components/chat"
import "../../stylecheets/style.sass";

export const AppMain = () => {
    const user = useAppSelector((state) => state.account.user)
    const userId = useAppSelector((state) => state.account.id)
    const token = useAppSelector((state) => state.account.token)
    const roomKey = useAppSelector((state) => state.account.roomKey)
    const tableStatus = useAppSelector((state) => state.tptef.tableStatus)
    const dispatch = useAppDispatch()
    const xhrTimeout = 3000

    const [tmpRoomKey, setTmpRoomKey] = useState("")
    const [tmpRoom, setTmpRoom] = useState("")
    const [tmpTargetRoom, setTmpTargetRoom] = useState({ "id": -1, "user": "", "userid": -1, "room": "", "timestamp": 0, "passhash": "" })
    const [contents, setContents] = useState([])
    const AppDispatch = useAppDispatch()

    useEffect(() => {
        if (tableStatus == "RTable") searchRoom()
    }, [userId])
    useEffect(() => {
        AppDispatch(tptefStartTable({ "tableStatus": "RTable" }))
        setTmpRoomKey(""); setTmpRoom("")
        searchRoom()
    }, [])


    const stringForSend = (_additionalDict: {} = {}) => {
        const _sendDict = Object.assign(
            {
                "token": token, "user": user, roomKey: roomKey
            }, _additionalDict)
        return (JSON.stringify(_sendDict))
    }
    // related to fetchAPI
    const searchRoom = () => {
        const sortSetContentsRev = (_contents: any = []) => {
            const _sortContentsRev = (a: any, b: any) => { return b["timestamp"] - a["timestamp"] }
            setContents(_contents.sort(_sortContentsRev))
        }
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
    const createRoom = () => {
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
                    case "processed":
                        {
                            dispatch(tptefStartTable({ tableStatus: "CTable", room: resJ["room"] }))
                            break;
                        }
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
                                            onClick={() => { HIModal("部屋名が未入力") }}>
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
                            onClick={() => { HIModal("ログインが必要") }}>
                            <i className="fa-solid fa-circle-info mx-1" style={{ pointerEvents: "none" }} />
                            部屋作成
                        </button> :
                        <button className="btn btn-outline-primary btn-lg" type="button"
                            onClick={() => {  $('#roomCreateModal').modal('show'); }}>
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
                                                dispatch(tptefStartTable({
                                                    tableStatus: "CTable",
                                                    room: tmpTargetRoom
                                                }))
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
        const enterButton = (_i: number) => {
            if (contents[_i]["passhash"] == "")
                return (
                    <button className="btn btn-outline-primary rounded-pill"
                        onClick={(evt: any) => {
                            dispatch(tptefStartTable({
                                tableStatus: "CTable",
                                room: JSON.parse(evt.target.value)
                            }))
                        }} value={JSON.stringify(contents[i])}>
                        <i className="fa-solid fa-right-to-bracket mx-1" style={{ pointerEvents: "none" }}></i>入室
                    </button>
                )
            if (contents[_i]["userid"] == userId)
                return (
                    <button className="btn btn-outline-dark rounded-pill"
                        onClick={(evt: any) => {
                            dispatch(tptefStartTable({
                                tableStatus: "CTable",
                                room: JSON.parse(evt.target.value)
                            }))
                        }} value={JSON.stringify(contents[i])}>
                        <i className="fa-solid fa-lock mx-1" style={{ pointerEvents: "none" }}></i>入室
                    </button>)
            return (
                <button className="btn btn-outline-dark rounded-pill"
                    onClick={(evt: any) => {
                        setTmpTargetRoom(JSON.parse(evt.target.value))
                        $('#roomInterModal').modal('show')
                    }} value={JSON.stringify(contents[i])}>
                    <i className="fa-solid fa-lock mx-1" style={{ pointerEvents: "none" }}></i>入室
                </button>)
        }
        const _tmpRecord = [];
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
                    {enterButton(i)}
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
    // applicationRender
    return (
        <div>
            {tableStatus == "RTable" ?
                <div className="m-1">
                    {roomTopForm()}
                    {roomTable()}
                </div> : <div />}
            {tableStatus == "CTable" ?
                <div className="m-1">
                    <CTable />
                </div> : <div />}
        </div>
    )
};

// titleLogo
export const titleLogo = () => {
    return (<h2 className="rotxin-2" style={{ fontFamily: "Impact", color: "black" }}>
        <i className="far fa-comments mx-1" style={{ pointerEvents: "none" }}></i>チャットアプリ
    </h2>)
}