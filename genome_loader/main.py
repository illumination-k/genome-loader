import click

from genome_loader import handlers
from genome_loader.config import ConfigModel
from genome_loader.logger_utils import LogLevel, set_loglevel


@click.group()
@click.option("--loglevel", type=click.Choice(["debug", "info", "warn", "error"]))
def main(loglevel: LogLevel = "error"):
    import shutil
    
    if shutil.which("gffread") is None:
        raise RuntimeError("gffread is required! Please install from https://github.com/gpertea/gffread")
    
    set_loglevel(loglevel)


config_path = "genomes.json"


@main.command("sync")
def sync():
    handlers.sync(ConfigModel.parse_file(config_path))


@main.command("genome-add")
def genome_add():
    handlers.genome_add(config_path)


if __name__ == "__main__":
    main()
