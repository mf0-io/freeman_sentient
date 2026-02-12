"""Freeman-specific Atomizer module.

Subclasses the base ROMA Atomizer with Freeman's personality signature.
The only override is DEFAULT_SIGNATURE — all logic is inherited from BaseModule.
"""

from roma_dspy.core.modules import Atomizer

from src.roma.modules.signatures import FreemanAtomizerSignature, FREEMAN_MISSION


class FreemanAtomizer(Atomizer):
    """Freeman-specialized task atomizer.

    Evaluates task complexity through Freeman's consciousness/freedom lens.
    """

    DEFAULT_SIGNATURE = FreemanAtomizerSignature
    MISSION = FREEMAN_MISSION
