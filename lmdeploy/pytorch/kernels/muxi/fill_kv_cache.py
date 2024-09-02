from torch import Tensor
import dlinfer.ops as ext_ops

def fill_kv_cache(k_states: Tensor, v_states: Tensor, k_caches: Tensor,
                  v_caches: Tensor, q_start_loc: Tensor, q_seq_length: Tensor,
                  kv_seq_length: Tensor, max_q_seq_length: int,
                  block_offsets: Tensor, context=None):
    # x = 32 // k_caches.element_size()
    # k_caches shape: [block_num, kv_head_num, head_size // x, block_size, x]
    # v_caches shape: [block_num, kv_head_num, block_size, head_size]

    ext_ops.fill_kv_cache(
        k_states,
        v_states,
        k_caches,
        v_caches,
        context.kv_start_indices,
    )
    return
