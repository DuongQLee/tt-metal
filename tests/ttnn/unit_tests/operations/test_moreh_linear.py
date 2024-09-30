# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.

# SPDX-License-Identifier: Apache-2.0

import pytest
import torch
import ttnn
from models.utility_functions import comp_allclose_and_pcc
from tests.ttnn.unit_tests.operations.test_moreh_matmul import get_tensors
from loguru import logger
from tests.ttnn.unit_tests.operations.test_utils import (
    get_compute_kernel_options,
    compute_kernel_options,
    compute_kernel_ids,
)


# TODO: add this feature in get_tensors method
def get_bias_tensors(bias_shape, require_bias_grad, device):
    npu_dtype = ttnn.bfloat16
    cpu_dtype = torch.bfloat16
    npu_layout = ttnn.TILE_LAYOUT
    cpu_layout = ttnn.ROW_MAJOR_LAYOUT

    bias = torch.randint(-10, 10, bias_shape, dtype=cpu_dtype)
    tt_bias = ttnn.Tensor(bias, npu_dtype).pad_to_tile(float("nan")).to(npu_layout).to(device)

    tt_bias_grad = None
    if require_bias_grad:
        bias_grad = torch.full(bias_shape, float("nan"), dtype=cpu_dtype)
        tt_bias_grad = ttnn.Tensor(bias_grad, npu_dtype).pad_to_tile(float("nan")).to(npu_layout).to(device)

    return tt_bias, bias, tt_bias_grad


def moreh_linear(shapes, has_bias, has_output, compute_kernel_config, device):
    torch.manual_seed(3072)
    input_shape, weight_shape, bias_shape, output_shape = shapes
    tt_input, tt_weight, _, _, _, _, torch_input, torch_weight, _ = get_tensors(
        input_shape, weight_shape, output_shape, False, False, False, device
    )

    npu_dtype = ttnn.bfloat16
    npu_layout = ttnn.TILE_LAYOUT
    cpu_dtype = torch.bfloat16
    torch_output = torch.randint(-2, 3, output_shape, dtype=cpu_dtype)
    tt_output = ttnn.Tensor(torch_output, npu_dtype).pad_to_tile(1).to(npu_layout).to(device) if has_output else None

    if has_bias:
        tt_bias, torch_bias, _ = get_bias_tensors(bias_shape, False, device)
    else:
        tt_bias, torch_bias = None, None

    ## TT Op
    tt_output = ttnn.operations.moreh.linear(
        tt_input, tt_weight, bias=tt_bias, output=tt_output, compute_kernel_config=compute_kernel_config
    )

    ## reference
    torch_output = torch.nn.functional.linear(torch_input, torch_weight, torch_bias)

    ## test for equivalance
    rtol = atol = 0.1
    cpu_layout = ttnn.ROW_MAJOR_LAYOUT
    ttcpu_output = tt_output.cpu().to(cpu_layout).unpad_from_tile(output_shape).to_torch()
    passing, output_pcc = comp_allclose_and_pcc(torch_output, ttcpu_output, pcc=0.999, rtol=rtol, atol=atol)
    logger.debug(f"Passing = {passing}")
    logger.debug(f"Output PCC = {output_pcc}")
    return passing


@pytest.mark.parametrize(
    "shapes",
    (
        # input, weight, bias(1d or scalar), output
        ([31, 31], [30, 31], [1, 30], [31, 30]),
        ([31, 31], [30, 31], [1, 1], [31, 30]),
        ([4, 4, 2, 31], [30, 31], [1, 30], [4, 4, 2, 30]),
        ([4, 4, 2, 31], [30, 31], [1, 1], [4, 4, 2, 30]),
        ([2, 2047], [1023, 2047], [1, 1023], [2, 1023]),
        ([2, 2047], [1023, 2047], [1, 1], [2, 1023]),
        ([32, 64], [1024, 64], [1, 1024], [32, 1024]),
        ([32, 64], [1024, 64], [1, 1], [32, 1024]),
        ([3, 32, 1023], [2047, 1023], [1, 2047], [3, 32, 2047]),
        ([3, 32, 1023], [2047, 1023], [1, 1], [3, 32, 2047]),
        ([2, 4, 4, 1024], [2047, 1024], [1, 2047], [2, 4, 4, 2047]),
        ([2, 4, 4, 1024], [2047, 1024], [1, 1], [2, 4, 4, 2047]),
        ([2, 1, 2, 3, 2, 2, 96, 95], [511, 95], [1, 1], [2, 1, 2, 3, 2, 2, 96, 511]),
        ([2, 1, 2, 3, 2, 2, 96, 95], [511, 95], [1, 511], [2, 1, 2, 3, 2, 2, 96, 511]),
    ),
)
@pytest.mark.parametrize("has_bias", [False, True])
@pytest.mark.parametrize("compute_kernel_options", compute_kernel_options, ids=compute_kernel_ids)
def test_moreh_linear(shapes, has_bias, compute_kernel_options, device):
    # TODO: Duong Remove skiptest until PR https://github.com/tenstorrent/tt-metal/pull/12794
    # is merged and apply fix from duong/fix_moreh_linear_fp32_dest_acc.
    if has_bias and compute_kernel_options:
        pytest.skip()
    torch.manual_seed(3072)
    compute_kernel_config = get_compute_kernel_options(compute_kernel_options)
    passing = moreh_linear(shapes, has_bias, True, compute_kernel_config, device)
    assert passing


