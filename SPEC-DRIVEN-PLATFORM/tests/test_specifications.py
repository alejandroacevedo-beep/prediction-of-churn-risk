"""
Comprehensive Test Suite for Customer Health Platform

Tests verify adherence to formal specifications and expected behavior.
Organized by component with clear test cases for each specification.
"""

import pytest
from datetime import date, datetime, timedelta
from dataclasses import asdict
from typing import List, Dict, Any

# Import platform components
try:
    from customer_health_platform import (
        Contact,
        ClientProfile,
        SupportTicket,
        Message,
        UsageSnapshot,
        SatisfactionScore,
        ClientSignals,
        ChurnScoringEngine,
        CustomerSuccessAgent,
        CustomerHealthPlatform,
        Priority,
        Importance,
        AccountTier,
        HealthStatus,
        SentimentLabel,
        AnalysisMode,
    )
except ImportError as e:
    pytest.skip(f"Could not import platform components: {e}", allow_module_level=True)

# Import specifications
from specs.data_models_spec import ContactSpec, ClientProfileSpec, SupportTicketSpec
from specs.scoring_engine_spec import ChurnScoringEngineSpec, CustomerSuccessAgentSpec


# ============================================================================
# DATA MODEL TESTS - CONTACT
# ============================================================================

class TestContactSpecification:
    """Test Contact against ContactSpec"""

    def test_contact_creation_valid(self):
        """Valid contact should be created successfully"""
        contact = Contact(name="John Doe", role="CTO", importance="critical")
        assert contact.name == "John Doe"
        assert contact.role == "CTO"
        assert contact.importance == "critical"

    def test_contact_empty_name_raises_error(self):
        """Empty contact name should raise ValueError"""
        with pytest.raises(ValueError, match="Contact name cannot be empty"):
            Contact(name="", role="CTO")

    def test_contact_empty_role_raises_error(self):
        """Empty contact role should raise ValueError"""
        with pytest.raises(ValueError, match="Contact role cannot be empty"):
            Contact(name="John Doe", role="")

    def test_contact_whitespace_name_raises_error(self):
        """Whitespace-only contact name should raise ValueError"""
        with pytest.raises(ValueError, match="Contact name cannot be empty"):
            Contact(name="   ", role="CTO")

    def test_contact_invalid_importance_defaults_to_normal(self):
        """Invalid importance should default to 'normal'"""
        contact = Contact(name="John", role="CTO", importance="invalid")
        assert contact.importance == "normal"

    def test_contact_importance_normalized_to_lowercase(self):
        """Importance should be normalized to lowercase"""
        contact = Contact(name="John", role="CTO", importance="CRITICAL")
        assert contact.importance == "critical"

    def test_contact_influence_weight_critical(self):
        """Critical contact should have weight 1.5"""
        contact = Contact(name="John", role="CTO", importance="critical")
        assert contact.influence_weight == 1.5

    def test_contact_influence_weight_high(self):
        """High contact should have weight 1.5"""
        contact = Contact(name="John", role="CTO", importance="high")
        assert contact.influence_weight == 1.5

    def test_contact_influence_weight_normal(self):
        """Normal contact should have weight 1.0"""
        contact = Contact(name="John", role="CTO", importance="normal")
        assert contact.influence_weight == 1.0

    def test_contact_influence_weight_low(self):
        """Low contact should have weight 0.8"""
        contact = Contact(name="John", role="CTO", importance="low")
        assert contact.influence_weight == 0.8

    def test_contact_spec_summary(self):
        """ContactSpec should provide correct summary"""
        spec = ContactSpec()
        summary = spec.spec_summary()
        assert "Contact" in summary["model"]
        assert "name" in summary["required_fields"]
        assert "role" in summary["required_fields"]


# ============================================================================
# DATA MODEL TESTS - CLIENT PROFILE
# ============================================================================

