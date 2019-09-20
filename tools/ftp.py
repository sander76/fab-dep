import logging
import os
import ssl
from ftplib import FTP_TLS
from pathlib import Path
from typing import Optional



import click

_LOGGER = logging.getLogger(__name__)

CLICK_INFO_COLOR = "bright_yellow"
CLICK_OK_COLOR = "green"
CLICK_ERROR_COLOR = "red"


class _NewFtpTls(FTP_TLS):
    """
     # replace original makepasv function with one which always returns
    # the peerhost of the control connections as peerhost for the data
    # connection
    # stackoverflow.com/questions/44057732/connecting-to-explicit-ftp-over-tls-in-python


    """

    def storbinary(self, cmd, fp, blocksize=8192, callback=None, rest=None):
        """Store a file in binary mode.  A new port is created for you.

        Args:
        cmd: A STOR command.
        fp: A file-like object with a read(num_bytes) method.
        blocksize: The maximum data size to read from fp and send over
            the connection at once.  [default: 8192]
        callback: An optional single parameter callable that is called on
            each block of data after it is sent.  [default: None]
        rest: Passed to transfercmd().  [default: None]

        Returns:
        The response code.
        """
        self.voidcmd("TYPE I")
        with self.transfercmd(cmd, rest) as conn:
            while 1:
                buf = fp.read(blocksize)
                if not buf:
                    break
                conn.sendall(buf)
                if callback:
                    callback(buf)
            ## shutdown ssl layer
            # if _SSLSocket is not None and isinstance(conn, _SSLSocket):
            #   conn.unwrap()
        return self.voidresp()

    def makepasv(self):
        host, port = super().makepasv()
        host = self.sock.getpeername()[0]
        return host, port


def _ftps_connect(ftp_host, user, passw) -> _NewFtpTls:
    """Connect to an fps ftp server.

    ftp_host: eg: ftp://test.com
    """
    _old_makepasv = _NewFtpTls.makepasv

    def _new_makepasv(self):
        host, port = _old_makepasv(self)
        host = self.sock.getpeername()[0]
        return host, port

    _NewFtpTls.makepasv = _new_makepasv

    ftps = _NewFtpTls(context=ssl.SSLContext(protocol=ssl.PROTOCOL_TLSv1_2))
    ftps.connect(host=ftp_host, port=21)

    ftps.auth()

    res = ftps.login(user=user, passwd=passw)
    ftps.prot_p()
    ftps.debugging = False
    return ftps


def _upload(
    file: Path,
    target_folder: str,
    ftps,
    block_size=1024,
    target_file_name: Optional[str] = None,
):
    ftps.cwd(target_folder)
    click.secho(f"Uploading {file.name}", fg=CLICK_INFO_COLOR, nl=False)

    if target_file_name:
        _target_name = target_file_name
    else:
        _target_name = file.name

    click.secho(f" target name {_target_name}", fg=CLICK_INFO_COLOR)

    length = os.path.getsize(file)
    with click.open_file(file, "rb") as fl:
        with click.progressbar(length=length) as bar:

            def _update_size(data):
                bar.update(len(data))

            try:
                res = ftps.storbinary(
                    "STOR %s" % _target_name, fl, block_size, _update_size
                )
                click.secho(str(res), fg=CLICK_INFO_COLOR)

            except Exception as err:
                print(err)


@click.command()
@click.argument("ftp_host")
@click.argument("user")
@click.argument("passw")
@click.argument("file")
@click.argument("target-folder")
@click.option("--target-name", help="Alternative target file name.")
def upload_file(ftp_host, user, passw, file, target_folder, target_name=None):
    """
    :param ftp_host: ftps host
    :param user: ftp user
    :param passw: ftp password
    :param file: file to upload
    :param target_folder: url folder target
    :return:
    """
    _file = Path(file)
    assert _file.exists()
    click.secho("Connecting...", fg=CLICK_INFO_COLOR, nl=False)
    connection = _ftps_connect(ftp_host, user, passw)
    click.secho("done", fg=CLICK_INFO_COLOR)

    _upload(_file, target_folder, connection, target_file_name=target_name)


@click.group()
def cli():
    """Main deploy entry"""
    pass


cli.add_command(upload_file)

if __name__ == "__main__":
    cli()
