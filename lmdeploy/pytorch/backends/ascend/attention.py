# Copyright (c) OpenMMLab. All rights reserved.
from typing import Optional, Sequence
from dataclasses import dataclass

from torch import Tensor, IntTensor

from ..attention import AttentionBuilder, AttentionImpl, AttentionMetadata

import torch

@dataclass
class AscendAttentionMetadata(AttentionMetadata):
    kv_start_indices: Optional[Tensor] = None
    block_size: int = 64
    attention_mask: Sequence[Tensor] = tuple()
    is_unpaged_prefill: Optional[bool] = None
    q_seqlens_int: IntTensor = None
    kv_seqlens_int: IntTensor = None
    kv_start_indices_1d: IntTensor = None
    block_offsets_int: IntTensor = None
    block_offsets_1d_int: IntTensor = None

class AscendAttentionImpl(AttentionImpl[AscendAttentionMetadata]):
    """ascend attention implementation."""

    def __init__(
        self,
        num_heads: int,
        head_size: int,
        scale: float = None,
        num_kv_heads: int = None,
        v_head_size: int = None,
        alibi_scale: float = None,
        sliding_window: int = None,
        logical_softcapping: float = None,
        **kwargs,
    ):
        super().__init__(
            num_heads,
            head_size,
            scale,
            num_kv_heads,
            v_head_size,
            alibi_scale,
            sliding_window,
            **kwargs,
        )

        from lmdeploy.pytorch.kernels.ascend import (fill_kv_cache,
                                                     paged_attention_fwd)
        self.fill_kv_cache = fill_kv_cache
        self.paged_attention_fwd = paged_attention_fwd
        self.block_size = 64

    def forward(
        self,
        query: Tensor,
        key: Tensor,
        value: Tensor,
        k_cache: Tensor,
        v_cache: Tensor,
        attn_metadata: AscendAttentionMetadata,
        inplace: bool = True,
    ) -> Tensor:
        """forward."""

        # block_offsets = attn_metadata.block_offsets
        # q_start_loc = attn_metadata.q_start_loc
        # q_seqlens = attn_metadata.q_seqlens
        # kv_seqlens = attn_metadata.kv_seqlens
        is_decoding = attn_metadata.is_decoding
        # kv_start_indices = attn_metadata.kv_start_indices
        # block_size = attn_metadata.block_size
        # attn_mask = attn_metadata.attention_mask
        # is_unpaged_prefill = attn_metadata.is_unpaged_prefill

        
        k_cache = k_cache.view(-1, self.block_size, self.num_kv_heads, self.v_head_size)
        v_cache = v_cache.view(-1, self.block_size, self.num_kv_heads, self.v_head_size)
        
        k_cache, v_cache = torch.ops.atb.fill_kv_cache(key, value, k_cache, v_cache, attn_metadata.kv_start_indices_1d)
        
        # k_cache = k_cache.view(-1, self.num_kv_heads * self.v_head_size)
        # v_cache = v_cache.view(-1, self.num_kv_heads * self.v_head_size)

        if is_decoding:
            block_offsets = attn_metadata.block_offsets_int
            attn_output = torch.ops.atb.paged_attention_decode(query, k_cache, v_cache, block_offsets, attn_metadata.kv_seqlens_int, None)
        else:
            attn_output = torch.ops.atb.context_attention(query, key, value, attn_metadata.kv_seqlens_int, None)
        return attn_output
        

        # # fill kv cache
        # k_cache, v_cache = self.fill_kv_cache(
        #     key,
        #     value,
        #     k_cache,
        #     v_cache,
        #     kv_start_indices
        # )
        
        # if inplace:
        #     attn_output = query[..., :self.v_head_size]
        # else:
        #     q_shape = query.shape
        #     o_shape = q_shape[:-1] + (self.v_head_size, )
        #     attn_output = query.new_empty(o_shape)

        # # import pdb;pdb.set_trace()
        # attn_output = self.paged_attention_fwd(
        #     query,
        #     key,
        #     value,
        #     attn_output,
        #     k_cache, 
        #     v_cache,
        #     block_offsets,
        #     q_start_loc=q_start_loc,
        #     q_seqlens=q_seqlens,
        #     kv_seqlens=kv_seqlens,
        #     is_decoding=is_decoding,
        #     block_size=block_size,
        #     attn_mask=attn_mask,
        #     is_unpaged_prefill=is_unpaged_prefill,
        # )

        # return attn_output


class AscendAttentionBuilder(AttentionBuilder[AscendAttentionMetadata]):
    """ascend attention builder."""

    @staticmethod
    def build(
        num_heads: int,
        head_size: int,
        scale: float = None,
        num_kv_heads: int = None,
        v_head_size: int = None,
        alibi_scale: float = None,
        sliding_window: int = None,
        logical_softcapping: float = None,
        **kwargs,
    ) -> AscendAttentionImpl:
        """build."""
        return AscendAttentionImpl(num_heads,
                                   head_size,
                                   scale=scale,
                                   num_kv_heads=num_kv_heads,
                                   v_head_size=v_head_size,
                                   alibi_scale=alibi_scale,
                                   sliding_window=sliding_window,
                                   logical_softcapping=logical_softcapping,
                                   **kwargs)
