from importlib import metadata

from .io import open

__version__ = metadata.version(__package__)

__all__ = ["open", "__version__"]

del metadata
