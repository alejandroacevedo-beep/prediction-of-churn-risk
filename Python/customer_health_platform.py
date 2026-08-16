from __future__ import annotations

import json
import os
import logging
from dataclasses import dataclass, field, asdict
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
from functools import lru_cache, wraps

try:
    import anthropic
except ImportError:
    anthropic = None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Priority(Enum):
    CRITICAL = 10
    HIGH = 6
    MEDIUM = 3
    LOW = 1

    def value_with_modifier(self, escalated: bool = False, is_open: bool = False) -> float:
        score = self.value
        if escalated:
            score += 4
        if is_open and self in (Priority.CRITICAL, Priority.HIGH):
            score += 3
        return score


class Importance(Enum):
    CRITICAL = 1.5
    HIGH = 1.5
    NORMAL = 1.0
    LOW = 0.8


class AccountTier(Enum):
    ENTERPRISE = {"weight": 2.0, "priority_threshold": 40}
    PROFESSIONAL = {"weight": 1.5, "priority_threshold": 50}
    STANDARD = {"weight": 1.0, "priority_threshold": 65}

    def config(self) -> Dict[str, Any]:
        return self.value


class HealthStatus(Enum):
    HEALTHY = "Healthy"
    WATCH = "Watch"
    AT_RISK = "At Risk"

    @classmethod
    def from_score(cls, score: int) -> HealthStatus:
        if score >= 60:
            return cls.AT_RISK
        elif score >= 30:
            return cls.WATCH
        return cls.HEALTHY


class SentimentLabel(Enum):
    FRUSTRATED = "frustrated"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"


class AnalysisMode(Enum):
    LLM_PREFERRED = "llm_preferred"
    LLM_REQUIRED = "llm_required"
    LOCAL_ONLY = "local_only"


@dataclass
class Contact:
    name: str
    role: str
    importance: str = "normal"

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Contact name cannot be empty")
        if not self.role or not self.role.strip():
            raise ValueError("Contact role cannot be empty")
        self.importance = self.importance.lower()
        if self.importance not in {"critical", "high", "normal", "low"}:
            self.importance = "normal"

    @property
    def influence_weight(self) -> float:
        weights = {"critical": 1.5, "high": 1.5, "normal": 1.0, "low": 0.8}
        return weights.get(self.importance, 1.0)


@dataclass
class ClientProfile:
    company_name: str
    business_goals: List[str]
    key_contacts: List[Contact]
    critical_features: List[str]
    communication_style: str
    open_commitments: List[str] = field(default_factory=list)
    known_risks: List[str] = field(default_factory=list)
    account_tier: str = "Standard"
    renewal_date: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.company_name or not self.company_name.strip():
            raise ValueError("Company name is required")
        if not self.key_contacts:
            raise ValueError("At least one key contact is required")
        if not self.critical_features:
            raise ValueError("At least one critical feature must be specified")

    @property
    def tier_config(self) -> Dict[str, Any]:
        try:
            tier = AccountTier[self.account_tier.upper()]
            return tier.config()
        except (KeyError, AttributeError):
            return AccountTier.STANDARD.config()

    @property
    def primary_contact(self) -> Optional[Contact]:
        by_importance = sorted(
            self.key_contacts,
            key=lambda c: ({"critical": 0, "high": 1, "normal": 2, "low": 3}.get(c.importance, 3)),
        )
        return by_importance[0] if by_importance else None

    def get_contact_weight(self, name: str) -> float:
        for contact in self.key_contacts:
            if contact.name.lower() == name.lower():
                return contact.influence_weight
        return 1.0

    def get_feature_priority(self, feature: str) -> float:
        return 1.5 if feature in self.critical_features else 1.0

    def days_to_renewal(self) -> Optional[int]:
        if not self.renewal_date:
            return None
        try:
            renewal = date.fromisoformat(self.renewal_date)
            return (renewal - date.today()).days
        except (ValueError, TypeError):
            return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "company_name": self.company_name,
            "business_goals": self.business_goals,
            "key_contacts": [
                {
                    "name": c.name,
                    "role": c.role,
                    "importance": c.importance,
                }
                for c in self.key_contacts
            ],
            "critical_features": self.critical_features,
            "communication_style": self.communication_style,
            "open_commitments": self.open_commitments,
            "known_risks": self.known_risks,
            "account_tier": self.account_tier,
            "renewal_date": self.renewal_date,
        }


