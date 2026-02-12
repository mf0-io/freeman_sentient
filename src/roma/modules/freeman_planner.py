"""Freeman-specific Planner module.

Subclasses the base ROMA Planner with Freeman's personality signature.
The only override is DEFAULT_SIGNATURE — all logic is inherited from BaseModule.
"""

from roma_dspy.core.modules import Planner

from src.roma.modules.signatures import FreemanPlannerSignature


class FreemanPlanner(Planner):
    """Freeman-specialized task planner.

    Decomposes complex tasks using Freeman's thinking methods:
    analogies, "what if?", 5 whys, critical thinking, dialectics.
    """

    DEFAULT_SIGNATURE = FreemanPlannerSignature
