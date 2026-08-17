"""
Customer Health Platform

This module contains the runtime implementation for the spec-driven customer
health, churn risk, and survey analysis platform.

It combines the formal contracts from the specs/ package with a working
Customer Health Platform that can evaluate support activity, churn risk,
customer sentiment, and survey-driven service quality indicators.
"""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from pathlib import Path
from statistics import mean
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


class Priority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Importance(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class AccountTier(str, Enum):
    ENTERPRISE = "ENTERPRISE"
    PROFESSIONAL = "PROFESSIONAL"
    STANDARD = "STANDARD"


class HealthStatus(str, Enum):
    HEALTHY = "Healthy"
    WATCH = "Watch"
    AT_RISK = "At Risk"


class SentimentLabel(str, Enum):
    FRUSTRATED = "frustrated"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"


class AnalysisMode(str, Enum):
    LLM_PREFERRED = "llm_preferred"
    LLM_REQUIRED = "llm_required"
    LOCAL_ONLY = "local_only"


@dataclass
class Contact:
    """A customer or stakeholder contact."""

    name: str
    role: str
    importance: str = "normal"
    influence_weight: float = field(init=False)

    def __post_init__(self) -> None:
        if not self.name or not str(self.name).strip():
            raise ValueError("Contact name cannot be empty")
        if not self.role or not str(self.role).strip():
            raise ValueError("Contact role cannot be empty")

        normalized = str(self.importance).strip().lower()
        valid = {"critical", "high", "normal", "low"}
        self.importance = normalized if normalized in valid else "normal"
        self.influence_weight = {"critical": 1.5, "high": 1.5, "normal": 1.0, "low": 0.8}.get(
            self.importance, 1.0
        )


@dataclass
class ClientProfile:
    """Account profile with business context and key contacts."""

    company_name: str
    business_goals: List[str]
    key_contacts: List[Contact]
    critical_features: List[str]
    communication_style: str
    account_tier: str = "STANDARD"
    renewal_date: Optional[str] = None
    open_commitments: List[str] = field(default_factory=list)
    known_risks: List[str] = field(default_factory=list)
    primary_contact: Optional[Contact] = field(init=False, default=None)

    def __post_init__(self) -> None:
        if not self.company_name or not str(self.company_name).strip():
            raise ValueError("Company name is required")
        if not self.business_goals:
            raise ValueError("At least one business goal is required")
        if not self.key_contacts:
            raise ValueError("At least one key contact is required")
        if not self.critical_features:
            raise ValueError("At least one critical feature must be specified")
        if not self.communication_style or not str(self.communication_style).strip():
            raise ValueError("Communication style is required")

        normalized_tier = str(self.account_tier).upper()
        if normalized_tier not in {"ENTERPRISE", "PROFESSIONAL", "STANDARD"}:
            normalized_tier = "STANDARD"
        self.account_tier = normalized_tier
        self.primary_contact = max(self.key_contacts, key=lambda c: c.influence_weight)

    @property
    def tier_config(self) -> Dict[str, Any]:
        config = {
            "ENTERPRISE": {"weight": 2.0, "priority_threshold": 40},
            "PROFESSIONAL": {"weight": 1.5, "priority_threshold": 50},
            "STANDARD": {"weight": 1.0, "priority_threshold": 65},
        }
        return config.get(self.account_tier, config["STANDARD"])

    def days_to_renewal(self) -> Optional[int]:
        if not self.renewal_date:
            return None
        try:
            renewal = datetime.fromisoformat(str(self.renewal_date)).date()
        except ValueError:
            try:
                renewal = datetime.strptime(str(self.renewal_date), "%Y-%m-%d").date()
            except ValueError:
                return None
        return (renewal - date.today()).days

    def get_contact_weight(self, contact_name: str) -> float:
        for contact in self.key_contacts:
            if contact.name == contact_name:
                return contact.influence_weight
        return 1.0

    def get_feature_priority(self, feature_name: str) -> float:
        return 1.5 if feature_name in self.critical_features else 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "company_name": self.company_name,
            "business_goals": list(self.business_goals),
            "key_contacts": [contact.__dict__ for contact in self.key_contacts],
            "critical_features": list(self.critical_features),
            "communication_style": self.communication_style,
            "account_tier": self.account_tier,
            "renewal_date": self.renewal_date,
            "open_commitments": list(self.open_commitments),
            "known_risks": list(self.known_risks),
        }


@dataclass
class SupportTicket:
    """Support ticket or incident record."""

    ticket_id: str
    opened_on: date
    closed_on: Optional[date]
    subject: str
    related_feature: str
    priority: str
    status: str
    reopened_count: int = 0

    def __post_init__(self) -> None:
        if not self.ticket_id or not str(self.ticket_id).strip():
            raise ValueError("Ticket ID cannot be empty")
        if not self.subject or not str(self.subject).strip():
            raise ValueError("Ticket subject cannot be empty")
        if self.closed_on and self.closed_on < self.opened_on:
            raise ValueError("Close date cannot be before open date")

        self.priority = str(self.priority).strip().lower()
        if self.priority not in {"critical", "high", "medium", "low"}:
            self.priority = "low"
        self.status = str(self.status).strip().lower()

    @property
    def is_unresolved(self) -> bool:
        return self.closed_on is None

    @property
    def critical_indicator(self) -> bool:
        return self.priority in {"critical", "high"} and self.is_unresolved

    @property
    def age_days(self) -> int:
        reference = self.closed_on or date.today()
        return (reference - self.opened_on).days

    def severity_score(self, is_critical_feature: bool = False) -> float:
        base_scores = {"critical": 10.0, "high": 6.0, "medium": 3.0, "low": 1.0}
        score = float(base_scores.get(self.priority, 1.0))
        if self.status == "escalated":
            score += 4.0
        if self.is_unresolved and self.priority in {"critical", "high"}:
            score += 3.0
        score += float(self.reopened_count) * 2.0
        if is_critical_feature:
            score *= 1.5
        return round(score, 2)


@dataclass
class Message:
    """Customer message or interaction."""

    message_id: str
    sent_on: date
    sender_name: str
    sender_role: str
    channel: str
    text: str

    def __post_init__(self) -> None:
        if not self.message_id or not str(self.message_id).strip():
            raise ValueError("Message ID and text are required")
        if not self.text or not str(self.text).strip():
            raise ValueError("Message ID and text are required")
        self.channel = str(self.channel).strip().lower()

    @property
    def text_length(self) -> int:
        return len(str(self.text))

    def is_escalation_indicator(self) -> bool:
        keywords = {"urgent", "critical", "down", "outage", "emergency", "failed"}
        lowered = str(self.text).lower()
        return any(keyword in lowered for keyword in keywords)


@dataclass
class UsageSnapshot:
    """A customer usage snapshot for a reporting period."""

    period_label: str
    active_users: int
    feature_usage_pct: float

    def __post_init__(self) -> None:
        if self.active_users < 0:
            raise ValueError("Active users cannot be negative")
        if not 0 <= float(self.feature_usage_pct) <= 100:
            raise ValueError("Feature usage percentage must be between 0 and 100")

    @property
    def adoption_health(self) -> str:
        value = float(self.feature_usage_pct)
        if value >= 80:
            return "excellent"
        if value >= 60:
            return "healthy"
        if value >= 40:
            return "concerning"
        return "critical"

    def change_from(self, previous: Optional["UsageSnapshot"]) -> Dict[str, float]:
        if previous is None:
            return {
                "user_change": 0.0,
                "user_change_pct": 0.0,
                "usage_change": 0.0,
            }
        user_change = self.active_users - previous.active_users
        user_change_pct = 0.0 if previous.active_users == 0 else (user_change / previous.active_users) * 100
        usage_change = self.feature_usage_pct - previous.feature_usage_pct
        return {
            "user_change": float(user_change),
            "user_change_pct": round(float(user_change_pct), 2),
            "usage_change": round(float(usage_change), 2),
        }


@dataclass
class SatisfactionScore:
    """Customer satisfaction metrics for a period."""

    period_label: str
    csat: Optional[float] = None
    nps: Optional[int] = None

    def __post_init__(self) -> None:
        if self.csat is not None and not 0 <= float(self.csat) <= 100:
            raise ValueError("CSAT must be between 0 and 100")
        if self.nps is not None and not -100 <= int(self.nps) <= 100:
            raise ValueError("NPS must be between -100 and 100")
        if self.csat is None and self.nps is None:
            raise ValueError("At least one satisfaction metric is required")

    @property
    def overall_sentiment(self) -> str:
        metrics = []
        if self.csat is not None:
            metrics.append(float(self.csat))
        if self.nps is not None:
            metrics.append(float(self.nps))
        if not metrics:
            return "neutral"
        avg = sum(metrics) / len(metrics)
        if avg >= 70:
            return "positive"
        if avg >= 40:
            return "neutral"
        return "negative"


@dataclass
class ClientSignals:
    """Aggregated customer support, usage, and satisfaction signals."""

    support_tickets: List[SupportTicket]
    usage_history: List[UsageSnapshot]
    satisfaction_history: List[SatisfactionScore]
    messages: List[Message] = field(default_factory=list)


class ChurnScoringEngine:
    """Compute churn risk and recommended actions from customer health data."""

    def score_tickets(self, profile: ClientProfile, tickets: Sequence[SupportTicket]) -> float:
        if not tickets:
            return 0.0
        scores = []
        for ticket in tickets:
            is_critical_feature = ticket.related_feature in profile.critical_features
            scores.append(ticket.severity_score(is_critical_feature=is_critical_feature))
        avg_score = sum(scores) / len(scores)
        return min(100.0, max(0.0, avg_score * 5.0))

    def score_usage(self, usage_history: Sequence[UsageSnapshot]) -> float:
        if not usage_history:
            return 0.0
        avg_usage = sum(float(item.feature_usage_pct) for item in usage_history) / len(usage_history)
        if avg_usage >= 80:
            return 5.0
        if avg_usage >= 60:
            return 20.0
        if avg_usage >= 40:
            return 45.0
        return 70.0

    def score_satisfaction(self, satisfaction_history: Sequence[SatisfactionScore]) -> float:
        if not satisfaction_history:
            return 0.0
        current = satisfaction_history[-1]
        if current.csat is not None:
            csat = float(current.csat)
        else:
            csat = 50.0
        if current.nps is not None:
            nps = float(current.nps)
        else:
            nps = 0.0
        score = (100 - csat) * 0.6 + max(0.0, (30 - nps)) * 0.5
        return min(100.0, max(0.0, score))

    def build_recommendations(
        self,
        profile: ClientProfile,
        risk_score: float,
        support_risk: float,
        usage_risk: float,
        satisfaction_risk: float,
    ) -> List[str]:
        recs: List[str] = []
        if support_risk >= 50:
            recs.append("Schedule a dedicated support review with account leadership")
        if usage_risk >= 40:
            recs.append("Launch a feature adoption plan to improve usability and activation")
        if satisfaction_risk >= 45:
            recs.append("Conduct a customer success business review to address satisfaction gaps")
        if risk_score >= profile.tier_config["priority_threshold"]:
            recs.append("Escalate to the account executive or renewal owner for proactive intervention")
        if not recs:
            recs.append("Maintain current engagement cadence and monitor trend changes")
        return recs

    def compute_churn_risk(self, profile: ClientProfile, signals: ClientSignals) -> Dict[str, Any]:
        support_risk = self.score_tickets(profile, signals.support_tickets)
        usage_risk = self.score_usage(signals.usage_history)
        satisfaction_risk = self.score_satisfaction(signals.satisfaction_history)

        raw_score = (
            support_risk * 0.35
            + usage_risk * 0.35
            + satisfaction_risk * 0.30
        )

        renewal_days = profile.days_to_renewal()
        multiplier = 1.0
        if renewal_days is not None:
            if renewal_days < 30:
                multiplier = 1.3
            elif renewal_days < 60:
                multiplier = 1.15

        risk_score = min(100, round(raw_score * multiplier))
        if risk_score >= 60:
            health_status = "At Risk"
        elif risk_score >= 30:
            health_status = "Watch"
        else:
            health_status = "Healthy"

        evidence = {
            "support_analysis": (
                f"Support risk {support_risk:.1f} based on {len(signals.support_tickets)} ticket(s) and "
                f"critical feature exposure."
            ),
            "usage_analysis": (
                f"Usage risk {usage_risk:.1f} based on adoption and feature-usage trends."
            ),
            "satisfaction_analysis": (
                f"Satisfaction risk {satisfaction_risk:.1f} based on CSAT/NPS deterioration."
            ),
            "renewal_urgency": (
                f"Renewal urgency: {'high' if renewal_days is not None and renewal_days < 60 else 'normal'}"
            ),
        }

        result = {
            "risk_score": int(risk_score),
            "health_status": health_status,
            "risk_factors": {
                "support_risk_score": round(support_risk, 2),
                "usage_risk_score": round(usage_risk, 2),
                "satisfaction_risk_score": round(satisfaction_risk, 2),
            },
            "evidence": evidence,
            "recommendations": self.build_recommendations(
                profile,
                float(risk_score),
                support_risk,
                usage_risk,
                satisfaction_risk,
            ),
        }
        return result


