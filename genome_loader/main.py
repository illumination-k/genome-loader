import click
from genome_loader.config import ConfigModel
from genome_loader import handlers

@click.group()
def main():
    pass

@main.command("sync")
def sync():
    config = "genomes.json"
    handlers.sync(ConfigModel.parse_file(config))

if __name__ == "__main__":
    main()