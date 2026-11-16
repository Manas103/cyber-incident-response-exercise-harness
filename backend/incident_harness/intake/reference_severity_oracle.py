"""An independently coded reimplementation of severity.classify_severity, diffed exactly
against it in tests/test_intake_severity_oracle_diff.py. Deliberately a different code
shape: severity.py walks an ordered rule list built from lambdas; this version is a plain
nested if/elif decision tree with no shared helper and no list of rules, built straight
from the same written matrix description, not derived from or copy-pasted out of
severity.py."""

from .channels import (
    DATA_SENSITIVITY_CUSTOMER_PII,
    DATA_SENSITIVITY_PAYMENT_OR_CREDENTIALS,
    SCOPE_PLATFORM_WIDE,
    SCOPE_SINGLE_CUSTOMER,
)
from .severity import SEV1_CRITICAL, SEV2_HIGH, SEV3_MEDIUM, SEV4_LOW, SeverityInputs


def classify_severity_reference(inputs: SeverityInputs) -> str:
    sensitivity = inputs.data_sensitivity
    scope = inputs.scope
    exploited = inputs.actively_exploited

    if sensitivity == DATA_SENSITIVITY_PAYMENT_OR_CREDENTIALS:
        if exploited:
            return SEV1_CRITICAL
        return SEV2_HIGH

    if sensitivity == DATA_SENSITIVITY_CUSTOMER_PII:
        if scope == SCOPE_PLATFORM_WIDE:
            if exploited:
                return SEV1_CRITICAL
            return SEV2_HIGH
        if exploited:
            return SEV2_HIGH
        return SEV3_MEDIUM

    if scope == SCOPE_PLATFORM_WIDE:
        if exploited:
            return SEV2_HIGH
        return SEV3_MEDIUM

    if exploited and scope != SCOPE_SINGLE_CUSTOMER:
        return SEV3_MEDIUM

    return SEV4_LOW