@dataclass
class SupportTicket:
    ticket_id: str
    opened_on: date
    closed_on: Optional[date]
    subject: str
    related_feature: str
    priority: str
    status: str
    reopened_count: int = 0

    def __post_init__(self) -> None:
        if not self.ticket_id or not self.ticket_id.strip():
            raise ValueError("Ticket ID cannot be empty")
        self.priority = self.priority.lower()
        self.status = self.status.lower()
        if self.closed_on and self.closed_on < self.opened_on:
            raise ValueError("Close date cannot be before open date")

    @property
    def is_unresolved(self) -> bool:
        return self.closed_on is None

    @property
    def age_days(self) -> int:
        end = self.closed_on or date.today()
        return (end - self.opened_on).days

    @property
    def critical_indicator(self) -> bool:
        return self.priority in {"critical", "high"} and self.is_unresolved

    def severity_score(self, is_critical_feature: bool = False) -> float:
        priority_map = {"critical": 10.0, "high": 6.0, "medium": 3.0, "low": 1.0}
        base_score = priority_map.get(self.priority, 2.0)

        if self.status == "escalated":
            base_score += 4.0
        if self.is_unresolved and self.priority in {"critical", "high"}:
            base_score += 3.0
        base_score += self.reopened_count * 2.0

        return base_score * (1.5 if is_critical_feature else 1.0)


@dataclass
class Message:
    message_id: str
    sent_on: date
    sender_name: str
    sender_role: str
    channel: str
    text: str

    def __post_init__(self) -> None:
        if not self.message_id or not self.text:
            raise ValueError("Message ID and text are required")
        self.channel = self.channel.lower()

    @property
    def text_length(self) -> int:
        return len(self.text)

    def is_escalation_indicator(self) -> bool:
        escalation_keywords = {"urgent", "critical", "down", "outage", "emergency", "failed"}
        text_lower = self.text.lower()
        return any(keyword in text_lower for keyword in escalation_keywords)


@dataclass
class UsageSnapshot:
    period_label: str
    active_users: int
    feature_usage_pct: float

    def __post_init__(self) -> None:
        if self.active_users < 0:
            raise ValueError("Active users cannot be negative")
        if not 0 <= self.feature_usage_pct <= 100:
            raise ValueError("Feature usage percentage must be between 0 and 100")

    @property
    def adoption_health(self) -> str:
        if self.feature_usage_pct >= 80:
            return "excellent"
        elif self.feature_usage_pct >= 60:
            return "healthy"
        elif self.feature_usage_pct >= 40:
            return "concerning"
        return "critical"

    def change_from(self, previous: UsageSnapshot) -> Dict[str, float]:
        return {
            "user_change": self.active_users - previous.active_users,
            "user_change_pct": (
                (self.active_users - previous.active_users) / previous.active_users * 100
                if previous.active_users > 0
                else 0
            ),
            "usage_change": self.feature_usage_pct - previous.feature_usage_pct,
        }


@dataclass
class SatisfactionScore:
    period_label: str
    csat: Optional[float] = None
    nps: Optional[int] = None

    def __post_init__(self) -> None:
        if self.csat is not None and not 0 <= self.csat <= 100:
            raise ValueError("CSAT must be between 0 and 100")
        if self.nps is not None and not -100 <= self.nps <= 100:
            raise ValueError("NPS must be between -100 and 100")

    @property
    def overall_sentiment(self) -> str:
        score = 0
        weight = 0
        if self.csat is not None:
            score += self.csat
            weight += 1
        if self.nps is not None:
            score += self.nps
            weight += 1
        if weight == 0:
            return "unknown"
        avg = score / weight
        if avg >= 70:
            return "positive"
        elif avg >= 40:
            return "neutral"
        return "negative"

    def deterioration_from(self, previous: SatisfactionScore) -> Dict[str, Optional[float]]:
        return {
            "csat_delta": (
                self.csat - previous.csat
                if self.csat is not None and previous.csat is not None
                else None
            ),
            "nps_delta": (
                self.nps - previous.nps if self.nps is not None and previous.nps is not None else None
            ),
        }


