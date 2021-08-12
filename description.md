# Journalx
## Supercharge your Obsidian Vault

Journalx allows you to turn your obsidian vault to a blog. It's still in early stages and requires a lot of work, but it's useful right away if you have some key ingredients in place.

### Prerequisites

- Python environment with Blogsidian installed
- Hugo blog setup

Your obsidian vault contains a lot of documents, but you want to publish only some them. Blogsidian handles:

- Automatically transfering documents that are tagged for publishing
- Transfers images to destination directory, and substitutes image paths in markdown
- [WIP] Watch dir for changes, and transfer on change
- [WIP] Build and publish after transfering documents
- [WIP] Handle other static assets other than files
- [WIP] Allow doc metadata to be specified by config file
- [WIP] Unit test for different scenarios
- [WIP] Better help messages

## Commands

Documents are transfered to blog directory, when they have the metadata values `publish: True` and `draft: False` in their metadata header.

If your documents don't have a yaml header (or only some of them do, not all), you can add it to all documents by

```bash
process.py --add_metadata
```



After you're done adding metadata, you can turn `publish:True` and `draft:False` on documents you want to publish, and they'll be transfered to configured `{publish_dir}/content/post` directory while the images will be transfered to `{publish_dir}/static/images`

```bash
process.py --publish
```

 
## Links

Learn more about journalx on [JournalX on Github](https://github.com/altairmn/journalx)