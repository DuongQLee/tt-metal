from pathlib import Path
import sys
import torch
import pytest
from loguru import logger

f = f"{Path(__file__).parent}"
sys.path.append(f"{f}/../../../..")

from python_api_testing.models.utility_functions_new import (
    tt_to_torch_tensor,
    torch_to_tt_tensor_rm,
    comp_allclose,
    comp_pcc,
)
import tt_lib
from python_api_testing.models.swin.tt.swin_self_output import (
    TtSwinSelfOutput,
)
from transformers import SwinModel


@pytest.mark.parametrize(
    "pcc",
    ((0.99),),
)
def test_swin_self_output_inference(pcc, reset_seeds):
    device = tt_lib.device.CreateDevice(tt_lib.device.Arch.GRAYSKULL, 0)
    tt_lib.device.InitializeDevice(device)
    tt_lib.device.SetDefaultDevice(device)
    host = tt_lib.device.GetHost()

    SELF_OUTPUT_LAYER_INDEX = 0
    base_address = f"encoder.layers.{SELF_OUTPUT_LAYER_INDEX}.blocks.{SELF_OUTPUT_LAYER_INDEX}.attention.output"

    model = SwinModel.from_pretrained("microsoft/swin-tiny-patch4-window7-224")

    # Torch swinselfoutput
    torch_model = (
        model.encoder.layers[SELF_OUTPUT_LAYER_INDEX]
        .blocks[SELF_OUTPUT_LAYER_INDEX]
        .attention.output
    )

    # Tt swinselfoutput
    dim = 96
    tt_model = TtSwinSelfOutput(
        config=model.config,
        dim=dim,
        state_dict=model.state_dict(),
        base_address=base_address,
        device=device,
        host=host,
    )

    # Run torch model
    hidden_states = torch.rand(64, 49, 96)
    input_tensor = torch.ones(64, 49, 96)

    torch_output = torch_model(hidden_states, input_tensor)

    # Run tt model
    hidden_states = torch.unsqueeze(hidden_states, 0)
    tt_hidden_states = torch_to_tt_tensor_rm(hidden_states, device)

    input_tensor = torch.unsqueeze(input_tensor, 0)
    tt_input_tensor = torch_to_tt_tensor_rm(input_tensor, device)

    tt_output = tt_model(tt_hidden_states, tt_input_tensor)

    # Compare outputs
    tt_output_torch = tt_to_torch_tensor(tt_output, host)
    tt_output_torch = tt_output_torch.squeeze(0)

    does_pass, pcc_message = comp_pcc(torch_output, tt_output_torch, pcc)

    logger.info(comp_allclose(torch_output, tt_output_torch))
    logger.info(pcc_message)

    tt_lib.device.CloseDevice(device)
    if does_pass:
        logger.info("SwinSelfOutput Passed!")
    else:
        logger.warning("SwinSelfOutput Failed!")

    assert does_pass
