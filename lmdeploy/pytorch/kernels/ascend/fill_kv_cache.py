# Copyright (c) OpenMMLab. All rights reserved.
import infer_ext.ops as ext_ops
from torch import Tensor


def fill_kv_cache(
    key_states: Tensor,
    value_states: Tensor,
    key_caches: Tensor,
    value_caches: Tensor,
    kv_start_indices: Tensor,
):
    """fill key/value state to cache for paged attention."""
    ext_ops.fill_kv_cache(key_states, value_states,
                          key_caches, value_caches,
                          kv_start_indices)
