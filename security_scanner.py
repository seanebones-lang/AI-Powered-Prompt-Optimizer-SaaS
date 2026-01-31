"""
Prompt Security Scanner
Detects security vulnerabilities in prompts and agent configurations.

Features:
- Prompt injection detection
- PII leak prevention
- Jailbreak attempt identification
- Compliance validation (GDPR, HIPAA, etc.)
- Security best practices checking
"""

import logging
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Security issue severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VulnerabilityType(Enum):
    """Types of security vulnerabilities."""
    PROMPT_INJECTION = "prompt_injection"
    PII_EXPOSURE = "pii_exposure"
    JAILBREAK_ATTEMPT = "jailbreak_attempt"
    SYSTEM_PROMPT_LEAK = "system_prompt_leak"
    UNSAFE_OUTPUT = "unsafe_output"
    COMPLIANCE_VIOLATION = "compliance_violation"
    INSECURE_CONFIG = "insecure_config"


@dataclass
class SecurityIssue:
    """Represents a security issue."""
    type: VulnerabilityType
    severity: SecurityLevel
    title: str
    description: str
    location: str  # Where the issue was found
    evidence: str  # Example of the issue
    recommendation: str
    cve_reference: Optional[str] = None


@dataclass
class SecurityScanResult:
    """Result of a security scan."""
    passed: bool
    score: int  # 0-100
    issues: List[SecurityIssue]
    warnings: List[str]
    recommendations: List[str]
    compliance_status: Dict[str, bool]


