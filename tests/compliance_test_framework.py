"""
Standards Compliance Testing Framework
Testing framework for ISO 26262, ISO 27001, GDPR, and other standards.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
import unittest

LOGGER = logging.getLogger(__name__)


class ComplianceStandard(Enum):
    """Compliance standards."""
    ISO_26262 = "ISO_26262"
    ISO_27001 = "ISO_27001"
    GDPR = "GDPR"
    ISO_14229 = "ISO_14229"
    ISO_15765 = "ISO_15765"
    ISO_25010 = "ISO_25010"


class TestResult(Enum):
    """Test result."""
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    SKIP = "SKIP"


@dataclass
class ComplianceTest:
    """Compliance test definition."""
    test_id: str
    standard: ComplianceStandard
    name: str
    description: str
    test_function: Callable[[], TestResult]
    required: bool = True
    asil_level: Optional[str] = None


class ComplianceTestFramework:
    """Framework for compliance testing."""
    
    def __init__(self):
        self.tests: Dict[str, ComplianceTest] = {}
        self.test_results: Dict[str, Dict[str, Any]] = {}
        self._register_tests()
    
    def _register_tests(self) -> None:
        """Register all compliance tests."""
        
        # ISO 26262 Tests
        self.register_test(ComplianceTest(
            test_id="ISO26262-001",
            standard=ComplianceStandard.ISO_26262,
            name="Safety Goals Defined",
            description="Verify that safety goals are defined for critical functions",
            test_function=self._test_safety_goals_defined,
            required=True,
            asil_level="D",
        ))
        
        self.register_test(ComplianceTest(
            test_id="ISO26262-002",
            standard=ComplianceStandard.ISO_26262,
            name="Safety Monitors Active",
            description="Verify that safety monitors are active and functioning",
            test_function=self._test_safety_monitors_active,
            required=True,
            asil_level="D",
        ))
        
        # ISO 27001 Tests
        self.register_test(ComplianceTest(
            test_id="ISO27001-001",
            standard=ComplianceStandard.ISO_27001,
            name="Encryption Enabled",
            description="Verify that data encryption is enabled",
            test_function=self._test_encryption_enabled,
            required=True,
        ))
        
        self.register_test(ComplianceTest(
            test_id="ISO27001-002",
            standard=ComplianceStandard.ISO_27001,
            name="Access Control Active",
            description="Verify that access control is implemented",
            test_function=self._test_access_control_active,
            required=True,
        ))
        
        self.register_test(ComplianceTest(
            test_id="ISO27001-003",
            standard=ComplianceStandard.ISO_27001,
            name="Audit Logging Active",
            description="Verify that audit logging is active",
            test_function=self._test_audit_logging_active,
            required=True,
        ))
        
        # GDPR Tests
        self.register_test(ComplianceTest(
            test_id="GDPR-001",
            standard=ComplianceStandard.GDPR,
            name="Consent Management",
            description="Verify that consent management is implemented",
            test_function=self._test_consent_management,
            required=True,
        ))
        
        self.register_test(ComplianceTest(
            test_id="GDPR-002",
            standard=ComplianceStandard.GDPR,
            name="Data Retention Policies",
            description="Verify that data retention policies are defined",
            test_function=self._test_data_retention_policies,
            required=True,
        ))
        
        self.register_test(ComplianceTest(
            test_id="GDPR-003",
            standard=ComplianceStandard.GDPR,
            name="Data Subject Rights",
            description="Verify that data subject rights are supported",
            test_function=self._test_data_subject_rights,
            required=True,
        ))
        
        # ISO 14229 Tests
        self.register_test(ComplianceTest(
            test_id="ISO14229-001",
            standard=ComplianceStandard.ISO_14229,
            name="UDS Services Implemented",
            description="Verify that all required UDS services are implemented",
            test_function=self._test_uds_services_implemented,
            required=True,
        ))
        
        # ISO 25010 Tests
        self.register_test(ComplianceTest(
            test_id="ISO25010-001",
            standard=ComplianceStandard.ISO_25010,
            name="Quality Metrics Tracked",
            description="Verify that quality metrics are being tracked",
            test_function=self._test_quality_metrics_tracked,
            required=False,
        ))
    
    def register_test(self, test: ComplianceTest) -> None:
        """Register a compliance test."""
        self.tests[test.test_id] = test
    
    def run_test(self, test_id: str) -> Dict[str, Any]:
        """Run a single compliance test."""
        test = self.tests.get(test_id)
        if not test:
            return {
                "test_id": test_id,
                "result": TestResult.SKIP,
                "message": "Test not found",
            }
        
        try:
            start_time = time.time()
            result = test.test_function()
            duration = time.time() - start_time
            
            test_result = {
                "test_id": test_id,
                "standard": test.standard.value,
                "name": test.name,
                "result": result.value,
                "duration": duration,
                "timestamp": time.time(),
            }
            
            self.test_results[test_id] = test_result
            return test_result
            
        except Exception as e:
            LOGGER.error("Error running test %s: %s", test_id, e)
            return {
                "test_id": test_id,
                "result": TestResult.FAIL.value,
                "message": str(e),
            }
    
    def run_all_tests(self, standard: Optional[ComplianceStandard] = None) -> Dict[str, Any]:
        """Run all compliance tests (optionally filtered by standard)."""
        results = {}
        
        for test_id, test in self.tests.items():
            if standard and test.standard != standard:
                continue
            
            results[test_id] = self.run_test(test_id)
        
        return results
    
    def get_compliance_report(self) -> Dict[str, Any]:
        """Get comprehensive compliance report."""
        total_tests = len(self.tests)
        passed = sum(1 for r in self.test_results.values() if r.get("result") == TestResult.PASS.value)
        failed = sum(1 for r in self.test_results.values() if r.get("result") == TestResult.FAIL.value)
        warnings = sum(1 for r in self.test_results.values() if r.get("result") == TestResult.WARNING.value)
        
        # Group by standard
        by_standard = {}
        for test_id, result in self.test_results.items():
            standard = result.get("standard", "UNKNOWN")
            if standard not in by_standard:
                by_standard[standard] = {"passed": 0, "failed": 0, "warnings": 0, "total": 0}
            
            by_standard[standard]["total"] += 1
            if result.get("result") == TestResult.PASS.value:
                by_standard[standard]["passed"] += 1
            elif result.get("result") == TestResult.FAIL.value:
                by_standard[standard]["failed"] += 1
            elif result.get("result") == TestResult.WARNING.value:
                by_standard[standard]["warnings"] += 1
        
        return {
            "summary": {
                "total_tests": total_tests,
                "passed": passed,
                "failed": failed,
                "warnings": warnings,
                "pass_rate": passed / total_tests if total_tests > 0 else 0.0,
            },
            "by_standard": by_standard,
            "test_results": self.test_results,
        }
    
    # Test Functions
    
    def _test_safety_goals_defined(self) -> TestResult:
        """Test: Safety goals are defined."""
        try:
            from core.functional_safety import get_safety_manager
            manager = get_safety_manager()
            goals = manager.safety_goals
            
            if len(goals) > 0:
                return TestResult.PASS
            return TestResult.FAIL
        except Exception:
            return TestResult.FAIL
    
    def _test_safety_monitors_active(self) -> TestResult:
        """Test: Safety monitors are active."""
        try:
            from core.functional_safety import get_safety_manager
            manager = get_safety_manager()
            
            if manager._running and len(manager.safety_monitors) > 0:
                return TestResult.PASS
            return TestResult.WARNING
        except Exception:
            return TestResult.FAIL
    
    def _test_encryption_enabled(self) -> TestResult:
        """Test: Encryption is enabled."""
        try:
            from core.security_manager import get_security_manager
            manager = get_security_manager()
            
            # Test encryption
            test_data = b"test data"
            encrypted = manager.encrypt_data(test_data)
            decrypted = manager.decrypt_data(encrypted)
            
            if decrypted == test_data:
                return TestResult.PASS
            return TestResult.FAIL
        except Exception:
            return TestResult.FAIL
    
    def _test_access_control_active(self) -> TestResult:
        """Test: Access control is active."""
        try:
            from core.security_manager import get_security_manager
            manager = get_security_manager()
            
            if len(manager.access_control) > 0:
                return TestResult.PASS
            return TestResult.FAIL
        except Exception:
            return TestResult.FAIL
    
    def _test_audit_logging_active(self) -> TestResult:
        """Test: Audit logging is active."""
        try:
            from core.security_manager import get_security_manager
            manager = get_security_manager()
            
            # Log a test event
            manager._log_security_event(
                manager.SecurityEventType.ACCESS_GRANTED,
                user_id="test",
                resource="test",
                action="test",
                result="test",
            )
            
            if len(manager.audit_log) > 0:
                return TestResult.PASS
            return TestResult.FAIL
        except Exception:
            return TestResult.FAIL
    
    def _test_consent_management(self) -> TestResult:
        """Test: Consent management is implemented."""
        try:
            from core.gdpr_compliance import get_gdpr_manager
            manager = get_gdpr_manager()
            
            # Test consent recording
            consent = manager.record_consent(
                user_id="test",
                consent_type=manager.ConsentType.DATA_COLLECTION,
                granted=True,
            )
            
            if consent and manager.has_consent("test", manager.ConsentType.DATA_COLLECTION):
                return TestResult.PASS
            return TestResult.FAIL
        except Exception:
            return TestResult.FAIL
    
    def _test_data_retention_policies(self) -> TestResult:
        """Test: Data retention policies are defined."""
        try:
            from core.gdpr_compliance import get_gdpr_manager
            manager = get_gdpr_manager()
            
            if len(manager.retention_policies) > 0:
                return TestResult.PASS
            return TestResult.FAIL
        except Exception:
            return TestResult.FAIL
    
    def _test_data_subject_rights(self) -> TestResult:
        """Test: Data subject rights are supported."""
        try:
            from core.gdpr_compliance import get_gdpr_manager
            manager = get_gdpr_manager()
            
            # Test data access request
            request = manager.request_data_access("test")
            
            if request:
                return TestResult.PASS
            return TestResult.FAIL
        except Exception:
            return TestResult.FAIL
    
    def _test_uds_services_implemented(self) -> TestResult:
        """Test: UDS services are implemented."""
        try:
            from interfaces.complete_uds_services import CompleteUDSServices, UDSService
            
            # Check that all services are defined
            services = [s for s in UDSService]
            if len(services) >= 20:  # At least 20 services
                return TestResult.PASS
            return TestResult.WARNING
        except Exception:
            return TestResult.FAIL
    
    def _test_quality_metrics_tracked(self) -> TestResult:
        """Test: Quality metrics are tracked."""
        try:
            from core.quality_manager import get_quality_manager
            manager = get_quality_manager()
            
            # Record a test measurement
            manager.record_measurement(
                manager.QualityMetric.AVAILABILITY,
                0.99,
            )
            
            if len(manager.measurements) > 0:
                return TestResult.PASS
            return TestResult.WARNING
        except Exception:
            return TestResult.WARNING


# Global instance
_test_framework: Optional[ComplianceTestFramework] = None


def get_test_framework() -> ComplianceTestFramework:
    """Get global test framework instance."""
    global _test_framework
    if _test_framework is None:
        _test_framework = ComplianceTestFramework()
    return _test_framework


__all__ = [
    "ComplianceTestFramework",
    "ComplianceStandard",
    "TestResult",
    "ComplianceTest",
    "get_test_framework",
]

