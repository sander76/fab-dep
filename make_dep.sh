#!/bin/bash

echo Running pyinstaller

cd /app/fab-dep

python3.7 -m pyinstaller fab.spec

cd dist/dist

cp * /app/fab_1.0-1/usr/bin/ -r
