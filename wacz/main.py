from argparse import ArgumentParser, RawTextHelpFormatter
from io import BytesIO, StringIO, TextIOWrapper
import os, json, datetime, shutil, zipfile, sys, gzip, pkg_resources, zlib
from wacz.waczindexer import WACZIndexer
from wacz.util import now, WACZ_VERSION, construct_passed_pages_dict
from wacz.validate import Validation, OUTDATED_WACZ
from wacz.util import validateJSON, get_py_wacz_version, validate_pages_jsonl_file
from warcio.timeutils import iso_date_to_timestamp
from warcio.bufferedreaders import DecompressingBufferedReader

"""
WACZ Generator
"""

PAGE_INDEX = "pages/pages.jsonl"
EXTRA_PAGES_INDEX = "pages/extraPages.jsonl"

PAGE_INDEX_TEMPLATE = "pages/{0}.jsonl"

# setting to size matching archiveweb.page defaults
DEFAULT_NUM_LINES = 1024


def main(args=None):
    parser = ArgumentParser(
        description="WACZ creator", formatter_class=RawTextHelpFormatter
    )

    parser.add_argument("-V", "--version", action="version", version=get_version())

    subparsers = parser.add_subparsers(dest="cmd")
    subparsers.required = True

    create = subparsers.add_parser("create", help="create wacz file")
    create.add_argument("inputs", nargs="+")
    create.add_argument("-f", "--file", action="store_true")

    create.add_argument("-o", "--output", default="archive.wacz")

    create.add_argument("-e", "--extra-pages")

    create.add_argument(
        "-t",
        "--text",
        help="Generates pages.jsonl with a full-text index. Must be run in addition with --detect-pages or it will have no effect",
        action="store_true",
    )

    create.add_argument(
        "-p",
        "--pages",
        help="Overrides the pages generation with the passed jsonl pages",
        action="store",
    )

    create.add_argument(
        "-d",
        "--detect-pages",
        help="Generates pages.jsonl without a text index",
        action="store_true",
    )

    create.add_argument(
        "-c",
        "--copy-pages",
        help="Overrides the pages/extra-pages options by copying files to WACZ without parsing",
        action="store_true",
    )

    create.add_argument(
        "--hash-type",
        choices=["sha256", "md5"],
        help="Allows the user to specify the hash type used. Currently we allow sha256 and md5",
    )

    create.add_argument(
        "-l",
        "--log-directory",
        help="Adds log files in specified directory to WACZ",
        action="store",
    )

    create.add_argument("--split-seeds", action="store_true")

    create.add_argument("--ts")
    create.add_argument("--url")
    create.add_argument("--date")
    create.add_argument("--title")
    create.add_argument("--desc")

    create.add_argument(
        "--signing-url",
        help="URL of signing server to obtain signature for datapackage-digest.json",
    )
    create.add_argument("--signing-token", help="Auth token for signing URL")

    create.set_defaults(func=create_wacz)

    validate = subparsers.add_parser("validate", help="validate a wacz file")
    validate.add_argument("-f", "--file", required=True)
    validate.set_defaults(func=validate_wacz)

    validate.add_argument(
        "--verify-auth",
        action="store_true",
        help="If set, will attempt to validate authenticity of the WACZ, either directly or via remote server if --verifier-url is also set",
    )

    validate.add_argument(
        "--verifier-url",
        help="URL of verify server to verify the signature, if any, in dapackage-digest.json",
    )

    index = subparsers.add_parser("index", help="generate a WACZ-level CDXJ index")
    index.add_argument(
        "-f", "--file", required=True, help="The WACZ file to read and index."
    )
    index.add_argument(
        "-o",
        "--output-file",
        required=False,
        default="-",
        help="The CDXJ output file. Defaults to '-' which means to print to STDOUT.",
    )
    index.add_argument(
        "-p",
        "--wacz-prefix",
        required=False,
        default=None,
        help="Prefix to use when referring to the WACZ file from the CDXJ index. e.g. if the prefix is '/disk/path/' and the WACZ is called example.wacz then the CDXJ file will refer to '/disk/path/example.wacz'.",
    )
    index.set_defaults(func=index_wacz)

    cmd = parser.parse_args(args=args)

    if cmd.cmd == "create" and cmd.ts is not None and cmd.url is None:
        parser.error("--url must be specified when --ts is passed")

    if cmd.cmd == "create" and cmd.detect_pages is not False and cmd.pages is not None:
        parser.error(
            "--pages and --detect-pages can't be set at the same time they cancel each other out."
        )

    value = cmd.func(cmd)
    return value


def get_version():
    return "%(prog)s " + get_py_wacz_version() + " -- WACZ File Format: " + WACZ_VERSION


