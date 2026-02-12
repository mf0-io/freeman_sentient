"""Freeman-specific Aggregator module.

Subclasses the base ROMA Aggregator with Freeman's personality signature.
The only override is DEFAULT_SIGNATURE — all logic is inherited from BaseModule.
"""

from roma_dspy.core.modules import Aggregator

from src.roma.modules.signatures import FreemanAggregatorSignature


class FreemanAggregator(Aggregator):
    """Freeman-specialized result aggregator.

    Synthesizes subtask results into a unified output maintaining Freeman's
    mission coherence and escalating intensity.
    """

    DEFAULT_SIGNATURE = FreemanAggregatorSignature
