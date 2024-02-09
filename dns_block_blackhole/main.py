from __future__ import annotations
import argparse
import sys

from dns_block_blackhole.commands import BaseCommand, RootCommand


def main():
    parser = argparse.ArgumentParser()
    RootCommand.configure_parser(parser)

    ns = parser.parse_args()
    if not issubclass(ns.command_cls, BaseCommand):
        raise NotImplementedError(f"received invalid command class: {ns.command_cls!r}")

    try:
        command = ns.command_cls(ns)
        command.run()
    except NotImplementedError:
        ns.child_parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
