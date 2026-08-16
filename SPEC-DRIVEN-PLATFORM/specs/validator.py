"""
Specification Validator and Compliance Checker

Validates that the platform components comply with formal specifications.
Provides a spec-driven testing framework.
"""

import logging
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, field
from datetime import date
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class SpecComplianceResult:
    """Result of a compliance check"""
    component: str
    spec_name: str
    compliant: bool
    issues: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "component": self.component,
            "spec_name": self.spec_name,
            "compliant": self.compliant,
            "issues": self.issues,
            "details": self.details,
        }


@dataclass
class ComplianceReport:
    """Overall compliance report"""
    total_checks: int
    passed_checks: int
    failed_checks: int
    compliance_percentage: float
    results: List[SpecComplianceResult] = field(default_factory=list)
    timestamp: str = ""

    def add_result(self, result: SpecComplianceResult) -> None:
        """Add a compliance result"""
        self.results.append(result)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "total_checks": self.total_checks,
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks,
            "compliance_percentage": self.compliance_percentage,
            "results": [r.to_dict() for r in self.results],
        }


class SpecValidator:
    """Validates components against their specifications"""

    @staticmethod
    def validate_contact_spec(contact: Any) -> SpecComplianceResult:
        """Validate Contact against specification"""
        issues = []
        compliant = True

        # Check required fields exist and are valid
        if not hasattr(contact, 'name') or not contact.name:
            issues.append("Contact must have non-empty 'name'")
            compliant = False

        if not hasattr(contact, 'role') or not contact.role:
            issues.append("Contact must have non-empty 'role'")
            compliant = False

        # Check importance is normalized
        if hasattr(contact, 'importance'):
            valid_values = {'critical', 'high', 'normal', 'low'}
            if contact.importance not in valid_values:
                issues.append(f"Contact importance must be one of {valid_values}")
                compliant = False

        # Check influence_weight calculation
        if hasattr(contact, 'influence_weight'):
            expected_weights = {
                'critical': 1.5,
                'high': 1.5,
                'normal': 1.0,
                'low': 0.8,
            }
            if contact.importance in expected_weights:
                if contact.influence_weight != expected_weights[contact.importance]:
                    issues.append(
                        f"Contact influence_weight {contact.influence_weight} "
                        f"does not match expected {expected_weights[contact.importance]}"
                    )
                    compliant = False

        return SpecComplianceResult(
            component="Contact",
            spec_name="ContactSpec",
            compliant=compliant,
            issues=issues,
        )

    @staticmethod
    def validate_profile_spec(profile: Any) -> SpecComplianceResult:
        """Validate ClientProfile against specification"""
        issues = []
        compliant = True

        # Check required fields
        if not hasattr(profile, 'company_name') or not profile.company_name:
            issues.append("Profile must have non-empty 'company_name'")
            compliant = False

        if not hasattr(profile, 'key_contacts') or not profile.key_contacts:
            issues.append("Profile must have at least one 'key_contacts'")
            compliant = False

        if not hasattr(profile, 'critical_features') or not profile.critical_features:
            issues.append("Profile must have at least one 'critical_features'")
            compliant = False

        # Check account tier configuration
        if hasattr(profile, 'account_tier') and hasattr(profile, 'tier_config'):
            valid_tiers = {'ENTERPRISE', 'PROFESSIONAL', 'STANDARD'}
            tier_upper = profile.account_tier.upper()
            if tier_upper not in valid_tiers:
                issues.append(f"Profile account_tier must be one of {valid_tiers}")
                compliant = False
            else:
                config = profile.tier_config
                required_keys = {'weight', 'priority_threshold'}
                if not all(k in config for k in required_keys):
                    issues.append(f"Tier config missing required keys: {required_keys}")
                    compliant = False

        # Check primary_contact exists when contacts exist
        if hasattr(profile, 'primary_contact'):
            if not profile.key_contacts and profile.primary_contact is not None:
                issues.append("primary_contact should be None when no key_contacts")
                compliant = False

        return SpecComplianceResult(
            component="ClientProfile",
            spec_name="ClientProfileSpec",
            compliant=compliant,
            issues=issues,
        )

    @staticmethod
    def validate_ticket_spec(ticket: Any) -> SpecComplianceResult:
        """Validate SupportTicket against specification"""
        issues = []
        compliant = True

        # Check required fields
        if not hasattr(ticket, 'ticket_id') or not ticket.ticket_id:
            issues.append("Ticket must have non-empty 'ticket_id'")
            compliant = False

        if not hasattr(ticket, 'priority'):
            issues.append("Ticket must have 'priority'")
            compliant = False
        else:
            valid_priorities = {'critical', 'high', 'medium', 'low'}
            if ticket.priority not in valid_priorities:
                issues.append(f"Ticket priority must be one of {valid_priorities}")
                compliant = False

        # Check date constraints
        if hasattr(ticket, 'opened_on') and hasattr(ticket, 'closed_on'):
            if ticket.closed_on and ticket.closed_on < ticket.opened_on:
                issues.append("Ticket closed_on cannot be before opened_on")
                compliant = False

        # Check computed properties
        if hasattr(ticket, 'is_unresolved') and hasattr(ticket, 'closed_on'):
            expected = ticket.closed_on is None
            if ticket.is_unresolved != expected:
                issues.append(f"is_unresolved {ticket.is_unresolved} does not match expected {expected}")
                compliant = False

        return SpecComplianceResult(
            component="SupportTicket",
            spec_name="SupportTicketSpec",
            compliant=compliant,
            issues=issues,
        )

    @staticmethod
    def validate_message_spec(message: Any) -> SpecComplianceResult:
        """Validate Message against specification"""
        issues = []
        compliant = True

        # Check required fields
        if not hasattr(message, 'message_id') or not message.message_id:
            issues.append("Message must have non-empty 'message_id'")
            compliant = False

        if not hasattr(message, 'text') or not message.text:
            issues.append("Message must have non-empty 'text'")
            compliant = False

        # Check channel is lowercase
        if hasattr(message, 'channel'):
            if message.channel != message.channel.lower():
                issues.append("Message 'channel' should be normalized to lowercase")
                compliant = False

        return SpecComplianceResult(
            component="Message",
            spec_name="MessageSpec",
            compliant=compliant,
            issues=issues,
        )

    @staticmethod
    def validate_churn_risk_output(result: Dict[str, Any]) -> SpecComplianceResult:
        """Validate ChurnScoringEngine output against specification"""
        issues = []
        compliant = True

        # Check required fields
        required_fields = {'risk_score', 'health_status', 'risk_factors', 'evidence', 'recommendations'}
        if not all(k in result for k in required_fields):
            missing = required_fields - set(result.keys())
            issues.append(f"Result missing required fields: {missing}")
            compliant = False

        # Check risk_score range
        if 'risk_score' in result:
            if not isinstance(result['risk_score'], (int, float)):
                issues.append("risk_score must be numeric")
                compliant = False
            elif not 0 <= result['risk_score'] <= 100:
                issues.append(f"risk_score {result['risk_score']} must be 0-100")
                compliant = False

        # Check health_status value
        if 'health_status' in result:
            valid_statuses = {'Healthy', 'Watch', 'At Risk'}
            if result['health_status'] not in valid_statuses:
                issues.append(f"health_status must be one of {valid_statuses}")
                compliant = False

        # Check risk_factors are numeric
        if 'risk_factors' in result:
            if not isinstance(result['risk_factors'], dict):
                issues.append("risk_factors must be a dict")
                compliant = False
            else:
                for key, value in result['risk_factors'].items():
                    if not isinstance(value, (int, float)):
                        issues.append(f"risk_factor '{key}' must be numeric")
                        compliant = False
                    elif not 0 <= value <= 100:
                        issues.append(f"risk_factor '{key}' {value} must be 0-100")
                        compliant = False

        # Check evidence
        if 'evidence' in result:
            if not isinstance(result['evidence'], dict):
                issues.append("evidence must be a dict")
                compliant = False
            elif not result['evidence']:
                issues.append("evidence cannot be empty")
                compliant = False

        # Check recommendations
        if 'recommendations' in result:
            if not isinstance(result['recommendations'], list):
                issues.append("recommendations must be a list")
                compliant = False
            elif not result['recommendations']:
                issues.append("recommendations cannot be empty")
                compliant = False

        return SpecComplianceResult(
            component="ChurnScoringEngine",
            spec_name="ChurnScoringEngineSpec",
            compliant=compliant,
            issues=issues,
            details={"output_keys": list(result.keys())},
        )

    @staticmethod
    def validate_sentiment_output(result: List[Dict[str, Any]]) -> SpecComplianceResult:
        """Validate sentiment analysis output against specification"""
        issues = []
        compliant = True

        if not isinstance(result, list):
            issues.append("Sentiment result must be a list")
            compliant = False
            return SpecComplianceResult(
                component="CustomerSuccessAgent",
                spec_name="SentimentAnalysisSpec",
                compliant=compliant,
                issues=issues,
            )

        valid_sentiments = {'frustrated', 'negative', 'neutral', 'positive'}

        for i, item in enumerate(result):
            if not isinstance(item, dict):
                issues.append(f"Item {i} must be a dict")
                compliant = False
                continue

            # Check required fields
            required = {'message_id', 'sentiment', 'confidence'}
            if not all(k in item for k in required):
                missing = required - set(item.keys())
                issues.append(f"Item {i} missing fields: {missing}")
                compliant = False

            # Check sentiment value
            if 'sentiment' in item and item['sentiment'] not in valid_sentiments:
                issues.append(f"Item {i} sentiment '{item['sentiment']}' invalid")
                compliant = False

            # Check confidence range
            if 'confidence' in item:
                if not isinstance(item['confidence'], (int, float)):
                    issues.append(f"Item {i} confidence must be numeric")
                    compliant = False
                elif not 0 <= item['confidence'] <= 1:
                    issues.append(f"Item {i} confidence {item['confidence']} must be 0-1")
                    compliant = False

        return SpecComplianceResult(
            component="CustomerSuccessAgent",
            spec_name="SentimentAnalysisSpec",
            compliant=compliant,
            issues=issues,
            details={"checked_items": len(result)},
        )


