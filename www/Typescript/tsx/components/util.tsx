// To prevent high freq access
export class stopf5_tsx {
    last_timestamp: { [label: string]: number }
    constructor() { this.last_timestamp = {} }
    public check(label: string, interval_ms: number = 3000, stopmsg: boolean = false) {
        if (this.last_timestamp[label] && Date.now() < this.last_timestamp[label] + interval_ms) {
            if (stopmsg == true) { alert("remaining cooling time: " + String(this.last_timestamp[label] - Date.now() + interval_ms) + "[ms]") }
            return false;
        }
        this.last_timestamp[label] = Date.now()
        return true;
    }
} export var stopf5 = new stopf5_tsx

export const jpclock = () => {
    const now: Date = new Date();
    return now.getFullYear() + "年 " + (now.getMonth() + 1) +
        "月 " + now.getDate() + "日 " + ["日 ", "月 ", "火 ", "水 ", "木 ", "金 ", "土 "][now.getDay()] +
        "曜日 " + now.getHours() + ": " + now.getMinutes() + ": " + now.getSeconds();
}

export const Query2Dict = (yourQuery: string = window.location.search) => {
    let ret_dict: { [key: string]: string } = {};
    if (yourQuery[0] == "?") yourQuery = yourQuery.slice(1)
    const data = yourQuery.split('&');
    for (let i = 0; i < data.length; i++) {
        let keyvalue: string[] = ["", ""]
        keyvalue = data[i].split('=');
        ret_dict[keyvalue[0]] = decodeURIComponent(keyvalue[1]).replace(/\+/g, ' ');
    }; return ret_dict;
}
export const Dict2Query = (query_dict: { [key: string]: string }) => {
    let ret_str: string = "?"
    const tmpkey_array: string[] = Object.keys(query_dict);
    const tmpvalue_array: string[] = Object.values(query_dict);
    for (let i = 0; i < tmpkey_array.length; i++) {
        if (tmpkey_array[i] == "") continue;
        ret_str += tmpkey_array[i] + "=" + tmpvalue_array[i] + "&"
    }; return ret_str
}
export const checkMailAddress = (mailAddress: string) => {
    let reg = /^[A-Za-z0-9]{1}[A-Za-z0-9_.-]*@{1}[A-Za-z0-9_.-]{1,}\.[A-Za-z0-9]{1,}$/;
    if (reg.test(mailAddress)) return true;
    return false;
}
export const Unixtime2String = (unixtime: number = 0) => {
    const now: Date = new Date(unixtime * 1000);
    const timestamp = now.getFullYear() + "年 " + String(now.getMonth() + 1) +
        "月 " + now.getDate() + "日 " + now.getHours() + ": " + now.getMinutes() + ": " + now.getSeconds();
    return timestamp
}

export const satisfyDictKeys = (_targetDict: {}, _keys: any[]) => {
    for (let _i = 0; _i < _keys.length; _i++) if (_keys[_i] in _targetDict == false) return false
    return true
}

export const toSignificantDigits = (_value: any, _digits = 5) => {
    var _val = String(_value); var _ret = ""; var _dig = _digits
    for (let _i = 0; _i < _val.length && _i < _dig; _i++) {
        if ("." == _val[_i]) _dig++
        _ret += _val[_i]
    }
    return _ret
}