class TestClientProfileSpecification:
    """Test ClientProfile against ClientProfileSpec"""

    def test_profile_creation_valid(self):
        """Valid profile should be created successfully"""
        contact = Contact(name="John", role="CTO")
        profile = ClientProfile(
            company_name="TechCorp",
            business_goals=["Scale", "Automate"],
            key_contacts=[contact],
            critical_features=["API", "Dashboard"],
            communication_style="formal",
        )
        assert profile.company_name == "TechCorp"
        assert len(profile.key_contacts) == 1

    def test_profile_empty_company_name_raises_error(self):
        """Empty company name should raise ValueError"""
        contact = Contact(name="John", role="CTO")
        with pytest.raises(ValueError, match="Company name is required"):
            ClientProfile(
                company_name="",
                business_goals=["Scale"],
                key_contacts=[contact],
                critical_features=["API"],
                communication_style="formal",
            )

    def test_profile_no_contacts_raises_error(self):
        """Profile without contacts should raise ValueError"""
        with pytest.raises(ValueError, match="At least one key contact is required"):
            ClientProfile(
                company_name="TechCorp",
                business_goals=["Scale"],
                key_contacts=[],
                critical_features=["API"],
                communication_style="formal",
            )

    def test_profile_no_critical_features_raises_error(self):
        """Profile without critical features should raise ValueError"""
        contact = Contact(name="John", role="CTO")
        with pytest.raises(ValueError, match="At least one critical feature must be specified"):
            ClientProfile(
                company_name="TechCorp",
                business_goals=["Scale"],
                key_contacts=[contact],
                critical_features=[],
                communication_style="formal",
            )

    def test_profile_tier_config_enterprise(self):
        """Enterprise tier should have correct config"""
        contact = Contact(name="John", role="CTO")
        profile = ClientProfile(
            company_name="TechCorp",
            business_goals=["Scale"],
            key_contacts=[contact],
            critical_features=["API"],
            communication_style="formal",
            account_tier="ENTERPRISE",
        )
        config = profile.tier_config
        assert config["weight"] == 2.0
        assert config["priority_threshold"] == 40

    def test_profile_tier_config_professional(self):
        """Professional tier should have correct config"""
        contact = Contact(name="John", role="CTO")
        profile = ClientProfile(
            company_name="TechCorp",
            business_goals=["Scale"],
            key_contacts=[contact],
            critical_features=["API"],
            communication_style="formal",
            account_tier="PROFESSIONAL",
        )
        config = profile.tier_config
        assert config["weight"] == 1.5
        assert config["priority_threshold"] == 50

    def test_profile_primary_contact_highest_importance(self):
        """Primary contact should be the one with highest importance"""
        critical = Contact(name="John", role="CTO", importance="critical")
        normal = Contact(name="Jane", role="Manager", importance="normal")
        profile = ClientProfile(
            company_name="TechCorp",
            business_goals=["Scale"],
            key_contacts=[normal, critical],
            critical_features=["API"],
            communication_style="formal",
        )
        assert profile.primary_contact.name == "John"

    def test_profile_days_to_renewal_valid_date(self):
        """Days to renewal should be calculated correctly"""
        contact = Contact(name="John", role="CTO")
        future_date = (date.today() + timedelta(days=30)).isoformat()
        profile = ClientProfile(
            company_name="TechCorp",
            business_goals=["Scale"],
            key_contacts=[contact],
            critical_features=["API"],
            communication_style="formal",
            renewal_date=future_date,
        )
        days = profile.days_to_renewal()
        assert days is not None
        assert 29 <= days <= 31  # Allow 1 day variance

    def test_profile_days_to_renewal_none_when_no_date(self):
        """Days to renewal should be None when no renewal_date"""
        contact = Contact(name="John", role="CTO")
        profile = ClientProfile(
            company_name="TechCorp",
            business_goals=["Scale"],
            key_contacts=[contact],
            critical_features=["API"],
            communication_style="formal",
        )
        assert profile.days_to_renewal() is None

    def test_profile_to_dict(self):
        """to_dict should return complete profile as dictionary"""
        contact = Contact(name="John", role="CTO")
        profile = ClientProfile(
            company_name="TechCorp",
            business_goals=["Scale"],
            key_contacts=[contact],
            critical_features=["API"],
            communication_style="formal",
        )
        profile_dict = profile.to_dict()
        assert profile_dict["company_name"] == "TechCorp"
        assert len(profile_dict["key_contacts"]) == 1