def validate_wacz(res):
    validate = Validation(
        res.file, verify_auth=res.verify_auth, verifier_url=res.verifier_url
    )
    version = validate.version
    validation_tests = []

    if version == OUTDATED_WACZ:
        print("Validation succeeded, the passed WACZ is outdated but valid")
        return 0

    elif version == WACZ_VERSION:
        validation_tests += [
            validate.check_required_contents,
            validate.frictionless_validate,
            validate.check_file_paths,
            validate.check_file_hashes,
            validate.check_data_package_hash_and_sig,
        ]
    else:
        print("Validation failed, the passed WACZ is invalid")
        return 1

    for func in validation_tests:
        success = func()
        if success is False:
            print("Validation failed, the passed WACZ is invalid")
            return 1

    print("Validation succeeded, the passed WACZ is valid")
    return 0


def index_wacz(res):
    # Open up the ZIP:
    with zipfile.ZipFile(res.file) as zf:
        # Determine the WACZ filename/path to use:
        wacz_path = os.path.basename(res.file)
        # Allow users to specify the prefix where the WACZ is stored:
        if res.wacz_prefix:
            wacz_path = f"{res.wacz_prefix}{wacz_path}"

        # Get a look-up table for offsets for each archive file:
        archive_offsets = {}
        archives_prefix = "archive/"
        for zinfo in zf.infolist():
            if zinfo.filename.startswith(archives_prefix):
                archive_name = zinfo.filename[len(archives_prefix) :]
                archive_offsets[archive_name] = zinfo.header_offset + len(
                    zinfo.FileHeader()
                )
                if zinfo.compress_type != 0:
                    raise Exception(
                        "Can't generate WACZ-level index from compressed WARC records! This file does not conform to the WACZ standard!"
                    )

        # Set up the output stream:
        with open(
            res.output_file, "w"
        ) if res.output_file != "-" else sys.stdout as f_out:
            # Stream through the index in the WACZ:
            index_file = "indexes/index.cdx.gz"
            zinfo = zf.getinfo(index_file)
            with zf.open(index_file) as f:
                reader = DecompressingBufferedReader(f)
                while True:
                    line = reader.readline()
                    # If we reach the end, end:
                    if len(line) == 0:
                        break
                    # Otherwise, decode the line:
                    surt, timestamp, json_data_str = (
                        line.decode("utf-8").rstrip("\n").split(" ", maxsplit=2)
                    )
                    json_data = json.loads(json_data_str)
                    # Also override the filename to point at the WACZ:
                    archive_filename = json_data["filename"]
                    json_data["filename"] = wacz_path
                    # Override the offset to include of file offset in the ZIP:
                    archive_offset = json_data["offset"]
                    json_data["offset"] = archive_offsets[archive_filename] + int(
                        archive_offset
                    )
                    # Output the modified values:
                    f_out.write(f"{surt} {timestamp} {json.dumps(json_data)}\n")


