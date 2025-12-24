import React from 'react';
import "../stylecheets/style.sass";

const bgImage: any = {
    //backgroundColor: "lavender",
    backgroundImage: "url(/static/img/aircraft-2795557_1280.jpg)",
    backgroundSize: "cover",
    backgroundAttachment: "fixed",
}

export const AppMain = () => {
    // renders
    const titleLogo = () => {
        return (
            <div className="titlelogo m-2 row">
                <h1 className="col-12 d-block d-lg-none ">
                    <div>VPSdeWP</div><div>ホームページ</div>
                </h1>
                <h1 className="col-lg-12 d-none d-lg-block " >
                    VPSdeWP の ホームページ
                </h1>
            </div>
        )
    }
    const indexColumns = () => {
        return (
            <div className="p-3">
                <div className="row text-center">
                    <h4 className="slidein-1"
                        style={{ backgroundColor: "rgba(225,160,225,0.8)", }}
                    >コンテンツ一覧</h4>
                    <div className="col-sm-6 col-md-4 p-1 fadein-3">
                        <div className="btn-col" style={{ background: "rgba(255,255,255,0.6)" }}>
                            <a className="a-nolink" href='https://github.com/jSm449g4d/summerhackathon_vol2' >
                                <div className="d-flex flex-column" style={{ height: "380px" }}>
                                    <h5>Flask通信</h5>
                                    <div className="d-flex flex-column flex-grow-1">
                                        <img className="img-fluid" src="/static/img/hakka.png" style={{ height: 150, objectFit: "contain" }} />
                                        2020/09/09~16に開催されたハッカソンの作品
                                        <ul style={{ listStyle: "none" }}>
                                            <li>チーム開発</li>
                                            <li>情報可視化で世の中を便利に!</li>
                                            <li>何時どれだけ、どんな記事?</li>
                                            <li>キーワード検索</li>
                                        </ul>
                                    </div>
                                </div>
                            </a>
                        </div>
                    </div>
                    <div className="col-sm-6 col-md-4 p-1 fadein-4">
                        <div className="btn-col" style={{ background: "rgba(255,255,255,0.6)" }}>
                            <a className="a-nolink" href='https://github.com/jSm449g4d/hleb' >
                                <div className="d-flex flex-column" style={{ height: "380px" }}>
                                    <h5>хлеб (半完全栄養食)</h5>
                                    <div className="d-flex flex-column flex-grow-1">
                                        <img className="img-fluid" src="/static/img/hleb.jpg" style={{ height: 150, objectFit: "contain" }} />
                                        汎用食
                                        <ul style={{ listStyle: "none" }}>
                                            <li>低カロリー(900[kcal]前後)</li>
                                            <li>低コスト(500[円]以下)</li>
                                            <li>高たんぱく(100[g]以上)</li>
                                            <li>ケト食(糖質20[g]前後)</li>
                                            <li>人工甘味料(NAS)不使用</li>
                                        </ul>
                                    </div>
                                </div>
                            </a>
                        </div>
                    </div>
                    <div className="col-sm-6 col-md-4 p-1 fadein-4">
                        <div className="btn-col" style={{ background: "rgba(255,255,255,0.6)" }}>
                            <a className="a-nolink" href='/?application=tskb/main' >
                                <div className="d-flex flex-column" style={{ height: "380px" }}>
                                    <h5>栄養計算アプリ(β版)</h5>
                                    <div className="d-flex flex-column flex-grow-1">
                                        <img className="img-fluid" src="/static/img/tskbtitle.png" style={{ height: 150, objectFit: "contain" }} />
                                        <ul style={{ listStyle: "none" }}>
                                            <li>現在開発中</li>
                                            <li>素材/食材を登録</li>
                                            <li>レシピを登録</li>
                                            <li>栄養素計算</li>
                                        </ul>
                                    </div>
                                </div>
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        )
    }

    return (
        <div>
            <div style={{ overflow: "hidden" }}>
                <div style={bgImage}>
                    <div style={{ background: "rgba(255,255,255,0.5)" }}>
                        <div>{titleLogo()}</div>
                        <div id="homepage_githubColumns">{indexColumns()}</div>
                    </div></div></div></div>
    );
};

//titleLogo
export const titleLogo = () => {
    return (<h2 className="rotxin-2" style={{ fontFamily: "Impact", color: "black" }} >
        <i className="fas fa-home mx-1" style={{ pointerEvents: "none" }} />ホームページ
    </h2>)
}