"""
Quick Start Guide: Spec-Driven Development

This module provides quick examples for getting started
with the spec-driven development approach.
"""

# ============================================================================
# EXAMPLE 1: Validating a Component Against Specification
# ============================================================================

def example_validate_contact():
    """Example: Validate a Contact against ContactSpec"""
    from customer_health_platform import Contact
    from specs.validator import SpecValidator
    
    # Create a contact
    contact = Contact(name="John Doe", role="CTO", importance="critical")
    
    # Validate against specification
    result = SpecValidator.validate_contact_spec(contact)
    
    # Check compliance
    if result.compliant:
        print(f"✓ {contact.name} is compliant with ContactSpec")
    else:
        print(f"✗ {contact.name} has compliance issues:")
        for issue in result.issues:
            print(f"  - {issue}")


# ============================================================================
# EXAMPLE 2: Running Full Compliance Check
# ============================================================================

def example_full_compliance_check():
    """Example: Run full compliance check on platform"""
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
    )
    from specs.validator import SpecRunner
    from datetime import date, timedelta
    
    # Create test data
    contact = Contact(name="John", role="CTO", importance="critical")
    profile = ClientProfile(
        company_name="TechCorp",
        business_goals=["Scale", "Automate"],
        key_contacts=[contact],
        critical_features=["API", "Dashboard"],
        communication_style="formal",
        account_tier="ENTERPRISE",
    )
    
    ticket = SupportTicket(
        ticket_id="TICK-001",
        opened_on=date.today(),
        closed_on=None,
        subject="Critical API Issue",
        related_feature="API",
        priority="critical",
        status="open",
    )
    
    usage = UsageSnapshot(
        period_label="Q1 2024",
        active_users=150,
        feature_usage_pct=85.0,
    )
    
    satisfaction = SatisfactionScore(
        period_label="Q1 2024",
        csat=88.0,
        nps=65,
    )
    
    signals = ClientSignals(
        support_tickets=[ticket],
        usage_history=[usage],
        satisfaction_history=[satisfaction],
        messages=[],
    )
    
    # Run compliance check
    runner = SpecRunner()
    test_data = {
        'contacts': [contact],
        'profiles': [profile],
        'tickets': [ticket],
        'messages': [],
        'churn_results': [],
        'sentiment_results': [],
    }
    
    report = runner.run_all_validations(test_data)
    runner.print_report()
    
    return report


# ============================================================================
# EXAMPLE 3: Validating Churn Risk Output
# ============================================================================

def example_validate_churn_risk():
    """Example: Validate churn risk output against specification"""
    from customer_health_platform import (
        Contact,
        ClientProfile,
        SupportTicket,
        UsageSnapshot,
        SatisfactionScore,
        ClientSignals,
        ChurnScoringEngine,
    )
    from specs.validator import SpecValidator
    from datetime import date
    
    # Setup
    contact = Contact(name="Jane", role="Manager")
    profile = ClientProfile(
        company_name="StartupCo",
        business_goals=["Growth"],
        key_contacts=[contact],
        critical_features=["Core API"],
        communication_style="casual",
    )
    
    ticket = SupportTicket(
        ticket_id="TICK-002",
        opened_on=date.today(),
        closed_on=None,
        subject="Performance Issue",
        related_feature="Core API",
        priority="high",
        status="open",
        reopened_count=1,
    )
    
    usage = UsageSnapshot(
        period_label="This Month",
        active_users=50,
        feature_usage_pct=60.0,
    )
    
    satisfaction = SatisfactionScore(
        period_label="This Month",
        csat=70.0,
    )
    
    signals = ClientSignals(
        support_tickets=[ticket],
        usage_history=[usage],
        satisfaction_history=[satisfaction],
        messages=[],
    )
    
    # Compute churn risk
    engine = ChurnScoringEngine()
    result = engine.compute_churn_risk(profile, signals)
    
    # Validate output
    validation = SpecValidator.validate_churn_risk_output(result)
    
    if validation.compliant:
        print(f"✓ Churn risk output is compliant")
        print(f"  Risk Score: {result['risk_score']}")
        print(f"  Health Status: {result['health_status']}")
    else:
        print(f"✗ Churn risk output has issues:")
        for issue in validation.issues:
            print(f"  - {issue}")
    
    return result


# ============================================================================
# EXAMPLE 4: Analyzing Sentiment Against Specification
# ============================================================================