def create_wacz(res):
    wacz = zipfile.ZipFile(res.output, "w")

    # write index
    data_file = zipfile.ZipInfo("indexes/index.cdx.gz", now())

    index_file = zipfile.ZipInfo("indexes/index.idx", now())
    index_file.compress_type = zipfile.ZIP_DEFLATED

    index_buff = BytesIO()

    text_wrap = TextIOWrapper(index_buff, "utf-8", write_through=True)

    wacz_indexer = None

    passed_pages_dict = {}

    # Handle pages
    if res.pages != None:
        if res.copy_pages:
            print("Copying passed pages.jsonl file to WACZ")

            if not validate_pages_jsonl_file(res.pages):
                print("Unable to create WACZ without valid pages.jsonl file, quitting")
                wacz.close()
                return 1

            with open(res.pages, "rb") as fh:
                pages_jsonl = zipfile.ZipInfo("pages/pages.jsonl", now())
                with wacz.open(pages_jsonl, "w") as pages_file:
                    shutil.copyfileobj(fh, pages_file)

        else:
            print("Validating passed pages.jsonl file")
            passed_content = []
            with open(res.pages, "rb") as fh:
                for line in fh:
                    if not line:
                        continue

                    try:
                        line = line.decode("utf-8")
                        passed_content.append(line)
                    except:
                        print("Page data not utf-8 encoded, skipping", line)

            # Create a dict of the passed pages that will be used in the construction of the index
            passed_pages_dict = construct_passed_pages_dict(passed_content)

    if res.extra_pages:
        if res.copy_pages:
            print("Copying passed extraPages.jsonl file to WACZ")
            if validate_pages_jsonl_file(res.extra_pages):
                extra_pages_jsonl = zipfile.ZipInfo("pages/extraPages.jsonl", now())
                with open(res.extra_pages, "rb") as fh:
                    with wacz.open(extra_pages_jsonl, "w") as extra_pages_file:
                        shutil.copyfileobj(fh, extra_pages_file)
            else:
                print("Ignoring invalid extraPages.jsonl file")
        else:
            print("Validating extra pages file")
            extra_page_data = []
            with open(res.extra_pages) as fh:
                data = fh.read()
                for page_str in data.strip().split("\n"):
                    page_json = validateJSON(page_str)

                    if not page_json:
                        print("Warning: Ignoring invalid extra page\n %s" % page_str)
                        continue

                    extra_page_data.append(page_str.encode("utf-8"))

            extra_pages_file = zipfile.ZipInfo(EXTRA_PAGES_INDEX, now())
            with wacz.open(extra_pages_file, "w") as efh:
                efh.write(b"\n".join(extra_page_data))

    print("Reading and Indexing All WARCs")
    with wacz.open(data_file, "w") as data:
        wacz_indexer = WACZIndexer(
            text_wrap,
            res.inputs,
            sort=True,
            post_append=True,
            compress=data,
            lines=DEFAULT_NUM_LINES,
            digest_records=True,
            fields="referrer,req.http:cookie",
            data_out_name="index.cdx.gz",
            hash_type=res.hash_type,
            main_url=res.url,
            main_ts=res.ts,
            detect_pages=res.detect_pages,
            passed_pages_dict=passed_pages_dict,
            extract_text=res.text,
            signing_url=res.signing_url,
            signing_token=res.signing_token,
            split_seeds=res.split_seeds,
        )

        wacz_indexer.process_all()

    index_buff.seek(0)

    with wacz.open(index_file, "w") as index:
        shutil.copyfileobj(index_buff, index)

    # write archives
    print("Writing archives...")
    for _input in res.inputs:
        archive_file = zipfile.ZipInfo.from_file(
            _input, "archive/" + os.path.basename(_input)
        )
        with wacz.open(archive_file, "w") as out_fh:
            with open(_input, "rb") as in_fh:
                shutil.copyfileobj(in_fh, out_fh)
                path = "archive/" + os.path.basename(_input)

    if wacz_indexer.passed_pages_dict != None:
        for key in wacz_indexer.passed_pages_dict:
            print(
                "Invalid passed page. We were unable to find a match for %s" % str(key)
            )

    if res.log_directory:
        print("Writing logs...")
        log_dir = os.path.abspath(res.log_directory)
        for log_file in os.listdir(log_dir):
            log_path = os.path.join(log_dir, log_file)
            log_wacz_file = zipfile.ZipInfo.from_file(
                log_path, "logs/{}".format(log_file)
            )
            with wacz.open(log_wacz_file, "w") as out_fh:
                with open(log_path, "rb") as in_fh:
                    shutil.copyfileobj(in_fh, out_fh)
                    path = "logs/{}".format(log_file)

    if len(wacz_indexer.pages) > 0 and res.pages == None and not res.copy_pages:
        print("Generating page index...")
        # generate pages/text
        wacz_indexer.write_page_list(
            wacz,
            PAGE_INDEX,
            wacz_indexer.serialize_json_pages(
                wacz_indexer.pages.values(),
                id="pages",
                title="Pages",
                has_text=wacz_indexer.has_text,
            ),
        )

    if len(wacz_indexer.pages) > 0 and res.pages != None and not res.copy_pages:
        print("Generating page index from passed pages...")
        # Initially set the default value of the header id and title
        id_value = "pages"
        title_value = "Pages"

        # If the user has provided a title or an id in a header of their file we will use those instead of our default.
        try:
            header = json.loads(passed_content[0])
        except:
            print("Warning: Ignoring invalid page header: " + passed_content[0])
            header = {}

        if "format" in header:
            print("Header detected in the passed pages.jsonl file")
            if "id" in header:
                id_value = header["id"]
            if "title" in header:
                title_value = header["title"]

        wacz_indexer.write_page_list(
            wacz,
            PAGE_INDEX,
            wacz_indexer.serialize_json_pages(
                wacz_indexer.pages.values(),
                id=id_value,
                title=title_value,
                has_text=wacz_indexer.has_text,
            ),
        )

    if len(wacz_indexer.extra_pages) > 0 and not res.copy_pages:
        wacz_indexer.write_page_list(
            wacz,
            EXTRA_PAGES_INDEX,
            wacz_indexer.serialize_json_pages(
                wacz_indexer.extra_pages.values(),
                id="extra-pages",
                title="Extra Pages",
                has_text=wacz_indexer.has_text,
            ),
        )

    if len(wacz_indexer.extra_page_lists) > 0 and not res.copy_pages:
        print("Generating extra page lists...")

        for name, pagelist in wacz_indexer.extra_page_lists.items():
            if name == "pages":
                name = shortuuid.uuid()
            filename = PAGE_INDEX_TEMPLATE.format(name)

            wacz_indexer.write_page_list(wacz, filename, pagelist)

    # generate datapackage
    print("Generating datapackage.json")

    datapackage = wacz_indexer.generate_datapackage(res, wacz)
    datapackage_file = zipfile.ZipInfo("datapackage.json", now())
    datapackage_file.compress_type = zipfile.ZIP_DEFLATED
    datapackage_bytes = datapackage.encode("utf-8")
    wacz.writestr(datapackage_file, datapackage_bytes)

    print("Generating datapackage-digest.json")
    datapackage_digest_file = zipfile.ZipInfo("datapackage-digest.json", now())
    datapackage_digest_file.compress_type = zipfile.ZIP_DEFLATED
    wacz.writestr(
        datapackage_digest_file,
        wacz_indexer.generate_datapackage_digest(datapackage_bytes),
    )

    wacz.close()

    return 0


if __name__ == "__main__":
    main()
