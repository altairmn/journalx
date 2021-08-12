import journalx.main as jx
import click
import configparser
import pathlib

@click.group()
def cli():
    pass

@cli.command()
@click.option("--publish-dir", help="directory which is root of website", required=True)
def init(publish_dir):
    """
    Initialize the config file for use
    """
    jx.lConfig.write(publish_dir)


@cli.command()
def publish():
    """
    publish all the posts in the directories
    """
    jx.publish()

@cli.command()
def add_metadata():
    """
    add metadata to all the files in the vault
    """
    jx.add_metadata()

@cli.command()
def showmd():
    for f in jx.md_files():
        print(f)