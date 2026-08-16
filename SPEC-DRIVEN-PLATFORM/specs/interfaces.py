"""
Platform Interfaces and Protocols

Defines the formal contracts and interfaces between major components.
These protocols ensure loose coupling and clear boundaries.
"""

from typing import Protocol, List, Dict, Any, Optional, runtime_checkable
from datetime import date
from dataclasses import dataclass


# ============================================================================
# DATA MODEL PROTOCOLS
# ============================================================================

@runtime_checkable
class DataModel(Protocol):
    """Base protocol for all data models"""

    def __post_init__(self) -> None:
        """Validate data during initialization"""
        ...


@runtime_checkable
class Scoreable(Protocol):
    """Protocol for objects that can be scored"""

    def severity_score(self, is_critical_feature: bool = False) -> float:
        """Calculate severity score"""
        ...

    @property
    def critical_indicator(self) -> bool:
        """Check if this represents a critical issue"""
        ...


@runtime_checkable
class SentimentBearing(Protocol):
    """Protocol for objects that can have sentiment analysis"""

    @property
    def text(self) -> str:
        """Get textual content for sentiment analysis"""
        ...

    def is_escalation_indicator(self) -> bool:
        """Check if this indicates escalation"""
        ...


# ============================================================================
# COMPONENT PROTOCOLS
# ============================================================================

@runtime_checkable
class ScoringEngine(Protocol):
    """Protocol for risk scoring engines"""

    def score_tickets(
        self,
        profile: Any,
        tickets: List[Any],
    ) -> float:
        """
        Score support tickets for risk.
        
        Args:
            profile: ClientProfile with critical features and tier info
            tickets: List of SupportTicket objects
            
        Returns:
            float: Risk score 0-100
        """
        ...

    def score_usage(self, usage_history: List[Any]) -> float:
        """
        Score usage adoption for risk.
        
        Args:
            usage_history: List of UsageSnapshot objects
            
        Returns:
            float: Risk score 0-100
        """
        ...

    def score_satisfaction(self, satisfaction_history: List[Any]) -> float:
        """
        Score satisfaction deterioration for risk.
        
        Args:
            satisfaction_history: List of SatisfactionScore objects
            
        Returns:
            float: Risk score 0-100
        """
        ...

    def compute_churn_risk(
        self,
        profile: Any,
        signals: Any,
    ) -> Dict[str, Any]:
        """
        Compute comprehensive churn risk.
        
        Args:
            profile: ClientProfile with account information
            signals: ClientSignals with support, usage, satisfaction data
            
        Returns:
            Dict with risk_score, health_status, risk_factors, evidence, recommendations
            
        Contract:
            {
                "risk_score": int (0-100),
                "health_status": "Healthy" | "Watch" | "At Risk",
                "risk_factors": {
                    "support_risk_score": float,
                    "usage_risk_score": float,
                    "satisfaction_risk_score": float,
                },
                "evidence": {
                    "support_analysis": str,
                    "usage_analysis": str,
                    "satisfaction_analysis": str,
                    "renewal_urgency": str,
                },
                "recommendations": List[str],
            }
        """
        ...