@dataclass
class ClientSignals:
    tickets: List[SupportTicket]
    messages: List[Message]
    usage_history: List[UsageSnapshot]
    satisfaction_history: List[SatisfactionScore]


class ScoreAggregator:
    def __init__(self) -> None:
        self.components: Dict[str, Dict[str, Any]] = {}
        self.evidence_log: List[str] = []

    def add_penalty(
        self,
        component: str,
        penalty: float,
        evidence: Optional[List[str]] = None,
        weight: float = 1.0,
    ) -> None:
        if component not in self.components:
            self.components[component] = {"penalty": 0.0, "weight": weight}
        self.components[component]["penalty"] += penalty * weight
        if evidence:
            self.evidence_log.extend(evidence)

    def final_score(self) -> float:
        return min(100.0, sum(c["penalty"] for c in self.components.values()))

    def breakdown(self) -> Dict[str, float]:
        return {k: round(v["penalty"], 1) for k, v in self.components.items()}

    def evidence(self) -> List[str]:
        return self.evidence_log


class ChurnScoringEngine:
    def __init__(self) -> None:
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def score_tickets(self, profile: ClientProfile, tickets: List[SupportTicket]) -> Dict[str, Any]:
        aggregator = ScoreAggregator()

        for ticket in tickets:
            feature_weight = profile.get_feature_priority(ticket.related_feature)
            severity = ticket.severity_score(is_critical_feature=feature_weight > 1.0)

            aggregator.add_penalty("support", severity, weight=1.0)

            if severity >= 6:
                aggregator.evidence_log.append(
                    f"{ticket.ticket_id} | {ticket.priority.upper()} | {ticket.status} "
                    f"| {ticket.related_feature} | severity: {severity:.1f}"
                )

        return {
            "penalty": aggregator.components.get("support", {}).get("penalty", 0.0),
            "evidence": aggregator.evidence(),
        }

    def score_usage(self, usage_history: List[UsageSnapshot]) -> Dict[str, Any]:
        if len(usage_history) < 2:
            return {"penalty": 0.0, "evidence": []}

        aggregator = ScoreAggregator()
        for i in range(1, len(usage_history)):
            previous = usage_history[i - 1]
            current = usage_history[i]
            changes = current.change_from(previous)

            if changes["usage_change"] < 0:
                usage_penalty = abs(changes["usage_change"]) * 0.6
                aggregator.add_penalty(
                    "usage_decline",
                    usage_penalty,
                    [
                        f"Feature usage: {previous.feature_usage_pct:.1f}% → {current.feature_usage_pct:.1f}% "
                        f"({changes['usage_change']:.1f} pts)"
                    ],
                )

            if changes["user_change"] < 0:
                user_penalty = abs(changes["user_change"]) * 0.5
                aggregator.add_penalty(
                    "user_decline",
                    user_penalty,
                    [f"Active users: {previous.active_users} → {current.active_users} ({changes['user_change_pct']:.1f}%)"],
                )

        return {"penalty": aggregator.final_score() / 2, "evidence": aggregator.evidence()}

    def score_satisfaction(self, sat_history: List[SatisfactionScore]) -> Dict[str, Any]:
        if len(sat_history) < 2:
            return {"penalty": 0.0, "evidence": []}

        aggregator = ScoreAggregator()
        for i in range(1, len(sat_history)):
            previous = sat_history[i - 1]
            current = sat_history[i]
            delta = current.deterioration_from(previous)

            if delta["csat_delta"] is not None and delta["csat_delta"] < 0:
                csat_penalty = abs(delta["csat_delta"]) * 0.5
                aggregator.add_penalty(
                    "csat_decline",
                    csat_penalty,
                    [f"CSAT: {previous.csat:.0f} → {current.csat:.0f} ({delta['csat_delta']:.0f} pts)"],
                )

            if delta["nps_delta"] is not None and delta["nps_delta"] < 0:
                nps_penalty = abs(delta["nps_delta"]) * 0.3
                aggregator.add_penalty(
                    "nps_decline",
                    nps_penalty,
                    [f"NPS: {previous.nps} → {current.nps} ({delta['nps_delta']} pts)"],
                )

        return {"penalty": aggregator.final_score() / 2, "evidence": aggregator.evidence()}

    def build_recommendations(self, profile: ClientProfile, score: int) -> List[str]:
        recommendations: List[str] = []
        tier_config = profile.tier_config
        threshold = tier_config.get("priority_threshold", 50)

        if score >= threshold:
            recommendations.extend(
                [
                    "Escalate to executive steering committee immediately",
                    "Initiate crisis management protocol with product leadership",
                    f"Develop recovery plan targeting {score} point reduction within 30 days",
                ]
            )
        elif score >= threshold * 0.6:
            recommendations.extend(
                [
                    "Schedule weekly customer business reviews",
                    "Implement proactive monitoring on critical features",
                    "Prepare detailed remediation roadmap",
                ]
            )
        else:
            recommendations.extend(
                [
                    "Continue standard engagement cadence",
                    "Conduct quarterly strategic account planning",
                    "Maintain adoption monitoring",
                ]
            )

        if profile.known_risks:
            recommendations.append(f"Risk mitigation: {profile.known_risks[0]}")

        days_to_renewal = profile.days_to_renewal()
        if days_to_renewal is not None and days_to_renewal < 90:
            recommendations.insert(0, f"URGENT: Renewal in {days_to_renewal} days — prioritize resolution")

        return recommendations

    def compute_churn_risk(self, profile: ClientProfile, signals: ClientSignals) -> Dict[str, Any]:
        ticket_result = self.score_tickets(profile, signals.tickets)
        usage_result = self.score_usage(signals.usage_history)
        sat_result = self.score_satisfaction(signals.satisfaction_history)

        raw_penalty = ticket_result["penalty"] + usage_result["penalty"] + sat_result["penalty"]
        score = int(min(100, round(raw_penalty)))
        status = HealthStatus.from_score(score).value

        evidence = ticket_result["evidence"] + usage_result["evidence"] + sat_result["evidence"]

        summary_map = {
            "Healthy": f"{profile.company_name} maintains operational stability with no material churn indicators.",
            "Watch": f"{profile.company_name} is showing deterioration across key health metrics requiring intervention.",
            "At Risk": f"{profile.company_name} faces immediate churn risk and requires executive intervention.",
        }

        self.logger.info(f"Churn risk computed for {profile.company_name}: score={score}, status={status}")

        return {
            "company_name": profile.company_name,
            "account_tier": profile.account_tier,
            "renewal_date": profile.renewal_date,
            "days_to_renewal": profile.days_to_renewal(),
            "score": score,
            "status": status,
            "summary": summary_map.get(status, "Account requires review."),
            "evidence": evidence,
            "breakdown": {
                "tickets_penalty": round(ticket_result["penalty"], 1),
                "usage_penalty": round(usage_result["penalty"], 1),
                "satisfaction_penalty": round(sat_result["penalty"], 1),
            },
            "recommended_focus": self.build_recommendations(profile, score),
        }


