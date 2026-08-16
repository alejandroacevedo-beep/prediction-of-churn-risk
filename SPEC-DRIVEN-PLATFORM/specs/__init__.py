"""
Customer Health Platform - Specification Package

This package contains formal specifications, protocols, validators,
and compliance tools for the spec-driven development approach.
"""

from .data_models_spec import (
    DataModelSpec,
    ContactSpec,
    ClientProfileSpec,
    SupportTicketSpec,
    MessageSpec,
    UsageSnapshotSpec,
    SatisfactionScoreSpec,
    ClientSignalsSpec,
)

from .scoring_engine_spec import (
    ScoringEngineSpec,
    ChurnScoringEngineSpec,
    SentimentAnalysisSpec,
    CustomerSuccessAgentSpec,
)

from .interfaces import (
    DataModel,
    Scoreable,
    SentimentBearing,
    ScoringEngine,
    SentimentAnalyzer,
    SuccessPlanner,
    HealthAnalyzer,
    Validatable,
    Configurable,
    PlatformInterface,
    DataValidationInterface,
    AnalysisContract,
    SentimentContract,
)

from .decorators import (
    SpecDriven,
    ContractCheckpoint,
    SpecCompliance,
)

from .validator import (
    SpecValidator,
    SpecRunner,
    SpecComplianceResult,
    ComplianceReport,
)

__all__ = [
    # Data model specs
    "DataModelSpec",
    "ContactSpec",
    "ClientProfileSpec",
    "SupportTicketSpec",
    "MessageSpec",
    "UsageSnapshotSpec",
    "SatisfactionScoreSpec",
    "ClientSignalsSpec",
    # Scoring specs
    "ScoringEngineSpec",
    "ChurnScoringEngineSpec",
    "SentimentAnalysisSpec",
    "CustomerSuccessAgentSpec",
    # Protocols
    "DataModel",
    "Scoreable",
    "SentimentBearing",
    "ScoringEngine",
    "SentimentAnalyzer",
    "SuccessPlanner",
    "HealthAnalyzer",
    "Validatable",
    "Configurable",
    "PlatformInterface",
    "DataValidationInterface",
    "AnalysisContract",
    "SentimentContract",
    # Decorators
    "SpecDriven",
    "ContractCheckpoint",
    "SpecCompliance",
    # Validators
    "SpecValidator",
    "SpecRunner",
    "SpecComplianceResult",
    "ComplianceReport",
]

__version__ = "1.0.0"
__description__ = "Spec-driven development framework for Customer Health Platform"
