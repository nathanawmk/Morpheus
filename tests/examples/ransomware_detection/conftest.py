# SPDX-FileCopyrightText: Copyright (c) 2023, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys

import pytest
import yaml

from _utils import TEST_DIRS
from _utils import import_or_skip

# pylint: disable=redefined-outer-name

SKIP_REASON = ("Tests for the ransomware_detection example require a number of packages not installed in the Morpheus "
               "development environment. See `examples/ransomware_detection/README.md` "
               "for details on installing these additional dependencies")


@pytest.fixture(autouse=True, scope='session')
def dask_distributed(fail_missing: bool):
    """
    All of the tests in this subdir requires dask.distributed
    """
    yield import_or_skip("dask.distributed", reason=SKIP_REASON, fail_missing=fail_missing)


@pytest.fixture(name="config")
def config_fixture(config):
    """
    The ransomware detection pipeline utilizes the FIL pipeline mode.
    """
    from morpheus.config import PipelineModes
    config.mode = PipelineModes.FIL
    yield config


@pytest.fixture(name="example_dir")
def example_dir_fixture():
    yield os.path.join(TEST_DIRS.examples_dir, 'ransomware_detection')


@pytest.fixture(name="conf_file")
def conf_file_fixture(example_dir):
    yield os.path.join(example_dir, 'config/ransomware_detection.yaml')


@pytest.fixture
def rwd_conf(conf_file):
    with open(conf_file, encoding='UTF-8') as fh:
        conf = yaml.safe_load(fh)

    yield conf


@pytest.fixture
def interested_plugins():
    yield ['ldrmodules', 'threadlist', 'envars', 'vadinfo', 'handles']


# Some of the code inside ransomware_detection performs imports in the form of:
#    from common....
# For this reason we need to ensure that the examples/ransomware_detection dir is in the sys.path first
# pylint: disable=unused-argument
@pytest.fixture(autouse=True)
@pytest.mark.usefixtures("request", "restore_sys_path", "reset_plugins")
def ransomware_detection_in_sys_path(example_dir):
    sys.path.append(example_dir)
