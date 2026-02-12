"""Freeman-specific Executor module.

Subclasses the base ROMA Executor with Freeman's personality signature.
The only override is DEFAULT_SIGNATURE — all logic is inherited from BaseModule.
"""

from roma_dspy.core.modules import Executor

from src.roma.modules.signatures import FreemanExecutorSignature


class FreemanExecutor(Executor):
    """Freeman-specialized task executor.

    Executes tasks with Freeman's characteristic voice: sarcastic, provocative,
    philosophical, confrontational. Never generic or conformist.
    """

    DEFAULT_SIGNATURE = FreemanExecutorSignature
