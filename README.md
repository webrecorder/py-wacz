## py-wacz

The **py-wacz** repository contains a Python module and command line utility
for working with web archive data using the [WACZ] format specification. Web
Archive Collection Zipped (WACZ) allows web archives to be shared and
distributed by providing a predictable way of packaging up web archive data and
metadata as a ZIP file. The **wacz** command line utility supports converting
any [WARC] files into WACZ files, and optionally generating full-text search
indices of pages.

## Install

Use pip to install the module and a command line utility:

```
pip install wacz
```

Once installed you can use the **wacz** command line utility to *create* and *validate* WACZ files.

## Create

To create a WACZ package you can point **wacz** at a WARC file and tell it
where to write the WACZ with the `-o` option:

```
wacz create -o myfile.wacz <path/to/WARC>
```

The resulting `myfile.wacz` should be loadable via [ReplayWeb.page].

**wacz** accepts the following options for  customizing how the WACZ file is assembled.

### -f --file

Explicitly declare the file being passed to the create function.

```
wacz create -f tests/fixtures/example-collection.warc
```

### -o --output

Explicitly declare the name of the wacz being created

```
wacz create tests/fixtures/example-collection.warc -o mywacz.wacz
```

### -t --text

Generates pages.jsonl page index with a full-text index, must be run in conjunction with --detect-pages. Will have no effect if run alone

```
wacz create tests/fixtures/example-collection.warc -t
```

### --detect-pages

Generates pages.jsonl page index without a full-text index

```
wacz create tests/fixtures/example-collection.warc --detect-pages
```

### -p --pages

Overrides the pages index generation with the passed jsonl pages.

```
wacz create tests/fixtures/example-collection.warc -p passed_pages.jsonl
```

### -t --text

You can add a full text index by including the --text tag

```
wacz create tests/fixtures/example-collection.warc -p passed_pages.jsonl --text
```

### --ts

Overrides the ts metadata value in the datapackage.json file

```
wacz create tests/fixtures/example-collection.warc --ts TIMESTAMP
```

### --url

Overrides the url metadata value in the datapackage.json file

```
wacz create tests/fixtures/example-collection.warc --url URL
```

### --title

Overrides the titles metadata value in the datapackage.json file

```
wacz create tests/fixtures/example-collection.warc --title TITLE
```

### --desc

Overrides the desc metadata value in the datapackage.json file

```
wacz create tests/fixtures/example-collection.warc --desc DESC
```
 
### --hash-type

Allows the user to specify the hash type used:  (sha256 or md5):

```
wacz create tests/fixtures/example-collection.warc --hash-type md5
```

### --signing-url

An optional URL for [WACZ signing server](https://github.com/webrecorder/authsign) which will be used to add a signature to the new WACZ.

This URL should point to an authsign `/sign` api endpoint.

See the section on `--verify-auth` for more info on signing and verification.

### --signing-token

An optional, secret token passed to signing server to allow access. See `authsign` for more details.


## Validate

You can also validate an existing WACZ file by running:

```
wacz validate myfile.wacz
```

### -f --file

Explicitly declare the file being passed to the validate function.

```
wacz validate -f tests/fixtures/example-collection.warc
```

### --verify-auth

New option in 0.4.0, this option also verifies the WACZ is signed, using [authsign](https://github.com/webrecorder/authsign)

The verification can be done locally, or via remote signing/verification server.

To use remote server, add `--verify-url` which should be a URL pointing to the authsign `/verify` endpoint.

To run locally, the `authsign` must be installed, which can be done by running `pip install wacz[signing]`.

See [WACZ Authentication Spec](https://github.com/webrecorder/wacz-auth-spec) on WACZ authentication.

This feature and the specification are still in development (alpha-quality) and is subject to change.



## Testing

If you are developing wacz you can run the unit tests with [pytest]:

```
pytest tests
```

[WACZ]: https://github.com/webrecorder/wacz-format
[WARC]: https://en.wikipedia.org/wiki/Web_ARChive
[ReplayWeb.page]: https://replayweb.page
[pytest]: https://docs.pytest.org/
