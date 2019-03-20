import pathlib


class Path(pathlib.Path):
    _flavour = pathlib._posix_flavour

    def __new__(cls, *args, **kwargs):
        if cls is pathlib.Path:
            cls = pathlib.PosixPath

        self = cls._from_parts(args, init=False)
        self._init()
        return self
