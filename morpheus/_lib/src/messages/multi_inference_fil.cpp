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

#include "morpheus/messages/multi_inference_fil.hpp"

#include "morpheus/messages/memory/tensor_memory.hpp"
#include "morpheus/messages/meta.hpp"
#include "morpheus/messages/multi.hpp"
#include "morpheus/messages/multi_inference.hpp"

#include <memory>
#include <utility>

namespace morpheus {
/****** Component public implementations *******************/
/****** MultiInferenceFILMessage****************************************/
MultiInferenceFILMessage::MultiInferenceFILMessage(std::shared_ptr<MessageMeta> meta,
                                                   TensorIndex mess_offset,
                                                   TensorIndex mess_count,
                                                   std::shared_ptr<TensorMemory> memory,
                                                   TensorIndex offset,
                                                   TensorIndex count,
                                                   std::string id_tensor_name) :
  DerivedMultiMessage(meta, mess_offset, mess_count, memory, offset, count, std::move(id_tensor_name))
{}

const TensorObject MultiInferenceFILMessage::get_input__0() const
{
    return this->get_input("input__0");
}

void MultiInferenceFILMessage::set_input__0(const TensorObject& input__0)
{
    this->set_input("input__0", input__0);
}

const TensorObject MultiInferenceFILMessage::get_seq_ids() const
{
    return this->get_input("seq_ids");
}

void MultiInferenceFILMessage::set_seq_ids(const TensorObject& seq_ids)
{
    this->set_input("seq_ids", seq_ids);
}

/****** MultiInferenceFILMessageInterfaceProxy *************************/
std::shared_ptr<MultiInferenceFILMessage> MultiInferenceFILMessageInterfaceProxy::init(
    std::shared_ptr<MessageMeta> meta,
    TensorIndex mess_offset,
    TensorIndex mess_count,
    std::shared_ptr<TensorMemory> memory,
    TensorIndex offset,
    TensorIndex count,
    std::string id_tensor_name)
{
    return std::make_shared<MultiInferenceFILMessage>(
        std::move(meta), mess_offset, mess_count, std::move(memory), offset, count, std::move(id_tensor_name));
}

pybind11::object MultiInferenceFILMessageInterfaceProxy::input__0(MultiInferenceFILMessage& self)
{
    return get_tensor_property(self, "input__0");
}

pybind11::object MultiInferenceFILMessageInterfaceProxy::seq_ids(MultiInferenceFILMessage& self)
{
    return get_tensor_property(self, "seq_ids");
}

}  // namespace morpheus
// Created by drobison on 3/17/22.
//
