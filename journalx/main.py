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
        def img_path_processor(matchobj):
            match_str = ''.join(["" if x is None else x for x in matchobj.group(1,2)])
            src_path = pathlib.Path(match_str)
            dest_path = f"/images/{src_path.name}"
            return matchobj.group(0).replace(match_str, dest_path)

        # for each file, find all images
        img_regex1 = r'!\[\S*\]\((\S*)\)'
        img_regex2 = r'<img src="(.*?)"'
        img_regex = re.compile(fr"{img_regex1}|{img_regex2}")
        imgs = re.findall(img_regex, self.content)

        # copy images to another folder
        for img in imgs:
            img_path = pathlib.Path(''.join(img))
            dest_path = dest_dir.joinpath(img_path.name)
            shutil.copy2(img_path, dest_path)

        # replace in content   
        self.content = re.sub(img_regex, img_path_processor, self.content)
    
    def process_codeblock(self, lang_name, start_tag, end_tag):
        cbl_pattern = fr'```{lang_name}(.*?)```'
        results = re.findall(cbl_pattern, self.content, flags = re.DOTALL)
        def regex_processor(matchobj):
            return f"{start_tag}{matchobj.group(1)}{end_tag}"
        self.content = re.sub(cbl_pattern, regex_processor, self.content, flags = re.DOTALL)

    def modify_metadata(self, fpath):
        ts_to_dt = lambda ts: datetime.datetime.fromtimestamp(ts)

        metadata_base = {
            "title": None,
            "date": None,
            "last_modified": None,
            "draft": True,
            "publish": False,
            "math": False,
            "mermaid": False
        }

        metadata = metadata_base
        metadata["date"] = ts_to_dt(fpath.stat().st_ctime)

        for k,v in self.metadata.items():
            metadata[k] = v

        for hnum in range(1,6):
            pattern = rf'^{"#"*hnum} (.*)$'
            title = re.search(pattern, self.content, flags=re.MULTILINE) 
            if title is not None:
                break
        metadata["title"] = f"\"{fpath.name}\"" if title is None else title.group(1)
        metadata["last_modified"] = ts_to_dt(fpath.stat().st_mtime)

        self.metadata = metadata

    def clear_metadata(self):
        self.metadata = {}


def add_metadata():
    for fpath in md_files():
        with open(fpath, 'r') as f:
            post = frontmatter.load(f)
            post.__class__ = Post
            post.modify_metadata(fpath)
        with open(fpath, 'w') as f:
            ftxt = frontmatter.dumps(post)
            f.write(ftxt)

def clear_metadata():
    for fpath in md_files():
        with open(fpath, 'r') as f:
            post = frontmatter.load(f)
            post.__class__ = Post
            post.clear_metadata()
        with open(fpath, 'w') as f:
            ftxt = frontmatter.dumps(post)
            f.write(ftxt)

def publish(fp = None):
    config = lConfig.get() # fails here if file doesn't exist
    publish_dir = pathlib.Path(config['settings']['publish_dir'])
    content_dir = publish_dir.joinpath("content/post")
    image_dir = publish_dir.joinpath("static/images")

    for fpath in md_files():
        if fp is not None and pathlib.Path(fp) != fpath:
            continue
        with open(fpath, 'r') as f:
            post = frontmatter.load(f)
            post.__class__ = Post

            if 'publish' in post.metadata and post.metadata['publish'] is True \
            and 'draft' in post.metadata and post.metadata['draft'] is False:
                # replace the images in the post and copy the images to image_dir
                post.move_images(image_dir)
                if 'mermaid' in post.metadata and post.metadata['mermaid'] is True:
                    post.process_codeblock(lang_name='mermaid', start_tag=r'{{< mermaid align="center">}}', end_tag=r'{{< /mermaid >}}')
            else:
                continue

        dest_path = content_dir.joinpath(f"{fpath.stem}.pdc")

        with open(dest_path, 'w') as f:
            ftxt = frontmatter.dumps(post)
            f.write(ftxt)