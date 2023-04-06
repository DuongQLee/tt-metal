import torch
import json
import numpy as np
from libs import tt_lib as ttm
from utility_functions import pad_activation, pad_weight, tilize_to_list, untilize, nearest_32, print_diff_argmax, tt2torch, tt2torch_rm


def torch2tt_tensor(py_tensor: torch.Tensor, tt_device):
    size = list(py_tensor.size())

    while len(size) < 4:
        size.insert(0, 1)

    tt_tensor = ttm.tensor.Tensor(
        py_tensor.reshape(-1).tolist(),
        size,
        ttm.tensor.DataType.BFLOAT16,
        ttm.tensor.Layout.ROW_MAJOR,
    ).to(ttm.tensor.Layout.TILE).to(tt_device)

    return tt_tensor


def tt2torch_tensor(tt_tensor):
    host = ttm.device.GetHost()
    tt_output = tt_tensor.to(host).to(ttm.tensor.Layout.ROW_MAJOR)
    py_output = torch.Tensor(tt_output.data()).reshape(tt_output.shape())
    return py_output

def tt_const_tensor(value, shape, device):
    pytorch_const = torch.full(shape, value)
    tt_const = torch2tt_tensor(pytorch_const, device)
    return tt_const


def tt_load_layer_weights(layer_name, state_dict):
    print(torch.tensor(state_dict[layer_name]).shape)
    weights = tilize_to_list(pad_weight(state_dict[layer_name]))
    return weights

def pt_load_layer_weights(layer_name, state_dict):
    print(torch.tensor(state_dict[layer_name]).shape)
    weights = torch.nn.Parameter(torch.tensor(state_dict[layer_name]))
    return weights

def read_model_config(json_file):
    # read file
    with open(json_file, 'r') as myfile:
        data=myfile.read()

    # parse file
    obj = json.loads(data)
    return obj


def print_corr_coef(x, y):
    x = torch.reshape(x, (-1, ))
    y = torch.reshape(y, (-1, ))

    input = torch.stack((x, y))

    corrval = torch.corrcoef(input)
    print(f"Corr coef:")
    print(f"{corrval}")
