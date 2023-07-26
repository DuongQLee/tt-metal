from pathlib import Path
import sys

f = f"{Path(__file__).parent}"
sys.path.append(f"{f}")
sys.path.append(f"{f}/..")
sys.path.append(f"{f}/../..")
sys.path.append(f"{f}/../../..")
sys.path.append(f"{f}/../../../..")

from transformers import AutoImageProcessor, ViTForImageClassification
import torch
from datasets import load_dataset
from loguru import logger
import pytest

import tt_lib
from models.utility_functions import torch_to_tt_tensor_rm, tt_to_torch_tensor
from tests.python_api_testing.models.utility_functions_new import Profiler
from models.utility_functions import disable_persistent_kernel_cache, enable_persistent_kernel_cache
from tests.python_api_testing.models.utility_functions_new import prep_report
from models.vit.tt.modeling_vit import vit_for_image_classification

BATCH_SIZE = 1

@pytest.mark.parametrize(
    "expected_inference_time, expected_compile_time",
    (
        (3.8,
        13.0,
        ),
    ),
)
def test_perf(use_program_cache, expected_inference_time, expected_compile_time):
    profiler = Profiler()
    disable_persistent_kernel_cache()
    first_key = "first_iter"
    second_key = "second_iter"
    cpu_key = "ref_key"

    dataset = load_dataset("huggingface/cats-image")
    image = dataset["test"]["image"][0]

    # Initialize the device
    device = tt_lib.device.CreateDevice(tt_lib.device.Arch.GRAYSKULL, 0)
    tt_lib.device.InitializeDevice(device)
    tt_lib.device.SetDefaultDevice(device)
    host = tt_lib.device.GetHost()

    image_processor = AutoImageProcessor.from_pretrained("google/vit-base-patch16-224")
    HF_model = ViTForImageClassification.from_pretrained(
        "google/vit-base-patch16-224"
    )  # loaded for the labels
    inputs = image_processor(image, return_tensors="pt")

    tt_inputs = torch_to_tt_tensor_rm(
        inputs["pixel_values"], device, put_on_device=False
    )
    tt_model = vit_for_image_classification(device)

    with torch.no_grad():
        profiler.start(cpu_key)
        logits = HF_model(**inputs).logits
        tt_lib.device.Synchronize()
        profiler.end(cpu_key)

        profiler.start(first_key)
        tt_output = tt_model(tt_inputs)[0]
        profiler.end(first_key)

        enable_persistent_kernel_cache()

        profiler.start(second_key)
        tt_output = tt_model(tt_inputs)[0]
        tt_lib.device.Synchronize()
        profiler.end(second_key)

    first_iter_time = profiler.get(first_key)
    second_iter_time = profiler.get(second_key)
    cpu_time = profiler.get(cpu_key)
    tt_lib.device.CloseDevice(device)
    prep_report(
        "vit", BATCH_SIZE, first_iter_time, second_iter_time, "base-patch16", cpu_time
    )
    compile_time = first_iter_time - second_iter_time
    logger.info(f"vit inference time: {second_iter_time}")
    logger.info(f"vit compile time: {compile_time}")
    assert second_iter_time < expected_inference_time, "vit is too slow"
    assert compile_time < expected_compile_time, "vit compile time is too slow"
