python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
waitress-serve --port=10443 wsgi:app
