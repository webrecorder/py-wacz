import unittest, os, zipfile, sys, gzip, json, tempfile
from wacz.main import main, now
from unittest.mock import patch
from wacz.util import hash_file
from frictionless import validate, Report

TEST_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fixtures")


class TestWaczFormat(unittest.TestCase):
    def find_resource(self, resource_list, filename):
        for file in resource_list:
            if filename in file["path"]:
                return file

    @classmethod
    @patch("wacz.main.now")
    def setUpClass(self, mock_now):
        mock_now.return_value = (2020, 10, 7, 22, 29, 10)
        self.tmpdir = tempfile.TemporaryDirectory()
        main(
            [
                "create",
                "-f",
                os.path.join(TEST_DIR, "example-collection.warc"),
                "-o",
                os.path.join(self.tmpdir.name, "valid_example_1.wacz"),
                "-l",
                os.path.join(TEST_DIR, "logs"),
            ]
        )
        with zipfile.ZipFile(
            os.path.join(self.tmpdir.name, "valid_example_1.wacz"), "r"
        ) as zip_ref:
            zip_ref.extractall(os.path.join(self.tmpdir.name, "unzipped_wacz_1"))
            zip_ref.close()

        self.wacz_file = os.path.join(self.tmpdir.name, "valid_example_1.wacz")
        self.warc_file = os.path.join(TEST_DIR, "example-collection.warc")

        self.wacz_archive_warc = os.path.join(
            self.tmpdir.name,
            "unzipped_wacz_1/archive/example-collection.warc",
        )
        self.wacz_index_cdx = os.path.join(
            self.tmpdir.name,
            "unzipped_wacz_1/indexes/index.cdx.gz",
        )
        self.wacz_index_idx = os.path.join(
            self.tmpdir.name,
            "unzipped_wacz_1/indexes/index.idx",
        )
        self.wacz_json = os.path.join(
            self.tmpdir.name,
            "unzipped_wacz_1/datapackage.json",
        )
        self.wacz_log = os.path.join(
            self.tmpdir.name, "unzipped_wacz_1/logs/wr-specs-crawl.log"
        )
        self.wacz_second_log = os.path.join(
            self.tmpdir.name, "unzipped_wacz_1/logs/wr-crawl.log"
        )

    def test_components(self):
        """Check that the basic components of a wacz file exist"""
        self.assertTrue(
            "example-collection.warc"
            in os.listdir(os.path.join(self.tmpdir.name, "unzipped_wacz_1/archive"))
        )
        self.assertTrue(
            "index.cdx.gz"
            in os.listdir(os.path.join(self.tmpdir.name, "unzipped_wacz_1/indexes"))
        )
        self.assertTrue(
            "index.idx"
            in os.listdir(os.path.join(self.tmpdir.name, "unzipped_wacz_1/indexes"))
        )
        self.assertTrue(
            "pages.jsonl"
            in os.listdir(os.path.join(self.tmpdir.name, "unzipped_wacz_1/pages"))
        )
        self.assertTrue(
            "datapackage.json"
            in os.listdir(os.path.join(self.tmpdir.name, "unzipped_wacz_1/"))
        )

    def test_archive_structure(self):
        """Check that the hash of the original warc file matches that of the warc file in the archive folder"""
        original_warc = hash_file("sha256", self.warc_file)

        archive_warc = hash_file("sha256", self.wacz_archive_warc)

        self.assertEqual(original_warc, archive_warc)

    def test_idx_structure(self):
        """Check that the idx file has the expected content"""
        with open(self.wacz_index_idx, "rb") as f:
            content = f.read()
        f.close()

        # doing a startswith because compressed gzip block may be different depending on platform, so sha256 is platform dependent
        # just checking that the hash is set
        self.assertTrue(
            content.startswith(
                b'!meta 0 {"format": "cdxj-gzip-1.0", "filename": "index.cdx.gz"}\ncom,example)/ 20201007212236 {"offset": 0, "length": 256, "digest": "sha256:',
            )
        )

    def test_cdx_structure(self):
        """Check that the cdx file has the expected content"""
        content = ""
        with gzip.open(self.wacz_index_cdx, "rb") as f:
            for line in f:
                content = content + line.decode()
        f.close()
        self.assertEqual(
            content,
            'com,example)/ 20201007212236 {"url": "http://www.example.com/", "mime": "text/html", "status": "200", "digest": "sha1:WJM2KPM4GF3QK2BISVUH2ASX64NOUY7L", "length": "1293", "offset": "845", "filename": "example-collection.warc", "recordDigest": "sha256:f78838ace891c96f7a6299e9e085b55a5aba8950a6d77f0f2e9ffe90f63255f2"}\n',
        )

    def test_logs(self):
        with open(self.wacz_log, "rb") as f:
            content = f.read()
        f.close()

        with open(self.wacz_second_log, "rb") as f:
            second_content = f.read()
        f.close()

        self.assertTrue(
            content.startswith(
                b'{"logLevel":"info","timestamp":"2023-02-23T20:29:36.908Z","context":"general","message":"Seeds","details":[{"url":"https://specs.webrecorder.net/","include":[{}],"exclude":[],"scopeType":"prefix","sitemap":false,"allowHash":false,"maxExtraHops":0,"maxDepth":99999}]}\n',
            )
        )
        self.assertTrue(
            second_content.startswith(
                b'{"logLevel":"info","timestamp":"2023-02-23T23:44:39.665Z","context":"general","message":"Page context being used with 1 worker","details":{}}\n'
            )
        )

    def test_data_package_structure(self):
        """Check that the package_descriptor is valid"""
        f = open(self.wacz_json, "rb")
        json_parse = json.loads(f.read())
        # Make sure it's recording the correct number of resources
        self.assertEqual(len(json_parse["resources"]), 6)

        # Check that the correct hash was recorded for a warc
        original_warc = hash_file("sha256", self.warc_file)

        warc_resource = self.find_resource(
            json_parse["resources"], "example-collection.warc"
        )
        self.assertEqual(original_warc, warc_resource["hash"])

        # Check that the correct hash was recorded for the index.idx
        original_wacz_index_idx = hash_file("sha256", self.wacz_index_idx)
        idx_resource = self.find_resource(json_parse["resources"], "idx")
        self.assertEqual(original_wacz_index_idx, idx_resource["hash"])

        # Check that the correct hash was recorded for the index.cdx.gz
        original_wacz_index_cdx = hash_file("sha256", self.wacz_index_cdx)
        cdx_resource = self.find_resource(json_parse["resources"], "cdx")
        self.assertEqual(original_wacz_index_cdx, cdx_resource["hash"])

        # Check that the correct hash was recorded for the log files
        original_wacz_log = hash_file("sha256", self.wacz_log)
        log_resource = self.find_resource(json_parse["resources"], "wr-specs-crawl.log")
        self.assertEqual(original_wacz_log, log_resource["hash"])

        second_wacz_log = hash_file("sha256", self.wacz_second_log)
        log_resource = self.find_resource(json_parse["resources"], "wr-crawl.log")
        self.assertEqual(second_wacz_log, log_resource["hash"])

        # Use frictionless validation
        valid = validate(self.wacz_json)
        self.assertTrue(valid.valid)


if __name__ == "__main__":
    unittest.main()
