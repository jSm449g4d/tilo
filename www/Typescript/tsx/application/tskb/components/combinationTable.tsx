import React, { useState, useEffect } from 'react';

import { HIModal, CIModal } from "../../../components/imodals";
import { satisfyDictKeys, Unixtime2String } from "../../../components/util";
import { accountSetState, tskbSetState, startTable } from '../../../components/slice'
import { useAppSelector, useAppDispatch } from '../../../components/store'


export const CTable = () => {
    const [contents, setContents] = useState([])
    const [tmpKeyword, setTmpKeyword] = useState("")
    const [tmpOffset, setTmpOffset] = useState(0)
    const [tmpListTags, setTmpListTags] = useState([])
    const [tmpSearchRadio, setTmpSearchRadio] = useState("name")
    const [tmpName, setTmpName] = useState("")
    const [tmpTag, setTmpTag] = useState("")
    const [tmpDescription, setTmpDescription] = useState("")
    const [tmpPrivateFlag, setTmpPrivateFlag] = useState(false)

    const user = useAppSelector((state) => state.account.user)
    const userId = useAppSelector((state) => state.account.id)
    const token = useAppSelector((state) => state.account.token)
    const tableStatus = useAppSelector((state) => state.tskb.tableStatus)
    const reloadFlag = useAppSelector((state) => state.tskb.reloadFlag)
    const AppDispatch = useAppDispatch()
    const xhrTimeout = 3000
    const xhrDelay = 100


    useEffect(() => {
        if (tableStatus == "CTable") setTimeout(() => gatherTag(), xhrDelay)
        setTmpKeyword("")
        setTmpListTags([])
    }, [reloadFlag])
    useEffect(() => {
        setTmpKeyword("")
        setTmpOffset(0)
        setTmpSearchRadio("name")
    }, [userId])
    const initCreateForm = () => {
        setTmpName("")
        setTmpTag("")
        setTmpDescription("")
        setTmpPrivateFlag(false)
    }
    const stringForSend = (_additionalDict: {} = {}) => {
        const _sendDict = Object.assign(
            {
                "token": token, "user": user,
            }, _additionalDict)
        return (JSON.stringify(_sendDict))
    }
    // fetchAPI
    const gatherTag = (_tmpPrivateFlag = false) => {
        const headers = new Headers();
        const formData = new FormData();
        formData.append("info", stringForSend())
        formData.append("gathertag", JSON.stringify({}))
        const request = new Request("/tskb/main.py", {
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
                        setTmpListTags(resJ["tags"])
                        setTimeout(() => searchCombination(undefined, undefined, tmpOffset), xhrDelay);
                        break;
                    }
                    default: {
                        if ("text" in resJ) CIModal(resJ["text"]); break;
                    }
                }
            })
            .catch(error => {
                CIModal("通信エラー")
                console.error(error.message)
            });
    }
    const searchCombination = (_keyword = tmpKeyword, _searchRadio = tmpSearchRadio, _offset: number = 0) => {
        setTmpKeyword(_keyword)
        setTmpOffset(_offset)
        setTmpSearchRadio(_searchRadio)
        const sortSetContentsRev = (_contents: any = []) => {
            const _sortContentsRev = (a: any, b: any) => { return b["timestamp"] - a["timestamp"] }
            setContents(_contents.sort(_sortContentsRev))
        }
        const headers = new Headers();
        const formData = new FormData();
        formData.append("info", stringForSend())
        formData.append("search", JSON.stringify({
            "keyword": _keyword, "offset": _offset, "search_radio": _searchRadio
        }))
        const request = new Request("/tskb/main.py", {
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
                        sortSetContentsRev(resJ["combinations"]);
                        AppDispatch(accountSetState({ token: resJ["token"] }));
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
    const createCombination = () => {
        const headers = new Headers();
        const formData = new FormData();
        formData.append("info", stringForSend())
        formData.append("create", JSON.stringify({
            "name": tmpName, "tag": tmpTag, "description": tmpDescription,
            "privateFlag": tmpPrivateFlag,
        }))
        const request = new Request("/tskb/main.py", {
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
                        setTimeout(() => {
                            AppDispatch(startTable({
                                tableStatus: "MTable",
                                combination: resJ["combination"]
                            }))
                        }, xhrDelay)
                        HIModal("レシピ作成成功")
                        break;
                    default: {
                        if ("text" in resJ) CIModal(resJ["text"]);
                        searchCombination(); break;
                    }
                }
            })
            .catch(error => {
                CIModal("通信エラー")
                console.error(error.message)
            });
    }
    // modal
    const CTCombinationCreateModal = () => {
        return (
            <div>
                <div className="modal fade" id="CTCombinationCreateModal" aria-labelledby="exampleModalLabel" aria-hidden="true">
                    <div className="modal-dialog">
                        <div className="modal-content">
                            <div className="modal-header">
                                <h4 className="modal-title">
                                    <i className="fa-solid fa-hammer mx-1" />レシピ作成
                                </h4>
                            </div>
                            <div className="modal-body d-flex flex-column justify-content-center">
                                <div className="input-group m-1">
                                    <span className="input-group-text">レシピ名</span>
                                    <input type="text" className="form-control" placeholder="レシピ名" aria-label="user"
                                        value={tmpName.slice(0, 50)}
                                        onChange={(evt) => { setTmpName(evt.target.value) }} />
                                </div>
                                <div className="input-group m-1">
                                    <span className="input-group-text"><i className="fa-solid fa-tag mx-1" /></span>
                                    <input className="form-control" type="text" placeholder="タグ名"
                                        value={tmpTag.slice(0, 20)}
                                        onChange={(evt: any) => setTmpTag(evt.target.value)} />
                                </div>
                                <h5>概説</h5>
                                <textarea className="form-control m-1" rows={4}
                                    value={tmpDescription.slice(0, 200)}
                                    onChange={(evt) => { setTmpDescription(evt.target.value) }} />
                                {tmpPrivateFlag == false ?
                                    <button className="btn btn-outline-warning btn-lg" type="button"
                                        onClick={() => { setTmpPrivateFlag(true) }}>
                                        <i className="fa-solid fa-lock-open mx-1" style={{ pointerEvents: "none" }} />
                                        公開&nbsp;&nbsp;
                                    </button> :
                                    <button className="btn btn-warning btn-lg" type="button"
                                        onClick={() => { setTmpPrivateFlag(false) }}>
                                        <i className="fa-solid fa-lock mx-1" style={{ pointerEvents: "none" }} />
                                        非公開
                                    </button>
                                }
                            </div>
                            <div className="modal-footer d-flex">
                                <button type="button" className="btn btn-secondary me-auto" data-bs-dismiss="modal">
                                    Close
                                </button>
                                {tmpName != "" && token != "" ? <div>
                                    <button type="button" className="btn btn-outline-primary " data-bs-dismiss="modal"
                                        onClick={() => createCombination()}>
                                        <i className="fa-solid fa-hammer mx-1" style={{ pointerEvents: "none" }} />作成
                                    </button>
                                </div> :
                                    <button type="button" className="btn btn-outline-primary" disabled>
                                        <i className="fa-solid fa-hammer mx-1" style={{ pointerEvents: "none" }} />作成
                                    </button>
                                }
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        )
    }
    // app
    const topForm = () => {
        const _searchNameForm = (
            <div className="input-group d-flex justify-content-center align-items-center my-1">
                <button className="btn btn-outline-success btn-lg" type="button" id="CTSearchButton"
                    onClick={() => { searchCombination() }}>
                    <i className="fa-solid fa-magnifying-glass mx-1" style={{ pointerEvents: "none" }} />
                    素材検索
                </button>
                <input className="flex-fill form-control form-control-lg" type="text" placeholder="レシピ検索"
                    value={tmpKeyword} onChange={(evt: any) => { setTmpKeyword(evt.target.value) }}
                    onKeyDown={(evt: any) => {
                        if (evt.key == "Enter") $("#CTSearchButton").trigger("click")
                    }} />
            </div>
        )
        const _searchRadioForm = (
            <div className="input-group d-flex justify-content-evenly my-1">
                <div className="form-check form-check-inline">
                    <input className="form-check-input" type="radio" name="exampleRadios"
                        checked={tmpSearchRadio == "name"}
                        onChange={() => setTmpSearchRadio("name")} />
                    <label className="form-check-label">
                        名前検索
                    </label>
                </div>
                <div className="form-check form-check-inline">
                    <input className="form-check-input" type="radio" name="exampleRadios"
                        checked={tmpSearchRadio == "tag"}
                        onChange={() => setTmpSearchRadio("tag")} />
                    <label className="form-check-label">
                        タグ検索
                    </label>
                </div>
                {userId != -1 ?
                    <div className="form-check form-check-inline">
                        <input className="form-check-input" type="radio" name="exampleRadios"
                            checked={tmpSearchRadio == "private"}
                            onChange={() => {
                                searchCombination("", "private")
                            }} />
                        <label className="form-check-label">
                            マイ素材表示
                        </label>
                    </div> :
                    <div />
                }
            </div>
        )
        const _selectTagForm = () => {
            const _tagButton = []
            for (let _i = 0; _i < tmpListTags.length; _i++) {
                _tagButton.push(
                    <button className="btn btn-outline-dark rounded-pill m-1"
                        type="button" value={tmpListTags[_i]}
                        onClick={(evt: any) => {
                            searchCombination(evt.target.value)
                        }}>
                        <i className="fa-solid fa-tag mx-1" style={{ pointerEvents: "none" }} />
                        {tmpListTags[_i]}
                    </button>
                )
            }
            return (
                <div className="my-1">
                    {_tagButton}
                </div>
            )
        }
        const _offsetButtonForm = () => {
            return (
                <div className="btn-group" role="group">
                    {0 < tmpOffset ?
                        <button type="button" className="btn btn-outline-primary"
                            onClick={() => {
                                searchCombination(undefined, undefined, tmpOffset - 1)
                            }}>←prev</button> :
                        <button type="button" className="btn btn-outline-primary"
                            disabled>←prev</button>
                    }
                    <span className="input-group-text mx-1"><h4>{tmpOffset}</h4></span>
                    {0 < contents.length ?
                        <button type="button" className="btn btn-outline-primary"
                            onClick={() => {
                                searchCombination(undefined, undefined, tmpOffset + 1)
                            }}>next→</button> :
                        <button type="button" className="btn btn-outline-primary"
                            disabled>next→</button>
                    }
                </div>
            )
        }
        return (
            <div>
                {_searchRadioForm}
                {tmpSearchRadio == "name" ? _searchNameForm : <div />}
                {tmpSearchRadio == "tag" ? _selectTagForm() : <div />}
                <div className="d-flex justify-content-between my-1">
                    <div />
                    {_offsetButtonForm()}
                    {token == "" ?
                        <div /> :
                        <button className="btn btn-outline-primary btn-lg" type="button"
                            onClick={() => {
                                initCreateForm();
                                $('#CTCombinationCreateModal').modal('show');
                            }} >
                            <i className="fa-solid fa-hammer mx-1" style={{ pointerEvents: "none" }} />
                            レシピ作成
                        </button>}
                </div>
            </div>)

    }
    const _tmpRecord = [];
    if (contents.length == 0) {
        _tmpRecord.push(
            <div className="row d-flex justify-content-center my-1 ">
                素材が存在しません
            </div>)
    }
    for (var i = 0; i < contents.length; i++) {
        const _tmpData = [];
        var _style = { background: "linear-gradient(rgba(60,60,60,0), rgba(60,60,60,0.2))" }
        if (contents[i]["userid"] == userId)
            _style = { background: "linear-gradient(rgba(60,60,60,0), rgba(100,200,150,0.3))" }
        if (contents[i]["passhash"] == "0")
            _style = { background: "linear-gradient(rgba(60,60,60,0), rgba(150,150,60,0.3))" }
        _tmpData.push(
            <div className="col-12 border d-flex" style={_style}>
                <h5 className="me-auto">
                    <i className="fa-solid fa-stroopwafel mx-1"></i>{contents[i]["name"]}
                </h5>
                <button className="btn btn-outline-primary rounded-pill"
                    onClick={(evt: any) => {
                        AppDispatch(startTable({
                            tableStatus: "MTable",
                            combination: JSON.parse(evt.target.value)
                        }))
                    }} value={JSON.stringify(contents[i])}>
                    <i className="fa-solid fa-right-to-bracket mx-1" style={{ pointerEvents: "none" }} />
                    閲覧
                </button>
            </div>)
        _tmpData.push(
            <div className="col-12 col-md-12 p-1">
                <div className="d-flex justify-content-center">
                    <img className="img-fluid" src={"/tskb/main.py?combination_imgid=" + contents[i]["id"]}
                        onError={(evt: any) => { evt.target.style.visibility = "hidden" }}
                        style={{ height: 300, objectFit: "contain" }} />
                </div>
            </div>)
        _tmpData.push(
            <div className="col-12 col-md-12 p-1" style={{ "wordBreak": "break-all" }}>
                {contents[i]["tag"] != "" ?
                    <button className="btn btn-outline-dark btn-sm rounded-pill" disabled>
                        <i className="fa-solid fa-tag mx-1" />{contents[i]["tag"]}
                    </button > :
                    <div />}
                {contents[i]["description"]}
            </div>)
        _tmpRecord.push(
            <div className="col-12 col-md-6 col-lg-4" style={{
                border: "1px inset silver", borderRadius: "5px", marginBottom: "3px", boxShadow: "2px 2px 1px rgba(60,60,60,0.2)"
            }}>
                <div className="row p-1">{_tmpData}</div>
            </div>
        )
    }
    return (
        <div className="p-1" style={{
            background: "linear-gradient(45deg,rgba(250,200,200,0.2), rgba(60,60,60,0.0))"
        }}>
            {CTCombinationCreateModal()}
            {topForm()}
            <div className="row m-1 slidein-1-reverse">
                {_tmpRecord}
            </div>
        </div>)
}