@pytest.mark.parametrize(
    "shapes",
    (
        # input, weight, bias(1d or scalar), output
        ([31, 31], [30, 31], [1, 30], [31, 30]),
        ([2, 1, 2, 3, 2, 2, 96, 95], [511, 95], [1, 1], [2, 1, 2, 3, 2, 2, 96, 511]),
    ),
)
@pytest.mark.parametrize("has_bias", [False, True])
def test_moreh_linear_wo_output(shapes, has_bias, device):
    torch.manual_seed(3072)
    compute_kernel_config = get_compute_kernel_options(False)
    passing = moreh_linear(shapes, has_bias, False, compute_kernel_config, device)
    assert passing


@pytest.mark.parametrize(
    "shapes",
    (
        # input, weight, bias(1d or scalar), output
        ([31, 31], [30, 31], [1, 1], [31, 30]),
        ([2, 1, 2, 3, 2, 2, 96, 95], [511, 95], [1, 511], [2, 1, 2, 3, 2, 2, 96, 511]),
    ),
)
def test_moreh_linear_enable_cache(shapes, device, use_program_cache):
    torch.manual_seed(3072)
    compute_kernel_config = get_compute_kernel_options(False)
    for i in range(2):
        passing = moreh_linear(shapes, True, True, compute_kernel_config, device)
        assert passing

    assert device.num_program_cache_entries() == 1


def moreh_linear_backward(
    shapes, requires_input_grad, requires_weight_grad, requires_bias_grad, compute_kernel_config, device
):
    input_shape, weight_shape, bias_shape, output_shape = shapes
    if not requires_input_grad and not requires_weight_grad and not requires_bias_grad:
        pytest.skip("At least one grad is requires")

    (
        tt_input,
        tt_weight,
        _,
        tt_output_grad,
        tt_input_grad,
        tt_weight_grad,
        torch_input,
        torch_weight,
        torch_output_grad,
    ) = get_tensors(input_shape, weight_shape, output_shape, requires_input_grad, requires_weight_grad, False, device)

    tt_bias, torch_bias, tt_bias_grad = get_bias_tensors(bias_shape, requires_bias_grad, device)

    ## tt linear backward
    tt_input_grad, tt_weight_grad, tt_bias_grad = ttnn.operations.moreh.linear_backward(
        tt_output_grad,
        tt_input,
        tt_weight,
        are_required_outputs=(requires_input_grad, requires_weight_grad, requires_bias_grad),
        bias=tt_bias,
        input_grad=tt_input_grad,
        weight_grad=tt_weight_grad,
        bias_grad=tt_bias_grad,
        compute_kernel_config=compute_kernel_config,
    )
    ## reference
    torch_output = torch.nn.functional.linear(
        torch_input.requires_grad_(requires_input_grad),
        torch_weight.requires_grad_(requires_weight_grad),
        torch_bias.requires_grad_(requires_bias_grad),
    )
    torch_output.backward(torch_output_grad)

    ## test for equivalance
    rtol = atol = 0.1
    cpu_layout = ttnn.ROW_MAJOR_LAYOUT
    if requires_input_grad:
        ttcpu_input_grad = tt_input_grad.cpu().to(cpu_layout).unpad_from_tile(input_shape).to_torch()
        passing, output_pcc = comp_allclose_and_pcc(torch_input.grad, ttcpu_input_grad, pcc=0.999, rtol=rtol, atol=atol)
        logger.debug(f"input_grad passing={passing} pcc={output_pcc}")
        assert passing
    else:
        assert tt_input_grad is None

    if requires_weight_grad:
        ttcpu_weight_grad = tt_weight_grad.cpu().to(cpu_layout).unpad_from_tile(weight_shape).to_torch()
        passing, output_pcc = comp_allclose_and_pcc(
            torch_weight.grad, ttcpu_weight_grad, pcc=0.999, rtol=rtol, atol=atol
        )
        logger.debug(f"weight_grad passing={passing} pcc={output_pcc}")
        assert passing
    else:
        assert tt_weight_grad is None

    if requires_bias_grad:
        ttcpu_bias_grad = tt_bias_grad.cpu().to(cpu_layout).unpad_from_tile(bias_shape).to_torch()
        passing, output_pcc = comp_allclose_and_pcc(torch_bias.grad, ttcpu_bias_grad, pcc=0.999, rtol=rtol, atol=atol)
        logger.debug(f"bias_grad passing={passing} pcc={output_pcc}")
        assert passing
    else:
        assert tt_bias_grad is None
    return passing


