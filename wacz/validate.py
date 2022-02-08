import tempfile, os, zipfile, json, pathlib, pkg_resources, gzip
from frictionless import validate
from wacz.util import hash_stream, now
from wacz.waczindexer import WACZIndexer
from io import BytesIO, StringIO, TextIOWrapper
import glob
import datetime
import logging
import requests

OUTDATED_WACZ = "0.1.0"


class Validation(object):
    def __init__(self, filename, verify_auth=False, verifier_url=None):
        self.dir = tempfile.TemporaryDirectory()
        self.wacz = filename
        with zipfile.ZipFile(filename, "r") as zip_ref:
            zip_ref.extractall(self.dir.name)
            zip_ref.close()
        self.detect_version()
        self.detect_hash_type()

        self.verify_auth = verify_auth
        self.verifier_url = verifier_url

    def check_required_contents(self):
        """Checks the general component of the wacz and notifies users whats missing"""
        if os.path.exists(os.path.join(self.dir.name, "datapackage.json")) is False:
            print("Datapackage is missing from your wacz file")
            return 1
        if (
            glob.glob(os.path.join(self.dir.name, "archive/*.warc")) == False
            and glob.glob(os.path.join(self.dir.name, "archive/*.warc.gz")) == False
        ):
            print(
                "A warc file is missing from your archive folder you must have a .warc or .warc.gz file in your archive folder"
            )
            return 1
        if (
            glob.glob(os.path.join(self.dir.name, "indexes/index.cdx.gz")) == False
            and glob.glob(os.path.join(self.dir.name, "indexes/index.cdx.gz")) == False
            and glob.glob(os.path.join(self.dir.name, "indexes/index.idx")) == False
        ):
            print(
                "An index file is missing from your indexes folder you must have an index.cdx.gz, index,cdx or index.idx in your index folder"
            )
            return 1
        if glob.glob(os.path.join(self.dir.name, "pages/pages.jsonl")) == False:
            print(
                "An index file is missing from your indexes folder you must have an index.cdx.gz, index,cdx or index.idx in your index folder"
            )
            return 1

        return 0

    def detect_hash_type(self):
        self.hash_type = None
        # we know the datapackage exists at this point because we're running it after the version check
        self.datapackage_path = os.path.join(self.dir.name, "datapackage.json")
        self.datapackage = json.loads(open(self.datapackage_path, "rb").read())
        try:
            self.hash_type = self.datapackage["resources"][0]["hash"].split(":")[0]
            return 0
        except:
            print(
                "\nHashing type was unable to be detected the wacz file may have no resources"
            )
            return 1

    def detect_version(self):
        self.version = None
        if os.path.exists(os.path.join(self.dir.name, "datapackage.json")):
            self.data_folder = os.listdir(self.dir.name)
            self.datapackage_path = os.path.join(self.dir.name, "datapackage.json")
            self.datapackage = json.loads(open(self.datapackage_path, "rb").read())

            try:
                self.version = self.datapackage["wacz_version"]
            except:
                print("\nVersion missing from datapackage.json, invalid wacz file")
                return

            print("\nVersion detected as %s" % self.version)
        elif os.path.exists(os.path.join(self.dir.name, "webarchive.yaml")):
            self.version = OUTDATED_WACZ
            self.webarchive_yaml = os.path.join(self.dir.name, "webarchive.yaml")
            print(
                "\nWACZ version detected as 0.1.0. This is an outdated version of WACZ."
            )
        else:
            print("\nVersion not able to be detected, invalid wacz file")

    def frictionless_validate(self):
        """Uses the frictionless data package to validate the datapackage.json file"""
        if validate(self.datapackage_path).valid == True:
            return True
        else:
            print(
                "\nFrictionless has detected that this is an invalid package with errors %s"
                % validate(self.datapackage_path).errors
            )
            return False

    def check_file_paths(self):
        """Uses the datapackage to check that all the files listed exist in the data folder or that the wacz contains a webarchive.yml file"""
        if self.version != OUTDATED_WACZ:
            package_files = [item["path"] for item in self.datapackage["resources"]]
            for filepath in pathlib.Path(self.dir.name).glob("**/*.*"):
                filename = os.path.basename(filepath)
                if (
                    filename != "datapackage.json"
                    and filename != "datapackage-digest.json"
                ):
                    file = str(filepath).split("/")[-2:]
                    file = "/".join(file)
                    if file not in package_files:
                        print("file %s is not listed in the datapackage" % file)
                        return False
        return True

    def check_compression(self):
        """WARCs and compressed cdx.gz should be in ZIP with 'store' compression (not deflate) Indexes and page list can be compressed"""
        wacz = zipfile.ZipInfo(self.wacz)
        if wacz.compress_type != 0:
            return False

        if os.path.exists(os.path.join(self.dir.name, "indexes/index.cdx.gz")):
            cdx = zipfile.ZipInfo(os.path.join(self.dir.name, "indexes/index.cdx.gz"))
            if cdx.compress_type != 0:
                return False

        archive_folder = os.listdir(os.path.join(self.dir.name, "archive"))
        for item in archive_folder:
            if ".warc" not in item and zf.getinfo(item).compress_type != 0:
                return False
        return True

    def check_indexes(self):
        """Indexing existing WARC which should match the index in the wacz"""
        if os.path.exists(os.path.join(self.dir.name, "indexes/index.cdx.gz")):
            for resource in self.datapackage["resources"]:
                if resource["path"] == "indexes/index.cdx.gz":
                    cdx = resource["hash"]
        else:
            return False

        archive_folder = os.listdir(os.path.join(self.dir.name, "archive"))
        for item in archive_folder:
            if ".warc" in item:
                warc = item
        wacz_file = tempfile.NamedTemporaryFile(delete=False)
        wacz = zipfile.ZipFile(wacz_file.name, "w")
        data_file = zipfile.ZipInfo("indexes/index.cdx.gz", now())
        index_buff = BytesIO()
        text_wrap = TextIOWrapper(index_buff, "utf-8", write_through=True)
        wacz_indexer = None
        with wacz.open(data_file, "w") as data:
            wacz_indexer = WACZIndexer(
                text_wrap,
                {},
                sort=True,
                compress=data,
                fields="referrer",
                data_out_name="index.cdx.gz",
                records="all",
                main_url="",
                detect_pages="",
            )

            wacz_indexer.process_all()
        wacz.close()
        dir = tempfile.TemporaryDirectory()
        with zipfile.ZipFile(self.wacz, "r") as zip_ref:
            zip_ref.extractall(dir.name)
            zip_ref.close()

        with open(os.path.join(dir.name, "indexes/index.cdx.gz"), "rb") as fd:
            size, hash_ = hash_stream(self.hash_type, fd)
            gzip_fd = gzip.GzipFile(fileobj=fd)

        return cdx == hash_

    def check_file_hashes(self):
        """Uses the datapackage to check that all the hashes of file in the data folder match those in the datapackage"""
        for filepath in pathlib.Path(self.dir.name).glob("**/*.*"):
            filename = os.path.basename(filepath)
            if filename != "datapackage.json" and filename != "datapackage-digest.json":
                with open(filepath, "rb") as fh:
                    size, hash_ = hash_stream(self.hash_type, fh)

                path = str(filepath).split("/")[-2:]
                path = "/".join(path)
                res = None
                for item in self.datapackage["resources"]:
                    if item["path"] == path:
                        res = item
                if res == None or (res["hash"] != hash_):
                    print(
                        "\nfile %s's hash does not match the hash listed in the datapackage"
                        % path
                    )
                    return False
        return True

    def check_data_package_hash_and_sig(self):
        data_digest_filename = os.path.join(self.dir.name, "datapackage-digest.json")
        if not os.path.exists(data_digest_filename):
            return True

        with open(data_digest_filename) as fh:
            data_digest = json.loads(fh.read())

        with open(os.path.join(self.dir.name, "datapackage.json"), "rb") as fh:
            size, hash_ = hash_stream(self.hash_type, fh)

        if hash_ != data_digest["hash"]:
            print("datapackage.json hash mismatch to datapackage-digest.json")
            return False

        signed_data = data_digest.get("signedData")
        if not signed_data:
            return True

        try:
            if self.datapackage.get("created") != signed_data.get("created"):
                print("signed timestamp != created timestamp")
                return False

            if not self.verify_auth:
                print(
                    "Note: Has signature, but auth verification skipped, run with --verify-auth to also include verification"
                )
                return True

            if self.verifier_url:
                res = requests.post(self.verifier_url, json=signed_data)
                success = res.status_code == 200
                msg = self.verifier_url
            else:
                try:
                    from authsign.verifier import Verifier
                except ImportError:
                    print(
                        "authsign package not found, can not verify signature. Try installing with 'pip install wacz[signing]'"
                    )
                    return False

                logging.basicConfig(
                    format="%(asctime)s: [%(levelname)s]: %(message)s",
                    level=logging.INFO,
                )

                verifier = Verifier()
                success = verifier(signed_data)
                msg = "direct check"

            if success:
                print("Successfully verified signature via: " + msg)
                return True
            else:
                print("Signature not verified via: " + msg)
                return False

        except Exception as e:
            import traceback

            traceback.print_exc()
            print("Validation failed due to error", e)
            return False

        return True

    def parse_date(self, string):
        if not string:
            return None

        return datetime.datetime.strptime(string, "%Y-%m-%dT%H:%M:%SZ")
