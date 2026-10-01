# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""FP32 and FP16 ONNX export with batch norm folded.

The FP32 model has a fixed input of 1 x 4 x 512 x 512 (the export input
size from the configuration) and a pinned opset. A second FP32 file has a
dynamic batch dimension. The FP16 file converts weights and activations to
float16 and keeps the Resize scales in float32, as ONNX requires.
"""

from __future__ import annotations

import hashlib
import tempfile
import warnings
from pathlib import Path

import onnx
import torch
from onnx import TensorProto, numpy_helper

from tiefer_lab.models.cloud_filter import IN_CHANNELS, CloudFilterNet, fold_batch_norm

INPUT_NAME = "reflectance"
OUTPUT_NAME = "logits"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def inline_constant_identities(model: onnx.ModelProto) -> onnx.ModelProto:
    """Replace Identity nodes that only alias an initialiser by a copy of it.

    The exporter de-duplicates identical initialisers this way; the copies
    leave a graph of compute operators only.
    """
    graph = model.graph
    initialisers = {init.name: init for init in graph.initializer}
    keep = []
    for node in graph.node:
        if node.op_type == "Identity" and len(node.input) == 1 and node.input[0] in initialisers:
            copy = onnx.TensorProto()
            copy.CopyFrom(initialisers[node.input[0]])
            copy.name = node.output[0]
            graph.initializer.append(copy)
        else:
            keep.append(node)
    del graph.node[:]
    graph.node.extend(keep)
    return model


def export_fp32(
    model: CloudFilterNet,
    path: Path,
    input_size: int,
    opset: int,
    dynamic_batch: bool = False,
) -> Path:
    """Export a batch-norm-folded copy of `model` to ONNX (FP32)."""
    folded = fold_batch_norm(model).cpu().float()
    dummy = torch.zeros(1, IN_CHANNELS, input_size, input_size)
    with tempfile.TemporaryDirectory() as tmp, warnings.catch_warnings():
        raw = Path(tmp) / "raw.onnx"
        # The TorchScript exporter is deprecated in recent PyTorch versions but
        # needs no extra dependency (docs/ASSUMPTIONS.md, section 5).
        warnings.simplefilter("ignore")
        torch.onnx.export(
            folded,
            (dummy,),
            raw,
            opset_version=opset,
            input_names=[INPUT_NAME],
            output_names=[OUTPUT_NAME],
            dynamic_axes={INPUT_NAME: {0: "batch"}, OUTPUT_NAME: {0: "batch"}}
            if dynamic_batch
            else None,
            do_constant_folding=True,
            dynamo=False,
        )
        proto = inline_constant_identities(onnx.load(raw))
    proto.doc_string = "Tiefer cloud filter, FP32, batch norm folded"
    onnx.checker.check_model(proto)
    path.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(proto, path)
    return path


def _resize_float_inputs(model: onnx.ModelProto) -> set[str]:
    """Names of the roi and scales inputs of Resize nodes, which stay float32."""
    names: set[str] = set()
    for node in model.graph.node:
        if node.op_type == "Resize":
            names.update(name for name in node.input[1:3] if name)
    return names


def convert_fp16(model: onnx.ModelProto) -> onnx.ModelProto:
    """Float32 weights, constants, inputs and outputs to float16, except Resize scales."""
    converted = onnx.ModelProto()
    converted.CopyFrom(model)
    graph = converted.graph
    keep = _resize_float_inputs(converted)
    for init in graph.initializer:
        if init.data_type == TensorProto.FLOAT and init.name not in keep:
            init.CopyFrom(
                numpy_helper.from_array(numpy_helper.to_array(init).astype("float16"), init.name)
            )
    for node in graph.node:
        if node.op_type != "Constant" or node.output[0] in keep:
            continue
        for attr in node.attribute:
            if attr.name == "value" and attr.t.data_type == TensorProto.FLOAT:
                tensor = numpy_helper.to_array(attr.t).astype("float16")
                attr.t.CopyFrom(numpy_helper.from_array(tensor))
    for value in list(graph.input) + list(graph.output):
        if value.type.tensor_type.elem_type == TensorProto.FLOAT:
            value.type.tensor_type.elem_type = TensorProto.FLOAT16
    del graph.value_info[:]
    converted.doc_string = "Tiefer cloud filter, FP16, batch norm folded"
    onnx.checker.check_model(converted)
    return converted


def export_fp16(fp32_path: Path, path: Path) -> Path:
    onnx.save(convert_fp16(onnx.load(fp32_path)), path)
    return path


def operator_types(path: Path) -> list[str]:
    return sorted({node.op_type for node in onnx.load(path).graph.node})