class SpecRunner:
    """
    Main specification runner.
    
    Orchestrates spec validation across the platform.
    """

    def __init__(self):
        self.validator = SpecValidator()
        self.report = None

    def run_all_validations(self, test_data: Dict[str, Any]) -> ComplianceReport:
        """
        Run all specification validations.
        
        Args:
            test_data: Dictionary with test components
                - contacts: List[Contact]
                - profiles: List[ClientProfile]
                - tickets: List[SupportTicket]
                - messages: List[Message]
                - churn_results: List[Dict]
                - sentiment_results: List[List[Dict]]
        
        Returns:
            ComplianceReport with all results
        """
        results = []

        # Validate contacts
        for contact in test_data.get('contacts', []):
            result = self.validator.validate_contact_spec(contact)
            results.append(result)
            logger.info(f"Contact validation: {result.compliant}")

        # Validate profiles
        for profile in test_data.get('profiles', []):
            result = self.validator.validate_profile_spec(profile)
            results.append(result)
            logger.info(f"Profile validation: {result.compliant}")

        # Validate tickets
        for ticket in test_data.get('tickets', []):
            result = self.validator.validate_ticket_spec(ticket)
            results.append(result)
            logger.info(f"Ticket validation: {result.compliant}")

        # Validate messages
        for message in test_data.get('messages', []):
            result = self.validator.validate_message_spec(message)
            results.append(result)
            logger.info(f"Message validation: {result.compliant}")

        # Validate churn scoring outputs
        for churn_result in test_data.get('churn_results', []):
            result = self.validator.validate_churn_risk_output(churn_result)
            results.append(result)
            logger.info(f"Churn risk validation: {result.compliant}")

        # Validate sentiment outputs
        for sentiment_result in test_data.get('sentiment_results', []):
            result = self.validator.validate_sentiment_output(sentiment_result)
            results.append(result)
            logger.info(f"Sentiment validation: {result.compliant}")

        # Compile report
        passed = sum(1 for r in results if r.compliant)
        total = len(results)
        
        report = ComplianceReport(
            total_checks=total,
            passed_checks=passed,
            failed_checks=total - passed,
            compliance_percentage=(passed / total * 100) if total > 0 else 100.0,
            results=results,
        )

        self.report = report
        return report

    def print_report(self) -> None:
        """Print compliance report to console"""
        if not self.report:
            logger.info("No report available. Run validations first.")
            return

        report = self.report
        print("\n" + "=" * 80)
        print("SPECIFICATION COMPLIANCE REPORT")
        print("=" * 80)
        print(f"Total Checks: {report.total_checks}")
        print(f"Passed: {report.passed_checks}")
        print(f"Failed: {report.failed_checks}")
        print(f"Compliance: {report.compliance_percentage:.1f}%")
        print("=" * 80)

        # Group by component
        by_component = {}
        for result in report.results:
            if result.component not in by_component:
                by_component[result.component] = []
            by_component[result.component].append(result)

        for component, results in sorted(by_component.items()):
            passed = sum(1 for r in results if r.compliant)
            print(f"\n{component}: {passed}/{len(results)} compliant")
            for result in results:
                status = "✓" if result.compliant else "✗"
                print(f"  {status} {result.spec_name}")
                if result.issues:
                    for issue in result.issues:
                        print(f"    - {issue}")

        print("\n" + "=" * 80)

    def to_json(self) -> str:
        """Convert report to JSON"""
        if not self.report:
            return "{}"
        return json.dumps(self.report.to_dict(), indent=2, default=str)


if __name__ == "__main__":
    # Example usage
    logger.info("Specification validation framework initialized")
    runner = SpecRunner()
    logger.info("Use SpecRunner to validate platform components")
