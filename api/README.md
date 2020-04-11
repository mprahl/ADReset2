# ADReset API

## Development

To setup a development environment:
* Create and activate a [Python virtual environment](https://virtualenv.pypa.io/en/stable/)
    (Python 3 is preferred)
* Install the API and its dependencies with:
  ```bash
  $ python setup.py develop
  ```

To start the development web server, run:

```bash
$ scripts/run-api.sh
```


## Run the Unit Tests

The unit tests use a tool called `tox` that allows you to run the tests using multiple Python
versions.

To install tox, run the following in your virtualenv:

```bash
$ pip install tox
```

To run the tests, run:

```bash
$ tox
```

To run just a single test, you can run:

```bash
$ tox -e py36 tests/api/test_v1.py::test_about
```

## Code Styling

The codebase conforms to the style enforced by `flake8` with the following exceptions:
* The maximum line length allowed is 100 characters instead of 80 characters

In addition to `flake8`, docstrings are also enforced by the plugin `flake8-docstrings` with
the following exemptions:
* D100: Missing docstring in public module
* D104: Missing docstring in public package

The format of the docstrings should be in the Sphynx style such as:

```
Add two integers together.

:param int num_one: a number to add with num_two
:param int num_two: a number to add with num_one
:return: the sum of num_one and num_two
:rtype: int
:raises ValueError: if the input values aren't integers
```

Additionally, [black](https://github.com/psf/black) is used to enforce other coding standards except
for quote normalization.
