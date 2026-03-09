import React, { useState, useEffect } from 'react';
import { createRoot } from "react-dom/client"
import { stopf5, Query2Dict } from "./util";
require.context('../application/', true, /\.ts(x?)$/)
import { Provider } from "react-redux"
import { HIModal, CIModal } from "./imodals";
import { store } from "./store";
import { accountInit, accountSetState } from './slice'
import { useAppSelector, useAppDispatch } from './store'

const xhrTimeout = 3000
const RESERVED_NAME = ["GUEST", "guest", "HOST", "host", "ANONYMOUS", "anonymous"]

export const AppWidgetHead = () => {

    const [tmpUser, setTmpUser] = useState("")
    const [tmpPass, setTmpPass] = useState("")
    const [tmpMail, setTmpMail] = useState("")
    const [tmpButtonFlag, setTmpButtonFlag] = useState(false)
    const [tmpRoomKey, setTmpRoomKey] = useState("")

    const user = useAppSelector((state) => state.account.user)
    const token = useAppSelector((state) => state.account.token)
    const mail = useAppSelector((state) => state.account.mail)
    const roomKey = useAppSelector((state) => state.account.roomKey)
    const dispatch = useAppDispatch()

    useEffect(() => {
        if (token == "") { _signupGuest() }
        const id = setInterval(() => { _newToken() }, 600000);
        return () => clearInterval(id);
    }, [token]);

    // accountControl
    const _logoutInit = () => {
        setTmpUser(""); setTmpPass(""); setTmpMail(""); setTmpRoomKey(""); setTmpButtonFlag(false); dispatch(accountInit());
    }
    const _formInit = () => {
        setTmpUser(""); setTmpPass(""); setTmpMail(""); setTmpRoomKey(""); setTmpButtonFlag(false);
    }

    // fetchAPI
    const postJson = (key: string, body: object, onProcessed?: (resJ: any) => void,) => {
        const formData = new FormData();
        formData.append("info", JSON.stringify({ "token": token, "user": tmpUser, "pass": tmpPass, "mail": tmpMail, "roomKey": roomKey }));
        formData.append(key, JSON.stringify(body));
        fetch(new Request("/login/main.py", {
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
    const _signupGuest = () => {
        const formData = new FormData();
        formData.append("info", JSON.stringify({ "token": "", "user": "guest", "pass": "", "mail": "", "roomKey": roomKey }));
        formData.append("signup", JSON.stringify({}));
        fetch(new Request("/login/main.py", {
            method: "POST",
            body: formData,
            signal: AbortSignal.timeout(xhrTimeout),
        }))
            .then(response => response.json())
            .then((resJ: any) => {
                switch (resJ["message"]) {
                    case "processed": { dispatch(accountSetState({ token: resJ["token"], id: resJ["id"], user: resJ["user"], mail: resJ["mail"] })); break; }
                    default: {
                        if ("text" in resJ) CIModal(resJ["text"]);
                        break;
                    }
                }
            })
            .catch((e) => CIModal("fetchAPI_Error", e.message));
    }
    const _login = () => {
        if (RESERVED_NAME.some((name) => tmpUser.toUpperCase().includes(name)
        )) { CIModal("userName_reserved", tmpUser + ": is RESERVED_NAME"); _formInit(); return; };
        postJson("login", {}, (resJ) => {
            dispatch(accountSetState({ token: resJ["token"], id: resJ["id"], user: resJ["user"], mail: resJ["mail"] }));
            _formInit();
        });
    };
    const _signup = () => {
        if (RESERVED_NAME.some((name) => tmpUser.toUpperCase().includes(name)
        )) { CIModal("userName_reserved", tmpUser + ": is RESERVED_NAME"); _formInit(); return; };
        postJson("signup", {}, (resJ) => {
            dispatch(accountSetState({ token: resJ["token"], id: resJ["id"], user: resJ["user"], mail: resJ["mail"] }));
            CIModal("Success", "Create account")
            _formInit();
        });
    }
    const _logout = () => { _logoutInit() }
    const _accountChange = () => {
        postJson("account_change", {}, (resJ) => {
            dispatch(accountSetState({ token: resJ["token"], id: resJ["id"], user: resJ["user"], mail: resJ["mail"] }));
            CIModal("Success", "Change account setting")
            _formInit();
        });
    }
    const _accountDelete = () => {
        postJson("account_delete", {}, () => {
            _logoutInit();
            CIModal("Success", "Deleted your account")
            _formInit();
        });
    };
    const _newToken = () => {
        if (token == "") return;
        postJson("new_token", {}, (resJ) => {
            dispatch(accountSetState({ token: resJ["token"], id: resJ["id"], user: resJ["user"] }));
        });
    }
    const _accountForm = () => {
        const accountLoginModal = () => {
            return (
                <div className="modal fade" id="accountLoginModal" aria-labelledby="exampleModalLabel" aria-hidden="true">
                    <div className="modal-dialog">
                        <div className="modal-content">
                            <div className="modal-headerrow">
                                <div className="modal-title d-flex m-2">
                                    <h3 className="me-auto"><i className="fa-solid fa-pen text-primary mx-1" />LogIn</h3>
                                    <button type="button" className="btn btn-outline-info"
                                        onClick={() =>
                                            HIModal("開発中",
                                                "現在メール機能は開発中の為、操作できません")} >
                                        <i className="fa-regular fa-envelope mx-1" style={{ pointerEvents: "none" }}></i>
                                        パスワード再設定
                                    </button>
                                </div>
                            </div>
                            <div className="modal-body">
                                <div className="row">
                                    <div className="input-group col-12 m-1">
                                        <span className="input-group-text">User</span>
                                        <input type="text" className="form-control" placeholder="Username" aria-label="Username"
                                            value={tmpUser} onChange={(evt) => { setTmpUser(evt.target.value) }} />
                                    </div>
                                    <div className="input-group col-12 m-1">
                                        <span className="input-group-text">Pass</span>
                                        <input type="password" className="form-control" placeholder="pass" aria-label="pass"
                                            aria-labelledby="passwordHelpBlock"
                                            value={String(tmpPass).replace(/[^0-9|^a-z|^A-Z|]/g, '')}
                                            onChange={(evt) => { setTmpPass(evt.target.value) }} />
                                    </div>
                                    <div className="form-check form-switch m-1 col-12">
                                        <input className="form-check-input" type="checkbox" role="switch"
                                            style={{ transform: "rotate(90deg)" }} disabled
                                            onChange={(evt: any) => {
                                                if (evt.target.checked == true) {
                                                    $('#accountSignupModalMail').prop("disabled", false)
                                                } else {
                                                    $('#accountSignupModalMail').prop("disabled", true)
                                                    setTmpMail("")
                                                }
                                            }}>
                                        </input><input type="text" className="form-control" placeholder="Mailaddress"
                                            value={tmpMail} onChange={(evt) => { setTmpMail(evt.target.value) }}
                                            disabled id="accountSignupModalMail" />
                                    </div>
                                    <div className="form-check m-1 col-12">
                                        {tmpUser == "" ?
                                            <div className="text-warning-emphasis">
                                                Plz Input Username
                                            </div> :
                                            <div />
                                        }
                                        {tmpPass.length < 8 ?
                                            <div className="text-warning-emphasis">
                                                Plz Input a password of 8 or more characters
                                            </div> :
                                            <div />
                                        }
                                    </div>
                                </div>
                            </div>
                            <div className="modal-footer d-flex">
                                <button type="button" className="btn btn-outline-secondary me-auto" data-bs-dismiss="modal"
                                    onClick={() => _formInit()}>
                                    Close
                                </button>
                                {tmpUser == "" || tmpPass.length < 8 ?
                                    <button type="button" className="btn btn-outline-success" disabled>
                                        <i className="fa-solid fa-circle-info mx-1" />Login
                                    </button> :
                                    <button type="button" className="btn btn-outline-success" data-bs-dismiss="modal"
                                        onClick={() => _login()}>
                                        <i className="fa-solid fa-arrow-right-to-bracket mx-1" style={{ pointerEvents: "none" }} />Login
                                    </button>
                                }
                            </div>
                        </div>
                    </div>
                </div>
            )
        }
        const accountSignupModal = () => {
            return (
                <div className="modal fade" id="accountSignupModal" aria-labelledby="exampleModalLabel" aria-hidden="true">
                    <div className="modal-dialog">
                        <div className="modal-content">
                            <div className="modal-headerrow">
                                <div className="modal-title d-flex m-2">
                                    <h3 className="me-auto"><i className="fa-solid fa-pen text-primary mx-1" />SignUp</h3>
                                </div>
                            </div>
                            <div className="modal-body">
                                <div className="row">
                                    <div className="input-group col-12 m-1">
                                        <span className="input-group-text">User</span>
                                        <input type="text" className="form-control" placeholder="Username" aria-label="Username"
                                            value={tmpUser} onChange={(evt) => { setTmpUser(evt.target.value) }} />
                                    </div>
                                    <div className="input-group col-12 m-1">
                                        <span className="input-group-text">Pass</span>
                                        <input type="password" className="form-control" placeholder="pass" aria-label="pass"
                                            aria-labelledby="passwordHelpBlock"
                                            value={String(tmpPass).replace(/[^0-9|^a-z|^A-Z|]/g, '')}
                                            onChange={(evt) => { setTmpPass(evt.target.value) }} />
                                    </div>
                                    <div className="form-check m-1 col-12">
                                        {tmpUser == "" ?
                                            <div className="text-warning-emphasis">
                                                Plz Input Username
                                            </div> :
                                            <div />
                                        }
                                        {tmpPass.length < 8 ?
                                            <div className="text-warning-emphasis">
                                                Plz Input a password of 8 or more characters
                                            </div> :
                                            <div />
                                        }
                                    </div>
                                </div>
                            </div>
                            <div className="modal-footer d-flex">
                                <button type="button" className="btn btn-outline-secondary me-auto" data-bs-dismiss="modal"
                                    onClick={() => _formInit()}>
                                    Close
                                </button>
                                {tmpUser == "" || tmpPass.length < 8 ?
                                    <button type="button" className="btn btn-outline-primary" disabled>
                                        <i className="fa-solid fa-circle-info mx-1" />Register
                                    </button> :
                                    <button type="button" className="btn btn-primary" data-bs-dismiss="modal"
                                        onClick={() => _signup()}>
                                        <i className="fa-solid fa-pen mx-1" style={{ pointerEvents: "none" }} />Register
                                    </button>
                                }
                            </div>
                        </div>
                    </div>
                </div>
            )
        }
        const accountConfigModal = () => {
            return (
                <div className="modal fade" id="accountConfigModal" aria-labelledby="exampleModalLabel" aria-hidden="true">
                    <div className="modal-dialog">
                        <div className="modal-content">
                            <div className="modal-headerrow">
                                <h3 className="modal-title row-12 m-1">
                                    <i className="fa-solid fa-wrench text-warning mx-1" />Account Config
                                </h3>
                                <h4 className="modal-title row-12 m-1">
                                    <i className="fa-regular fa-user mx-1" />{user}
                                </h4>
                                <h5 className="modal-title row-12 m-1">
                                    {mail == "" ?
                                        <div>
                                            <i className="fa-regular fa-envelope mx-1" />Not Registered
                                        </div>
                                        : <div>
                                            <i className="fa-regular fa-envelope mx-1" />{mail}
                                        </div>}
                                </h5>
                            </div>
                            <div className="modal-body">
                                <div className="form-check form-switch m-1">
                                    <input className="form-check-input" type="checkbox" role="switch"
                                        style={{ transform: "rotate(90deg)" }}
                                        onChange={(evt: any) => {
                                            if (evt.target.checked == true) {
                                                $('#accountConfigModalUser').prop("disabled", false)
                                            } else {
                                                $('#accountConfigModalUser').prop("disabled", true)
                                                setTmpUser("")
                                            }
                                        }}>
                                    </input><input type="text" className="form-control" placeholder="Username"
                                        value={tmpUser} onChange={(evt) => { setTmpUser(evt.target.value) }}
                                        disabled id="accountConfigModalUser" />
                                </div>
                                <div className="form-check form-switch m-1">
                                    <input className="form-check-input" type="checkbox" role="switch"
                                        style={{ transform: "rotate(90deg)" }}
                                        onChange={(evt: any) => {
                                            if (evt.target.checked == true) {
                                                $('#accountConfigModalPass').prop("disabled", false)
                                            } else {
                                                $('#accountConfigModalPass').prop("disabled", true)
                                                setTmpPass("")
                                            }
                                        }}>
                                    </input><input type="password" className="form-control" placeholder="Password"
                                        value={String(tmpPass).replace(/[^0-9|^a-z|^A-Z|]/g, '')}
                                        onChange={(evt) => { setTmpPass(evt.target.value) }}
                                        disabled id="accountConfigModalPass" />
                                </div>
                                <div className="form-check form-switch m-1">
                                    <input className="form-check-input" type="checkbox" role="switch"
                                        style={{ transform: "rotate(90deg)" }} disabled
                                        onChange={(evt: any) => {
                                            if (evt.target.checked == true) {
                                                $('#accountConfigModalMail').prop("disabled", false)
                                            } else {
                                                $('#accountConfigModalMail').prop("disabled", true)
                                                setTmpMail("")
                                            }
                                        }}>
                                    </input><input type="text" className="form-control" placeholder="Mailaddress"
                                        value={tmpMail} onChange={(evt) => { setTmpMail(evt.target.value) }}
                                        disabled id="accountConfigModalMail" />
                                </div>
                                <div className="form-check m-1">
                                    {tmpUser == "" && tmpPass.length < 8 && tmpMail == "" ?
                                        <div className="text-warning-emphasis">
                                            Plz Input a password of 8 or more characters
                                        </div> :
                                        <div />
                                    }
                                </div>
                            </div>
                            <div className="modal-footer d-flex">
                                <button type="button" className="btn btn-outline-secondary" data-bs-dismiss="modal">Close</button>
                                {tmpUser == "" && tmpPass.length < 8 && tmpMail == "" ?
                                    <button type="button" className="btn btn-info me-auto"
                                        onClick={() =>
                                            HIModal("変更したい情報を入力して下さい",
                                                "各項目のチェックボックスをオンにすることで入力可能になります。" +
                                                "オンにした項目が更新されます。" +
                                                "パスワードは八文字以上。" +
                                                "※現在メール機能は開発中の為、選択できません。")}>
                                        <i className="fa-solid fa-circle-info mx-1" />Update
                                    </button> :
                                    <button type="button" className="btn btn-warning me-auto" data-bs-dismiss="modal"
                                        onClick={() => _accountChange()}>
                                        <i className="fa-regular fa-user mx-1" style={{ pointerEvents: "none" }} />Update
                                    </button>

                                }
                                <div className="form-check form-switch m-1">
                                    <input className="form-check-input" type="checkbox" role="switch"
                                        style={{ transform: "rotate(90deg)" }}
                                        onChange={(evt: any) => setTmpButtonFlag(evt.target.checked)}>
                                    </input>
                                    {tmpButtonFlag == false ?
                                        <button className="btn btn-danger" type="button" data-bs-dismiss="modal" disabled>
                                            <i className="fa-solid fa-trash mx-1" style={{ pointerEvents: "none" }}></i>Delete
                                        </button> :
                                        <button className="btn btn-danger" type="button" data-bs-dismiss="modal"
                                            onClick={() => _accountDelete()} >
                                            <i className="fa-solid fa-trash mx-1" style={{ pointerEvents: "none" }}></i>Delete
                                        </button>
                                    }
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )
        }
        const roomKeyModal = () => {
            return (
                <div className="modal fade" id="roomKeyModal" aria-labelledby="exampleModalLabel" aria-hidden="true">
                    <div className="modal-dialog">
                        <div className="modal-content">
                            <div className="modal-header">
                                <h1 className="modal-title fs-5">
                                    <i className="fa-solid fa-key mx-1" />Set RoomKey
                                </h1>
                            </div>
                            <div className="modal-body row">
                                <div className="input-group m-1 col-12">
                                    <span className="input-group-text">Pass</span>
                                    <input type="password" className="form-control" placeholder="RoomKey" aria-label="RoomKey"
                                        value={tmpRoomKey} onChange={(evt) => { setTmpRoomKey(evt.target.value) }} />
                                </div>
                            </div>
                            <div className="modal-footer">
                                <button type="button" value={-1} id="roomInterModalButton"
                                    className="btn btn-secondary" data-bs-dismiss="modal" onClick={() => { _formInit() }}>
                                    Close
                                </button>
                                <button type="button" className="btn btn-outline-primary" data-bs-dismiss="modal"
                                    onClick={
                                        () => {
                                            dispatch(accountSetState({ roomKey: tmpRoomKey }))
                                            _formInit()
                                        }}>
                                    {tmpRoomKey == "" ? <div>Unset Key</div> :
                                        <div><i className="fa-solid fa-right-to-bracket mx-1" style={{ pointerEvents: "none" }} />Set Key</div>}
                                </button>

                            </div>
                        </div>
                    </div>
                </div>
            )
        }
        const roomKeyButton = () => {
            return (
                <button className="btn btn-outline-dark" type="button" aria-expanded="false"
                    onClick={() => { $('#roomKeyModal').modal('show'); }}>
                    {roomKey == "" ?
                        <div style={{ color: "gray", fontWeight: "bold" }}><i className="fa-solid fa-key mx-1" style={{ pointerEvents: "none" }} />No key</div> :
                        <div style={{ color: "olive", fontWeight: "bold" }}><i className="fa-solid fa-key mx-1" style={{ pointerEvents: "none" }} />Set key</div>
                    }
                </button>)
        }
        const _userNameTitle = () => {
            return (
                <div className="d-flex justify-content-center align-items-center h-100">
                    {token != "" ? <h4 className="mx-2"> {user}</h4> : <h3 className="mx-2">  No User</h3>}
                </div>)
        }
        return (
            <div>
                {accountLoginModal()}
                {accountSignupModal()}
                {accountConfigModal()}
                {roomKeyModal()}
                <div className="d-flex flex-column">
                    {_userNameTitle()}
                    {user.includes("GUEST") || user.includes("HOST") || user.includes("ANONYMOUS") ?
                        <div className="d-flex justify-content-center align-items-center h-100">
                            <div className="btn-group">
                                {roomKeyButton()}
                                <button className="btn btn-outline-success" type="button" aria-expanded="false"
                                    onClick={() => { _formInit(); $('#accountLoginModal').modal('show'); }}>
                                    <i className="fa-solid fa-arrow-right-to-bracket mx-1" style={{ pointerEvents: "none" }}></i>Login
                                </button>
                                <button className="btn btn-outline-primary" type="button" aria-expanded="false"
                                    onClick={() => { _formInit(); $('#accountSignupModal').modal('show'); }}>
                                    <i className="fa-solid fa-pen mx-1" style={{ pointerEvents: "none" }}></i>Signup
                                </button>
                            </div>
                        </div> :
                        <div className="d-flex justify-content-center align-items-center h-100">
                            <div className="btn-group">
                                {roomKeyButton()}
                                <button className="btn btn-outline-dark" type="button" aria-expanded="false"
                                    onClick={() => { _formInit(); $('#accountConfigModal').modal('show'); }}>
                                    <i className="fa-solid fa-wrench mx-1" style={{ pointerEvents: "none" }}></i>Config
                                </button>
                                <button className="btn btn-outline-dark" type="button" aria-expanded="false"
                                    onClick={() => { _logout() }}>
                                    <i className="fa-solid fa-right-from-bracket mx-1" style={{ pointerEvents: "none" }}></i>Logout
                                </button>
                            </div>
                        </div>}
                </div>
            </div>)
    }
    // mainAppRender
    const _switchApp = (application: string) => {
        if (stopf5.check("_switchapp", 50, true) == false) return; // To prevent high freq access
        import("../application/" + application).then((module) => {
            const appMain = createRoot(document.getElementById("appMain")!)
            appMain.render(<Provider store={store}><module.AppMain /></Provider>)
            const titlelogo = createRoot(document.getElementById("titlelogo")!)
            titlelogo.render(<Provider store={store}><module.titleLogo /></Provider>)
        })
    }
    return (
        <div style={{ borderBottom: "3px double gray", background: "linear-gradient(rgba(60,60,60,0),rgba(60,60,60,0.1))" }}>
            <div className="my-1 mx-2 row">
                <div className="col-12 col-lg-6 d-flex align-items-center">
                    <div className="dropdown">
                        <ul className="dropdown-menu ">
                            <li><a className="dropdown-item btn-col" style={{ fontSize: "1.5em" }}
                                onClick={() => { _switchApp("homepage") }}>
                                <i className="fas fa-home mx-1" style={{ pointerEvents: "none" }}></i>ホームページ
                            </a></li>
                            <li><a className="dropdown-item btn-col" style={{ fontSize: "1.5em" }}
                                onClick={() => { _switchApp("tptef/main") }}>
                                <i className="far fa-comments mx-1" style={{ pointerEvents: "none" }}></i>チャット α版
                            </a></li>
                            <li><a className="dropdown-item btn-col" style={{ fontSize: "1.5em" }}
                                onClick={() => { }}>{/**() => { _switchApp("tskb/main") } */}
                                <i className="fa-solid fa-book mx-1" style={{ pointerEvents: "none" }}></i>栄養計算 β版{"(工事中)"}
                            </a></li>
                        </ul>
                        <button className="btn btn-outline-primary dropdown-toggle"
                            type="button" data-bs-toggle="dropdown" aria-expanded="false">
                            <i className="fa-solid fa-book mx-1" style={{ pointerEvents: "none" }} />アプリ一覧
                        </button>
                    </div>
                    <div className="mx-2 flex-fill">
                        <div id="titlelogo">タイトル未設定</div>
                    </div>
                </div>
                <div className="col-12 col-lg-6">
                    {_accountForm()}
                </div>
            </div></div>
    );
}

export const AppWidgetFoot = () => {
    return (
        <div className="d-flex justify-content-between p-2"
            style={{ color: "goldenrod", backgroundColor: "royalblue", border: "3px double silver" }}>
            <div>
                <b style={{ fontSize: "1.5em" }}>Links: </b>
                <i className="fab fa-github fa-2x fa-btn-goldbadge mx-1"
                    onClick={() => window.location.href = "https://github.com/jSm449g4d/"}></i>
            </div>
            <h5>===tilo===</h5>
            <div onClick={(evt) => { }}></div>
        </div>
    );
}
