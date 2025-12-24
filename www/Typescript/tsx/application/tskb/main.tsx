import React, { useState, useEffect } from 'react';

import { startTable, tskbSetState } from '../../components/slice'
import { useAppSelector, useAppDispatch } from '../../components/store'
import { HIModal, CIModal } from "../../components/imodals";
import { CTable } from "./components/combinationTable"
import { EMTable } from "./components/explorematerialtable"
import { MTable } from "./components/materialtable"
import { CMTable } from "./components/configmaterialtable"
import "../../stylecheets/style.sass";

export const AppMain = () => {
    const userId = useAppSelector((state) => state.account.id)
    const tableStatus = useAppSelector((state) => state.tskb.tableStatus)
    const AppDispatch = useAppDispatch()

    useEffect(() => {
        AppDispatch(startTable({ "tableStatus": "CTable" }))
    }, [userId])
    useEffect(() => {
        AppDispatch(startTable({ "tableStatus": "CTable" }))
    }, [])
    //<CTable/> 
    return (
        <div style={{ overflow: "hidden" }}>
            {tableStatus == "CTable" ?
                <CTable /> :
                <div></div>
            }
            {tableStatus == "MTable" ?
                <MTable /> :
                <div></div>
            }
            {tableStatus == "CMTable" ?
                <CMTable /> :
                <div></div>
            }
            <div className="my-1" />
            {tableStatus != "CTable" ?
                <EMTable /> :
                <div></div>
            }
        </div>
    )
};

// titleLogo
export const titleLogo = () => {
    const tableStatus = useAppSelector((state) => state.tskb.tableStatus)
    const [tmpSubtitle, setTmpSubtitle] = useState("")
    useEffect(() => {
        if (tableStatus == "CTable") setTmpSubtitle("レシピ検索")
        if (tableStatus == "MTable") setTmpSubtitle("レシピ閲覧")
        if (tableStatus == "CMTable") setTmpSubtitle("素材編集")
    }, [tableStatus])
    return (
        <div>
            <div className="rotxin-2 row" style={{ fontFamily: "Impact", color: "black" }}>
                <h2 className="col-12 col-md-6">
                    <i className="fa-solid fa-book mx-1" style={{ pointerEvents: "none" }}></i>栄養計算
                </h2>
                <h4 className="col-12 col-md-6">
                    {tmpSubtitle}
                </h4>
            </div>
        </div>)
}