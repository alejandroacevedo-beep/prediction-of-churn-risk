from customer_health_platform import (
    ChurnScoringEngine,
    ClientProfile,
    ClientSignals,
    create_demo_profile,
    create_demo_signals,
)

__all__ = [
    "ChurnScoringEngine",
    "ClientProfile",
    "ClientSignals",
    "create_demo_profile",
    "create_demo_signals",
    "get_demo_profile",
    "get_demo_signals",
    "score_tickets",
    "score_usage",
    "score_satisfaction",
    "compute_churn_risk",
]

import json


def get_demo_profile() -> ClientProfile:
    return create_demo_profile()


def get_demo_signals() -> ClientSignals:
    return create_demo_signals()


def score_tickets(profile: ClientProfile, tickets: list):
    engine = ChurnScoringEngine()
    return engine.score_tickets(profile, tickets)


def score_usage(usage_history: list):
    engine = ChurnScoringEngine()
    return engine.score_usage(usage_history)


def score_satisfaction(sat_history: list):
    engine = ChurnScoringEngine()
    return engine.score_satisfaction(sat_history)


def compute_churn_risk(profile: ClientProfile, signals: ClientSignals):
    engine = ChurnScoringEngine()
    return engine.compute_churn_risk(profile, signals)


if __name__ == "__main__":
    profile = get_demo_profile()
    signals = get_demo_signals()
    result = compute_churn_risk(profile, signals)
    print(json.dumps(result, indent=2, default=str))