class LLMConfig:
    def __init__(
        self,
        mode: AnalysisMode = AnalysisMode.LLM_PREFERRED,
        fallback_to_local: bool = True,
        max_retries: int = 2,
    ) -> None:
        self.mode = mode
        self.fallback_to_local = fallback_to_local
        self.max_retries = max_retries
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def is_available(self) -> bool:
        available = anthropic is not None and bool(os.getenv("ANTHROPIC_API_KEY"))
        if not available:
            self.logger.warning("Anthropic API not available; using local analysis")
        return available

    def should_use_llm(self) -> bool:
        if self.mode == AnalysisMode.LOCAL_ONLY:
            return False
        if self.mode == AnalysisMode.LLM_REQUIRED:
            return self.is_available()
        return self.is_available()


def _retry_with_backoff(max_retries: int = 2, base_delay: int = 1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries or not isinstance(e, (
                        anthropic.APIConnectionError if anthropic else Exception,
                        anthropic.RateLimitError if anthropic else Exception,
                        anthropic.APIStatusError if anthropic else Exception,
                    )):
                        raise
                    delay = base_delay * (2 ** attempt)
                    logger.warning(
                        f"API error on attempt {attempt + 1}/{max_retries + 1}, retrying in {delay}s: {e}"
                    )
                    import time
                    time.sleep(delay)
        return wrapper
    return decorator


class CustomerSuccessAgent:
    def __init__(self, llm_config: Optional[LLMConfig] = None) -> None:
        self.llm_config = llm_config or LLMConfig()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
        self.timeout = int(os.getenv("LLM_TIMEOUT", "30"))

    @_retry_with_backoff(max_retries=2)
    def _call_claude_json(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.3,
    ) -> Any:
        if not self.llm_config.is_available():
            raise RuntimeError("Anthropic API is not configured.")

        client = anthropic.Anthropic(timeout=self.timeout)
        response = client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

        text = "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        )
        text = text.strip()
        if text.startswith("```"):
            text = text.strip("`").lstrip("json").strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parsing failed: {e}\nRaw text: {text[:200]}")
            raise ValueError(f"Failed to parse LLM response as JSON: {e}")

    @staticmethod
    @lru_cache(maxsize=128)
    def _get_sentiment_keywords() -> Dict[str, List[str]]:
        return {
            "negative": [
                "down again", "failing", "issue", "problem", "outage", "escalation",
                "bug", "cost us", "not working", "urgent", "broken", "disaster",
                "unacceptable", "horrible", "terrible", "worst",
            ],
            "positive": [
                "thanks", "quick turnaround", "appreciate", "resolved", "smooth",
                "great support", "excellent", "fantastic", "impressed", "satisfied",
                "solved", "outstanding", "delighted",
            ],
        }

    def _sentiment_from_text(self, text: str) -> Dict[str, Any]:
        keywords = self._get_sentiment_keywords()
        lowered = text.lower()

        score = 0.0
        matched_keywords = []

        for keyword in keywords["negative"]:
            if keyword in lowered:
                score -= 0.6
                matched_keywords.append(keyword)
        for keyword in keywords["positive"]:
            if keyword in lowered:
                score += 0.4
                matched_keywords.append(keyword)

        score = max(-1.0, min(1.0, score))

        if score <= -0.5:
            label = SentimentLabel.FRUSTRATED.value
        elif score <= -0.15:
            label = SentimentLabel.NEGATIVE.value
        elif score >= 0.25:
            label = SentimentLabel.POSITIVE.value
        else:
            label = SentimentLabel.NEUTRAL.value

        return {
            "sentiment_score": round(score, 2),
            "sentiment_label": label,
            "matched_keywords": matched_keywords[:3],
        }

    def analyze_message_sentiment(self, messages: List[Dict]) -> List[Dict]:
        if not self.llm_config.should_use_llm():
            enriched = []
            for message in messages:
                result = dict(message)
                sentiment = self._sentiment_from_text(message.get("text", ""))
                result.update({
                    "sentiment_score": sentiment["sentiment_score"],
                    "sentiment_label": sentiment["sentiment_label"],
                    "analysis_mode": "local",
                })
                enriched.append(result)
            return enriched

        try:
            system_prompt = (
                "You are an expert customer sentiment analyst. Assess tone and emotional content. "
                "Return JSON with message_id, sentiment_score (-1.0 to 1.0), and sentiment_label "
                "(positive|neutral|negative|frustrated). Be concise and precise."
            )
            user_prompt = json.dumps(
                [
                    {
                        "message_id": m.get("message_id"),
                        "sender_role": m.get("sender_role"),
                        "text": m.get("text"),
                    }
                    for m in messages
                ],
                indent=2,
            )

            results = self._call_claude_json(system_prompt, user_prompt, max_tokens=800) or []
            by_id = {
                entry.get("message_id"): entry
                for entry in results
                if isinstance(entry, dict) and "message_id" in entry
            }

            enriched = []
            for message in messages:
                entry = dict(message)
                result = by_id.get(message.get("message_id"), {})
                entry.update({
                    "sentiment_score": result.get("sentiment_score"),
                    "sentiment_label": result.get("sentiment_label"),
                    "analysis_mode": "llm",
                })
                enriched.append(entry)
            return enriched

        except Exception as e:
            self.logger.error(f"LLM sentiment analysis failed: {e}")
            if self.llm_config.fallback_to_local:
                return self.analyze_message_sentiment(messages)
            raise

    def _explain_and_plan_local(
        self, profile: Dict, risk_result: Dict, sentiment_messages: List[Dict]
    ) -> Dict:
        company_name = profile.get("company_name", "Account")
        score = risk_result.get("score", 0)
        status = risk_result.get("status", "Healthy")
        evidence = risk_result.get("evidence", [])

        key_risks = []
        if score >= 60:
            key_risks.extend([
                {
                    "risk": "Product reliability crisis affecting customer operations",
                    "evidence": evidence[0] if evidence else "Critical issues unresolved",
                    "severity": "critical",
                },
                {
                    "risk": "Adoption decline indicates decreasing value realization",
                    "evidence": evidence[1] if len(evidence) > 1 else "Usage trending down",
                    "severity": "high",
                },
            ])
        elif score >= 30:
            key_risks.extend([
                {
                    "risk": "Emerging operational issues requiring attention",
                    "evidence": evidence[0] if evidence else "Issues detected",
                    "severity": "high",
                },
                {
                    "risk": "Customer sentiment deterioration",
                    "evidence": "Satisfaction scores declining",
                    "severity": "medium",
                },
            ])

        priority_actions = []
        if score >= 60:
            priority_actions.extend([
                {
                    "action": "Initiate crisis management with C-level executive alignment",
                    "owner": "Account Executive + VP Customer Success",
                    "priority": "critical",
                },
                {
                    "action": "Develop 30-day recovery plan targeting critical product issues",
                    "owner": "Customer Success Manager + Product Lead",
                    "priority": "critical",
                },
                {
                    "action": "Conduct executive business review to reset expectations",
                    "owner": "Account Executive",
                    "priority": "high",
                },
            ])
        elif score >= 30:
            priority_actions.extend([
                {
                    "action": "Schedule strategic business review within 2 weeks",
                    "owner": "Customer Success Manager",
                    "priority": "high",
                },
                {
                    "action": "Establish weekly touchpoint cadence with primary sponsor",
                    "owner": "Customer Success Manager",
                    "priority": "high",
                },
                {
                    "action": "Develop targeted remediation roadmap",
                    "owner": "Product + Customer Success",
                    "priority": "medium",
                },
            ])

        status_desc = {
            "Healthy": "stable and operationally sound",
            "Watch": "showing meaningful deterioration",
            "At Risk": "facing critical churn risk",
        }.get(status, "requiring attention")

        return {
            "summary": (
                f"{company_name} is currently {status_desc}. "
                f"With a risk score of {score}/100, immediate attention is {'critical' if score >= 60 else 'recommended' if score >= 30 else 'not required'}."
            ),
            "key_risks": key_risks,
            "priority_actions": priority_actions,
            "analysis_mode": "local",
        }

    def explain_and_plan(
        self, profile: Dict, risk_result: Dict, sentiment_messages: List[Dict]
    ) -> Dict:
        if not self.llm_config.should_use_llm():
            return self._explain_and_plan_local(profile, risk_result, sentiment_messages)

        try:
            system_prompt = (
                "You are a Customer Success strategist with expertise in account health analysis. "
                "Provide executive-level insights and actionable strategies. "
                "Return JSON with summary, key_risks (list with risk, evidence, severity), "
                "and priority_actions (list with action, owner, priority). "
                "Be specific and data-driven."
            )
            user_prompt = json.dumps(
                {
                    "client_profile": profile,
                    "risk_result": risk_result,
                    "sentiment_messages": sentiment_messages[:5],
                },
                indent=2,
                default=str,
            )
            return self._call_claude_json(system_prompt, user_prompt, max_tokens=1500)
        except Exception as e:
            self.logger.error(f"LLM plan generation failed: {e}")
            if self.llm_config.fallback_to_local:
                return self._explain_and_plan_local(profile, risk_result, sentiment_messages)
            raise

    def _draft_outreach_local(
        self, profile: Dict, risk_result: Dict, plan: Dict
    ) -> Dict:
        company_name = profile.get("company_name", "Client")
        risk_status = risk_result.get("status", "Healthy")
        contacts = profile.get("key_contacts") or []
        primary_contact = "Valued Customer"
        if contacts and isinstance(contacts, list) and isinstance(contacts[0], dict):
            primary_contact = contacts[0].get("name", "Valued Customer")

        tone = "urgent" if risk_status == "At Risk" else "proactive" if risk_status == "Watch" else "collaborative"

        subject_templates = {
            "At Risk": f"Urgent: {company_name} account recovery plan",
            "Watch": f"{company_name} account health check-in and next steps",
            "Healthy": f"Strategic partnership discussion - {company_name} account",
        }

        body_templates = {
            "At Risk": (
                f"Hi {primary_contact},\n\n"
                f"I wanted to reach out regarding the current status of the {company_name} account. "
                f"We've identified several critical issues affecting product reliability and adoption that require immediate attention. "
                f"I'd like to schedule an urgent call with you and key stakeholders to align on a recovery plan.\n\n"
                f"Key concerns:\n"
                f"• Unresolved critical product issues\n"
                f"• Declining user adoption\n"
                f"• Reduced customer satisfaction\n\n"
                f"I've prepared a detailed action plan and recovery timeline. Let's align on priorities this week.\n\n"
                f"Best regards,\nCustomer Success Team"
            ),
            "Watch": (
                f"Hi {primary_contact},\n\n"
                f"I'm reaching out to discuss the {company_name} account and emerging opportunities for improvement. "
                f"We've noticed some trends we'd like to address collaboratively.\n\n"
                f"Areas of focus:\n"
                f"• Feature adoption and value realization\n"
                f"• Support and operational excellence\n"
                f"• Strategic alignment on upcoming initiatives\n\n"
                f"Let's schedule a business review to ensure we're supporting your success. "
                f"Are you available for a 30-minute call next week?\n\n"
                f"Best regards,\nCustomer Success Team"
            ),
            "Healthy": (
                f"Hi {primary_contact},\n\n"
                f"I hope you're enjoying strong results with {company_name}. "
                f"I'd like to discuss strategic growth opportunities and how we can maximize value going forward.\n\n"
                f"I'm available for a quarterly business review at your convenience.\n\n"
                f"Best regards,\nCustomer Success Team"
            ),
        }

        return {
            "recipient": primary_contact,
            "subject": subject_templates.get(risk_status, f"Follow-up: {company_name} account"),
            "body": body_templates.get(risk_status, "Let's connect to discuss account status."),
            "tone": tone,
            "analysis_mode": "local",
        }

    def draft_outreach_message(
        self, profile: Dict, risk_result: Dict, plan: Dict
    ) -> Dict:
        if not self.llm_config.should_use_llm():
            return self._draft_outreach_local(profile, risk_result, plan)

        try:
            system_prompt = (
                "Draft a professional, customer-facing outreach email ready for human review. "
                "Tailor to the customer's communication style. Mention concrete risks but avoid "
                "over-promising. Return JSON with recipient, subject, body, and tone."
            )
            user_prompt = json.dumps(
                {
                    "client_profile": profile,
                    "risk_result": risk_result,
                    "plan": plan,
                },
                indent=2,
                default=str,
            )
            return self._call_claude_json(system_prompt, user_prompt, max_tokens=800)
        except Exception as e:
            self.logger.error(f"LLM outreach drafting failed: {e}")
            if self.llm_config.fallback_to_local:
                return self._draft_outreach_local(profile, risk_result, plan)
            raise


class CustomerHealthPlatform:
    def __init__(self, llm_config: Optional[LLMConfig] = None) -> None:
        self.scoring_engine = ChurnScoringEngine()
        self.agent = CustomerSuccessAgent(llm_config)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def analyze_account(
        self,
        profile: ClientProfile,
        signals: ClientSignals,
        include_outreach_draft: bool = True,
    ) -> Dict[str, Any]:
        self.logger.info(f"Starting comprehensive analysis for {profile.company_name}")

        risk_result = self.scoring_engine.compute_churn_risk(profile, signals)

        profile_dict = profile.to_dict()
        messages_dict = [asdict(msg) for msg in signals.messages]
        for msg in messages_dict:
            msg["sent_on"] = str(msg["sent_on"])

        sentiment_messages = self.agent.analyze_message_sentiment(messages_dict)
        plan = self.agent.explain_and_plan(profile_dict, risk_result, sentiment_messages)

        outreach = None
        if include_outreach_draft:
            outreach = self.agent.draft_outreach_message(profile_dict, risk_result, plan)

        analysis_result = {
            "timestamp": datetime.now().isoformat(),
            "account": profile.company_name,
            "risk_assessment": risk_result,
            "sentiment_analysis": sentiment_messages,
            "executive_summary": plan.get("summary"),
            "key_risks": plan.get("key_risks"),
            "priority_actions": plan.get("priority_actions"),
            "draft_outreach": outreach,
        }

        self.logger.info(
            f"Analysis complete for {profile.company_name}: "
            f"score={risk_result['score']}, status={risk_result['status']}"
        )

        return analysis_result


def create_demo_profile() -> ClientProfile:
    return ClientProfile(
        company_name="Northstar Logistics",
        business_goals=[
            "Reduce shipment delays across regional hubs",
            "Automate invoice reconciliation for multi-country billing",
            "Increase adoption of the analytics layer for executive reporting",
        ],
        key_contacts=[
            Contact(name="Jane Roberts", role="CTO", importance="high"),
            Contact(name="Mike Chen", role="Sponsor", importance="high"),
            Contact(name="Priya Nair", role="Developer", importance="normal"),
        ],
        critical_features=["Route Optimizer", "Invoice Sync", "Executive Analytics"],
        communication_style="Direct, concise written updates, prefers actionable next steps",
        open_commitments=[
            "Resolve Invoice Sync EU outage before August 15",
            "Deliver ETA accuracy remediation summary to stakeholder group",
        ],
        known_risks=[
            "Contract renewal decision in 60 days",
            "Leadership is sensitive to customer-facing disruption",
        ],
        account_tier="Enterprise",
        renewal_date="2026-09-30",
    )


def create_demo_signals() -> ClientSignals:
    tickets = [
        SupportTicket(
            "T-101",
            date(2026, 7, 20),
            date(2026, 7, 22),
            "Route Optimizer returning incorrect ETAs",
            "Route Optimizer",
            "high",
            "resolved",
            reopened_count=1,
        ),
        SupportTicket(
            "T-108",
            date(2026, 7, 29),
            None,
            "Invoice Sync failing for EU accounts",
            "Invoice Sync",
            "critical",
            "escalated",
            reopened_count=0,
        ),
        SupportTicket(
            "T-110",
            date(2026, 8, 3),
            None,
            "Minor dashboard UI glitch",
            "Dashboard",
            "low",
            "open",
            reopened_count=0,
        ),
    ]

    messages = [
        Message(
            "M-1",
            date(2026, 7, 22),
            "Jane Roberts",
            "CTO",
            "email",
            "The ETA bug cost us a key client escalation this week. We need a durable fix, not a temporary patch.",
        ),
        Message(
            "M-2",
            date(2026, 7, 30),
            "Jane Roberts",
            "CTO",
            "chat",
            "Invoice Sync is down again for our EU accounts. This is the second outage this month.",
        ),
        Message(
            "M-3",
            date(2026, 8, 4),
            "Priya Nair",
            "Developer",
            "chat",
            "Thanks for the quick response on the dashboard issue. We would still like a permanent fix to the exporter workflow.",
        ),
    ]

    usage_history = [
        UsageSnapshot("Last month", active_users=48, feature_usage_pct=71.0),
        UsageSnapshot("This month", active_users=39, feature_usage_pct=54.0),
    ]

    satisfaction_history = [
        SatisfactionScore("Last quarter", csat=82.0, nps=35),
        SatisfactionScore("This quarter", csat=61.0, nps=5),
    ]

    return ClientSignals(
        tickets=tickets,
        messages=messages,
        usage_history=usage_history,
        satisfaction_history=satisfaction_history,
    )


if __name__ == "__main__":
    try:
        platform = CustomerHealthPlatform()
        profile = create_demo_profile()
        signals = create_demo_signals()

        result = platform.analyze_account(profile, signals, include_outreach_draft=True)
        print(json.dumps(result, indent=2, default=str))

    except Exception as e:
        logger.error(f"Platform execution failed: {e}", exc_info=True)
        error_output = {
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "error_type": type(e).__name__,
        }
        print(json.dumps(error_output, indent=2))
        raise
