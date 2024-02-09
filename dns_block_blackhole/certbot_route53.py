import argparse
import re
import shlex
from dns_block_blackhole.commands import BaseCommand, RootCommand
from dns_block_blackhole.errors import InformativeException


class _Common(BaseCommand):
    _EMAIL_RE = re.compile(
        # From: https://uibakery.io/regex-library/email-regex-python
        "(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"
        '"(?:[\\x01-\\x08\\x0b\\x0c\\x0e-\\x1f\\x21\\x23-\\x5b\\x5d-\\x7f]|'
        '\\\\[\\x01-\\x09\\x0b\\x0c\\x0e-\\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*'
        "[a-z0-9])?\\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\\[(?:(?:25[0-5]|2[0-4]"
        "[0-9]|[01]?[0-9][0-9]?)\\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|"
        "[a-z0-9-]*[a-z0-9]:(?:[\\x01-\\x08\\x0b\\x0c\\x0e-\\x1f\\x21-\\x5a\\x53-"
        "\\x7f]|\\\\[\\x01-\\x09\\x0b\\x0c\\x0e-\\x7f])+)\\])"
    )

    def __init__(self, ns: argparse.Namespace):
        super().__init__(ns)

        try:
            import certbot.main
            import boto3
            import botocore.exceptions
        except ImportError as exc:
            raise InformativeException(
                f"failed importing '{exc.name}'; are the correct optional dependencies installed?"
            )
        self.certbot_main = certbot.main.main
        self.boto3 = boto3
        self.botocore_exceptions = botocore.exceptions

        self.root = RootCommand(ns)
        self.cert_name = ns.name or ""
        self.email = ns.email
        self.domains = ns.domains
        self.keep_valid_cert = not ns.force
        self.test_mode = ns.test
        self.dry_run = ns.dry_run
        self.extra_args = [*(ns.extra_args_opt or []), *(ns.extra_args_pos or [])]
        if self.extra_args and self.extra_args[0] == "--":
            self.extra_args = self.extra_args[1:]

        if not isinstance(self.cert_name, str):
            raise ValueError(f"invalid cert name: {self.cert_name!r}")
        if not isinstance(self.email, str) or not self._EMAIL_RE.match(self.email):
            raise ValueError(f"invalid email address: {self.email!r}")
        if (
            not self.domains
            or not isinstance(self.domains, list)
            or not all(isinstance(d, str) for d in self.domains)
        ):
            raise ValueError(f"invalid domain list: {self.domains!r}")
        if not isinstance(self.test_mode, bool):
            raise ValueError(f"non-bool value for test mode: {self.test_mode!r}")
        if not isinstance(self.dry_run, bool):
            raise ValueError(f"non-bool value for dry run: {self.dry_run!r}")
        if not isinstance(self.extra_args, list) or not all(
            isinstance(a, str) for a in self.extra_args
        ):
            raise ValueError(f"invalid extra args: {self.extra_args!r}")

    @classmethod
    def configure_parser(cls, p: argparse.ArgumentParser):
        super().configure_parser(p)
        p.add_argument("--name", "-n", help="name for the cert (used by certbot)")
        p.add_argument(
            "--email", "-e", required=True, help="email for account notifications"
        )
        p.add_argument(
            "--domain",
            "-d",
            dest="domains",
            nargs="+",
            required=True,
            help="domains to manage",
        )
        p.add_argument(
            "--force",
            "-f",
            action="store_true",
            help="if the request matches an existing cert, overwrite it anyway",
        )
        p.add_argument("--test", action="store_true", help="use a staging ACME server")
        p.add_argument(
            "--dry-run", action="store_true", help="do not edit any actual files"
        )

        p.add_argument(
            "--",
            metavar="...",
            dest="extra_args_opt",
            nargs="...",
            help="use to force start of passthrough arguments",
        )

        p.add_argument(
            "extra_args_pos",
            metavar="...",
            nargs="...",
            help="extra (unrecognized) arguments are passed through unmodified to certbot",
        )

    def check_aws_creds(self):
        sts = self.boto3.client("sts")
        try:
            sts.get_caller_identity()
        except self.botocore_exceptions.NoCredentialsError:
            raise InformativeException(
                "AWS credentials not found; are they set up right? See: "
                "https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html"
            )

    @property
    def certbot_args(self) -> list[str]:
        args = []
        if not self.root.interactive:
            args.append("--non-interactive")
            args.append("--agree-tos")
        if self.test_mode:
            args.append("--test-cert")
        if self.dry_run:
            args.append("--dry-run")

        args.append("--keep" if self.keep_valid_cert else "--reinstall")
        args.append("--dns-route53")

        if self.cert_name:
            args.extend(["--cert-name", self.cert_name])

        args.extend(["-m", self.email])

        for domain in self.domains:
            args.extend(["-d", domain])

        args.extend(self.extra_args)

        return args


class AcquireCertCommand(_Common):
    def run(self):
        print("Checking AWS credentials...")
        self.check_aws_creds()
        args = ["certonly", *self.certbot_args]
        print("Requesting cert using args:", shlex.join(args))
        self.certbot_main(args)


class RenewCertCommand(_Common):
    def run(self):
        print("renew")
        print("Checking AWS credentials...")
        self.check_aws_creds()
