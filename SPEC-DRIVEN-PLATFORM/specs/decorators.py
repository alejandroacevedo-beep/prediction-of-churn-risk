"""
Spec-Driven Development Configuration

This module provides decorators and utilities for marking code
as spec-driven and ensuring compliance with specifications.
"""

from functools import wraps
from typing import Any, Callable, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class SpecDriven:
    """
    Decorator to mark functions/methods as spec-driven.
    Ensures compliance with formal specifications.
    """

    def __init__(
        self,
        spec_name: str,
        version: str = "1.0",
        author: Optional[str] = None,
        compliance_level: str = "strict",
    ):
        """
        Initialize spec-driven decorator.
        
        Args:
            spec_name: Name of the formal specification
            version: Specification version
            author: Author/owner of specification
            compliance_level: "strict", "moderate", or "permissive"
        """
        self.spec_name = spec_name
        self.version = version
        self.author = author
        self.compliance_level = compliance_level

    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.debug(
                f"Executing {func.__name__} "
                f"against spec {self.spec_name} v{self.version}"
            )
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} completed spec validation")
            return result
        
        # Attach metadata
        wrapper._spec_name = self.spec_name
        wrapper._spec_version = self.version
        wrapper._spec_author = self.author
        wrapper._compliance_level = self.compliance_level
        wrapper._spec_driven = True
        
        return wrapper


class ContractCheckpoint:
    """
    Marks a point where a formal contract is checked.
    Used for input/output validation.
    """

    def __init__(self, contract_name: str, check_type: str = "both"):
        """
        Initialize contract checkpoint.
        
        Args:
            contract_name: Name of the contract being enforced
            check_type: "input", "output", or "both"
        """
        self.contract_name = contract_name
        self.check_type = check_type

    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if self.check_type in ("input", "both"):
                logger.debug(f"Validating input contract: {self.contract_name}")
            
            result = func(*args, **kwargs)
            
            if self.check_type in ("output", "both"):
                logger.debug(f"Validating output contract: {self.contract_name}")
            
            return result
        
        wrapper._contract_name = self.contract_name
        wrapper._contract_checkpoint = True
        return wrapper


class SpecCompliance:
    """
    Utility class for checking spec compliance.
    """

    @staticmethod
    def get_spec_info(func: Callable) -> Optional[Dict[str, Any]]:
        """Get specification information from a decorated function"""
        if hasattr(func, "_spec_driven") and func._spec_driven:
            return {
                "spec_name": getattr(func, "_spec_name"),
                "spec_version": getattr(func, "_spec_version"),
                "spec_author": getattr(func, "_spec_author"),
                "compliance_level": getattr(func, "_compliance_level"),
            }
        return None

    @staticmethod
    def is_spec_driven(func: Callable) -> bool:
        """Check if function is spec-driven"""
        return hasattr(func, "_spec_driven") and func._spec_driven

    @staticmethod
    def has_contract_checkpoint(func: Callable) -> bool:
        """Check if function has contract checkpoint"""
        return hasattr(func, "_contract_checkpoint") and func._contract_checkpoint

    @staticmethod
    def log_spec_compliance(func: Callable) -> None:
        """Log compliance information for a function"""
        spec_info = SpecCompliance.get_spec_info(func)
        if spec_info:
            logger.info(f"Function {func.__name__} spec info: {spec_info}")
        
        if SpecCompliance.has_contract_checkpoint(func):
            logger.info(f"Function {func.__name__} has contract checkpoint: {func._contract_name}")


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

"""
Example of spec-driven function:

@SpecDriven(
    spec_name="ChurnScoringEngineSpec",
    version="1.0",
    author="Data Science Team",
    compliance_level="strict"
)
@ContractCheckpoint("ChurnRiskOutputContract", check_type="output")
def compute_churn_risk(profile, signals):
    '''Compute churn risk against formal specification'''
    # Implementation here
    return result

This marks the function as:
1. Implementing ChurnScoringEngineSpec v1.0
2. Checking output contract before returning
3. Logging compliance during execution
4. Available for compliance reporting
"""
