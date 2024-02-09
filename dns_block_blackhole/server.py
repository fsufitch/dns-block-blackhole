import argparse
import functools
from pathlib import Path
from dns_block_blackhole.asgi_app import create_asgi_app
from dns_block_blackhole.commands import BaseCommand
from dns_block_blackhole.errors import InformativeException


class ServerCommand(BaseCommand):
    def __init__(self, ns: argparse.Namespace):
        super().__init__(ns)
        self.ssl_enabled = bool(ns.ssl)
        self.host = str(ns.host)
        self.port = int(ns.port or (443 if self.ssl_enabled else 80))
        self.debug = bool(ns.debug)

        self.ssl_cert = Path(ns.ssl_cert or '')
        self.ssl_key = Path(ns.ssl_key or '')

        if not self.host:
            raise InformativeException("host is required")
        if self.port not in range(1, 65536):
            raise InformativeException(f"invalid port: {self.port}")

        if self.ssl_enabled and not (
            self.ssl_cert.is_file() and self.ssl_key.is_file()
        ):
            raise InformativeException("SSL enabled, but cert/key files are not valid")
        if not self.ssl_enabled and (self.ssl_cert.is_file() or self.ssl_key.is_file()):
            raise InformativeException("SSL disabled, but SSL cert/key specified")

    @classmethod
    def configure_parser(cls, p: argparse.ArgumentParser):
        super().configure_parser(p)
        p.description = "run the black hole HTTP/S server(s)"
        p.add_argument(
            "--host", "-H", default="0.0.0.0", help="host/address to listen to"
        )
        p.add_argument(
            "--port",
            "-p",
            type=int,
            help="port to listen HTTP on; default is 80 for HTTP, 443 for HTTPS",
        )
        p.add_argument("--ssl", action="store_true", help="enable HTTPS mode")
        p.add_argument("--ssl-cert", "-c", help="path to SSL certfile")
        p.add_argument("--ssl-key", "-k", help="path to SSL keyfile")
        p.add_argument("--debug", action="store_true", help="enable debug mode")

    def run(self):
        import uvicorn

        asgi_app = create_asgi_app(self.debug)

        uvicorn_run = uvicorn.run

        if self.ssl_enabled:
            uvicorn_run = functools.partial(
                uvicorn_run,
                ssl_keyfile=str(self.ssl_key),
                ssl_certfile=str(self.ssl_cert),
            )

        uvicorn_run(asgi_app, host=self.host, port=self.port, reload=self.debug)
