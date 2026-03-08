"""xformers.ops stub: CPU에서 torch scaled_dot_product_attention으로 fallback."""
import torch
import torch.nn.functional as F


class LowerTriangularMask:
    def __init__(self, *args, **kwargs):
        pass

    def materialize(self, shape, dtype=torch.float32, device="cpu"):
        seq_len = shape[-1]
        mask = torch.triu(torch.ones(seq_len, seq_len, device=device), diagonal=1).bool()
        return mask.masked_fill(mask, float('-inf')).to(dtype)


def memory_efficient_attention(query, key, value, attn_bias=None, scale=None, **kwargs):
    if scale is None:
        scale = query.shape[-1] ** -0.5
    return F.scaled_dot_product_attention(query, key, value, attn_mask=None, scale=scale)


def scaled_dot_product_attention(query, key, value, attn_bias=None, scale=None, **kwargs):
    return memory_efficient_attention(query, key, value, attn_bias=attn_bias, scale=scale)


def unbind(tensor, dim=0):
    return torch.unbind(tensor, dim=dim)


def fmha(*args, **kwargs):
    raise NotImplementedError("fmha not supported in CPU stub")
