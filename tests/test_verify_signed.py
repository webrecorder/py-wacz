import unittest, os
from wacz.main import main


TEST_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "fixtures")


class TestVerifySigned(unittest.TestCase):
    def test_wacz_valid_and_verify_sig(self):
        self.assertEqual(
            main(
                [
                    "validate",
                    "--verify-auth",
                    "-f",
                    os.path.join(TEST_DIR, "valid_signed_example_1.wacz"),
                ]
            ),
            0,
        )

    def test_wacz_valid_and_not_valid_sig(self):
        self.assertEqual(
            main(
                [
                    "validate",
                    "--verify-auth",
                    "-f",
                    os.path.join(TEST_DIR, "invalid_signed_example_1.wacz"),
                ]
            ),
            1,
        )

    def test_wacz_valid_not_signed(self):
        self.assertEqual(
            main(
                [
                    "validate",
                    "--verify-auth",
                    "-f",
                    os.path.join(TEST_DIR, "valid_example_1.wacz"),
                ]
            ),
            1,
        )
