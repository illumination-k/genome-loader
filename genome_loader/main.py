from typing import Literal

import click

from genome_loader import handlers
from genome_loader.config import ConfigModel
from genome_loader.logger_utils import LogLevel, set_loglevel


@click.group()
@click.option("--loglevel", type=click.Choice(["debug", "info", "warn", "error"]))
def main(loglevel: LogLevel = "error"):
    set_loglevel(loglevel)


@main.command("sync")
def sync():
    config = "genomes.json"
    handlers.sync(ConfigModel.parse_file(config))


if __name__ == "__main__":
    main()

