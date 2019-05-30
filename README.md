# dcovr
A tool to generate delta code coverage report from gcovr report

## requirements

- python packagges: jinja2

## install

Option1:
just copy dcovr dir to the git repo root. move dcovr.exe to git repo root

Option2:
Install the dcovr package and mv dcovr.exe to your `PATH`

## example

`./dcovr.exe --since=7fff --until=01222 --prefix=utcov. --report-dir=./test_output/report/`
