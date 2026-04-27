from .io import open  # noqa E402
from importlib import metadata

__version__ = metadata.version(__package__)

__all__ = ["open", "__version__"]

del metadata
