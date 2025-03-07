/*
 * SPDX-FileCopyrightText: Copyright (c) 2021-2023, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
 * SPDX-License-Identifier: Apache-2.0
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#pragma once

#include "morpheus/messages/multi.hpp"
#include "morpheus/objects/dev_mem_info.hpp"  // for DevMemInfo
#include "morpheus/objects/filter_source.hpp"

#include <boost/fiber/context.hpp>
#include <boost/fiber/future/future.hpp>
#include <mrc/node/rx_sink_base.hpp>
#include <mrc/node/rx_source_base.hpp>
#include <mrc/node/sink_properties.hpp>
#include <mrc/node/source_properties.hpp>
#include <mrc/segment/builder.hpp>
#include <mrc/segment/object.hpp>
#include <mrc/types.hpp>
#include <pymrc/node.hpp>
#include <rxcpp/rx.hpp>

#include <cstddef>  // for size_t
#include <map>
#include <memory>
#include <string>
#include <thread>
#include <vector>

namespace morpheus {
/****** Component public implementations *******************/
/****** FilterDetectionStage********************************/

/**
 * @addtogroup stages
 * @{
 * @file
 */

#pragma GCC visibility push(default)
/**
 * @brief FilterDetectionsStage is used to filter rows from a dataframe based on values in a tensor or dataframe column
 * using a specified criteria. Rows in the `meta` dataframe are excluded if their associated value in the datasource
 * indicated by `field_name` is less than or equal to `threshold`.
 *
 * This stage can operate in two different modes set by the `copy` argument.
 * When the `copy` argument is `true` (default), rows that meet the filter criteria are copied into a new dataframe.
 * When `false` sliced views are used instead.
 *
 * Setting `copy=true` should be used when the number of matching records is expected to be both high and in
 * non-adjacent rows. In this mode, the stage will generate only one output message for each incoming message,
 * regardless of the size of the input and the number of matching records. However this comes at the cost of needing to
 * allocate additional memory and perform the copy.
 * Note: In most other stages, messages emitted contain a reference to the original `MessageMeta` emitted into the
 * pipeline by the source stage. When using copy mode this won't be the case and could cause the original `MessageMeta`
 * to be deallocated after this stage.
 *
 * Setting `copy=false` should be used when either the number of matching records is expected to be very low or are
 * likely to be contained in adjacent rows. In this mode, slices of contiguous blocks of rows are emitted in multiple
 * output messages. Performing a slice is relatively low-cost, however for each incoming message the number of emitted
 * messages could be high (in the worst case scenario as high as half the number of records in the incoming message).
 * Depending on the downstream stages, this can cause performance issues, especially if those stages need to acquire
 * the Python GIL.
 */
class FilterDetectionsStage
  : public mrc::pymrc::PythonNode<std::shared_ptr<MultiMessage>, std::shared_ptr<MultiMessage>>
{
  public:
    using base_t = mrc::pymrc::PythonNode<std::shared_ptr<MultiMessage>, std::shared_ptr<MultiMessage>>;
    using typename base_t::sink_type_t;
    using typename base_t::source_type_t;
    using typename base_t::subscribe_fn_t;

    /**
     * @brief Construct a new Filter Detections Stage object
     *
     * @param threshold : Threshold to classify
     * @param copy : Whether or not to perform a copy default=true
     * @param filter_source : Indicate if the values used for filtering exist in either an output tensor
     * (`FilterSource::TENSOR`) or a column in a Dataframe (`FilterSource::DATAFRAME`).
     * @param field_name : Name of the tensor or Dataframe column to filter on default="probs"
     */
    FilterDetectionsStage(float threshold, bool copy, FilterSource filter_source, std::string field_name = "probs");

  private:
    subscribe_fn_t build_operator();
    DevMemInfo get_tensor_filter_source(const std::shared_ptr<morpheus::MultiMessage>& x);
    DevMemInfo get_column_filter_source(const std::shared_ptr<morpheus::MultiMessage>& x);

    float m_threshold;
    bool m_copy;
    FilterSource m_filter_source;
    std::string m_field_name;
    std::size_t m_num_class_labels;
    std::map<std::size_t, std::string> m_idx2label;
};

/****** FilterDetectionStageInterfaceProxy******************/
/**
 * @brief Interface proxy, used to insulate python bindings.
 */
struct FilterDetectionStageInterfaceProxy
{
    /**
     * @brief Create and initialize a FilterDetectionStage, and return the result
     *
     * @param builder : Pipeline context object reference
     * @param name : Name of a stage reference
     * @param threshold : Threshold to classify
     * @param copy : Whether or not to perform a copy default=true
     * @param filter_source : Indicate if the values used for filtering exist in either an output tensor
     * (`FilterSource::TENSOR`) or a column in a Dataframe (`FilterSource::DATAFRAME`).
     * @param field_name : Name of the tensor or Dataframe column to filter on default="probs"
     * @return std::shared_ptr<mrc::segment::Object<FilterDetectionsStage>>
     */
    static std::shared_ptr<mrc::segment::Object<FilterDetectionsStage>> init(mrc::segment::Builder& builder,
                                                                             const std::string& name,
                                                                             float threshold,
                                                                             bool copy,
                                                                             FilterSource filter_source,
                                                                             std::string field_name);
};

#pragma GCC visibility pop
/** @} */  // end of group
}  // namespace morpheus