def example_sentiment_analysis():
    """Example: Analyze sentiment against specification"""
    from customer_health_platform import CustomerSuccessAgent
    from specs.validator import SpecValidator
    from datetime import date
    
    # Create test messages
    messages = [
        {
            "message_id": "MSG-001",
            "text": "The system is down! This is critical!",
            "sender_name": "Client",
            "channel": "email",
            "sent_on": str(date.today()),
        },
        {
            "message_id": "MSG-002",
            "text": "Everything is working great now. Thanks!",
            "sender_name": "Client",
            "channel": "email",
            "sent_on": str(date.today()),
        },
    ]
    
    # Analyze sentiment
    agent = CustomerSuccessAgent()
    result = agent.analyze_message_sentiment(messages)
    
    # Validate against specification
    validation = SpecValidator.validate_sentiment_output(result)
    
    if validation.compliant:
        print(f"✓ Sentiment analysis is compliant")
        for item in result:
            print(f"  {item['message_id']}: {item.get('sentiment', 'unknown')}")
    else:
        print(f"✗ Sentiment analysis has issues:")
        for issue in validation.issues:
            print(f"  - {issue}")
    
    return result


# ============================================================================
# EXAMPLE 5: Using Spec-Driven Decorators
# ============================================================================

def example_spec_driven_decorators():
    """Example: Mark functions as spec-driven"""
    from specs.decorators import SpecDriven, ContractCheckpoint, SpecCompliance
    
    # Define a spec-driven function
    @SpecDriven(
        spec_name="MyAnalysisSpec",
        version="1.0",
        author="Analytics Team",
        compliance_level="strict"
    )
    @ContractCheckpoint("MyAnalysisContract", check_type="both")
    def analyze_data(data):
        """Analyze data against formal specification"""
        return {"result": "analyzed"}
    
    # Check if function is spec-driven
    if SpecCompliance.is_spec_driven(analyze_data):
        spec_info = SpecCompliance.get_spec_info(analyze_data)
        print(f"✓ Function is spec-driven:")
        print(f"  Spec: {spec_info['spec_name']}")
        print(f"  Version: {spec_info['spec_version']}")
        print(f"  Compliance Level: {spec_info['compliance_level']}")
    
    # Check for contract checkpoint
    if SpecCompliance.has_contract_checkpoint(analyze_data):
        print(f"✓ Function has contract checkpoint: {analyze_data._contract_name}")
    
    # Log compliance info
    SpecCompliance.log_spec_compliance(analyze_data)


# ============================================================================
# EXAMPLE 6: Testing Against Specifications
# ============================================================================

def example_test_against_spec():
    """Example: Write tests that verify specifications"""
    from customer_health_platform import Contact
    
    # Test 1: Contact creation
    contact = Contact(name="John", role="CTO", importance="critical")
    assert contact.name == "John"
    assert contact.role == "CTO"
    assert contact.importance == "critical"
    assert contact.influence_weight == 1.5  # From spec
    print("✓ Contact specification test passed")
    
    # Test 2: Invalid contact
    try:
        Contact(name="", role="CTO")
        print("✗ Should have raised ValueError for empty name")
    except ValueError as e:
        print(f"✓ Correctly raised error: {e}")
    
    # Test 3: Importance normalization
    contact2 = Contact(name="Jane", role="Manager", importance="CRITICAL")
    assert contact2.importance == "critical"  # Should be lowercase
    print("✓ Importance normalization test passed")
    
    # Test 4: Default importance
    contact3 = Contact(name="Bob", role="Developer")
    assert contact3.importance == "normal"
    assert contact3.influence_weight == 1.0  # Default
    print("✓ Default importance test passed")


# ============================================================================
# MAIN: RUN ALL EXAMPLES
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("SPEC-DRIVEN DEVELOPMENT QUICK START EXAMPLES")
    print("=" * 80)
    
    print("\n1. Validating a Contact Against Specification")
    print("-" * 80)
    example_validate_contact()
    
    print("\n2. Running Full Compliance Check")
    print("-" * 80)
    report = example_full_compliance_check()
    
    print("\n3. Validating Churn Risk Output")
    print("-" * 80)
    example_validate_churn_risk()
    
    print("\n4. Analyzing Sentiment Against Specification")
    print("-" * 80)
    example_sentiment_analysis()
    
    print("\n5. Using Spec-Driven Decorators")
    print("-" * 80)
    example_spec_driven_decorators()
    
    print("\n6. Testing Against Specifications")
    print("-" * 80)
    example_test_against_spec()
    
    print("\n" + "=" * 80)
    print("All examples completed successfully!")
    print("=" * 80)
