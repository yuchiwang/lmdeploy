# Copyright (c) OpenMMLab. All rights reserved.
import infer_ext.ops as ext_ops
from torch import Tensor

def rms_norm(hidden_states: Tensor, weight: Tensor, epsilon: float = 1e-6, out: Tensor = None):
    print(f"[rms_norm, input]: {hidden_states[0, 0, 0:100:10].cpu()}  {hidden_states.abs().mean().cpu()}")
    # hidden_states [total_seq_len, hidden_size]
    # weight [hidden_size]
    #return hidden_states
    #print("hs:",hidden_states.shape)
    #print("weight:",weight.shape)
    #if hidden_states.shape[0]== 1 and hidden_states.ndim == 3:
    #    hidden_states = hidden_states.view(hidden_states.shape[1],hidden_states.shape[2])
    output = ext_ops.rms_norm(hidden_states, weight, epsilon)
    if out is None:
        out = output
    else:
        out.copy_(output)
    print(f"[rms_norm, output]: {output[0, 0, 0:100:10].cpu()}  {output.abs().mean().cpu()}")
    return out
