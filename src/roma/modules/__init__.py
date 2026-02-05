"""Freeman ROMA modules.

Freeman-specific ROMA module subclasses that inject personality via DSPy signatures.
"""

from src.roma.modules.freeman_atomizer import FreemanAtomizer
from src.roma.modules.freeman_planner import FreemanPlanner
from src.roma.modules.freeman_executor import FreemanExecutor
from src.roma.modules.freeman_aggregator import FreemanAggregator
from src.roma.modules.freeman_verifier import FreemanVerifier

__all__ = [
    "FreemanAtomizer",
    "FreemanPlanner",
    "FreemanExecutor",
    "FreemanAggregator",
    "FreemanVerifier",
]
