"""
Data Models Specification

Defines the formal specifications for all data model classes in the Customer Health Platform.
These specifications document expected behavior, constraints, and contracts.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Protocol
from abc import ABC, abstractmethod
from datetime import date


class DataModelSpec(ABC):
    """Base specification for all data models"""

    @abstractmethod
    def validate(self) -> bool:
        """Validate the model against its specification"""
        pass

    @abstractmethod
    def spec_summary(self) -> Dict[str, Any]:
        """Return specification summary"""
        pass


# ============================================================================
# CONTACT SPECIFICATION
# ============================================================================

class ContactSpec(DataModelSpec):
    """
    Specification for Contact data model
    
    Requirements:
    - name: Non-empty string, required
    - role: Non-empty string, required
    - importance: One of {critical, high, normal, low}, defaults to 'normal'
    - influence_weight: Computed property based on importance level
    
    Constraints:
    - Cannot create Contact with empty/whitespace name or role
    - importance values are normalized to lowercase
    - Invalid importance values default to 'normal'
    
    Expected Behavior:
    - influence_weight returns: critical/high=1.5, normal=1.0, low=0.8
    """

    IMPORTANCE_WEIGHTS = {
        "critical": 1.5,
        "high": 1.5,
        "normal": 1.0,
        "low": 0.8,
    }
    
    VALID_IMPORTANCE = {"critical", "high", "normal", "low"}

    @dataclass
    class Blueprint:
        name: str
        role: str
        importance: str = "normal"

    def validate(self) -> bool:
        return True

    def spec_summary(self) -> Dict[str, Any]:
        return {
            "model": "Contact",
            "required_fields": ["name", "role"],
            "optional_fields": ["importance"],
            "constraints": {
                "name": "Non-empty string",
                "role": "Non-empty string",
                "importance": f"One of {self.VALID_IMPORTANCE}, defaults to 'normal'",
            },
            "computed_properties": {
                "influence_weight": "Based on importance level"
            },
        }


# ============================================================================
# CLIENT PROFILE SPECIFICATION
# ============================================================================

class ClientProfileSpec(DataModelSpec):
    """
    Specification for ClientProfile data model
    
    Requirements:
    - company_name: Non-empty string, required
    - business_goals: List of strings, required
    - key_contacts: List of Contact objects, at least 1 required
    - critical_features: List of strings, at least 1 required
    - communication_style: String, required
    - account_tier: One of {ENTERPRISE, PROFESSIONAL, STANDARD}, defaults to STANDARD
    - renewal_date: ISO format date string, optional
    - open_commitments: List of strings, defaults to empty
    - known_risks: List of strings, defaults to empty
    
    Tier Configuration:
    - ENTERPRISE: weight=2.0, priority_threshold=40
    - PROFESSIONAL: weight=1.5, priority_threshold=50
    - STANDARD: weight=1.0, priority_threshold=65
    
    Expected Behavior:
    - tier_config returns appropriate configuration for account tier
    - primary_contact returns contact with highest importance
    - days_to_renewal calculates days until renewal date
    - get_contact_weight returns influence weight for named contact
    - get_feature_priority returns 1.5 for critical features, 1.0 otherwise
    - to_dict returns complete profile as dictionary
    """

    VALID_TIERS = {"ENTERPRISE", "PROFESSIONAL", "STANDARD"}
    
    TIER_CONFIGS = {
        "ENTERPRISE": {"weight": 2.0, "priority_threshold": 40},
        "PROFESSIONAL": {"weight": 1.5, "priority_threshold": 50},
        "STANDARD": {"weight": 1.0, "priority_threshold": 65},
    }

    def validate(self) -> bool:
        return True

    def spec_summary(self) -> Dict[str, Any]:
        return {
            "model": "ClientProfile",
            "required_fields": [
                "company_name",
                "business_goals",
                "key_contacts",
                "critical_features",
                "communication_style",
            ],
            "optional_fields": [
                "account_tier",
                "renewal_date",
                "open_commitments",
                "known_risks",
            ],
            "constraints": {
                "company_name": "Non-empty string",
                "key_contacts": "At least 1 contact required",
                "critical_features": "At least 1 feature required",
                "account_tier": f"One of {self.VALID_TIERS}",
            },
            "tier_configurations": self.TIER_CONFIGS,
        }


# ============================================================================
# SUPPORT TICKET SPECIFICATION
# ============================================================================

class SupportTicketSpec(DataModelSpec):
    """
    Specification for SupportTicket data model
    
    Requirements:
    - ticket_id: Non-empty string, unique identifier
    - opened_on: date object, when ticket was opened
    - closed_on: Optional date object, when ticket was closed
    - subject: String description of issue
    - related_feature: Feature affected by the issue
    - priority: One of {critical, high, medium, low}
    - status: String status, normalized to lowercase
    - reopened_count: Integer count of reopenings, defaults to 0
    
    Constraints:
    - closed_on cannot be before opened_on
    - priority and status are normalized to lowercase
    
    Severity Scoring:
    - Base priority scores: critical=10.0, high=6.0, medium=3.0, low=1.0
    - Escalated status adds 4.0 points
    - Unresolved critical/high adds 3.0 points
    - Each reopening adds 2.0 points
    - Critical features multiply severity by 1.5
    
    Computed Properties:
    - is_unresolved: Returns True if closed_on is None
    - age_days: Days between opened_on and closed_on (or today)
    - critical_indicator: True if priority is critical/high AND unresolved
    """

    PRIORITY_SCORES = {
        "critical": 10.0,
        "high": 6.0,
        "medium": 3.0,
        "low": 1.0,
    }
    
    VALID_PRIORITIES = set(PRIORITY_SCORES.keys())

    def validate(self) -> bool:
        return True

    def spec_summary(self) -> Dict[str, Any]:
        return {
            "model": "SupportTicket",
            "required_fields": [
                "ticket_id",
                "opened_on",
                "subject",
                "related_feature",
                "priority",
                "status",
            ],
            "optional_fields": ["closed_on", "reopened_count"],
            "constraints": {
                "ticket_id": "Non-empty string",
                "closed_on": "Must be >= opened_on",
                "priority": f"One of {self.VALID_PRIORITIES}",
            },
            "severity_calculation": {
                "base_scores": self.PRIORITY_SCORES,
                "escalated_bonus": 4.0,
                "unresolved_bonus": 3.0,
                "reopened_multiplier": 2.0,
                "critical_feature_multiplier": 1.5,
            },
        }


# ============================================================================
# MESSAGE SPECIFICATION
# ============================================================================

class MessageSpec(DataModelSpec):
    """
    Specification for Message data model
    
    Requirements:
    - message_id: Non-empty string, unique identifier
    - sent_on: date object, when message was sent
    - sender_name: String, name of sender
    - sender_role: String, role of sender
    - channel: String channel identifier, normalized to lowercase
    - text: Non-empty string, message content
    
    Constraints:
    - Both message_id and text are required (cannot be empty)
    - channel is normalized to lowercase
    
    Escalation Detection:
    - Keywords: {urgent, critical, down, outage, emergency, failed}
    - is_escalation_indicator() returns True if any keyword found in text
    
    Computed Properties:
    - text_length: Length of message text
    """

    ESCALATION_KEYWORDS = {"urgent", "critical", "down", "outage", "emergency", "failed"}

    def validate(self) -> bool:
        return True

    def spec_summary(self) -> Dict[str, Any]:
        return {
            "model": "Message",
            "required_fields": [
                "message_id",
                "sent_on",
                "sender_name",
                "sender_role",
                "channel",
                "text",
            ],
            "constraints": {
                "message_id": "Non-empty string",
                "text": "Non-empty string",
                "channel": "Normalized to lowercase",
            },
            "escalation_keywords": self.ESCALATION_KEYWORDS,
        }


# ============================================================================
# USAGE SNAPSHOT SPECIFICATION
# ============================================================================

class UsageSnapshotSpec(DataModelSpec):
    """
    Specification for UsageSnapshot data model
    
    Requirements:
    - period_label: String describing time period
    - active_users: Non-negative integer, number of active users
    - feature_usage_pct: Float between 0-100, usage percentage
    
    Constraints:
    - active_users >= 0
    - 0 <= feature_usage_pct <= 100
    
    Adoption Health Levels:
    - >= 80%: excellent
    - >= 60%: healthy
    - >= 40%: concerning
    - < 40%: critical
    
    Computed Properties:
    - adoption_health: Health status based on usage percentage
    - change_from(previous): Returns dict with:
        - user_change: absolute change in users
        - user_change_pct: percentage change in users
        - usage_change: absolute change in usage percentage
    """

    HEALTH_THRESHOLDS = {
        "excellent": 80,
        "healthy": 60,
        "concerning": 40,
        "critical": 0,
    }

    def validate(self) -> bool:
        return True

    def spec_summary(self) -> Dict[str, Any]:
        return {
            "model": "UsageSnapshot",
            "required_fields": [
                "period_label",
                "active_users",
                "feature_usage_pct",
            ],
            "constraints": {
                "active_users": ">= 0",
                "feature_usage_pct": "0-100",
            },
            "adoption_health_thresholds": self.HEALTH_THRESHOLDS,
        }


# ============================================================================
# SATISFACTION SCORE SPECIFICATION
# ============================================================================

class SatisfactionScoreSpec(DataModelSpec):
    """
    Specification for SatisfactionScore data model
    
    Requirements:
    - period_label: String describing time period
    - csat: Optional float between 0-100 (Customer Satisfaction)
    - nps: Optional integer between -100-100 (Net Promoter Score)
    
    Constraints:
    - 0 <= csat <= 100 (if provided)
    - -100 <= nps <= 100 (if provided)
    - At least one metric must be provided
    
    Computed Properties:
    - overall_sentiment: Averages available metrics to determine sentiment level
    """

    def validate(self) -> bool:
        return True

    def spec_summary(self) -> Dict[str, Any]:
        return {
            "model": "SatisfactionScore",
            "required_fields": ["period_label"],
            "optional_fields": ["csat", "nps"],
            "constraints": {
                "csat": "0-100 (optional)",
                "nps": "-100 to 100 (optional)",
            },
            "notes": "At least one of csat or nps should be provided",
        }


# ============================================================================
# CLIENT SIGNALS SPECIFICATION
# ============================================================================

class ClientSignalsSpec(DataModelSpec):
    """
    Specification for ClientSignals data model
    
    Aggregates all customer signals for comprehensive analysis:
    - support_tickets: List[SupportTicket], required
    - usage_history: List[UsageSnapshot], required
    - satisfaction_history: List[SatisfactionScore], required
    - messages: List[Message], optional
    
    Expected Behavior:
    - Represents complete customer health snapshot
    - Used as input to ChurnScoringEngine and CustomerSuccessAgent
    - All collections must be valid and non-empty (except messages)
    """

    def validate(self) -> bool:
        return True

    def spec_summary(self) -> Dict[str, Any]:
        return {
            "model": "ClientSignals",
            "required_fields": [
                "support_tickets",
                "usage_history",
                "satisfaction_history",
            ],
            "optional_fields": ["messages"],
            "constraints": {
                "support_tickets": "Non-empty list of SupportTicket objects",
                "usage_history": "Non-empty list of UsageSnapshot objects",
                "satisfaction_history": "Non-empty list of SatisfactionScore objects",
                "messages": "List of Message objects (can be empty)",
            },
        }
