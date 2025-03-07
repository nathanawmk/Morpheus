#!/usr/bin/env python
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

import mrc
import numpy as np
import pandas as pd
import pytest
from mrc.core import operators as ops

import cudf

from _utils import assert_results
from _utils.stages.conv_msg import ConvMsg
from morpheus.common import TypeId
from morpheus.common import typeid_to_numpy_str
from morpheus.messages import MessageMeta
from morpheus.messages import MultiMessage
from morpheus.messages import MultiResponseMessage
from morpheus.pipeline import LinearPipeline
from morpheus.pipeline.single_port_stage import SinglePortStage
from morpheus.stages.input.in_memory_source_stage import InMemorySourceStage
from morpheus.stages.output.compare_dataframe_stage import CompareDataFrameStage
from morpheus.stages.output.in_memory_sink_stage import InMemorySinkStage
from morpheus.stages.postprocess.add_scores_stage import AddScoresStage
from morpheus.stages.postprocess.serialize_stage import SerializeStage
from morpheus.stages.preprocess.deserialize_stage import DeserializeStage


class CheckPreAlloc(SinglePortStage):
    """
    Acts like add-class/add-scores in that it requests a preallocation, the node will assert that the preallocation
    occurred with the correct type.
    """

    def __init__(self, c, probs_type):
        super().__init__(c)
        self._expected_type = cudf.dtype(typeid_to_numpy_str(probs_type))
        self._class_labels = c.class_labels
        self._needed_columns.update({label: probs_type for label in c.class_labels})

    @property
    def name(self):
        return "check-prealloc"

    def accepted_types(self):
        return (MultiMessage, )

    def supports_cpp_node(self):
        return False

    def _check_prealloc(self, msg: MultiMessage):
        df = msg.get_meta()
        for label in self._class_labels:
            assert label in df.columns
            assert df[label].dtype == self._expected_type

        return msg

    def _build_single(self, builder: mrc.Builder, input_stream):
        stream = builder.make_node(self.unique_name, ops.map(self._check_prealloc))
        builder.make_edge(input_stream[0], stream)

        return stream, input_stream[1]


@pytest.mark.parametrize('probs_type', [TypeId.FLOAT32, TypeId.FLOAT64])
def test_preallocation(config, filter_probs_df, probs_type):
    config.class_labels = ['frogs', 'lizards', 'toads', 'turtles']
    probs_np_type = typeid_to_numpy_str(probs_type)
    expected_df = pd.DataFrame(
        data={c: np.zeros(len(filter_probs_df), dtype=probs_np_type)
              for c in config.class_labels})

    pipe = LinearPipeline(config)
    mem_src = pipe.set_source(InMemorySourceStage(config, [filter_probs_df]))
    pipe.add_stage(DeserializeStage(config))
    pipe.add_stage(ConvMsg(config, columns=list(filter_probs_df.columns), probs_type=probs_np_type))
    pipe.add_stage(CheckPreAlloc(config, probs_type=probs_type))
    pipe.add_stage(SerializeStage(config, include=[f"^{c}$" for c in config.class_labels]))
    comp_stage = pipe.add_stage(CompareDataFrameStage(config, expected_df))

    assert len(mem_src.get_needed_columns()) == 0

    pipe.run()

    assert mem_src.get_needed_columns() == {
        'frogs': probs_type, 'lizards': probs_type, 'toads': probs_type, 'turtles': probs_type
    }

    assert_results(comp_stage.get_results())


@pytest.mark.parametrize('probs_type', [TypeId.FLOAT32, TypeId.FLOAT64])
def test_preallocation_multi_segment_pipe(config, filter_probs_df, probs_type):
    """
    Test ensures that when columns are needed for preallocation in a multi-segment pipeline, the preallocagtion will
    always be performed on the closest source to the stage that requested preallocation. Which in cases where the
    requesting stage is not in the first segment, then the preallocation will be performed on the segment ingress
    """
    config.class_labels = ['frogs', 'lizards', 'toads', 'turtles']
    probs_np_type = typeid_to_numpy_str(probs_type)
    expected_df = pd.DataFrame(
        data={c: np.zeros(len(filter_probs_df), dtype=probs_np_type)
              for c in config.class_labels})

    pipe = LinearPipeline(config)
    mem_src = pipe.set_source(InMemorySourceStage(config, [filter_probs_df]))
    pipe.add_segment_boundary(MessageMeta)
    pipe.add_stage(DeserializeStage(config))
    pipe.add_segment_boundary(MultiMessage)
    pipe.add_stage(ConvMsg(config, columns=list(filter_probs_df.columns), probs_type=typeid_to_numpy_str(probs_type)))
    (_, boundary_ingress) = pipe.add_segment_boundary(MultiResponseMessage)
    pipe.add_stage(CheckPreAlloc(config, probs_type=probs_type))
    pipe.add_segment_boundary(MultiResponseMessage)
    pipe.add_stage(SerializeStage(config, include=[f"^{c}$" for c in config.class_labels]))
    pipe.add_segment_boundary(MessageMeta)
    comp_stage = pipe.add_stage(CompareDataFrameStage(config, expected_df))

    assert len(mem_src.get_needed_columns()) == 0

    pipe.run()

    assert len(mem_src.get_needed_columns()) == 0
    assert boundary_ingress.get_needed_columns() == {
        'frogs': probs_type, 'lizards': probs_type, 'toads': probs_type, 'turtles': probs_type
    }

    assert_results(comp_stage.get_results())


@pytest.mark.use_cpp
def test_preallocation_error(config, filter_probs_df):
    """
    Verify that we get a raised exception when add_scores attempts to use columns that don't exist
    """
    config.class_labels = ['frogs', 'lizards', 'toads', 'turtles']

    pipe = LinearPipeline(config)
    mem_src = pipe.set_source(InMemorySourceStage(config, [filter_probs_df]))
    pipe.add_stage(DeserializeStage(config))
    pipe.add_stage(ConvMsg(config, columns=list(filter_probs_df.columns), probs_type='f4'))
    add_scores = pipe.add_stage(AddScoresStage(config))
    pipe.add_stage(SerializeStage(config, include=[f"^{c}$" for c in config.class_labels]))
    mem_sink = pipe.add_stage(InMemorySinkStage(config))

    assert len(mem_src.get_needed_columns()) == 0
    assert len(add_scores.get_needed_columns()) > 0
    add_scores._needed_columns = {}
    assert len(add_scores.get_needed_columns()) == 0

    try:
        pipe.run()
    except Exception as e:
        assert isinstance(e, RuntimeError)

        # Ensure the error mentioned populating the needed_columns and using a stage with the PreallocatorMixin
        # Without depending on a specific string
        assert "frogs" in str(e)
        assert "PreallocatorMixin" in str(e)
        assert "needed_columns" in str(e)

    assert len(mem_src.get_needed_columns()) == 0
    assert len(mem_sink.get_messages()) == 0
