"""
Churn Scoring Engine Specification

Defines the formal specifications for the ChurnScoringEngine component.
Documents expected behavior, algorithms, and contracts.
"""

from typing import Dict, Any, List, Protocol
from abc import ABC, abstractmethod


class ScoringEngineSpec(ABC):
    """Base specification for scoring engines"""

    @abstractmethod
    def validate_inputs(self) -> bool:
        """Validate inputs against specification"""
        pass

    @abstractmethod
    def spec_summary(self) -> Dict[str, Any]:
        """Return specification summary"""
        pass


# ============================================================================
# CHURN SCORING ENGINE SPECIFICATION
# ============================================================================

class ChurnScoringEngineSpec(ScoringEngineSpec):
    """
    Specification for ChurnScoringEngine
    
    Purpose:
    - Calculate churn risk based on multiple customer signals
    - Provide evidence-backed explanations for risk assessments
    - Support tier-aware scoring thresholds
    - Generate actionable recommendations
    
    Input Requirements:
    - ClientProfile: Account information with tier and critical features
    - ClientSignals: Support tickets, usage history, satisfaction scores
    
    Output Contract:
    Returns dictionary with:
    {
        "risk_score": float (0-100),
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
    
    Health Status Mapping:
    - risk_score >= 60: "At Risk" (red)
    - 30 <= risk_score < 60: "Watch" (yellow)
    - risk_score < 30: "Healthy" (green)
    
    ========================================================================
    SUPPORT TICKET SCORING SPECIFICATION
    ========================================================================
    
    Algorithm:
    1. For each ticket, calculate severity_score() based on:
       - Base priority (critical=10, high=6, medium=3, low=1)
       - Escalation status (+4)
       - Open/critical status (+3)
       - Reopenings (+2 per reopening)
       - Critical feature multiplier (x1.5)
    
    2. Aggregate severity scores with weighting:
       - Critical issues weight highest
       - Recent issues weight more
       - Feature criticality amplifies impact
    
    3. Normalize to 0-100 risk score
    
    Risk Thresholds (tier-aware):
    - ENTERPRISE: score >= 40 = high risk
    - PROFESSIONAL: score >= 50 = high risk
    - STANDARD: score >= 65 = high risk
    
    Evidence Generation:
    - List critical and open tickets
    - Identify affected critical features
    - Quantify urgency (days open, reopenings)
    - Provide trend analysis if multiple periods available
    
    ========================================================================
    USAGE SCORING SPECIFICATION
    ========================================================================
    
    Algorithm:
    1. Calculate adoption health for current period
    2. Detect adoption trends:
       - Declining users = high risk
       - Declining feature usage = high risk
       - Stagnant users = medium risk
    
    3. Weight factors:
       - Current adoption health: 40%
       - User trend: 35%
       - Feature adoption trend: 25%
    
    4. Normalize to 0-100 risk score
    
    Risk Levels:
    - Adoption health "critical" = high risk
    - User decline >10% over period = high risk
    - Feature usage decline >20% = high risk
    - No recent usage data = medium risk
    
    Evidence Generation:
    - Current adoption level and health status
    - User count trends
    - Feature adoption trends
    - Comparison to previous period (if available)
    
    ========================================================================
    SATISFACTION SCORING SPECIFICATION
    ========================================================================
    
    Algorithm:
    1. Calculate sentiment deterioration:
       - Compare current to previous satisfaction metrics
       - Detect declining CSAT/NPS = high risk
    
    2. Weight factors:
       - Current satisfaction level: 50%
       - Deterioration trend: 50%
    
    3. Normalize to 0-100 risk score
    
    Risk Levels:
    - CSAT < 60: high risk
    - NPS < 0: high risk
    - CSAT declining >10 points: high risk
    - NPS declining >10 points: high risk
    
    Evidence Generation:
    - Current CSAT/NPS values
    - Trends over time
    - Interpretation of satisfaction levels
    - Correlation with support issues
    
    ========================================================================
    OVERALL CHURN RISK COMPUTATION SPECIFICATION
    ========================================================================
    
    Algorithm:
    1. Calculate individual risk scores:
       - support_risk = score_tickets()
       - usage_risk = score_usage()
       - satisfaction_risk = score_satisfaction()
    
    2. Apply tier-aware weights (from account tier):
       - weight = tier.config()["weight"]
       - Affects priority_threshold interpretation
    
    3. Calculate composite score:
       - weighted_support = support_risk * 0.35
       - weighted_usage = usage_risk * 0.35
       - weighted_satisfaction = satisfaction_risk * 0.30
       - composite = weighted_support + weighted_usage + weighted_satisfaction
    
    4. Apply renewal urgency multiplier:
       - If renewal < 30 days away: multiply by 1.3
       - If renewal < 60 days away: multiply by 1.15
       - Otherwise: multiply by 1.0
    
    5. Cap at 100 and round to integer
    
    6. Determine health_status:
       - Compare against tier-specific thresholds
       - Generate evidence summary
       - Create actionable recommendations
    
    ========================================================================
    RECOMMENDATIONS SPECIFICATION
    ========================================================================
    
    Recommendations are tier-specific and risk-driven:
    
    High Risk (score >= threshold):
    - ENTERPRISE: Risk-based specific actions
    - PROFESSIONAL: More general guidance
    - STANDARD: Self-service recommendations
    
    Types of Recommendations:
    - Immediate Escalations: "Escalate to Account Executive"
    - Product Actions: "Schedule product training", "Implement feature adoption plan"
    - Support Actions: "Schedule support review", "Assign dedicated support"
    - Success Actions: "Schedule business review", "Conduct health check"
    - Retention Actions: "Discuss renewal opportunities", "Address concerns"
    
    Recommendation Generation Logic:
    1. If critical unresolved tickets: Escalate support
    2. If usage declining: Suggest adoption plan
    3. If satisfaction low: Suggest business review
    4. If renewal near and at-risk: Escalate executive attention
    5. If tier-specific threshold breached: Generate tier-appropriate actions
    """

    # Risk Score Thresholds (0-100)
    HEALTH_STATUS_THRESHOLDS = {
        "at_risk": 60,
        "watch": 30,
        "healthy": 0,
    }

    # Tier-specific priority thresholds
    TIER_THRESHOLDS = {
        "ENTERPRISE": 40,
        "PROFESSIONAL": 50,
        "STANDARD": 65,
    }

    # Component weights in composite score
    COMPONENT_WEIGHTS = {
        "support": 0.35,
        "usage": 0.35,
        "satisfaction": 0.30,
    }

    # Risk level descriptions
    RISK_LEVELS = {
        "critical": "Immediate action required",
        "high": "Escalate and address",
        "medium": "Monitor and plan interventions",
        "low": "Maintain normal engagement",
    }

    def validate_inputs(self) -> bool:
        return True

    def spec_summary(self) -> Dict[str, Any]:
        return {
            "component": "ChurnScoringEngine",
            "purpose": "Calculate churn risk from multiple customer signals",
            "health_status_thresholds": self.HEALTH_STATUS_THRESHOLDS,
            "tier_thresholds": self.TIER_THRESHOLDS,
            "component_weights": self.COMPONENT_WEIGHTS,
            "methods": {
                "score_tickets": "Calculate support ticket risk score",
                "score_usage": "Calculate usage adoption risk score",
                "score_satisfaction": "Calculate satisfaction deterioration risk score",
                "compute_churn_risk": "Composite churn risk calculation",
                "build_recommendations": "Generate tier-aware action recommendations",
            },
        }


