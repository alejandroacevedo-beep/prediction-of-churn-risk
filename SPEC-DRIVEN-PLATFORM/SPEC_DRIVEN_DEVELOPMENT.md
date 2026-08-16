# Spec-Driven Development Guide

## Overview

Your Customer Health Platform has been transformed into a **spec-driven development** system. This approach ensures code quality, maintainability, and compliance through formal specifications, comprehensive testing, and contract-based development.

---

## What is Spec-Driven Development?

Spec-driven development is a methodology where:

1. **Formal Specifications** define expected behavior, constraints, and contracts
2. **Tests** verify compliance with specifications
3. **Code** implements specifications with clear contracts
4. **Validation** ensures adherence throughout development
5. **Documentation** is generated from specifications

---

## Architecture

### Directory Structure

```
c:\Users\Ijdga\OneDrive\Actual work systems\
├── customer_health_platform.py          [Main Platform]
├── churn_scoring.py                     [Backward Compatibility Wrapper]
├── claude_agent.py                      [Backward Compatibility Wrapper]
│
├── specs/                               [SPECIFICATIONS]
│   ├── __init__.py
│   ├── data_models_spec.py             [Data Model Specifications]
│   ├── scoring_engine_spec.py           [Scoring & Sentiment Specs]
│   ├── interfaces.py                    [Protocols & Contracts]
│   ├── decorators.py                    [Spec-Driven Decorators]
│   └── validator.py                     [Compliance Validator]
│
├── tests/                               [TEST SUITE]
│   ├── __init__.py
│   └── test_specifications.py           [Specification Tests]
│
└── SPEC_DRIVEN_DEVELOPMENT.md           [This Guide]
```

---

## Core Concepts

### 1. Specifications

Located in `specs/` directory, formal specifications document:

- **Data Model Specifications** (`data_models_spec.py`)
  - Contact, ClientProfile, SupportTicket, Message
  - UsageSnapshot, SatisfactionScore, ClientSignals
  - Constraints, validation rules, computed properties

- **Scoring Engine Specifications** (`scoring_engine_spec.py`)
  - Churn risk calculation algorithms
  - Sentiment analysis modes
  - Executive summary generation
  - Customer outreach drafting

- **Interfaces & Protocols** (`interfaces.py`)
  - Runtime-checkable protocol definitions
  - Component contracts
  - Method signatures with guarantees
  - Output format guarantees

### 2. Formal Contracts

Each major component has explicit contracts defining:

```python
# INPUT CONTRACT
# Guarantees about what the function accepts

# PROCESSING CONTRACT  
# Guarantees about how the function operates

# OUTPUT CONTRACT
# Guarantees about what the function returns
```

### 3. Validation Layer

The validation system (`specs/validator.py`) provides:

- **SpecValidator**: Validates components against specifications
- **SpecRunner**: Orchestrates all validations
- **ComplianceReport**: Detailed compliance results

---

## How to Use

### Running Tests

```bash
# Run all specification tests
python -m pytest tests/test_specifications.py -v

# Run specific test class
python -m pytest tests/test_specifications.py::TestContactSpecification -v

# Run with coverage
python -m pytest tests/test_specifications.py --cov=customer_health_platform
```

### Validating Compliance

```python
from specs.validator import SpecRunner, SpecValidator
from customer_health_platform import Contact, ClientProfile

# Validate a single component
contact = Contact(name="John", role="CTO")
result = SpecValidator.validate_contact_spec(contact)
print(f"Compliant: {result.compliant}")
print(f"Issues: {result.issues}")

# Run comprehensive validation
runner = SpecRunner()
test_data = {
    'contacts': [contact],
    'profiles': [],
    'tickets': [],
    'messages': [],
    'churn_results': [],
    'sentiment_results': [],
}
report = runner.run_all_validations(test_data)
runner.print_report()
```

### Applying Spec-Driven Decorators

Mark functions as spec-driven for compliance tracking:

```python
from specs.decorators import SpecDriven, ContractCheckpoint

@SpecDriven(
    spec_name="ChurnScoringEngineSpec",
    version="1.0",
    compliance_level="strict"
)
@ContractCheckpoint("ChurnRiskOutputContract", check_type="output")
def compute_churn_risk(profile, signals):
    """Compute churn risk against formal specification"""
    # Implementation
    return result
```

---

## Specification Details

### Data Models Specification

Each data model has formal requirements:

#### Contact Specification

