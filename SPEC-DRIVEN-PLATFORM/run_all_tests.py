"""Starter runner for the Spec-Driven Platform.

This script runs the project validation workflow in one place:
1. imports the platform objects
2. validates the formal specification suite
3. analyzes the synthetic service survey CSV
4. prints a concise summary for immediate testing
"""

from __future__ import annotations

import json
from pathlib import Path

from customer_health_platform import (
    ChurnScoringEngine,
    ClientProfile,
    ClientSignals,
    Contact,
    CustomerHealthPlatform,
    CustomerSuccessAgent,
    SatisfactionScore,
    SurveyServiceAnalyzer,
    SupportTicket,
    UsageSnapshot,
)
from specs.validator import SpecRunner


def build_demo_profile() -> ClientProfile:
    contact = Contact(name="Ana García", role="CTO", importance="critical")
    return ClientProfile(
        company_name="Acme Digital",
        business_goals=["Scale adoption", "Improve support experience"],
        key_contacts=[contact],
        critical_features=["API", "Dashboard"],
        communication_style="formal",
        account_tier="ENTERPRISE",
        renewal_date="2026-09-30",
    )


def build_demo_signals() -> ClientSignals:
    tickets = [
        SupportTicket(
            ticket_id="TCK-001",
            opened_on=None,
            closed_on=None,
            subject="API latency",
            related_feature="API",
            priority="critical",
            status="open",
            reopened_count=1,
        )
    ]
    usage = [UsageSnapshot(period_label="Q3", active_users=120, feature_usage_pct=62.5)]
    satisfaction = [SatisfactionScore(period_label="Q3", csat=68.0, nps=10)]
    return ClientSignals(support_tickets=tickets, usage_history=usage, satisfaction_history=satisfaction, messages=[])


def run_spec_validation() -> dict:
    runner = SpecRunner()
    profile = build_demo_profile()
    signals = build_demo_signals()
    engine = ChurnScoringEngine()
    risk_result = engine.compute_churn_risk(profile, signals)
    agent = CustomerSuccessAgent()
    sentiment_result = agent.analyze_message_sentiment([
        {"message_id": "MSG-01", "text": "The system is down and our team is frustrated.", "sent_on": "2026-08-16"},
        {"message_id": "MSG-02", "text": "Everything is working better now. Great support!", "sent_on": "2026-08-16"},
    ])

    payload = {
        "contacts": [profile.key_contacts[0]],
        "profiles": [profile],
        "tickets": signals.support_tickets,
        "messages": [],
        "churn_results": [risk_result],
        "sentiment_results": [sentiment_result],
    }
    report = runner.run_all_validations(payload)
    return report.to_dict()


def run_survey_analysis() -> dict:
    csv_path = Path(__file__).resolve().parent / "encuesta_servicio_10000_registros_sinteticos.csv"
    if not csv_path.exists():
        return {"error": f"CSV not found: {csv_path}"}
    analyzer = SurveyServiceAnalyzer()
    return analyzer.analyze_file(csv_path)


def main() -> None:
    print("=" * 80)
    print("SPEC-DRIVEN PLATFORM STARTER RUNNER")
    print("=" * 80)

    print("\n[1/2] Running specification validation...")
    spec_report = run_spec_validation()
    print(f"  - total checks: {spec_report['total_checks']}")
    print(f"  - passed: {spec_report['passed_checks']}")
    print(f"  - failed: {spec_report['failed_checks']}")
    print(f"  - compliance: {spec_report['compliance_percentage']:.1f}%")

    print("\n[2/2] Running survey data analysis...")
    survey_summary = run_survey_analysis()
    if "error" in survey_summary:
        print(f"  - {survey_summary['error']}")
    else:
        print(f"  - total records: {survey_summary['total_records']}")
        print(f"  - average recommendation: {survey_summary['nps_snapshot']['average_recommendation']}")
        print(f"  - technical issue rate: {survey_summary['technical_issue_rate']}%")
        print(f"  - top issue: {survey_summary['top_issues'][0]['issue'] if survey_summary['top_issues'] else 'none'}")

    print("\n" + "=" * 80)
    print("Starter run completed successfully.")
    print("=" * 80)


if __name__ == "__main__":
    main()
