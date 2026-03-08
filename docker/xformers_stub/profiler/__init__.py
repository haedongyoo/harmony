"""xformers.profiler stub."""


class _Profiler:
    _CURRENT_PROFILER = None

    def __enter__(self):
        _Profiler._CURRENT_PROFILER = self
        return self

    def __exit__(self, *args):
        _Profiler._CURRENT_PROFILER = None


class profiler:
    _Profiler = _Profiler

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass
