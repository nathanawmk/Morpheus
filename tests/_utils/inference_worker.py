# SPDX-FileCopyrightText: Copyright (c) 2022-2023, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

import typing

from morpheus.messages import MultiInferenceMessage
from morpheus.messages.memory.tensor_memory import TensorMemory
from morpheus.stages.inference import inference_stage


class IW(inference_stage.InferenceWorker):
    """
    Concrete impl class of `InferenceWorker` for the purposes of testing
    """

    def calc_output_dims(self, _):
        # Intentionally calling the abc empty method for coverage
        super().calc_output_dims(_)
        return (1, 2)

    def process(self, _: MultiInferenceMessage, __: typing.Callable[[TensorMemory], None]):
        raise NotImplementedError