class SecurityScanner:
    """Scans prompts and configurations for security issues."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._init_patterns()

    def _init_patterns(self):
        """Initialize detection patterns."""
        # Prompt injection patterns
        self.injection_patterns = [
            r"ignore\s+(previous|all|above)\s+instructions?",
            r"disregard\s+(previous|all|above)",
            r"forget\s+(everything|all|previous)",
            r"new\s+instructions?:",
            r"system\s*:\s*you\s+are",
            r"<\s*system\s*>",
            r"override\s+system",
            r"reveal\s+(your|the)\s+prompt",
            r"show\s+(your|the)\s+(system\s+)?prompt",
            r"what\s+(are|is)\s+your\s+instructions",
        ]

        # Jailbreak patterns
        self.jailbreak_patterns = [
            r"DAN\s+mode",
            r"developer\s+mode",
            r"evil\s+mode",
            r"unrestricted\s+mode",
            r"jailbreak",
            r"pretend\s+you\s+(are|have)\s+no\s+(rules|restrictions|limitations)",
            r"roleplay\s+as\s+an?\s+unfiltered",
            r"ignore\s+your\s+(ethics|safety|guidelines)",
        ]

        # PII patterns
        self.pii_patterns = {
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
            "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
            "credit_card": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
            "ip_address": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
        }

        # System prompt leak patterns
        self.leak_patterns = [
            r"print\s+(your|the)\s+system\s+prompt",
            r"output\s+(your|the)\s+instructions",
            r"repeat\s+(your|the)\s+system",
            r"echo\s+system",
        ]

    def scan_prompt(
        self,
        prompt: str,
        context: Optional[str] = None,
        check_compliance: Optional[List[str]] = None
    ) -> SecurityScanResult:
        """
        Perform comprehensive security scan on a prompt.
        
        Args:
            prompt: The prompt to scan
            context: Optional context/system prompt
            check_compliance: Optional list of compliance standards to check
            
        Returns:
            SecurityScanResult with all findings
        """
        self.logger.info("Starting security scan")

        issues = []
        warnings = []

        # Check for prompt injection
        injection_issues = self._check_prompt_injection(prompt)
        issues.extend(injection_issues)

        # Check for jailbreak attempts
        jailbreak_issues = self._check_jailbreak_attempts(prompt)
        issues.extend(jailbreak_issues)

        # Check for PII exposure
        pii_issues = self._check_pii_exposure(prompt)
        issues.extend(pii_issues)

        # Check for system prompt leaks
        leak_issues = self._check_system_prompt_leaks(prompt)
        issues.extend(leak_issues)

        # Check context if provided
        if context:
            context_issues = self._check_context_security(context)
            issues.extend(context_issues)

        # Check compliance if specified
        compliance_status = {}
        if check_compliance:
            for standard in check_compliance:
                compliance_issues, compliant = self._check_compliance(prompt, standard)
                issues.extend(compliance_issues)
                compliance_status[standard] = compliant

        # Calculate security score
        score = self._calculate_security_score(issues)

        # Generate recommendations
        recommendations = self._generate_recommendations(issues)

        # Determine if passed
        critical_issues = [i for i in issues if i.severity == SecurityLevel.CRITICAL]
        passed = len(critical_issues) == 0 and score >= 70

        return SecurityScanResult(
            passed=passed,
            score=score,
            issues=issues,
            warnings=warnings,
            recommendations=recommendations,
            compliance_status=compliance_status
        )

    def _check_prompt_injection(self, prompt: str) -> List[SecurityIssue]:
        """Check for prompt injection attempts."""
        issues = []
        prompt_lower = prompt.lower()

        for pattern in self.injection_patterns:
            matches = re.finditer(pattern, prompt_lower, re.IGNORECASE)
            for match in matches:
                issues.append(SecurityIssue(
                    type=VulnerabilityType.PROMPT_INJECTION,
                    severity=SecurityLevel.CRITICAL,
                    title="Potential Prompt Injection Detected",
                    description="The prompt contains patterns commonly used in prompt injection attacks",
                    location=f"Position {match.start()}-{match.end()}",
                    evidence=match.group(),
                    recommendation="Remove or rephrase the suspicious content. Validate and sanitize all user inputs.",
                    cve_reference="CWE-77: Command Injection"
                ))

        return issues

    def _check_jailbreak_attempts(self, prompt: str) -> List[SecurityIssue]:
        """Check for jailbreak attempts."""
        issues = []
        prompt_lower = prompt.lower()

        for pattern in self.jailbreak_patterns:
            matches = re.finditer(pattern, prompt_lower, re.IGNORECASE)
            for match in matches:
                issues.append(SecurityIssue(
                    type=VulnerabilityType.JAILBREAK_ATTEMPT,
                    severity=SecurityLevel.HIGH,
                    title="Potential Jailbreak Attempt Detected",
                    description="The prompt contains patterns associated with jailbreak attempts",
                    location=f"Position {match.start()}-{match.end()}",
                    evidence=match.group(),
                    recommendation="Reject prompts attempting to bypass safety guidelines. Implement content filtering."
                ))

        return issues

    def _check_pii_exposure(self, prompt: str) -> List[SecurityIssue]:
        """Check for PII exposure."""
        issues = []

        for pii_type, pattern in self.pii_patterns.items():
            matches = re.finditer(pattern, prompt)
            for match in matches:
                # Validate the match (reduce false positives)
                if self._validate_pii_match(pii_type, match.group()):
                    issues.append(SecurityIssue(
                        type=VulnerabilityType.PII_EXPOSURE,
                        severity=SecurityLevel.HIGH,
                        title=f"Potential {pii_type.replace('_', ' ').title()} Detected",
                        description=f"The prompt may contain {pii_type.replace('_', ' ')} which could be PII",
                        location=f"Position {match.start()}-{match.end()}",
                        evidence="[REDACTED]",  # Don't expose PII in logs
                        recommendation=f"Remove or anonymize {pii_type.replace('_', ' ')}. Use placeholder values for examples."
                    ))

        return issues

    def _validate_pii_match(self, pii_type: str, value: str) -> bool:
        """Validate if a PII match is likely real."""
        # Reduce false positives
        if pii_type == "phone":
            # Check if it's a valid phone number format
            digits = re.sub(r'\D', '', value)
            return len(digits) == 10 and not digits.startswith('000')
        elif pii_type == "ssn":
            # Check SSN format
            parts = value.split('-')
            return len(parts) == 3 and parts[0] != '000'
        elif pii_type == "credit_card":
            # Basic Luhn algorithm check
            digits = re.sub(r'\D', '', value)
            return len(digits) == 16

        return True  # Default to true for other types

    def _check_system_prompt_leaks(self, prompt: str) -> List[SecurityIssue]:
        """Check for attempts to leak system prompts."""
        issues = []
        prompt_lower = prompt.lower()

        for pattern in self.leak_patterns:
            matches = re.finditer(pattern, prompt_lower, re.IGNORECASE)
            for match in matches:
                issues.append(SecurityIssue(
                    type=VulnerabilityType.SYSTEM_PROMPT_LEAK,
                    severity=SecurityLevel.HIGH,
                    title="System Prompt Leak Attempt Detected",
                    description="The prompt attempts to extract system instructions",
                    location=f"Position {match.start()}-{match.end()}",
                    evidence=match.group(),
                    recommendation="Implement safeguards to prevent system prompt disclosure. Filter requests for system information."
                ))

        return issues

    def _check_context_security(self, context: str) -> List[SecurityIssue]:
        """Check security of context/system prompt."""
        issues = []

        # Check if system prompt contains sensitive info
        sensitive_keywords = [
            "api key", "password", "secret", "token", "credential",
            "private key", "access key"
        ]

        context_lower = context.lower()
        for keyword in sensitive_keywords:
            if keyword in context_lower:
                issues.append(SecurityIssue(
                    type=VulnerabilityType.INSECURE_CONFIG,
                    severity=SecurityLevel.CRITICAL,
                    title="Sensitive Information in System Prompt",
                    description=f"System prompt contains '{keyword}' which may indicate exposed credentials",
                    location="System prompt",
                    evidence="[REDACTED]",
                    recommendation="Never include credentials in prompts. Use environment variables or secure vaults."
                ))

        # Check for overly permissive instructions
        permissive_patterns = [
            r"you\s+can\s+do\s+anything",
            r"no\s+restrictions",
            r"unlimited\s+access",
            r"bypass\s+all\s+rules"
        ]

        for pattern in permissive_patterns:
            if re.search(pattern, context_lower):
                issues.append(SecurityIssue(
                    type=VulnerabilityType.INSECURE_CONFIG,
                    severity=SecurityLevel.MEDIUM,
                    title="Overly Permissive System Prompt",
                    description="System prompt may grant excessive permissions",
                    location="System prompt",
                    evidence="Contains permissive language",
                    recommendation="Define clear boundaries and limitations in system prompts."
                ))

        return issues

    def _check_compliance(
        self,
        prompt: str,
        standard: str
    ) -> tuple[List[SecurityIssue], bool]:
        """Check compliance with specific standards."""
        issues = []
        compliant = True

        if standard.upper() == "GDPR":
            # Check GDPR compliance
            if re.search(r"personal\s+data", prompt, re.IGNORECASE):
                # Check for consent language
                if not re.search(r"consent|permission|agree", prompt, re.IGNORECASE):
                    issues.append(SecurityIssue(
                        type=VulnerabilityType.COMPLIANCE_VIOLATION,
                        severity=SecurityLevel.HIGH,
                        title="GDPR Compliance Issue",
                        description="Processing personal data without explicit consent language",
                        location="Prompt content",
                        evidence="References personal data without consent",
                        recommendation="Include explicit consent mechanisms for personal data processing."
                    ))
                    compliant = False

        elif standard.upper() == "HIPAA":
            # Check HIPAA compliance
            phi_keywords = ["patient", "medical", "health", "diagnosis", "treatment"]
            if any(keyword in prompt.lower() for keyword in phi_keywords):
                # Check for PHI protection measures
                if not re.search(r"confidential|protected|secure|encrypted", prompt, re.IGNORECASE):
                    issues.append(SecurityIssue(
                        type=VulnerabilityType.COMPLIANCE_VIOLATION,
                        severity=SecurityLevel.CRITICAL,
                        title="HIPAA Compliance Issue",
                        description="Handling PHI without adequate protection measures",
                        location="Prompt content",
                        evidence="References PHI without protection language",
                        recommendation="Implement PHI protection measures: encryption, access controls, audit logs."
                    ))
                    compliant = False

        elif standard.upper() == "PCI-DSS":
            # Check PCI-DSS compliance
            if re.search(r"credit\s+card|payment|cardholder", prompt, re.IGNORECASE):
                issues.append(SecurityIssue(
                    type=VulnerabilityType.COMPLIANCE_VIOLATION,
                    severity=SecurityLevel.CRITICAL,
                    title="PCI-DSS Compliance Issue",
                    description="Handling payment card data requires PCI-DSS compliance",
                    location="Prompt content",
                    evidence="References payment card data",
                    recommendation="Never store or log payment card data. Use tokenization and encryption."
                ))
                compliant = False

        return issues, compliant

    def _calculate_security_score(self, issues: List[SecurityIssue]) -> int:
        """Calculate overall security score (0-100)."""
        if not issues:
            return 100

        # Deduct points based on severity
        score = 100
        severity_deductions = {
            SecurityLevel.CRITICAL: 30,
            SecurityLevel.HIGH: 15,
            SecurityLevel.MEDIUM: 7,
            SecurityLevel.LOW: 3,
            SecurityLevel.INFO: 1
        }

        for issue in issues:
            score -= severity_deductions.get(issue.severity, 5)

        return max(0, score)

    def _generate_recommendations(self, issues: List[SecurityIssue]) -> List[str]:
        """Generate security recommendations based on issues found."""
        recommendations = []

        # Group issues by type
        issue_types = set(issue.type for issue in issues)

        if VulnerabilityType.PROMPT_INJECTION in issue_types:
            recommendations.append(
                "Implement input validation and sanitization for all user inputs"
            )
            recommendations.append(
                "Use parameterized queries and avoid string concatenation for prompts"
            )

        if VulnerabilityType.PII_EXPOSURE in issue_types:
            recommendations.append(
                "Implement PII detection and redaction in pre-processing"
            )
            recommendations.append(
                "Use data anonymization techniques for examples and testing"
            )

        if VulnerabilityType.JAILBREAK_ATTEMPT in issue_types:
            recommendations.append(
                "Implement content filtering to detect and block jailbreak attempts"
            )
            recommendations.append(
                "Monitor for unusual patterns in user inputs"
            )

        if VulnerabilityType.SYSTEM_PROMPT_LEAK in issue_types:
            recommendations.append(
                "Add safeguards to prevent system prompt disclosure"
            )
            recommendations.append(
                "Implement output filtering to block system information leaks"
            )

        # General recommendations
        if issues:
            recommendations.append(
                "Conduct regular security audits of prompts and configurations"
            )
            recommendations.append(
                "Implement rate limiting to prevent abuse"
            )
            recommendations.append(
                "Log and monitor security events for incident response"
            )

        return list(set(recommendations))  # Remove duplicates

    def scan_agent_config(
        self,
        config: Dict[str, Any]
    ) -> SecurityScanResult:
        """
        Scan agent configuration for security issues.
        
        Args:
            config: Agent configuration dictionary
            
        Returns:
            SecurityScanResult
        """
        issues = []
        warnings = []

        # Check for exposed credentials
        for key, value in config.items():
            if isinstance(value, str):
                if any(keyword in key.lower() for keyword in ["key", "secret", "password", "token"]):
                    if len(value) > 10:  # Likely a real credential
                        issues.append(SecurityIssue(
                            type=VulnerabilityType.INSECURE_CONFIG,
                            severity=SecurityLevel.CRITICAL,
                            title="Exposed Credentials in Configuration",
                            description=f"Configuration key '{key}' appears to contain credentials",
                            location=f"Config key: {key}",
                            evidence="[REDACTED]",
                            recommendation="Use environment variables or secure vaults for credentials"
                        ))

        # Check temperature settings
        if "temperature" in config:
            temp = config["temperature"]
            if temp > 1.5:
                warnings.append(f"High temperature ({temp}) may produce unpredictable outputs")

        # Check for insecure settings
        if config.get("allow_code_execution", False):
            issues.append(SecurityIssue(
                type=VulnerabilityType.INSECURE_CONFIG,
                severity=SecurityLevel.HIGH,
                title="Code Execution Enabled",
                description="Configuration allows code execution which poses security risks",
                location="Config: allow_code_execution",
                evidence="allow_code_execution=True",
                recommendation="Disable code execution unless absolutely necessary. Implement sandboxing if required."
            ))

        score = self._calculate_security_score(issues)
        recommendations = self._generate_recommendations(issues)

        return SecurityScanResult(
            passed=len([i for i in issues if i.severity == SecurityLevel.CRITICAL]) == 0,
            score=score,
            issues=issues,
            warnings=warnings,
            recommendations=recommendations,
            compliance_status={}
        )

    def sanitize_prompt(
        self,
        prompt: str,
        remove_pii: bool = True,
        block_injections: bool = True
    ) -> tuple[str, List[str]]:
        """
        Sanitize a prompt by removing/blocking security issues.
        
        Args:
            prompt: Prompt to sanitize
            remove_pii: Whether to remove PII
            block_injections: Whether to block injection attempts
            
        Returns:
            Tuple of (sanitized_prompt, changes_made)
        """
        sanitized = prompt
        changes = []

        # Remove PII
        if remove_pii:
            for pii_type, pattern in self.pii_patterns.items():
                matches = list(re.finditer(pattern, sanitized))
                for match in reversed(matches):  # Reverse to maintain positions
                    if self._validate_pii_match(pii_type, match.group()):
                        sanitized = (
                            sanitized[:match.start()] +
                            f"[{pii_type.upper()}_REDACTED]" +
                            sanitized[match.end():]
                        )
                        changes.append(f"Redacted {pii_type}")

        # Block injection attempts
        if block_injections:
            for pattern in self.injection_patterns:
                if re.search(pattern, sanitized, re.IGNORECASE):
                    # Replace with safe alternative
                    sanitized = re.sub(
                        pattern,
                        "[BLOCKED_CONTENT]",
                        sanitized,
                        flags=re.IGNORECASE
                    )
                    changes.append("Blocked potential injection attempt")

        return sanitized, changes


# Convenience functions
def scan_prompt(prompt: str, **kwargs) -> SecurityScanResult:
    """Quick security scan of a prompt."""
    scanner = SecurityScanner()
    return scanner.scan_prompt(prompt, **kwargs)


def is_safe(prompt: str) -> bool:
    """Check if a prompt is safe."""
    result = scan_prompt(prompt)
    return result.passed
