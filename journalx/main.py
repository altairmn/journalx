import os
import markdown
import glob
import pathlib
import frontmatter
import argparse
import copy
import datetime
import re
import shutil
from . import config
import click
import configparser


# utils
def md_files():
    """
    Returns path objects for each .md file in the cwd and subdirectories
    """
    root_dir = pathlib.Path().cwd()
    md_pattern = f"{root_dir}/**/*.md"
    op = glob.glob(md_pattern, recursive=True)
    for fpath in op:
        yield root_dir.joinpath(fpath)

# config
class lConfig(object):
    cpath = pathlib.Path().cwd().joinpath('config.ini')

    @classmethod
    def exists(cls):
        return cls.cpath.exists() and cls.cpath.is_file()

    @classmethod
    def get(cls):
        if cls.exists() is False:
            click.ClickException("No config.ini file in dir")

        config = configparser.ConfigParser()
        config.read(cls.cpath) 
        return config
    
    @classmethod
    def write(cls, publish_dir = None):
        if cls.exists() is True:
            raise click.ClickException("config.ini file already exists in directory")

        config = configparser.ConfigParser()
        config['settings'] = {
            "publish_dir": publish_dir
        }
        with open(cls.cpath, 'w') as f:
            config.write(f)

# post
class Post(frontmatter.Post):
    def __init__(self):
        super(Post, self).__init__()

    def move_images(self, dest_dir):
        """
        Change image path and copy images to image dir
        """
        def get_img_path_processor(img_dir):
            def process_img_path(matchobj):
                src_path = pathlib.Path(matchobj.group(2))
                dest_path = img_dir.joinpath(src_path.name)
                return matchobj.group(0).replace(matchobj.group(2), dest_path.as_posix())
            return process_img_path

        img_processor = get_img_path_processor(dest_dir)

        # for each file, find all images
        img_regex = r'!\[(\S*)\]\((\S*)\)'
        imgs = re.findall(img_regex, self.content)

        # copy images to another folder
        for img in imgs:
            img_path = pathlib.Path(img[1])
            dest_path = dest_dir.joinpath(img_path.name)
            shutil.copy2(img_path, dest_path)

        # replace in content   
        self.content = re.sub(img_regex, img_processor, self.content)

    def modify_metadata(self, fpath):
        ts_to_dt = lambda ts: datetime.datetime.fromtimestamp(ts)

        metadata_base = {
            "title": None,
            "created_date": None,
            "modified_date": None,
            "draft": True,
            "publish": False,
            "math": False
        }

        metadata = metadata_base
        metadata["title"] = f"\"{fpath.name}\""
        metadata["created_date"] = ts_to_dt(fpath.stat().st_ctime)
        metadata["modified_date"] = ts_to_dt(fpath.stat().st_mtime)

        for k,v in self.metadata.items():
            metadata[k] = v

        self.metadata = metadata


def add_metadata():
    for fpath in md_files():
        with open(fpath, 'r') as f:
            post = frontmatter.load(f)
            post.__class__ = Post
            post.modify_metadata(fpath)
        with open(fpath, 'w') as f:
            ftxt = frontmatter.dumps(post)
            f.write(ftxt)

def publish():
    config = lConfig.get() # fails here if file doesn't exist
    publish_dir = pathlib.Path(config['settings']['publish_dir'])
    content_dir = publish_dir.joinpath("content/post")
    image_dir = publish_dir.joinpath("static/images")

    for fpath in md_files():
        with open(fpath, 'r') as f:
            post = frontmatter.load(f)
            post.__class__ = Post

            if 'publish' in post.metadata and post.metadata['publish'] is True \
            and 'draft' in post.metadata and post.metadata['draft'] is False:
                # replace the images in the post and copy the images to image_dir
                post.move_images(image_dir)
            else:
                continue

        dest_path = content_dir.joinpath(fpath.name)

        with open(dest_path, 'w') as f:
            ftxt = frontmatter.dumps(post)
            f.write(ftxt)