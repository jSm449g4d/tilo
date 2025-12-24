import React from 'react';
import { createRoot } from "react-dom/client"
import { Provider } from "react-redux"
import { Query2Dict } from "./components/util";
import { store } from "./components/store";
import { AppWidgetHead, AppWidgetFoot } from "./components/widget";
import { IModalsRender } from "./components/imodals";

require.context('./application/', true, /\.ts(x?)$/)
// arias
var _application = "homepage"
if ("application" in Query2Dict() == true) { _application = Query2Dict()["application"] }
//render
import("./application/" + _application).then(async (module) => {
    const root = createRoot(document.getElementById("root"))
    await root.render(
        <React.StrictMode>
            <Provider store={store}>
                <AppWidgetHead />
                <div id="appMain" />
                <AppWidgetFoot />
                <IModalsRender />
            </Provider>
        </React.StrictMode>);


    // need delay because the page is not yet fully rendered at this time.
    setTimeout(() => {
        const appMain = createRoot(document.getElementById("appMain"))
        appMain.render(<Provider store={store}><module.AppMain /></Provider>)
        const titlelogo = createRoot(document.getElementById("titlelogo"))
        titlelogo.render(<Provider store={store}><module.titleLogo /></Provider>)
    }, 100);
})
