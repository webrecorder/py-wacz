import unittest, os, zipfile, sys, gzip, json, tempfile
from wacz.main import main, now
from unittest.mock import patch
from wacz.util import hash_stream
from frictionless import validate, Report

TEST_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fixtures")


class TestWaczFor(unittest.TestCase):
    @classmethod
    @patch("wacz.main.now")
    def setUpClass(self, mock_now):
        mock_now.return_value = (2020, 10, 7, 22, 29, 10)
        self.tmpdir = tempfile.TemporaryDirectory()
        with open(os.path.join(self.tmpdir.name, "test-pages.jsonl"), "wt") as fh:
            fh.write('{"format": "json-pages-1.0", "id": "pages", "title": "Pages"}\n')
            fh.write(
                '{"id": "abcdef", "url": "https://www.example.com/#hashtag", "title": "Example", "loadState": 4}\n'
            )

        main(
            [
                "create",
                "-f",
                os.path.join(TEST_DIR, "example-collection.warc"),
                "-p",
                os.path.join(self.tmpdir.name, "test-pages.jsonl"),
                "-o",
                os.path.join(self.tmpdir.name, "example-custom-page.wacz"),
            ]
        )

    def test_hash(self):
        with zipfile.ZipFile(
            os.path.join(self.tmpdir.name, "example-custom-page.wacz"), "r"
        ) as zip_ref:
            zip_ref.extract(
                "pages/pages.jsonl",
                os.path.join(self.tmpdir.name, "extract-custom-page"),
            )
            zip_ref.close()

        with open(
            os.path.join(
                self.tmpdir.name, "extract-custom-page", "pages", "pages.jsonl"
            ),
            "rt",
        ) as f:
            content = f.read()

        assert (
            content
            == """\
{"format": "json-pages-1.0", "id": "pages", "title": "Pages"}
{"id": "abcdef", "url": "https://www.example.com/#hashtag", "title": "Example", "loadState": 4, "ts": "2020-10-07T21:22:36Z"}
"""
        )
