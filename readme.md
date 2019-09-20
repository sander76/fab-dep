# Fabricator deployment tool

## Usage

type `fab` at the command prompt and let the help guide you.

## Building

Both a windows10 (64bit) and Ubuntu linux 18.04 (64bit) need to be built.

### Windows

- Goto the root of this project
- Make sure the virtualenv is active (pipenv shell)
- `pyinstaller fab.spec`
- The installer will be built in the `dist` folder
- Zip up the `fab` folder to fab.zip
- Upload it to: https://motorisation.hde.nl/bin/fabricator/win10/fab.zip

### Linux

- Run the docker container: `docker run -it --entrypoint /bin/bash bionic-fabtool`
- Update the repo
- run the script tools/make_dep.sh
- upload the file: `python ftp.py upload-file motorisation.hde.nl <user> <pass> /app/fab.deb /motorisation.hde.nl/bin/fabricator/ubuntu18_04/`


# Building:

`flit build`


## installing from git:

`pipx install --verbose --spec git+https://github.com/sander76/fab-dep.git fab_deploy`

## updating

`pipx upgrade --verbose --spec git+https://github.com/sander76/fab-dep.git fab_deploy`
