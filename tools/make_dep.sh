#!/bin/bash

rm /app/fab/usr/bin/* -r
rm /app/fab/DEBIAN/* -r

cd /app/fab-dep

git pull

pipenv lock -r > reqs.txt
pipenv lock -r -d > reqs-dev.txt

python3.7 -m pip install -r /app/fab-dep/reqs.txt
python3.7 -m pip install -r /app/fab-dep/reqs-dev.txt

echo Running pyinstaller

pyinstaller fab.spec

python3.7 /app/fab-dep/tools/make_control_file.py

cp /app/fab-dep/dist/fab/* /app/fab/usr/bin/ -r


#cp /app/fab-dep/control /app/fab/DEBIAN/

cd /app
dpkg-deb --build fab
