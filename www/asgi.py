# Standard
import importlib
import inspect
import os
import sys
from pathlib import Path
from typing import Any

# Additional
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    PlainTextResponse,
    Response,
)
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.join("./", __file__)))
os.makedirs("./tmp", exist_ok=True)

# Flask_Startup
app = FastAPI()
templates = Jinja2Templates(directory="./templates")
app.mount("/static", StaticFiles(directory="./html/static"), name="static")


# Index
@app.api_route("/", methods=["GET", "POST"])
def indexpage_show(request: Request) -> Response:
    try:
        return FileResponse(os.path.join("html/index.html"))
    except Exception as e:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "STATUS_ERROR_TEXT": str(e)},
            status_code=500,
        )


# FaaS
@app.api_route("/{name:path}.py", methods=["GET", "POST"])
async def py_show(name: str, request: Request) -> Response:
    try:
        result = importlib.import_module(
            "Python." + name.replace("/", ".").replace("..", "_")
        ).show(request)
        if inspect.isawaitable(result):
            result = await result
        return result
    except Exception as e:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "STATUS_ERROR_TEXT": str(e)},
            status_code=500,
        )


# ws
@app.websocket("/{name:path}.ws")
async def ws_endpoint(name: str, ws: WebSocket):
    try:
        await importlib.import_module(
            "Python." + name.replace("/", ".").replace("..", "_")
        ).ws_endpoint(ws)
    except Exception as e:
        pass


# html: domain/* → www/html/*
@app.api_route("/{name:path}", methods=["GET", "POST"])
async def html_show(name: str) -> Response:
    try:
        return FileResponse(
            os.path.join("html", name).replace("\\", "/").replace("..", "_")
        )
    except Exception:
        return PlainTextResponse("cant_access", status_code=404)


application = app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("asgi:app")