@runtime_checkable
class SentimentAnalyzer(Protocol):
    """Protocol for sentiment analysis engines"""

    def analyze_message_sentiment(
        self,
        messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Analyze sentiment of customer messages.
        
        Args:
            messages: List of message dicts with text content
            
        Returns:
            List of sentiment analysis dicts with:
            {
                "message_id": str,
                "sentiment": "frustrated" | "negative" | "neutral" | "positive",
                "confidence": float (0-1),
                "escalation_indicator": bool,
                "summary": str,
            }
        """
        ...


@runtime_checkable
class SuccessPlanner(Protocol):
    """Protocol for customer success planning"""

    def explain_and_plan(
        self,
        profile: Dict[str, Any],
        risk_result: Dict[str, Any],
        sentiment_messages: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Generate executive summary and action plan.
        
        Args:
            profile: Client profile dict
            risk_result: Churn risk assessment result
            sentiment_messages: List of sentiment-analyzed messages
            
        Returns:
            Dict with:
            {
                "summary": str,
                "key_risks": List[str],
                "priority_actions": List[str],
                "urgency": "critical" | "high" | "medium" | "low",
            }
        """
        ...

    def draft_outreach_message(
        self,
        profile: Dict[str, Any],
        risk_result: Dict[str, Any],
        plan: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Draft customer outreach message.
        
        Args:
            profile: Client profile dict
            risk_result: Churn risk assessment result
            plan: Success plan from explain_and_plan
            
        Returns:
            Dict with:
            {
                "subject": str,
                "greeting": str,
                "opening": str,
                "main_body": str,
                "next_steps": str,
                "signature": str,
            }
        """
        ...


# ============================================================================
# ORCHESTRATION PROTOCOLS
# ============================================================================

@runtime_checkable
class HealthAnalyzer(Protocol):
    """Protocol for comprehensive health analysis"""

    def analyze_account(
        self,
        profile: Any,
        signals: Any,
        include_outreach: bool = True,
    ) -> Dict[str, Any]:
        """
        Perform comprehensive customer health analysis.
        
        Args:
            profile: ClientProfile with account information
            signals: ClientSignals with customer data
            include_outreach: Whether to generate outreach draft
            
        Returns:
            Complete analysis dict with:
            {
                "risk_assessment": {
                    "risk_score": int,
                    "health_status": str,
                    "risk_factors": Dict,
                    "evidence": Dict,
                    "recommendations": List[str],
                },
                "sentiment_analysis": {
                    "messages": List[Dict],
                    "overall_sentiment": str,
                },
                "success_plan": {
                    "summary": str,
                    "key_risks": List[str],
                    "priority_actions": List[str],
                    "urgency": str,
                },
                "outreach_draft": Dict (optional),
            }
        """
        ...


# ============================================================================
# VALIDATION PROTOCOLS
# ============================================================================

@runtime_checkable
class Validatable(Protocol):
    """Protocol for validatable objects"""

    def validate(self) -> bool:
        """Validate object state"""
        ...

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        ...


# ============================================================================
# CONFIGURATION PROTOCOLS
# ============================================================================

@runtime_checkable
class Configurable(Protocol):
    """Protocol for configurable components"""

    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        ...

    def validate_config(self) -> bool:
        """Validate configuration"""
        ...


# ============================================================================
# INTERFACE DEFINITIONS
# ============================================================================

class PlatformInterface:
    """
    Main platform interface definition.
    
    This interface documents the primary entry points and expected
    usage patterns for the Customer Health Platform.
    """

    @staticmethod
    def analyze_customer_health(
        profile: "ClientProfile",
        signals: "ClientSignals",
        analysis_mode: str = "comprehensive",
    ) -> Dict[str, Any]:
        """
        Primary entry point for customer health analysis.
        
        Args:
            profile: Complete customer profile (ClientProfile)
            signals: Customer signals (ClientSignals)
            analysis_mode: "comprehensive" | "risk_only" | "sentiment_only"
            
        Returns:
            Complete analysis results
        """
        raise NotImplementedError

    @staticmethod
    def get_churn_risk(
        profile: "ClientProfile",
        signals: "ClientSignals",
    ) -> Dict[str, Any]:
        """
        Get churn risk assessment only.
        
        Args:
            profile: Customer profile
            signals: Customer signals
            
        Returns:
            Risk assessment dict
        """
        raise NotImplementedError

    @staticmethod
    def analyze_sentiment(
        messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Analyze sentiment of customer messages.
        
        Args:
            messages: List of message dicts
            
        Returns:
            Sentiment analysis results
        """
        raise NotImplementedError

    @staticmethod
    def generate_success_plan(
        profile: "ClientProfile",
        risk_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate customer success plan.
        
        Args:
            profile: Customer profile
            risk_result: Risk assessment result
            
        Returns:
            Success plan dict
        """
        raise NotImplementedError


class DataValidationInterface:
    """
    Interface for data validation operations.
    
    All data models should implement validation against
    their formal specifications.
    """

    @staticmethod
    def validate_contact(contact: "Contact") -> bool:
        """Validate Contact specification"""
        raise NotImplementedError

    @staticmethod
    def validate_profile(profile: "ClientProfile") -> bool:
        """Validate ClientProfile specification"""
        raise NotImplementedError

    @staticmethod
    def validate_ticket(ticket: "SupportTicket") -> bool:
        """Validate SupportTicket specification"""
        raise NotImplementedError

    @staticmethod
    def validate_signals(signals: "ClientSignals") -> bool:
        """Validate ClientSignals specification"""
        raise NotImplementedError


# ============================================================================
# CONTRACT DEFINITIONS
# ============================================================================

@dataclass
class AnalysisContract:
    """
    Formal contract for analysis operations.
    
    Guarantees:
    - Input validation before processing
    - Deterministic output format
    - Evidence backing all conclusions
    - Tier-appropriate recommendations
    - Graceful error handling with fallbacks
    """

    risk_score: int  # 0-100
    health_status: str  # "Healthy" | "Watch" | "At Risk"
    risk_factors: Dict[str, float]
    evidence: Dict[str, str]
    recommendations: List[str]
    timestamp: Optional[str] = None

    def validate(self) -> bool:
        """Validate contract compliance"""
        # Risk score must be 0-100
        if not 0 <= self.risk_score <= 100:
            return False
        
        # Health status must be valid
        valid_statuses = {"Healthy", "Watch", "At Risk"}
        if self.health_status not in valid_statuses:
            return False
        
        # All risk factors must be 0-100
        if not all(0 <= score <= 100 for score in self.risk_factors.values()):
            return False
        
        # Must have evidence
        if not self.evidence:
            return False
        
        # Must have recommendations
        if not self.recommendations:
            return False
        
        return True


@dataclass
class SentimentContract:
    """
    Formal contract for sentiment analysis results.
    
    Guarantees:
    - Valid sentiment label from fixed set
    - Confidence score between 0-1
    - Escalation indicator boolean
    - Text-based evidence for conclusion
    """

    message_id: str
    sentiment: str  # "frustrated" | "negative" | "neutral" | "positive"
    confidence: float  # 0-1
    escalation_indicator: bool
    summary: str

    def validate(self) -> bool:
        """Validate contract compliance"""
        # Sentiment must be valid
        valid_sentiments = {"frustrated", "negative", "neutral", "positive"}
        if self.sentiment not in valid_sentiments:
            return False
        
        # Confidence must be 0-1
        if not 0 <= self.confidence <= 1:
            return False
        
        # Must have summary
        if not self.summary:
            return False
        
        return True
