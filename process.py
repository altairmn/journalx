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
import config

def parse():
    parser = argparse.ArgumentParser()
    parser.add_argument("--add_metadata", action="store_true", dest="add_metadata", help="Add metadata to all the files")
    parser.add_argument("--publish", action="store_true", dest="publish", help="Publish the posts")
    parser.print_help()
    args = parser.parse_args()
    return args.__dict__

def ts_to_dt(ts):
    return datetime.datetime.fromtimestamp(ts)

class FileMetadata(object):
    def __init__(self, base):
        self.base = base

    def apply(self, fpath):
        with open(fpath, 'r') as f:
            post = frontmatter.load(f)

        metadata = copy.deepcopy(self.base)
        metadata["title"] = f"\"{fpath.name}\""
        metadata["created_date"] = ts_to_dt(fpath.stat().st_ctime)
        metadata["modified_date"] = ts_to_dt(fpath.stat().st_mtime)

        for k,v in post.metadata.items():
            metadata[k] = v

        write_post(fpath, metadata, post.content)

def write_post(fpath, metadata, content):
        # remove the metadata and then add it
        meta_text = [f"{k}: {v}" for k,v in metadata.items()]
        with open(fpath, 'w') as f:
            f.write("---\n")
            f.write('\n'.join(meta_text))
            f.write("\n---\n\n")
            f.write(content)


def add_metadata():
    vault_dir = pathlib.Path(config.vault_dir)

    # look for all markdown files
    md_pattern = f"{vault_dir.as_posix()}/**/*.md"
    op = glob.glob(md_pattern, recursive=True)

    # collect all the files that have to be published
    metadata_base = {
        "title": None,
        "created_date": None,
        "modified_date": None,
        "draft": True,
        "publish": False,
        "math": False
    }
    fmeta = FileMetadata(metadata_base)

    for fname in op:
        try:
            fpath = vault_dir.joinpath(fname)
            fmeta.apply(fpath)
        except Exception as exc:
            print(exc)

def get_img_path_processor(img_dir):
    def process_img_path(matchobj):
        src_path = pathlib.Path(matchobj.group(2))
        dest_path = img_dir.joinpath(src_path.name)
        return matchobj.group(0).replace(matchobj.group(2), dest_path.as_posix())
    return process_img_path

def process_images(content, publish_dir):
    img_dir = publish_dir.joinpath("static/images")
    img_processor = get_img_path_processor(img_dir)

    # for each file, find all images
    img_regex = r'!\[(\S*)\]\((\S*)\)'
    imgs = re.findall(img_regex, content)

    # copy images to another folder
    for img in imgs:
        img_path = pathlib.Path(img[1])
        dest_path = img_dir.joinpath(img_path.name)
        shutil.copy2(img_path, dest_path)

    # replace in content   
    content = re.sub(img_regex, img_processor, content)

    # write to dest
    return content    
    

def publish(publish_dir):
    vault_dir = pathlib.Path(config.vault_dir)

    # look for all markdown files
    md_pattern = f"{vault_dir.as_posix()}/**/*.md"
    op = glob.glob(md_pattern, recursive=True)

    content_dir = publish_dir.joinpath("content/post/")

    for fpath_str in op:
        fpath = vault_dir.joinpath(fpath_str)
        with open(fpath, 'r') as f:
            try:
                post = frontmatter.load(f)
                if 'publish' in post.metadata and post.metadata['publish'] is True \
                and 'draft' in post.metadata and post.metadata['draft'] is False:
                    # replace the images in the post
                    content = process_images(post.content, publish_dir)

                    # write post to destination
                    dest_path = content_dir.joinpath(fpath.name)
                    write_post(dest_path, post.metadata, content)
            except Exception as exc:
                pass

if __name__ == "__main__":
    action = parse()
    if (config.vault_dir is None || config.publish_dir is None):
        print("Please specify both vault_dir and publish_dir. Exiting..")
        exit(0)

    if (action['add_metadata'] == True):
        print("Adding metadata to content...")
        add_metadata()
    elif (action['publish'] == True):
        publish_dir = pathlib.Path(config.publish_dir)
        print("Publishing content...")
        publish(publish_dir)