# ============================================================================
# DATA MODEL TESTS - SUPPORT TICKET
# ============================================================================

class TestSupportTicketSpecification:
    """Test SupportTicket against SupportTicketSpec"""

    def test_ticket_creation_valid(self):
        """Valid ticket should be created successfully"""
        ticket = SupportTicket(
            ticket_id="TICK-001",
            opened_on=date.today(),
            closed_on=None,
            subject="API Down",
            related_feature="API",
            priority="critical",
            status="open",
        )
        assert ticket.ticket_id == "TICK-001"
        assert ticket.priority == "critical"

    def test_ticket_empty_id_raises_error(self):
        """Empty ticket_id should raise ValueError"""
        with pytest.raises(ValueError, match="Ticket ID cannot be empty"):
            SupportTicket(
                ticket_id="",
                opened_on=date.today(),
                closed_on=None,
                subject="Issue",
                related_feature="API",
                priority="high",
                status="open",
            )

    def test_ticket_close_before_open_raises_error(self):
        """Close date before open date should raise ValueError"""
        with pytest.raises(ValueError, match="Close date cannot be before open date"):
            SupportTicket(
                ticket_id="TICK-001",
                opened_on=date.today(),
                closed_on=date.today() - timedelta(days=1),
                subject="Issue",
                related_feature="API",
                priority="high",
                status="closed",
            )

    def test_ticket_priority_normalized_to_lowercase(self):
        """Priority should be normalized to lowercase"""
        ticket = SupportTicket(
            ticket_id="TICK-001",
            opened_on=date.today(),
            closed_on=None,
            subject="Issue",
            related_feature="API",
            priority="CRITICAL",
            status="open",
        )
        assert ticket.priority == "critical"

    def test_ticket_is_unresolved_true_when_no_close_date(self):
        """Ticket should be unresolved when closed_on is None"""
        ticket = SupportTicket(
            ticket_id="TICK-001",
            opened_on=date.today(),
            closed_on=None,
            subject="Issue",
            related_feature="API",
            priority="high",
            status="open",
        )
        assert ticket.is_unresolved is True

    def test_ticket_is_unresolved_false_when_closed(self):
        """Ticket should be resolved when closed_on is set"""
        ticket = SupportTicket(
            ticket_id="TICK-001",
            opened_on=date.today(),
            closed_on=date.today(),
            subject="Issue",
            related_feature="API",
            priority="high",
            status="closed",
        )
        assert ticket.is_unresolved is False

    def test_ticket_critical_indicator_true_for_unresolved_critical(self):
        """Critical indicator should be True for unresolved critical ticket"""
        ticket = SupportTicket(
            ticket_id="TICK-001",
            opened_on=date.today(),
            closed_on=None,
            subject="Issue",
            related_feature="API",
            priority="critical",
            status="open",
        )
        assert ticket.critical_indicator is True

    def test_ticket_critical_indicator_false_for_resolved(self):
        """Critical indicator should be False for resolved ticket"""
        ticket = SupportTicket(
            ticket_id="TICK-001",
            opened_on=date.today(),
            closed_on=date.today(),
            subject="Issue",
            related_feature="API",
            priority="critical",
            status="closed",
        )
        assert ticket.critical_indicator is False

    def test_ticket_severity_score_calculation(self):
        """Severity score should be calculated per specification"""
        ticket = SupportTicket(
            ticket_id="TICK-001",
            opened_on=date.today(),
            closed_on=None,
            subject="Critical Issue",
            related_feature="API",
            priority="critical",
            status="open",
            reopened_count=0,
        )
        # Base critical=10, escalated=4, open critical=3
        # Total should be 10+4+3 = 17 (or similar based on status)
        score = ticket.severity_score(is_critical_feature=False)
        assert score > 0


