
FROM debian:forky-slim

# Init
ENV APP /var/www
WORKDIR $APP
COPY . .
RUN apt update -q;apt upgrade -yq

# Javascript
WORKDIR $APP/html/static
RUN apt install nodejs npm -yq
RUN npm install -g npm
RUN npm install

# Typescript
WORKDIR $APP/Typescript
# Webpack
RUN npx webpack

# Python3
WORKDIR $APP
RUN apt install gcc python3-pip python3-venv -yq
RUN python3 -m venv .venv
# RUN . .venv/bin/activate
RUN ./.venv/bin/pip install -U pip
RUN ./.venv/bin/pip install -Ur requirements.txt

# Hosting
WORKDIR $APP
CMD bash -c "./.venv/bin/uvicorn --host 0.0.0.0 --port 8080 asgi:application"
