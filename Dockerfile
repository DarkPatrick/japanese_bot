# docker build --no-cache -t japanese_tg_bot .
# docker build -t japanese_tg_bot .
# docker run japanese_tg_bot

FROM python:3.10
FROM postgres
FROM ubuntu:latest

RUN apt-get update
RUN apt-get -y install sudo
RUN sudo apt-get install -y software-properties-common
RUN sudo add-apt-repository ppa:deadsnakes/ppa
RUN sudo apt-get update
RUN apt install -y wget
RUN sudo apt-get install xz-utils
# RUN wget https://www.python.org/ftp/python/3.9.13/Python-3.9.13.tar.xz
# RUN tar -xf Python-3.9.13.tar.xz
RUN wget https://www.python.org/ftp/python/3.10.0/Python-3.10.0.tar.xz
# RUN tar -xf Python-3.9.13.tar.xz
RUN tar -xf Python-3.10.0.tar.xz
RUN apt-get install -y python3-pip
# RUN apt-get install -yq python3.9-dev python3.9-venv libpq-dev
# RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python3.9-dev python3.9-venv libpq-dev
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python3.10-dev python3.10-venv

# RUN alias python3=python3.9
RUN alias python3=python3.10

# ADD . .

ENV YOUR_ENV=default
ENV POETRY_HOME=/opt/poetry
# ENV POETRY_VENV=/opt/poetry-venv
ENV POETRY_VENV=.venv
ENV POETRY_CACHE_DIR=/opt/.cache
ENV POETRY_VERSION=1.2.2

RUN pip3 install "poetry==$POETRY_VERSION"

RUN sudo pip3 install APScheduler
RUN python3 -m pip install virtualenv

RUN python3 -m venv $POETRY_VENV \
    && $POETRY_VENV/bin/pip3 install -U pip setuptools \
    && $POETRY_VENV/bin/pip3 install poetry==${POETRY_VERSION}

ENV PATH="${PATH}:${POETRY_VENV}/bin"

# WORKDIR /app

# Install dependencies
COPY poetry.lock pyproject.toml ./
RUN poetry env use $(which python3)
RUN poetry install

RUN poetry run pip3 install python-telegram-bot[all] -U --pre

# Run your app
# COPY . /app

# RUN poetry run pip3 install python-telegram-bot[all] -U --pre
RUN pip3 show apscheduler

ADD . .


# # RUN pip3 install 
# RUN echo ls
# CMD ["python3", "--version"]
# CMD ["poetry", "--version"]
# CMD ["ls", ".venv/bin"]
CMD ["pwd"]
# CMD ["poetry", "run", "python3", "-c", "'help(\"modules\")'"]
# CMD ["poetry", "run", "python3", "src/main.py"]
# CMD ["poetry", "run", ".venv/bin/python3", "src/mod_test.py"]
# CMD ["poetry", "run", "/.venv/bin/python3.10", "--version"]

# ADD . .