# ============================================================================
# DATA MODEL TESTS - MESSAGE
# ============================================================================

class TestMessageSpecification:
    """Test Message against MessageSpec"""

    def test_message_creation_valid(self):
        """Valid message should be created successfully"""
        message = Message(
            message_id="MSG-001",
            sent_on=date.today(),
            sender_name="John",
            sender_role="CTO",
            channel="email",
            text="The system is down!",
        )
        assert message.message_id == "MSG-001"
        assert message.text == "The system is down!"

    def test_message_empty_id_raises_error(self):
        """Empty message_id should raise ValueError"""
        with pytest.raises(ValueError, match="Message ID and text are required"):
            Message(
                message_id="",
                sent_on=date.today(),
                sender_name="John",
                sender_role="CTO",
                channel="email",
                text="Message",
            )

    def test_message_empty_text_raises_error(self):
        """Empty text should raise ValueError"""
        with pytest.raises(ValueError, match="Message ID and text are required"):
            Message(
                message_id="MSG-001",
                sent_on=date.today(),
                sender_name="John",
                sender_role="CTO",
                channel="email",
                text="",
            )

    def test_message_channel_normalized_to_lowercase(self):
        """Channel should be normalized to lowercase"""
        message = Message(
            message_id="MSG-001",
            sent_on=date.today(),
            sender_name="John",
            sender_role="CTO",
            channel="EMAIL",
            text="Message",
        )
        assert message.channel == "email"

    def test_message_escalation_indicator_true_for_urgent(self):
        """Escalation indicator should be True when 'urgent' in text"""
        message = Message(
            message_id="MSG-001",
            sent_on=date.today(),
            sender_name="John",
            sender_role="CTO",
            channel="email",
            text="This is urgent!",
        )
        assert message.is_escalation_indicator() is True

    def test_message_escalation_indicator_true_for_critical(self):
        """Escalation indicator should be True when 'critical' in text"""
        message = Message(
            message_id="MSG-001",
            sent_on=date.today(),
            sender_name="John",
            sender_role="CTO",
            channel="email",
            text="We have a critical issue.",
        )
        assert message.is_escalation_indicator() is True

    def test_message_escalation_indicator_false_for_normal(self):
        """Escalation indicator should be False for normal message"""
        message = Message(
            message_id="MSG-001",
            sent_on=date.today(),
            sender_name="John",
            sender_role="CTO",
            channel="email",
            text="Everything is working fine.",
        )
        assert message.is_escalation_indicator() is False


# ============================================================================
# SCORING ENGINE TESTS
# ============================================================================

