#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2019-2023, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

from __future__ import print_function

import argparse
import os
import re
import subprocess
import sys
import tempfile

MIN_VERSION = (12, 0, 0)
VERSION_REGEX = re.compile(r"clang-format version ([0-9.]+)")
# NOTE: populate this list with more top-level dirs as we add more of them
# to the rmm repo
DEFAULT_DIRS = ["src", "include", "tests", "benchmarks"]


def parse_clang_version(version_string):
    match = VERSION_REGEX.search(version_string)
    if match is None:
        raise Exception("Failed to figure out clang-format version!")
    version = match.group(1)
    return tuple(map(int, version.split('.')))


def parse_args():
    argparser = argparse.ArgumentParser("Runs clang-format on a project")
    argparser.add_argument(
        "-dstdir",
        type=str,
        default=None,
        help="Directory to store the temporary outputs of"
        " clang-format. If nothing is passed for this, then"
        " a temporary dir will be created using `mkdtemp`",
    )
    argparser.add_argument(
        "-exe",
        type=str,
        default="clang-format",
        help="Path to clang-format exe",
    )
    argparser.add_argument(
        "-inplace",
        default=False,
        action="store_true",
        help="Replace the source files itself.",
    )
    argparser.add_argument(
        "-regex",
        type=str,
        default=r"[.](cc|cpp|cu|cuh|h|hpp)$",
        help="Regex string to filter in sources",
    )
    argparser.add_argument(
        "-ignore",
        type=str,
        default=None,
        help="Regex used to ignore files from matched list",
    )
    argparser.add_argument(
        "-v",
        dest="verbose",
        action="store_true",
        help="Print verbose messages",
    )

    src_group = argparser.add_mutually_exclusive_group()
    src_group.add_argument(
        "-files",
        type=str,
        default=[],
        nargs="+",
        help="List of files to scan",
    )
    src_group.add_argument("dirs",
                           type=str,
                           default=[],
                           nargs="*",
                           help="List of dirs where to find sources (ignored if -files is set)")

    args = argparser.parse_args()
    args.regex_compiled = re.compile(args.regex)

    if args.ignore is not None:
        args.ignore_compiled = re.compile(args.ignore)
    else:
        args.ignore_compiled = None

    if args.dstdir is None:
        args.dstdir = tempfile.mkdtemp()

    ret = subprocess.check_output("%s --version" % args.exe, shell=True)
    ret = ret.decode("utf-8")
    version = parse_clang_version(ret)
    if version < MIN_VERSION:
        raise Exception("clang-format exe must be v%s found '%s'" % (MIN_VERSION, version))
    if len(args.dirs) == 0 and len(args.files) == 0:
        args.dirs = DEFAULT_DIRS
    return args


def list_all_src_files(file_regex, ignore_regex, srcfiles, srcdirs, dstdir, inplace):
    allFiles = []
    for srcfile in srcfiles:
        if re.search(file_regex, srcfile):
            if ignore_regex is not None and re.search(ignore_regex, srcfile):
                continue

            if inplace:
                dstfile = srcfile
            else:
                dstfile = os.path.join(dstdir, srcfile)

            allFiles.append((srcfile, dstfile))

    for srcdir in srcdirs:
        for root, dirs, files in os.walk(srcdir):
            for f in files:
                src = os.path.join(root, f)
                if re.search(file_regex, src):
                    if ignore_regex is not None and re.search(ignore_regex, src):
                        continue
                    if inplace:
                        _dir = root
                    else:
                        _dir = os.path.join(dstdir, root)
                    dst = os.path.join(_dir, f)
                    allFiles.append((src, dst))

    return allFiles


def run_clang_format(src, dst, exe, verbose):
    dstdir = os.path.dirname(dst)
    if not os.path.exists(dstdir):
        os.makedirs(dstdir)
    # run the clang format command itself
    if src == dst:
        cmd = "%s -i %s" % (exe, src)
    else:
        cmd = "%s %s > %s" % (exe, src, dst)
    try:
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError:
        print("Failed to run clang-format! Maybe your env is not proper?")
        raise
    # run the diff to check if there are any formatting issues
    cmd = "diff -q %s %s >/dev/null" % (src, dst)
    try:
        subprocess.check_call(cmd, shell=True)
        if verbose:
            print("%s passed" % os.path.basename(src))
    except subprocess.CalledProcessError:
        print("%s failed! 'diff %s %s' will show formatting violations!" % (os.path.basename(src), src, dst))
        return False
    return True


def main():
    args = parse_args()
    # Attempt to making sure that we run this script from root of repo always
    if not os.path.exists(".git"):
        print("Error!! This needs to always be run from the root of repo")
        sys.exit(-1)

    all_files = list_all_src_files(
        args.regex_compiled,
        args.ignore_compiled,
        args.files,
        args.dirs,
        args.dstdir,
        args.inplace,
    )

    # actual format checker
    status = True
    for src, dst in all_files:
        if not run_clang_format(src, dst, args.exe, args.verbose):
            status = False
    if not status:
        print("clang-format failed! You have 2 options:")
        print(" 1. Look at formatting differences above and fix them manually")
        print(" 2. Or run the below command to bulk-fix all these at once")
        print("Bulk-fix command: ")
        print("  python %s -inplace" % " ".join(sys.argv))
        sys.exit(-1)
    return


if __name__ == "__main__":
    main()
