import hashlib, datetime, json
from warcio.timeutils import iso_date_to_timestamp
import pkg_resources

WACZ_VERSION = "1.1.1"


BUFF_SIZE = 1024 * 64


def check_http_and_https(url, ts, pages_dict):
    """Checks for http and https versions of the passed url
    in the pages dict
    :param url to check, pages_dict the user passed
    :returns: True or False depending on if a match was found
    :rtype: boolean
    """
    parts = url.split(":", 1)
    if len(parts) < 2:
        return ""

    url_body = parts[1]
    checks = [
        f"http:{url_body}",
        f"https:{url_body}",
        f"{ts}/http:{url_body}",
        f"{ts}/https:{url_body}",
    ]

    for check in checks:
        if check in pages_dict:
            return check

    return ""


def get_py_wacz_version():
    """Get version of the py-wacz package"""
    return pkg_resources.get_distribution("wacz").version


def hash_stream(hash_type, stream):
    """Hashes the stream with given hash_type hasher"""
    try:
        hasher = hashlib.new(hash_type)
    except:
        return 0, ""

    size = 0

    while True:
        buff = stream.read(BUFF_SIZE)
        size += len(buff)
        hasher.update(buff)
        if not buff:
            break

    return size, hash_type + ":" + hasher.hexdigest()


def construct_passed_pages_dict(passed_pages_list):
    """Creates a dictionary of the passed pages with the url as the key or ts/url if ts is present and the title and text as the values if they have been passed"""
    passed_pages_dict = {}

    for page_data in passed_pages_list:
        # Skip invalid page data
        try:
            page_dict = json.loads(page_data)
        except:
            print("Warning: Skipping invalid page {0}".format(page_data))
            continue

        # Skip the file's header if it's been set
        if "format" not in page_dict:
            url = page_dict.pop("url", "")

            # Set the default key as url
            key = url

            # If timestamp is present overwrite the key to be 'ts/url'
            if "ts" in page_dict:
                key = iso_date_to_timestamp(page_dict.pop("ts")) + "/" + url

            # Add the key to the dictionary with remaining data
            passed_pages_dict[key] = page_dict

    return passed_pages_dict


def now():
    """Returns the current time"""
    return tuple(datetime.datetime.utcnow().timetuple()[:6])


def validateJSON(jsonData):
    """Attempts to validate a string as json"""
    try:
        json.loads(jsonData)
    except ValueError as err:
        return False
    return True
