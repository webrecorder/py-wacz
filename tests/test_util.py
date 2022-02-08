import unittest
import tempfile
import os
import zipfile, json, gzip, hashlib
from io import BytesIO

from wacz.util import hash_stream, validateJSON

TEST_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fixtures")


class TestUtilFunctions(unittest.TestCase):
    def test_util_hash(self):
        """When invoking the util hash method a  hash should be returned"""
        test_hash = "sha256:%s" % hashlib.sha256("test".encode("utf-8")).hexdigest()
        bytes_, hash_ = hash_stream("sha256", BytesIO("test".encode("utf-8")))
        self.assertEqual(bytes_, 4)
        self.assertEqual(hash_, test_hash)

        test_hash = "md5:%s" % hashlib.md5("test".encode("utf-8")).hexdigest()
        bytes_, hash_ = hash_stream("md5", BytesIO("test".encode("utf-8")))
        self.assertEqual(bytes_, 4)
        self.assertEqual(hash_, test_hash)

    def test_util_validate_json_succeed(self):
        """validate json method should succed with valid json"""
        self.assertTrue(validateJSON('{"test": "test"}'))

    def test_util_validate_json_fail(self):
        """validate json method should fail with valid json"""
        self.assertFalse(validateJSON('test": "test"}'))


if __name__ == "__main__":
    unittest.main()
