# Customer Health Platform

## Overview

A unified, enterprise-grade software platform for comprehensive customer churn assessment and customer success intelligence. Combines advanced risk scoring, sentiment analysis, and AI-powered recommendations.

## Architecture

The platform is organized into three main layers:

### 1. Data Models Layer
Core data structures representing customer accounts and their signals:
- `Contact`: Key customer contact with influence weighting
- `ClientProfile`: Complete account profile with business context
- `SupportTicket`: Support request with severity scoring
- `Message`: Customer communication for sentiment analysis
- `UsageSnapshot`: Feature adoption metrics
- `SatisfactionScore`: Customer satisfaction metrics (CSAT/NPS)
- `ClientSignals`: Aggregated signals for an account

### 2. Scoring & Analysis Layer
- **ChurnScoringEngine**: Calculates churn risk based on support tickets, usage, and satisfaction
  - `score_tickets()`: Severity-weighted ticket analysis
  - `score_usage()`: Adoption trend tracking
  - `score_satisfaction()`: Sentiment deterioration measurement
  - `compute_churn_risk()`: Comprehensive risk assessment
  
- **CustomerSuccessAgent**: AI-powered insights and recommendations
  - `analyze_message_sentiment()`: LLM or local sentiment detection
  - `explain_and_plan()`: Executive summary with action plans
  - `draft_outreach_message()`: Customer-facing communication drafts

### 3. Orchestration Layer
- **CustomerHealthPlatform**: Main entry point for integrated analysis
  - `analyze_account()`: Complete end-to-end analysis workflow

## Key Features

### Churn Risk Scoring
- Multi-factor assessment (support, usage, satisfaction)
- Tier-aware thresholds (Enterprise, Professional, Standard)
- Renewal urgency detection
- Evidence-backed explanations

### Sentiment Analysis
- Dual-mode operation: LLM-powered (Claude) with intelligent local fallback
- Keyword-based local analysis with caching
- Escalation indicator detection
- Message-level sentiment tracking

### Executive Recommendations
- Tier-specific action plans
- Priority-based task ownership
- Recovery timeline targets
- Risk mitigation strategies

### Professional Outreach Drafts
- Status-aware communication templates
- Primary contact extraction
- Tone matching (urgent/proactive/collaborative)
- Human-reviewable drafts

## Usage

### Basic Usage
```python
from customer_health_platform import (
    CustomerHealthPlatform,
    create_demo_profile,
    create_demo_signals,
)

# Initialize platform
platform = CustomerHealthPlatform()

# Load or create account data
profile = create_demo_profile()
signals = create_demo_signals()

# Run comprehensive analysis
result = platform.analyze_account(profile, signals)

# Result contains:
# - risk_assessment: Churn risk score, status, evidence
# - sentiment_analysis: Message-level sentiment with keywords
# - executive_summary: High-level account health summary
# - key_risks: Prioritized risk factors
# - priority_actions: Actionable next steps with ownership
# - draft_outreach: Ready-to-use customer communication
```

### Custom Configuration
```python
from customer_health_platform import (
    CustomerHealthPlatform,
    LLMConfig,
    AnalysisMode,
)

# Use local analysis only (no API calls)
llm_config = LLMConfig(mode=AnalysisMode.LOCAL_ONLY)
platform = CustomerHealthPlatform(llm_config=llm_config)

# Use LLM only (fail if unavailable)
llm_config = LLMConfig(mode=AnalysisMode.LLM_REQUIRED)
platform = CustomerHealthPlatform(llm_config=llm_config)

# LLM preferred with local fallback (default)
llm_config = LLMConfig(mode=AnalysisMode.LLM_PREFERRED, fallback_to_local=True)
platform = CustomerHealthPlatform(llm_config=llm_config)
```

## Configuration

### Environment Variables
- `ANTHROPIC_API_KEY`: Claude API key (optional, enables LLM features)
- `ANTHROPIC_MODEL`: Model name (default: `claude-3-5-sonnet-20241022`)
- `LLM_TIMEOUT`: API timeout in seconds (default: `30`)