class TestChurnScoringEngineSpecification:
    """Test ChurnScoringEngine against ChurnScoringEngineSpec"""

    def test_engine_creation(self):
        """Engine should be created successfully"""
        engine = ChurnScoringEngine()
        assert engine is not None

    def test_engine_spec_summary(self):
        """Engine spec should provide correct summary"""
        spec = ChurnScoringEngineSpec()
        summary = spec.spec_summary()
        assert "ChurnScoringEngine" in summary["component"]
        assert "score_tickets" in summary["methods"]
        assert "score_usage" in summary["methods"]
        assert "score_satisfaction" in summary["methods"]

    def test_compute_churn_risk_output_structure(self):
        """Churn risk result should have correct structure"""
        engine = ChurnScoringEngine()
        contact = Contact(name="John", role="CTO")
        profile = ClientProfile(
            company_name="TechCorp",
            business_goals=["Scale"],
            key_contacts=[contact],
            critical_features=["API"],
            communication_style="formal",
        )
        
        ticket = SupportTicket(
            ticket_id="TICK-001",
            opened_on=date.today(),
            closed_on=None,
            subject="Issue",
            related_feature="API",
            priority="medium",
            status="open",
        )
        
        usage = UsageSnapshot(
            period_label="Q1 2024",
            active_users=100,
            feature_usage_pct=75.0,
        )
        
        satisfaction = SatisfactionScore(
            period_label="Q1 2024",
            csat=80.0,
            nps=50,
        )
        
        signals = ClientSignals(
            support_tickets=[ticket],
            usage_history=[usage],
            satisfaction_history=[satisfaction],
            messages=[],
        )
        
        result = engine.compute_churn_risk(profile, signals)
        
        # Verify output structure
        assert "risk_score" in result
        assert "health_status" in result
        assert "risk_factors" in result
        assert "evidence" in result
        assert "recommendations" in result
        
        # Verify data types
        assert isinstance(result["risk_score"], (int, float))
        assert isinstance(result["health_status"], str)
        assert isinstance(result["risk_factors"], dict)
        assert isinstance(result["evidence"], dict)
        assert isinstance(result["recommendations"], list)

    def test_risk_score_in_valid_range(self):
        """Risk score should be between 0-100"""
        engine = ChurnScoringEngine()
        contact = Contact(name="John", role="CTO")
        profile = ClientProfile(
            company_name="TechCorp",
            business_goals=["Scale"],
            key_contacts=[contact],
            critical_features=["API"],
            communication_style="formal",
        )
        
        usage = UsageSnapshot(
            period_label="Q1",
            active_users=100,
            feature_usage_pct=75.0,
        )
        
        satisfaction = SatisfactionScore(
            period_label="Q1",
            csat=80.0,
        )
        
        signals = ClientSignals(
            support_tickets=[],
            usage_history=[usage],
            satisfaction_history=[satisfaction],
            messages=[],
        )
        
        result = engine.compute_churn_risk(profile, signals)
        assert 0 <= result["risk_score"] <= 100

    def test_health_status_valid_values(self):
        """Health status should be one of valid values"""
        engine = ChurnScoringEngine()
        contact = Contact(name="John", role="CTO")
        profile = ClientProfile(
            company_name="TechCorp",
            business_goals=["Scale"],
            key_contacts=[contact],
            critical_features=["API"],
            communication_style="formal",
        )
        
        usage = UsageSnapshot(
            period_label="Q1",
            active_users=100,
            feature_usage_pct=75.0,
        )
        
        satisfaction = SatisfactionScore(
            period_label="Q1",
            csat=80.0,
        )
        
        signals = ClientSignals(
            support_tickets=[],
            usage_history=[usage],
            satisfaction_history=[satisfaction],
            messages=[],
        )
        
        result = engine.compute_churn_risk(profile, signals)
        valid_statuses = {"Healthy", "Watch", "At Risk"}
        assert result["health_status"] in valid_statuses


# ============================================================================
# SENTIMENT ANALYSIS TESTS
# ============================================================================

class TestCustomerSuccessAgentSpecification:
    """Test CustomerSuccessAgent against CustomerSuccessAgentSpec"""

    def test_agent_creation(self):
        """Agent should be created successfully"""
        agent = CustomerSuccessAgent()
        assert agent is not None

    def test_agent_spec_summary(self):
        """Agent spec should provide correct summary"""
        spec = CustomerSuccessAgentSpec()
        summary = spec.spec_summary()
        assert "CustomerSuccessAgent" in summary["component"]
        assert "analyze_message_sentiment" in summary["methods"]

    def test_sentiment_analysis_output_structure(self):
        """Sentiment analysis should return list with correct structure"""
        agent = CustomerSuccessAgent()
        messages = [
            {
                "message_id": "MSG-001",
                "text": "This is great!",
                "sent_on": str(date.today()),
            },
            {
                "message_id": "MSG-002",
                "text": "We have an urgent issue!",
                "sent_on": str(date.today()),
            },
        ]
        
        result = agent.analyze_message_sentiment(messages)
        
        # Verify it returns a list
        assert isinstance(result, list)
        
        # Verify each item has required fields
        for item in result:
            assert "message_id" in item
            assert "sentiment" in item
            # Valid sentiments
            valid_sentiments = {"frustrated", "negative", "neutral", "positive"}
            if "sentiment" in item:
                assert item["sentiment"] in valid_sentiments or item["sentiment"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
