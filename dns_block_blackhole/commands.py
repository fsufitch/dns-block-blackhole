from __future__ import annotations
from abc import ABC
import argparse



class BaseCommand(ABC):
    def __init__(self, ns: argparse.Namespace):
        self.parser_ns = ns

    def run(self):
        # Not marked as abstract, so that we can catch NotImplementedError later
        raise NotImplementedError()

    @classmethod
    def configure_parser(cls, p: argparse.ArgumentParser):
        p.set_defaults(command_cls=cls, child_parser=p)


class RootCommand(BaseCommand):
    def __init__(self, ns: argparse.Namespace):
        super().__init__(ns)
        self.interactive = bool(self.parser_ns.interactive)
        if not isinstance(self.interactive, bool):
            raise ValueError(f"non-bool value for interactive: {self.interactive!r}")

    @classmethod
    def configure_parser(cls, p: argparse.ArgumentParser):
        super().configure_parser(p)
        p.description = (
            "HTTP/S server to redirect to with your pihole, plus related utilities"
        )
        p.add_argument(
            "--interactive",
            "-i",
            action="store_true",
            help="use prompts where necessary",
        )

        subp = p.add_subparsers()
        CertbotRoute53Command.configure_parser(subp.add_parser("certbot-route53"))

        from dns_block_blackhole.server import ServerCommand
        ServerCommand.configure_parser(subp.add_parser("server"))


class CertbotRoute53Command(BaseCommand):
    @classmethod
    def configure_parser(cls, p: argparse.ArgumentParser):
        super().configure_parser(p)
        p.description = "manage SSL certs using Certbot and AWS Route53"

        subp = p.add_subparsers()
        from dns_block_blackhole.certbot_route53 import (
            AcquireCertCommand,
            RenewCertCommand,
        )

        AcquireCertCommand.configure_parser(subp.add_parser("acquire-cert"))
        RenewCertCommand.configure_parser(subp.add_parser("renew-cert"))
