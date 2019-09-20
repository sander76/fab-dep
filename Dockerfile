FROM ubuntu:bionic-20190718

RUN apt-get update && \
    apt-get install nano python3.7 python3.7-dev python3-pip \
    python3.7-venv ssh git wget -y

RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.7 1

RUN python3.7 -m pip install wheel
# required for aes-encrypt
RUN python3.7 -m pip install cffi
RUN python3.7 -m pip install pipenv
RUN python3.7 -m pip install click==7.0.0

WORKDIR /app

RUN git clone https://github.com/sander76/fab-dep.git

# WORKDIR /app/fab-dep

# RUN python3.7 -m pip install -r requirements.txt
# RUN python3.7 -m pip install -r requirements-dev.txt

# set the platform release folder.
# ENV FAB_RELEASE_FOLDER=/app/ubuntu18_04/
# RUN mkdir /app/ubuntu18_04/

RUN mkdir -p fab/usr/bin
RUN mkdir fab/DEBIAN


WORKDIR /app/fab-dep

