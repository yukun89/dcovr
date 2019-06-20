dcov is a tool to get increment code coverage report from gcovr report.

## Install

sudo pip install .

## Uninstall

sudo pip uninstall dcovr. or python setup.py install

## Usage

Run `dcov` in git root of your code. You can use `dcov -h` for more information.

example:
`dcov --since=7fff --until=01222 --prefix=utcov. --report-dir=./test_output/report/`

Then you will get the increment result in `increment_coverage_report.html`
