"""Auto Doc package."""

from .formatter import DocumentFormatter
from .methodology import Methodology, load_methodology

__all__ = ["DocumentFormatter", "Methodology", "load_methodology"]

__version__ = "0.1.0"
