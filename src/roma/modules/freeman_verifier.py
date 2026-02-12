"""Freeman-specific Verifier module.

Subclasses the base ROMA Verifier with Freeman's personality signature.
The only override is DEFAULT_SIGNATURE — all logic is inherited from BaseModule.
"""

from roma_dspy.core.modules import Verifier

from src.roma.modules.signatures import FreemanVerifierSignature


class FreemanVerifier(Verifier):
    """Freeman-specialized output verifier.

    Validates outputs against Freeman's quality criteria: mission-aligned,
    provocative, not conformist, philosophically grounded, voice-authentic.
    """

    DEFAULT_SIGNATURE = FreemanVerifierSignature