### Logging
Configured to output INFO level with timestamps:
```
2026-08-15 09:48:58,866 - customer_health_platform - INFO - Starting analysis...
```

## Enum Types

### Priority
- `CRITICAL` (10): Critical priority tickets
- `HIGH` (6): High priority tickets
- `MEDIUM` (3): Medium priority tickets
- `LOW` (1): Low priority tickets

### Importance
- `CRITICAL` (1.5): Critical contact
- `HIGH` (1.5): High importance
- `NORMAL` (1.0): Normal importance
- `LOW` (0.8): Low importance

### AccountTier
- `ENTERPRISE`: weight=2.0, threshold=40
- `PROFESSIONAL`: weight=1.5, threshold=50
- `STANDARD`: weight=1.0, threshold=65

### HealthStatus
- `HEALTHY`: score < 30
- `WATCH`: 30 ≤ score < 60
- `AT_RISK`: score ≥ 60

### AnalysisMode
- `LLM_PREFERRED`: Use LLM if available, fallback to local
- `LLM_REQUIRED`: Use LLM only, fail if unavailable
- `LOCAL_ONLY`: Never use LLM, always use local analysis

## Scoring Methodology

### Risk Score Components

1. **Support Tickets (0-100)**
   - Base score by priority: Critical=10, High=6, Medium=3, Low=1
   - Escalation bonus: +4
   - Open & high-priority bonus: +3
   - Reopening penalty: +2 per reopen
   - Critical feature multiplier: ×1.5

2. **Usage Decline (0-50)**
   - Feature usage drop: -0.6 points per 1% decline
   - Active user drop: -0.5 points per user decline

3. **Satisfaction Decline (0-50)**
   - CSAT drop: -0.5 points per 1% decline
   - NPS drop: -0.3 points per point decline

### Final Score
Aggregated from all components, capped at 100.

## Error Handling

- Comprehensive validation on all data models
- Graceful fallback from LLM to local analysis
- Retry logic with exponential backoff for API calls
- Detailed error logging for debugging

## Output Structure

```json
{
  "timestamp": "ISO 8601 timestamp",
  "account": "Company name",
  "risk_assessment": {
    "score": 0-100,
    "status": "Healthy|Watch|At Risk",
    "summary": "Executive summary",
    "evidence": ["List of findings"],
    "breakdown": {"tickets": X, "usage": Y, "satisfaction": Z},
    "recommended_focus": ["Action items"]
  },
  "sentiment_analysis": [
    {
      "message_id": "ID",
      "sentiment_score": -1.0 to 1.0,
      "sentiment_label": "frustrated|negative|neutral|positive",
      "analysis_mode": "llm|local"
    }
  ],
  "executive_summary": "Account status summary",
  "key_risks": [
    {"risk": "Description", "evidence": "Supporting data", "severity": "critical|high|medium"}
  ],
  "priority_actions": [
    {"action": "Description", "owner": "Team", "priority": "critical|high|medium"}
  ],
  "draft_outreach": {
    "recipient": "Contact name",
    "subject": "Email subject",
    "body": "Email body",
    "tone": "urgent|proactive|collaborative"
  }
}
```

## Integration Points

The platform is designed for easy integration with:
- Customer Success dashboards
- CRM systems (Salesforce, HubSpot)
- Ticketing systems (Jira, Zendesk)
- Analytics platforms
- Email/communication systems

## Performance Considerations

- Sentiment keyword detection uses LRU caching (128 entries)
- Scoring calculations are deterministic and fast
- LLM calls can be batched for efficiency
- Suitable for real-time account health checks

## Future Enhancements

- Multi-language sentiment analysis
- Predictive churn modeling
- Custom scoring weights per customer segment
- Historical trend analysis
- Automated action execution
- Integration with customer communication platforms