class CustomerSuccessAgent:
    """Analyze customer sentiment and prepare success actions."""

    ESCALATION_KEYWORDS = {"urgent", "critical", "down", "outage", "emergency", "failed"}
    NEGATIVE_KEYWORDS = {"frustrated", "disappointed", "angry", "issue", "problem", "failed", "not working"}
    POSITIVE_KEYWORDS = {"great", "excellent", "happy", "satisfied", "resolved", "working well"}

    def analyze_message_sentiment(self, messages: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for index, message in enumerate(messages):
            text = str(message.get("text", "")).strip()
            if not text:
                continue
            lowered = text.lower()
            escalation = any(keyword in lowered for keyword in self.ESCALATION_KEYWORDS)
            negative_score = sum(1 for keyword in self.NEGATIVE_KEYWORDS if keyword in lowered)
            positive_score = sum(1 for keyword in self.POSITIVE_KEYWORDS if keyword in lowered)

            if escalation:
                sentiment = "frustrated"
            elif negative_score > positive_score:
                sentiment = "negative"
            elif positive_score > negative_score:
                sentiment = "positive"
            else:
                sentiment = "neutral"

            confidence = 0.55 + max(negative_score, positive_score) * 0.10
            if escalation:
                confidence += 0.15
            confidence = min(1.0, round(confidence, 2))

            results.append(
                {
                    "message_id": str(message.get("message_id", f"MSG-{index + 1}")),
                    "sentiment": sentiment,
                    "confidence": confidence,
                    "escalation_indicator": escalation,
                    "summary": f"Detected {sentiment} sentiment with {'urgent escalation' if escalation else 'standard review'} context.",
                }
            )
        return results

    def explain_and_plan(
        self,
        profile: Dict[str, Any],
        risk_result: Dict[str, Any],
        sentiment_messages: Sequence[Dict[str, Any]],
    ) -> Dict[str, Any]:
        risk_score = float(risk_result.get("risk_score", 0))
        if risk_score >= 60:
            urgency = "critical"
        elif risk_score >= 40:
            urgency = "high"
        elif risk_score >= 20:
            urgency = "medium"
        else:
            urgency = "low"

        summary = (
            f"The account {profile.get('company_name', 'customer')} is at {risk_result.get('health_status', 'Healthy')} "
            f"health with a risk score of {risk_score}."
        )

        key_risks = [
            f"Risk score: {risk_score}",
            "Service quality and delivery concerns remain active",
            "Customer sentiment needs monitoring and intervention",
        ]

        priority_actions = [
            "Review support backlog and delivery health with the account team",
            "Confirm renewal and business priority alignment",
            "Close the most cited issues from the most recent customer feedback",
        ]

        if sentiment_messages:
            frustrated = sum(1 for item in sentiment_messages if item.get("sentiment") == "frustrated")
            if frustrated:
                priority_actions.append("Prioritize outreach to calm and recover trust around recent service disruption")

        return {
            "summary": summary,
            "key_risks": key_risks,
            "priority_actions": priority_actions,
            "urgency": urgency,
        }

    def draft_outreach_message(
        self,
        profile: Dict[str, Any],
        risk_result: Dict[str, Any],
        plan: Dict[str, Any],
    ) -> Dict[str, Any]:
        contact = (profile.get("key_contacts") or [{}])[0]
        primary_name = contact.get("name", "there") if isinstance(contact, dict) else "there"
        subject = f"Priority follow-up for {profile.get('company_name', 'your team')}"
        greeting = f"Hi {primary_name},"
        opening = (
            f"I want to address the current customer health signal for {profile.get('company_name', 'your team')} and "
            f"the recent service experience reflected in the latest score of {risk_result.get('risk_score', 0)}."
        )
        main_body = (
            "We have identified the main drivers behind the current health assessment and are aligning a focused action plan "
            "to improve experience, delivery confidence, and renewal readiness."
        )
        next_steps = (
            "Please join a short follow-up session with our team next week so we can review the main issues, confirm priorities, and align the recovery plan."
        )
        signature = "Best regards,\nCustomer Success Team"
        return {
            "subject": subject,
            "greeting": greeting,
            "opening": opening,
            "main_body": main_body,
            "next_steps": next_steps,
            "signature": signature,
        }


class CustomerHealthPlatform:
    """Orchestrates the customer health platform and decision-support workflows."""

    def __init__(self) -> None:
        self.engine = ChurnScoringEngine()
        self.agent = CustomerSuccessAgent()

    def analyze_account(
        self,
        profile: ClientProfile,
        signals: ClientSignals,
        include_outreach: bool = True,
    ) -> Dict[str, Any]:
        risk_assessment = self.engine.compute_churn_risk(profile, signals)
        sentiment_messages = self.agent.analyze_message_sentiment(
            [{"message_id": msg.message_id, "text": msg.text} for msg in signals.messages]
        )
        success_plan = self.agent.explain_and_plan(profile.to_dict(), risk_assessment, sentiment_messages)
        outreach_message = None
        if include_outreach:
            outreach_message = self.agent.draft_outreach_message(profile.to_dict(), risk_assessment, success_plan)

        return {
            "risk_assessment": risk_assessment,
            "sentiment_analysis": {
                "messages": sentiment_messages,
                "overall_sentiment": "positive" if not sentiment_messages else "neutral",
            },
            "success_plan": success_plan,
            "outreach_message": outreach_message,
        }


class SurveyServiceAnalyzer:
    """Analyze CSV survey datasets for service quality, support, and churn risk."""

    def load_csv(self, csv_path: str | Path) -> List[Dict[str, str]]:
        path = Path(csv_path)
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            return [dict(row) for row in reader]

    @staticmethod
    def _safe_int(value: Any, default: int = 0) -> int:
        try:
            return int(float(str(value).replace(",", ".")))
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        try:
            return float(str(value).replace(",", "."))
        except (TypeError, ValueError):
            return default

    def analyze_file(self, csv_path: str | Path) -> Dict[str, Any]:
        rows = self.load_csv(csv_path)
        total_records = len(rows)

        renewal_counts = Counter()
        continuation_scores = []
        recommendation_scores = []
        technical_issue_count = 0
        value_scores = []
        issue_counter: Counter[str] = Counter()
        unsupported_reason_pattern = {"no he considerado abandonar", "el servicio cumple", "no considero necesaria"}

        for row in rows:
            renewal_label = str(row.get("Probabilidad de renovar/continuar próximos 3 meses", "")).strip()
            renewal_counts[renewal_label] += 1
            continuation_scores.append({
                "Muy probable": 4,
                "Probable": 3,
                "Poco probable": 1,
                "Nada probable": 0,
            }.get(renewal_label, 0))

            recommendation = self._safe_int(row.get("Probabilidad de recomendar (1-10)", 0), 0)
            recommendation_scores.append(recommendation)

            technical_flag = str(row.get("Dificultad técnica, retraso o problema no resuelto reciente", "")).strip().lower()
            if technical_flag in {"sí", "si", "yes", "y", "true", "1"}:
                technical_issue_count += 1

            value_score = self._safe_int(row.get("Valor general en relación con el precio (1-5)", 0), 0)
            value_scores.append(value_score)

            reason = str(row.get("Razón principal si considera no continuar", "")).strip()
            if reason and not any(pattern in reason.lower() for pattern in unsupported_reason_pattern):
                issue_counter[reason] += 1
            if reason and reason.lower() not in {"no he considerado abandonar el servicio.", "el servicio cumple con lo esperado.", "no considero necesaria una mejora urgente; el servicio funciona bien."}:
                issue_counter[reason] += 1

        top_issues = [
            {"issue": issue, "count": count}
            for issue, count in issue_counter.most_common(5)
        ]

        avg_recommendation = round(sum(recommendation_scores) / len(recommendation_scores), 2) if recommendation_scores else 0.0
        avg_value = round(sum(value_scores) / len(value_scores), 2) if value_scores else 0.0

        summary = {
            "total_records": total_records,
            "renewal_probability": {
                "distribution": dict(sorted(renewal_counts.items())),
                "average_score": round(sum(continuation_scores) / len(continuation_scores), 2) if continuation_scores else 0.0,
            },
            "nps_snapshot": {
                "average_recommendation": avg_recommendation,
                "min": min(recommendation_scores) if recommendation_scores else 0,
                "max": max(recommendation_scores) if recommendation_scores else 0,
            },
            "technical_issue_rate": round((technical_issue_count / total_records) * 100, 2) if total_records else 0.0,
            "average_value_score": avg_value,
            "top_issues": top_issues,
        }
        return summary