# ============================================================================
# SENTIMENT ANALYSIS SPECIFICATION
# ============================================================================

class SentimentAnalysisSpec(ABC):
    """Specification for sentiment analysis component"""

    @abstractmethod
    def spec_summary(self) -> Dict[str, Any]:
        pass


class CustomerSuccessAgentSpec(SentimentAnalysisSpec):
    """
    Specification for CustomerSuccessAgent
    
    Purpose:
    - Analyze customer sentiment from messages
    - Generate executive summaries with AI
    - Draft customer-facing outreach messages
    - Provide intelligent fallback when LLM unavailable
    
    ========================================================================
    SENTIMENT ANALYSIS SPECIFICATION
    ========================================================================
    
    Input:
    - List of Message objects with text content
    
    Output Contract:
    Returns list of sentiment analysis objects with:
    {
        "message_id": str,
        "sentiment": "frustrated" | "negative" | "neutral" | "positive",
        "confidence": float (0-1),
        "escalation_indicator": bool,
        "summary": str,
    }
    
    Analysis Modes:
    1. LLM_PREFERRED (default):
       - Try Claude AI for nuanced analysis
       - Fall back to local analysis on error
       - Cache results for consistency
    
    2. LLM_REQUIRED:
       - Use Claude AI exclusively
       - Raise error if unavailable
       - No fallback
    
    3. LOCAL_ONLY:
       - Use keyword-based local analysis only
       - No external API calls
       - Fast and deterministic
    
    Local Sentiment Analysis Algorithm:
    1. Check for escalation keywords: {urgent, critical, down, outage, emergency, failed}
    2. Calculate sentiment score based on keywords:
       - Negative keywords: frustrated, disappointed, angry, frustrated, issue, problem, failed
       - Positive keywords: great, excellent, happy, satisfied, resolved
    3. Classify:
       - escalation_indicator present: "frustrated"
       - negative_score > positive_score: "negative"
       - negative_score == positive_score: "neutral"
       - positive_score > negative_score: "positive"
    4. Confidence based on keyword matches (0.5-1.0)
    
    LLM Analysis:
    - Use Claude 3.5 Sonnet for nuanced understanding
    - Provide message context for better analysis
    - Parse structured output with confidence scores
    
    ========================================================================
    EXECUTIVE SUMMARY GENERATION SPECIFICATION
    ========================================================================
    
    Input:
    - ClientProfile: Account information
    - ChurnScoringEngine result: Risk assessment
    - Sentiment analysis: Message sentiment
    
    Output Contract:
    {
        "summary": str,  # 2-3 sentence executive summary
        "key_risks": List[str],  # 3-5 key risk factors
        "priority_actions": List[str],  # 3-5 recommended actions
        "urgency": "critical" | "high" | "medium" | "low",
    }
    
    Summary Generation Logic:
    1. Synthesize churn score, sentiment, and profile
    2. Identify top 2-3 risk drivers
    3. Recommend tier-appropriate actions
    4. Assess urgency based on risk score and renewal date
    
    LLM Path:
    - Send context to Claude
    - Request structured output
    - Parse and validate response
    - Fall back to template if parsing fails
    
    Local Path:
    - Use risk score thresholds
    - Apply tier-specific templates
    - Extract key risks from scoring result
    
    ========================================================================
    OUTREACH MESSAGE GENERATION SPECIFICATION
    ========================================================================
    
    Input:
    - ClientProfile: Customer context
    - ChurnScoringEngine result: Risk details
    - Executive plan: Summary with key risks and actions
    
    Output Contract:
    {
        "subject": str,  # Email subject line
        "greeting": str,  # Personalized greeting
        "opening": str,  # Opening paragraph
        "main_body": str,  # Main message content
        "next_steps": str,  # Call to action
        "signature": str,  # Sign-off
    }
    
    Message Generation Logic:
    1. Personalize using primary contact from profile
    2. Reference account tier for tone appropriateness
    3. Address key risks from assessment
    4. Provide clear next steps
    5. Tailor to communication style (formal, casual, technical)
    
    LLM Path:
    - Send profile, risks, and tone guidance to Claude
    - Request professional business email
    - Validate output length and tone
    - Fall back to template if needed
    
    Local Path:
    - Use tier-specific templates
    - Insert primary contact name
    - Reference top risks from assessment
    - Use appropriate closing for communication style
    
    Constraints:
    - Keep message concise (200-400 words)
    - Use professional but warm tone
    - Include specific risk references
    - Always include clear next steps
    """

    # Sentiment label definitions
    VALID_SENTIMENTS = {"frustrated", "negative", "neutral", "positive"}

    # LLM configuration modes
    ANALYSIS_MODES = {"llm_preferred", "llm_required", "local_only"}

    # Local sentiment keywords
    ESCALATION_KEYWORDS = {"urgent", "critical", "down", "outage", "emergency", "failed"}
    NEGATIVE_KEYWORDS = {"frustrated", "disappointed", "angry", "issue", "problem", "failed", "not working"}
    POSITIVE_KEYWORDS = {"great", "excellent", "happy", "satisfied", "resolved", "working well"}

    def spec_summary(self) -> Dict[str, Any]:
        return {
            "component": "CustomerSuccessAgent",
            "purpose": "AI-powered sentiment analysis and customer success recommendations",
            "valid_sentiments": self.VALID_SENTIMENTS,
            "analysis_modes": self.ANALYSIS_MODES,
            "methods": {
                "analyze_message_sentiment": "Analyze customer message sentiment",
                "explain_and_plan": "Generate executive summary with action plan",
                "draft_outreach_message": "Draft customer-facing communication",
            },
        }
