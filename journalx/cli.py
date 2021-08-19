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
@click.option('-f', '--file', 'fpath', type=click.Path(exists=True, resolve_path=True))
def publish(fpath):
    """
    publish all the posts in the directories
    """
    jx.publish(fpath)

@cli.group()
def metadata():
    """
    add metadata to all the files in the vault
    """
    pass

@metadata.command()
def update():
    """
    Update metadata to all md files in the vault.
    Adds in missing files.
    """
    print("Adding metadata...")
    jx.add_metadata()

@metadata.command()
def clear():
    """
    Clear metadata from all files in the vault
    """
    print("Clearing metadata...")
    jx.clear_metadata()