@pytest.mark.parametrize(
    "shapes",
    (
        # input, weight, bias(1d or scalar), output
        ([31, 31], [30, 31], [1, 30], [31, 30]),
        ([31, 31], [30, 31], [1, 1], [31, 30]),
        ([4, 4, 2, 31], [30, 31], [1, 30], [4, 4, 2, 30]),
        ([4, 4, 2, 31], [30, 31], [1, 1], [4, 4, 2, 30]),
        ([2, 2047], [1023, 2047], [1, 1023], [2, 1023]),
        ([2, 2047], [1023, 2047], [1, 1], [2, 1023]),
        ([32, 64], [1024, 64], [1, 1024], [32, 1024]),
        ([32, 64], [1024, 64], [1, 1], [32, 1024]),
        ([3, 32, 1023], [1536, 1023], [1, 1536], [3, 32, 1536]),
        ([3, 32, 1023], [1536, 1023], [1, 1], [3, 32, 1536]),
        ([2, 4, 4, 1024], [1536, 1024], [1, 1536], [2, 4, 4, 1536]),
        ([2, 4, 4, 1024], [1200, 1024], [1, 1], [2, 4, 4, 1200]),
        ([2, 1, 2, 1, 2, 2, 96, 95], [127, 95], [1, 1], [2, 1, 2, 1, 2, 2, 96, 127]),
        ([2, 1, 2, 3, 2, 2, 96, 95], [127, 95], [1, 127], [2, 1, 2, 3, 2, 2, 96, 127]),
    ),
)
@pytest.mark.parametrize(
    "requires_grads",
    (
        (True, False),
        (False, True),
        (True, True),
    ),
)
@pytest.mark.parametrize("requires_bias_grad", [True, False])
@pytest.mark.parametrize("compute_kernel_options", compute_kernel_options, ids=compute_kernel_ids)
def test_moreh_linear_backward(shapes, requires_grads, requires_bias_grad, compute_kernel_options, device):
    torch.manual_seed(3072)
    requires_input_grad, requires_weight_grad = requires_grads
    compute_kernel_config = get_compute_kernel_options(compute_kernel_options)
    passing = moreh_linear_backward(
        shapes, requires_input_grad, requires_weight_grad, requires_bias_grad, compute_kernel_config, device
    )
    assert passing


@pytest.mark.parametrize(
    "shapes",
    (
        # input, weight, bias(1d or scalar), output
        ([31, 31], [30, 31], [1, 30], [31, 30]),
        ([31, 31], [30, 31], [1, 1], [31, 30]),
        ([2, 4, 4, 1024], [1536, 1024], [1, 1536], [2, 4, 4, 1536]),
        ([32, 1023], [1536, 1023], [1, 1], [32, 1536]),
    ),
)
def test_moreh_linear_backward_enable_cache(shapes, device, use_program_cache):
    torch.manual_seed(3072)
    requires_input_grad, requires_weight_grad, requires_bias_grad = (True, True, True)
    compute_kernel_config = get_compute_kernel_options(False)
    num_program_cache_entries_list = []

    for i in range(2):
        passing = moreh_linear_backward(
            shapes, requires_input_grad, requires_weight_grad, requires_bias_grad, compute_kernel_config, device
        )
        num_program_cache_entries_list.append(device.num_program_cache_entries())
        assert passing
    assert len(set(num_program_cache_entries_list)) == 1
