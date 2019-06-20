# -*- coding:utf-8 -*-
#
# A report generator for gcov 3.4
#
# This routine generates a format that is similar to the format generated
# by the Python coverage.py module.  This code is similar to the
# data processing performed by lcov's geninfo command.  However, we
# don't worry about parsing the *.gcna files, and backwards compatibility for
# older versions of gcov is not supported.
#
# Outstanding issues
#   - verify that gcov 3.4 or newer is being used
#   - verify support for symbolic links
#
# For documentation, bug reporting, and updates,
# see http://gcovr.com/
#
#  _________________________________________________________________________
#
#  Gcovr: A parsing and reporting tool for gcov
#  Copyright (c) 2013 Sandia Corporation.
#  This software is distributed under the BSD License.
#  Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,
#  the U.S. Government retains certain rights in this software.
#  For more information, see the README.md file.
# _________________________________________________________________________
#
#

import os
import sys

from argparse import ArgumentParser, ArgumentTypeError

from .utils import (Logger)
from .version import __version__
from .increment_generator import generate_delta_report


# helper for percentage actions
def check_percentage(value):
    try:
        x = float(value)
        if not (0.0 <= x <= 100.0):
            raise ValueError()
    except ValueError:
        raise ArgumentTypeError(
            "{value} not in range [0.0, 100.0]".format(value=value))
    return x


def create_argument_parser():
    """Create the argument parser."""

    parser = ArgumentParser(add_help=False)
    parser.usage = "dcovr [--since COMMIT_1] [--until COMMIT_2] [options]"
    parser.description = \
        "A utility to run dcov and summarize the coverage in simple reports."

    parser.epilog = "See <http://gcovr.com/> for the full manual."

    # Style guide for option help messages:
    # - Prefer complete sentences.
    # - Phrase first sentence as a command:
    #   “Print report”, not “Prints report”.
    # - Must be readable on the command line,
    #   AND parse as reStructured Text.

    options = parser.add_argument_group('Options')
    options.add_argument(
        "-h", "--help",
        help="Show this help message, then exit.",
        action="help"
    )
    options.add_argument(
        "--version",
        help="Print the version number, then exit.",
        action="store_true",
        dest="version",
        default=False
    )
    options.add_argument(
        "-v", "--verbose",
        help="Print progress messages. "
             "Please include this output in bug reports.",
        action="store_true",
        dest="verbose",
        default=False
    )
    options.add_argument(
        "-r", "--report-dir",
        help="The root directory of your gcovr report files. "
             "Defaults to '%(default)s', the current directory. "
             "File names are reported relative to this root. "
             "The --root is the default --filter.",
        action="store",
        dest="source_report_dir",
        default='.'
    )
    options.add_argument(
        "--since",
        help="The start commit in git repo",
        action="store",
        dest="since",
        default=None
    )
    options.add_argument(
        "--until",
        help="The end commit in git repo",
        action="store",
        dest="until",
        default=None
    )
    options.add_argument(
        "--prefix",
        help="The prefix of the gcovr file",
        action="store",
        dest="prefix",
        default=None
    )
    options.add_argument(
        "--missing_prefix",
        help="The missing prefix",
        action="store",
        dest="missing_prefix_dir",
        default="src/"
    )

    output_options = parser.add_argument_group(
        "Output Options",
        description="Dcovr prints a html report by default, "
    )
    output_options.add_argument(
        "-o", "--output",
        help="Print output to this filename. Defaults to stdout. ",
        action="store",
        dest="output",
        default=None
    )
    output_options.add_argument(
        "--html-absolute-paths",
        help="Use absolute paths to link the --html-details reports. "
             "Defaults to relative links.",
        action="store_false",
        dest="relative_anchors",
        default=True
    )
    output_options.add_argument(
        "-s", "--print-summary",
        help="Print a small report to stdout "
             "with line & branch percentage coverage. "
             "This is in addition to other reports. "
             "Default: %(default)s.",
        action="store_true",
        dest="print_summary",
        default=False
    )

    return parser


COPYRIGHT = (
    "Copyright 2013-2018 the gcovr authors\n"
    "Copyright 2013 Sandia Corporation\n"
    "Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation,\n"
    "the U.S. Government retains certain rights in this software."
)


def main(args=None):
    parser = create_argument_parser()
    options = parser.parse_args(args=args)

    logger = Logger(options.verbose)

    if options.version:
        logger.msg(
            "gcovr {version}\n"
            "\n"
            "{copyright}",
            version=__version__, copyright=COPYRIGHT)
        sys.exit(0)

    # check the following args: html-dir, since, until, output
    if options.output is not None:
        options.output = os.path.abspath(options.output)

    if options.since is None:
        logger.error("please input the 'since' commit")
        sys.exit(0)
    if options.until is None:
        logger.error("please input the 'until' commit")
        sys.exit(0)
    if options.source_report_dir is None:
        logger.error("please input the gcov report dir")
        sys.exit(0)
    if options.prefix is None:
        logger.error("please input the 'prefix' of gcovr report file")
        sys.exit(0)
    if options.missing_prefix_dir is None:
        logger.error("please input the gcovr root")
        sys.exit(0)
    logger.verbose_msg("checking: html report dir {html_dir}\n"
            "since commit {since_commit}\n"
            "until commit {until_commit}\n"
            "gcovr report prefix {gcovr_prefix}\n"
            "gcovr missing prefix {gcovr_missingg_prefx}\n",
            html_dir=options.source_report_dir,
            since_commit=options.since,
            until_commit=options.until,
            gcovr_prefix=options.prefix,
            gcovr_missingg_prefx=options.missing_prefix_dir)
    generate_delta_report(options)


if __name__ == '__main__':
    main()
