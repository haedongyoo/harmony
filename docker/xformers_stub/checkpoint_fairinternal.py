"""xformers.checkpoint_fairinternal stub."""
import torch.utils.checkpoint


def checkpoint(func, *args, **kwargs):
    return torch.utils.checkpoint.checkpoint(func, *args, use_reentrant=False)


def _get_default_policy(*args, **kwargs):
    return None
