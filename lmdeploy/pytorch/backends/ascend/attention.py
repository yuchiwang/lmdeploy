# Copyright (c) OpenMMLab. All rights reserved.
from typing import Optional, Sequence
from dataclasses import dataclass

from torch import Tensor

from ..attention import AttentionBuilder, AttentionImpl, AttentionMetadata


@dataclass
class AscendAttentionMetadata(AttentionMetadata):
    kv_start_indices: Optional[Tensor] = None
    attention_mask: Sequence[Tensor] = tuple()
    unpaged_prefill_flag: Optional[Tensor] = None


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

        block_offsets = attn_metadata.block_offsets
        q_start_loc = attn_metadata.q_start_loc
        q_seqlens = attn_metadata.q_seqlens
        kv_seqlens = attn_metadata.kv_seqlens
        kv_start_indices = attn_metadata.kv_start_indices
        is_decoding = attn_metadata.is_decoding
        attn_mask = attn_metadata.attention_mask
        unpaged_prefill_flag = attn_metadata.unpaged_prefill_flag

        # fill kv cache
        self.fill_kv_cache(
            key,
            value,
            k_cache,
            v_cache,
            kv_start_indices
        )

        if inplace:
            attn_output = query[..., :self.v_head_size]
        else:
            q_shape = query.shape
            o_shape = q_shape[:-1] + (self.v_head_size, )
            attn_output = query.new_empty(o_shape)

        self.paged_attention_fwd(
            query,
            key,
            value,
            attn_output,
            k_cache,
            v_cache,
            block_offsets,
            q_start_loc=q_start_loc,
            q_seqlens=q_seqlens,
            kv_seqlens=kv_seqlens,
            is_decoding=is_decoding,
            attn_mask=attn_mask,
            unpaged_prefill_flag=unpaged_prefill_flag,
        )

        return attn_output


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
