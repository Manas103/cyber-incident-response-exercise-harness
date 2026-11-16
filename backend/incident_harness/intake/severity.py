"""The written severity matrix: a fixed, ordered set of rules over 3 inputs (what data is
exposed, how many customers are in scope, whether the issue is actively being exploited),
each rule naming the severity it produces. This is the "written matrix" the resume bullet
names; it is written down here once, in order, specifically so a human reviewer could print
this table and audit a classification by hand, the same reason detector.py's playbook
comparison above is spelled out rather than learned.

Implementation note (for the reference-oracle diff in reference_severity_oracle.py): this
version walks MATRIX_RULES, an ordered list of (predicate, severity) pairs, top to bottom,
and returns the first predicate that matches. The reference oracle is a differently-shaped
nested if/elif decision tree over the same 3 inputs, built independently from the same
written rules, not a renamed copy."""

from dataclasses import dataclass
from typing import Callable

from .channels import (
    DATA_SENSITIVITY_CUSTOMER_PII,
    DATA_SENSITIVITY_PAYMENT_OR_CREDENTIALS,
    SCOPE_PLATFORM_WIDE,
    SCOPE_SINGLE_CUSTOMER,
)

SEV1_CRITICAL = "SEV1"
SEV2_HIGH = "SEV2"
SEV3_MEDIUM = "SEV3"
SEV4_LOW = "SEV4"


@dataclass(frozen=True)
class SeverityInputs:
    data_sensitivity: str
    scope: str
    actively_exploited: bool


def _rule(predicate: Callable[[SeverityInputs], bool], severity: str) -> tuple[Callable[[SeverityInputs], bool], str]:
    return predicate, severity


# The written matrix, in the order a reviewer is meant to read it: most severe rule first.
# Every rule after the first only applies when no earlier rule matched.
MATRIX_RULES: list[tuple[Callable[[SeverityInputs], bool], str]] = [
    _rule(lambda i: i.data_sensitivity == DATA_SENSITIVITY_PAYMENT_OR_CREDENTIALS and i.actively_exploited, SEV1_CRITICAL),
    _rule(lambda i: i.data_sensitivity == DATA_SENSITIVITY_PAYMENT_OR_CREDENTIALS, SEV2_HIGH),
    _rule(lambda i: i.data_sensitivity == DATA_SENSITIVITY_CUSTOMER_PII and i.scope == SCOPE_PLATFORM_WIDE and i.actively_exploited, SEV1_CRITICAL),
    _rule(lambda i: i.data_sensitivity == DATA_SENSITIVITY_CUSTOMER_PII and i.scope == SCOPE_PLATFORM_WIDE, SEV2_HIGH),
    _rule(lambda i: i.data_sensitivity == DATA_SENSITIVITY_CUSTOMER_PII and i.actively_exploited, SEV2_HIGH),
    _rule(lambda i: i.data_sensitivity == DATA_SENSITIVITY_CUSTOMER_PII, SEV3_MEDIUM),
    _rule(lambda i: i.scope == SCOPE_PLATFORM_WIDE and i.actively_exploited, SEV2_HIGH),
    _rule(lambda i: i.scope == SCOPE_PLATFORM_WIDE, SEV3_MEDIUM),
    _rule(lambda i: i.actively_exploited and i.scope != SCOPE_SINGLE_CUSTOMER, SEV3_MEDIUM),
    _rule(lambda _i: True, SEV4_LOW),
]


def classify_severity(inputs: SeverityInputs) -> str:
    for predicate, severity in MATRIX_RULES:
        if predicate(inputs):
            return severity
    raise AssertionError("unreachable: the final rule matches unconditionally")
