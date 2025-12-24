# Standard
import os
import sys
import importlib

# Additional
import flask


# Flask_Startup
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.join("./", __file__)))
app = flask.Flask(
    __name__, template_folder="./templates/", static_folder="./html/static/"
)
app.config["MAX_CONTENT_LENGTH"] = 100000000
os.makedirs("./tmp", exist_ok=True)


# Index
@app.route("/", methods=["GET", "POST"])
def indexpage_show():
    try:  # Apache2.4 index
        return flask.send_file(os.path.join("html/index.html"))
    except Exception as e:  # Flask index
        return flask.render_template("error.html", STATUS_ERROR_TEXT=str(e)), 500


# FaaS: domain/Flask/**/*.py → www/Flask/**/*.py
@app.route("/<path:name>.py", methods=["GET", "POST"])
@app.route("/Flask/<path:name>.py", methods=["GET", "POST"])
def py_show(name):
    try:
        return importlib.import_module(
            "Flask." + name.replace("/", ".").replace("..", "_")
        ).show(flask.request)
    except Exception as e:
        return flask.render_template("error.html", STATUS_ERROR_TEXT=str(e)), 500


# html: domain/* → www/html/*
@app.route("/<path:name>", methods=["GET", "POST"])
def html_show(name):
    try:
        return flask.send_file(
            os.path.join("html", name).replace("\\", "/").replace("..", "_")
        )
    except Exception as e:
        return "cant_access", 404


application = app

if __name__ == "__main__":
    app.run()
