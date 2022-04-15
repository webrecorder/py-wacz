# 0.4.6

- wacz zip write: ensure zip file is fully closed on exit (fixes #20
- ci: add ci for py3.10
- wacz create: support --url, --detect-pages and --split-seeds to write detect pages to extraPages.jsonl, specified seed to pages.jsonl
- text extract: don't raise exception, keep parsed text

# 0.4.5
- Pages: also ignore pages with invalid utf-8 encoding

# 0.4.4

- Pages: read pages line by line in case of large pages file

# 0.4.3

- Pages: Better page parsing fix, more lenient on page parsing errors: print error and continue, ignoring invalid page 

# 0.4.2

- Pages: Fix parsing of page URLs that contain extra ':'

# 0.4.1

- More efficient hash computation

# 0.4.0

- Add support for signing and verification!

# 0.3.1

- Ensure passed in pages are check via both http and https URLs
- Update to cdxj-indexer 1.4.1, supporting improved indexing of JSON POST requests

# 0.3.0

- Add `name` field to `resources` for better compatibility with frictionless spec.

# wacz 0.3.0b1

Improved compatibility with frictionless data spec

- Top-level `title`, `description`, `created`, `software` fields and optional `mainPageURL` and `mainPageTS` fields.
- Include full WARC record digests in `recordDigest` field in CDX, `digest` in IDX
- Support for `pages/extraPages.jsonl` passed in via --extra-pages/-e flag
