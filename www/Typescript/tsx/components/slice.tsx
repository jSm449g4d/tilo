import { createSlice } from '@reduxjs/toolkit'
import React from 'react';

export const accountSlice = createSlice({
  name: 'account',
  initialState: {
    token: "", user: "", id: -1, roomKey: "", mail: ""
  },
  reducers: {
    accountInit: (state) => {
      state.token = ""; state.user = ""; state.id = -1; state.roomKey = "", state.mail = ""
    },
    accountSetState: (state, action: { payload: any }) => {
      if ("token" in action.payload) state.token = action.payload.token
      if ("user" in action.payload) state.user = action.payload.user
      if ("id" in action.payload) state.id = action.payload.id
      if ("mail" in action.payload) state.mail = action.payload.mail
      if ("roomKey" in action.payload) state.roomKey = action.payload.roomKey
    },
  },
})
export const { accountInit, accountSetState } = accountSlice.actions


export const tptefSlice = createSlice({
  name: 'tptef',
  initialState: {
    tableStatus: "",
    reloadFlag: 0,
    room: { "id": -1, "user": "", "userid": -1, "room": "", "timestamp": 0, "passhash": "" },
  },
  reducers: {
    tptefSetState: (state, action: { payload: any }) => {
      if ("tableStatus" in action.payload) state.tableStatus = action.payload.tableStatus
      if ("room" in action.payload) state.room = action.payload.room
    },
    tptefStartTable: (state, action: { payload: any }) => {
      if ("room" in action.payload) state.room = action.payload.room
      if ("tableStatus" in action.payload) state.tableStatus = action.payload.tableStatus
      state.reloadFlag++
    },
  },
})
export const { tptefSetState, tptefStartTable } = tptefSlice.actions

export const tskbSlice = createSlice({
  name: 'tskb',
  initialState: {
    tableStatus: "",
    reloadFlag: 0,
    combination: {
      // "(id,name,tag,description,userid,user,passhash,timestamp,img,contents)"
      "id": -1, "name": "", "tag": "", "description": "", "userid": -1, "user": "",
      "passhash": "", "timestamp": 0, "img": "", "contents": "{}"
    },
    material: {
      // "(id,name,tag,description,userid,user,passhash,timestamp,img,"
      // "unit,cost,carbo,fiber,protein,fat,saturated_fat,n3,DHA_EPA,n6,"
      // "ca,cl,cr,cu,i,fe,mg,mn,mo,p,k,se,na,zn,va,vb1,vb2,vb3,vb5,vb6,vb7,vb9,vb12,vc,vd,ve,vk,colin,kcal)"
      "id": -1, "name": "", "tag": "", "description": "", "userid": -1, "user": "",
      "passhash": "", "timestamp": 0, "img": "", "unit": "100", "cost": "0", "carbo": "0", "fiber": "0",
      "protein": "0", "fat": "0", "saturated_fat": "0", "n3": "0", "DHA_EPA": "0", "n6": "0",
      "ca": "0", "cl": "0", "cr": "0", "cu": "0", "i": "0", "fe": "0", "mg": "0", "mn": "0",
      "mo": "0", "p": "0", "k": "0", "se": "0", "na": "0", "zn": "0", "va": "0",
      "vb1": "0", "vb2": "0", "vb3": "0", "vb5": "0", "vb6": "0", "vb7": "0", "vb9": "0",
      "vb12": "0", "vc": "0", "vd": "0", "ve": "0", "vk": "0", "colin": "0", "kcal": "0",
    },
  },
  reducers: {
    tskbSetState: (state, action: { payload: any }) => {
      if ("tableStatus" in action.payload) state.tableStatus = action.payload.tableStatus
      if ("combination" in action.payload) state.combination = action.payload.combination
      if ("material" in action.payload) state.material = action.payload.material
    },
    startTable: (state, action: { payload: any }) => {
      if ("combination" in action.payload)
        if (action.payload.combination == null) {
          state.combination = {
            "id": -1, "name": "", "tag": "", "description": "", "userid": -1, "user": "",
            "passhash": "", "timestamp": 0, "img": "", "contents": "{}"
          }
        } else state.combination = action.payload.combination
      if ("material" in action.payload)
        if (action.payload.material == null) {
          state.material = {
            "id": -1, "name": "", "tag": "", "description": "", "userid": -1, "user": "",
            "passhash": "", "timestamp": 0, "img": "", "unit": "100", "cost": "0", "carbo": "0", "fiber": "0",
            "protein": "0", "fat": "0", "saturated_fat": "0", "n3": "0", "DHA_EPA": "0", "n6": "0",
            "ca": "0", "cl": "0", "cr": "0", "cu": "0", "i": "0", "fe": "0", "mg": "0", "mn": "0",
            "mo": "0", "p": "0", "k": "0", "se": "0", "na": "0", "zn": "0", "va": "0",
            "vb1": "0", "vb2": "0", "vb3": "0", "vb5": "0", "vb6": "0", "vb7": "0", "vb9": "0",
            "vb12": "0", "vc": "0", "vd": "0", "ve": "0", "vk": "0", "colin": "0", "kcal": "0",
          }
        } else state.material = action.payload.material
      if ("tableStatus" in action.payload) state.tableStatus = action.payload.tableStatus
      state.reloadFlag++
    },
  },
})
export const { tskbSetState, startTable } = tskbSlice.actions