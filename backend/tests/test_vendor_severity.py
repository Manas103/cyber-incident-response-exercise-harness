import pytest

from incident_harness.intake.reference_severity_oracle import classify_severity_reference
from incident_harness.intake.severity import classify_severity
from incident_harness.vendor.fixtures import build_vendor_severity_sample


@pytest.mark.parametrize("inputs", build_vendor_severity_sample(500, seed=20261116))
def test_primary_matches_reference_oracle_over_vendor_derived_inputs(inputs):
    assert classify_severity(inputs) == classify_severity_reference(inputs)
