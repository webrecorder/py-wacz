# 0.6.0

- Fix usage on newer Python and setuptools version. (https://github.com/webrecorder/py-wacz/pull/54)
- Modernize packaging using pyproject.toml. (https://github.com/webrecorder/py-wacz/pull/55)
- Correctly report all validation errors when a WACZ fails to validate. (https://github.com/webrecorder/py-wacz/pull/62)

Note: the minimum Python version is now 3.11.

# 0.5.0

- Add --copy-pages option to copy pages.jsonl/extraPages.jsonl directly to WACZ by @tw4l in https://github.com/webrecorder/py-wacz/pull/43

# 0.4.9

- Fix typos by @stavares843 in https://github.com/webrecorder/py-wacz/pull/31
- Update README to fix --verifier-url param by @vbanos in https://github.com/webrecorder/py-wacz/pull/34
- Ignore hashtag when matching pages to URLs in WARCs by @ikreymer in https://github.com/webrecorder/py-wacz/pull/35

# 0.4.8

- Add -l/--log-directory option to add logs directory to WACZ

# 0.4.7

- include request cookie in cdxj via 'req.http:cookie' field (#27)
- fix Click dependency version

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