```
Required Fields:
- name: Non-empty string
- role: Non-empty string

Optional Fields:
- importance: critical|high|normal|low, defaults to normal

Constraints:
- Cannot create with empty name or role
- importance is normalized to lowercase
- Invalid importance defaults to 'normal'

Computed Properties:
- influence_weight: 1.5 (critical/high), 1.0 (normal), 0.8 (low)
```

#### ClientProfile Specification

```
Required Fields:
- company_name: Non-empty string
- business_goals: List of strings
- key_contacts: At least 1 Contact
- critical_features: At least 1 feature
- communication_style: String

Optional Fields:
- account_tier: ENTERPRISE|PROFESSIONAL|STANDARD
- renewal_date: ISO format date
- open_commitments: List of strings
- known_risks: List of strings

Tier Configuration:
- ENTERPRISE: weight=2.0, priority_threshold=40
- PROFESSIONAL: weight=1.5, priority_threshold=50
- STANDARD: weight=1.0, priority_threshold=65
```

#### SupportTicket Specification

```
Severity Scoring Algorithm:
1. Base priority scores: critical=10, high=6, medium=3, low=1
2. Escalated status: +4
3. Unresolved critical/high: +3
4. Each reopening: +2
5. Critical feature multiplier: x1.5

Health Status Mapping:
- risk_score >= 60: "At Risk"
- 30-60: "Watch"  
- < 30: "Healthy"
```

### Scoring Engine Specification

#### Component Weights

```python
COMPONENT_WEIGHTS = {
    "support": 0.35,      # Support ticket risk
    "usage": 0.35,        # Usage adoption risk
    "satisfaction": 0.30, # Satisfaction deterioration risk
}
```

#### Risk Calculation

```
1. Calculate individual risk scores
2. Apply tier-aware weights
3. Calculate composite score
4. Apply renewal urgency multiplier (0.3x-1.3x)
5. Cap at 100
6. Determine health status
```

### Sentiment Analysis Specification

#### Analysis Modes

```
1. LLM_PREFERRED (default)
   - Try Claude AI first
   - Fall back to local analysis
   - Cache results

2. LLM_REQUIRED
   - Use Claude AI only
   - Raise error if unavailable

3. LOCAL_ONLY
   - Keyword-based analysis
   - No API calls
   - Fast and deterministic
```

#### Local Sentiment Algorithm

```
Escalation Keywords: {urgent, critical, down, outage, emergency, failed}
Negative Keywords: {frustrated, disappointed, angry, issue, problem}
Positive Keywords: {great, excellent, happy, satisfied, resolved}

Classification:
- escalation_keyword present → "frustrated"
- negative_score > positive_score → "negative"
- negative_score == positive_score → "neutral"
- positive_score > negative_score → "positive"
```

---

## Output Contracts

### Churn Risk Result

```python
{
    "risk_score": int,           # 0-100
    "health_status": str,        # "Healthy"|"Watch"|"At Risk"
    "risk_factors": {
        "support_risk_score": float,      # 0-100
        "usage_risk_score": float,        # 0-100
        "satisfaction_risk_score": float, # 0-100
    },
    "evidence": {
        "support_analysis": str,
        "usage_analysis": str,
        "satisfaction_analysis": str,
        "renewal_urgency": str,
    },
    "recommendations": List[str],
}
```

### Sentiment Analysis Result

```python
[
    {
        "message_id": str,
        "sentiment": str,           # frustrated|negative|neutral|positive
        "confidence": float,        # 0-1
        "escalation_indicator": bool,
        "summary": str,
    }
]
```

### Success Plan Result

```python
{
    "summary": str,                # Executive summary
    "key_risks": List[str],        # Top 3-5 risks
    "priority_actions": List[str], # Recommended actions
    "urgency": str,                # critical|high|medium|low
}
```

---

## Compliance Levels

### Strict Compliance

```python
@SpecDriven(compliance_level="strict")
def function():
    """All specifications must be met exactly"""
```

All requirements must be satisfied. No deviations allowed.

### Moderate Compliance

```python
@SpecDriven(compliance_level="moderate")  
def function():
    """Major specifications must be met"""
```

Core requirements enforced. Minor deviations allowed with documentation.

### Permissive Compliance

```python
@SpecDriven(compliance_level="permissive")
def function():
    """Specifications guide but don't enforce"""
```

Specifications provide guidance. Deviations logged for audit trail.

---

## Development Workflow

### 1. Design Phase

Write specification for the component:

```python
# specs/my_spec.py
class MyComponentSpec:
    """Define what MyComponent should do"""
    
    def spec_summary(self):
        return {
            "component": "MyComponent",
            "required_fields": [...],
            "constraints": {...},
        }
```

### 2. Test Phase

