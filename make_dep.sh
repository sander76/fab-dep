#!/bin/bash

cd /app/fab-deb

git pull

python3.7 -m pip install /app/fab-dep/requirements.txt
python3.7 -m pip install /app/fab-dep/requirements-dev.txt

echo Running pyinstaller

cd /app/fab-dep

pyinstaller fab.spec

rm /app/fab/usr/bin/* -r

cp /app/fab-dep/dist/fab/* /app/fab/usr/bin/ -r
cp /app/fab-dep/control /app/fab/DEBIAN/

cd /app
dpkg-deb --build fab
