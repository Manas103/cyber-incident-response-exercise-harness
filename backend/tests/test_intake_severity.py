import pytest

from incident_harness.intake.fixtures import build_severity_inputs_sample
from incident_harness.intake.reference_severity_oracle import classify_severity_reference
from incident_harness.intake.severity import SEV1_CRITICAL, SEV2_HIGH, SEV3_MEDIUM, SEV4_LOW, SeverityInputs, classify_severity


def test_exploited_payment_data_is_critical():
    inputs = SeverityInputs(data_sensitivity="payment_or_credentials", scope="single_customer", actively_exploited=True)
    assert classify_severity(inputs) == SEV1_CRITICAL


def test_unexploited_payment_data_is_high_not_critical():
    inputs = SeverityInputs(data_sensitivity="payment_or_credentials", scope="single_customer", actively_exploited=False)
    assert classify_severity(inputs) == SEV2_HIGH


def test_no_sensitive_data_and_narrow_scope_and_not_exploited_is_low():
    inputs = SeverityInputs(data_sensitivity="none", scope="single_customer", actively_exploited=False)
    assert classify_severity(inputs) == SEV4_LOW


def test_customer_pii_single_customer_not_exploited_is_medium():
    inputs = SeverityInputs(data_sensitivity="customer_pii", scope="single_customer", actively_exploited=False)
    assert classify_severity(inputs) == SEV3_MEDIUM


@pytest.mark.parametrize("inputs", build_severity_inputs_sample(500, seed=20260801))
def test_primary_matches_reference_oracle(inputs):
    assert classify_severity(inputs) == classify_severity_reference(inputs)


def test_every_combination_of_the_24_produces_exactly_one_severity():
    sample = build_severity_inputs_sample(24, seed=1)
    assert len(sample) == 24
    for inputs in sample:
        severity = classify_severity(inputs)
        assert severity in {SEV1_CRITICAL, SEV2_HIGH, SEV3_MEDIUM, SEV4_LOW}