Write tests that verify the specification:

```python
# tests/test_my_spec.py
def test_my_component_meets_spec():
    """Verify MyComponent meets specification"""
    component = MyComponent(...)
    assert component.required_property == expected
```

### 3. Implementation Phase

Implement according to specification:

```python
# customer_health_platform.py
@SpecDriven(spec_name="MyComponentSpec")
class MyComponent:
    """Implementation of MyComponentSpec"""
    pass
```

### 4. Validation Phase

Validate implementation against specification:

```python
from specs.validator import SpecValidator

result = SpecValidator.validate_my_component(component)
assert result.compliant, result.issues
```

---

## Best Practices

### 1. Always Define Contracts

Every public function should have clear input/output contracts:

```python
def analyze_account(profile, signals):
    """
    INPUT CONTRACT:
    - profile: ClientProfile with valid tier
    - signals: ClientSignals with non-empty lists
    
    OUTPUT CONTRACT:
    - Returns dict with: risk_score (0-100), health_status, ...
    - All fields always present
    - Evidence always non-empty
    """
```

### 2. Use Type Hints

Leverage Python type hints with specs:

```python
def compute_churn_risk(
    profile: ClientProfile,
    signals: ClientSignals,
) -> Dict[str, Any]:
    """Compute with formal spec compliance"""
```

### 3. Test Against Specs

Write tests that verify specification compliance:

```python
def test_contact_spec_validation():
    spec = ContactSpec()
    contact = Contact(...)
    result = SpecValidator.validate_contact_spec(contact)
    assert result.compliant
```

### 4. Document Algorithms

Document complex algorithms per specification:

```python
def score_tickets(profile, tickets):
    """
    Algorithm per SupportTicketSpec:
    1. Calculate severity_score() for each ticket
    2. Aggregate with weighting
    3. Normalize to 0-100
    """
```

### 5. Validate Inputs/Outputs

Always validate against contracts:

```python
def process(data):
    # Validate input
    assert validate_input_contract(data)
    
    # Process
    result = do_processing(data)
    
    # Validate output
    assert validate_output_contract(result)
    
    return result
```

---

## Compliance Reporting

### Generate Compliance Report

```python
from specs.validator import SpecRunner

runner = SpecRunner()
report = runner.run_all_validations(test_data)
runner.print_report()

# Save as JSON
with open("compliance_report.json", "w") as f:
    f.write(runner.to_json())
```

### Report Structure

```
SPECIFICATION COMPLIANCE REPORT
==============================
Total Checks: 25
Passed: 24
Failed: 1
Compliance: 96.0%

Contact: 5/5 compliant
  ✓ ContactSpec
  
ClientProfile: 4/4 compliant
  ✓ ClientProfileSpec
  
SupportTicket: 5/6 compliant
  ✗ SupportTicketSpec
    - risk_factor 'support_risk' 125 must be 0-100
```

---

## FAQ

**Q: How do I add a new component to the spec-driven system?**

A: 
1. Create specification in `specs/`
2. Create tests in `tests/`
3. Add validator to `specs/validator.py`
4. Implement component per spec
5. Run compliance checks

**Q: Can I modify existing specifications?**

A: Specifications should be versioned. Changes should:
1. Increment version number
2. Document breaking changes
3. Update all tests
4. Mark deprecated behaviors

**Q: How strict should compliance be?**

A: Use appropriate level:
- **Strict**: Critical components (scoring, validation)
- **Moderate**: Supporting components (utilities, helpers)  
- **Permissive**: Experimental/optional features

**Q: How do I handle spec violations?**

A: 
1. Document the violation
2. Log with compliance reporter
3. Create issue to fix violation
4. Update spec if violation is justified

---

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Spec Compliance Check

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run specification tests
        run: pytest tests/test_specifications.py -v
      - name: Run compliance validation
        run: python -m specs.validator
```

---

## Resources

- [Specifications](specs/): Formal component specifications
- [Tests](tests/): Comprehensive test suite
- [Validators](specs/validator.py): Compliance checking tools
- [Decorators](specs/decorators.py): Spec-driven markers
- [Interfaces](specs/interfaces.py): Protocol definitions

---

## Summary

Your platform is now spec-driven with:

✅ **Formal Specifications** for all major components
✅ **Comprehensive Tests** validating specification compliance
✅ **Protocol Definitions** ensuring clear contracts
✅ **Validation Tools** for automated compliance checking
✅ **Decorator System** for marking spec-driven code
✅ **Compliance Reporting** for audit trails

This ensures **high quality, maintainability, and accountability** throughout development.
