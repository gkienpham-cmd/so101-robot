"""BeanSight VN: evaluation-first tooling for the SO-101 coffee workcell."""

from .models import Decision, ExperimentManifest, FailureCode, Label, PerceptionResult, TrialRecord

__all__ = [
    "Decision",
    "ExperimentManifest",
    "FailureCode",
    "Label",
    "PerceptionResult",
    "TrialRecord",
]

__version__ = "0.1.0"
