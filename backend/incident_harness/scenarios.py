"""The fixed exercise design: 6 incident-response scenarios over a
simulated utility IT (and one OT/SCADA) estate, each with a written
playbook of exactly 4 named steps.

Taxonomy (documented, not incidental): every playbook step belongs to
exactly one of 4 phases, in fixed order:

  detect     - the responder recognizes the incident from a specific
               signal (an alert, a log line, a report).
  contain    - the responder stops the incident from spreading further
               (isolate a host, revoke a credential, block a source).
  eradicate  - the responder removes the cause (malware, a rogue key,
               an unauthorized session) so it cannot resume on its own.
  recover    - the responder restores normal operation and confirms it.

This is a deliberately narrowed slice of NIST SP 800-61's six-phase
lifecycle (Preparation and Post-Incident Activity are exercise-design
and after-action concerns, not things a responder does in reaction to
a single inject, so they are not modeled as inject-triggered steps
here; the after-action side of the excluded phase is exactly what
after_action.py covers separately). 6 scenarios x 4 phases = 24 named
playbook steps total, one per phase per scenario, which is the count
the after-action report in after_action.py covers."""

from dataclasses import dataclass

PHASES = ("detect", "contain", "eradicate", "recover")


@dataclass(frozen=True)
class PlaybookStepDef:
    step_id: str
    scenario_id: str
    phase: str
    order_index: int
    name: str


@dataclass(frozen=True)
class ScenarioDef:
    scenario_id: str
    name: str
    description: str
    steps: tuple[PlaybookStepDef, ...]


def _steps(scenario_id: str, detect: str, contain: str, eradicate: str, recover: str) -> tuple[PlaybookStepDef, ...]:
    names = {"detect": detect, "contain": contain, "eradicate": eradicate, "recover": recover}
    return tuple(
        PlaybookStepDef(
            step_id=f"{scenario_id}.{phase}",
            scenario_id=scenario_id,
            phase=phase,
            order_index=index,
            name=names[phase],
        )
        for index, phase in enumerate(PHASES)
    )


SCENARIOS: tuple[ScenarioDef, ...] = (
    ScenarioDef(
        scenario_id="ransomware_corporate_it",
        name="Ransomware on Corporate IT",
        description="A ransomware strain encrypts file shares across the corporate IT estate of a "
        "simulated regional utility, starting on a departmental file server.",
        steps=_steps(
            "ransomware_corporate_it",
            detect="Identify mass file-encryption activity via EDR alert triage",
            contain="Isolate affected hosts from the corporate network segment",
            eradicate="Remove the ransomware binary and its persistence mechanisms",
            recover="Restore encrypted file shares from offline backup",
        ),
    ),
    ScenarioDef(
        scenario_id="phishing_credential_compromise",
        name="Phishing-Driven Credential Compromise",
        description="A credential-harvesting phishing campaign compromises a corporate mailbox, which "
        "is then used to send further phishing internally.",
        steps=_steps(
            "phishing_credential_compromise",
            detect="Confirm the credential-harvesting phishing report via email gateway logs",
            contain="Force a password reset and revoke active sessions for the compromised account",
            eradicate="Block the sender domain and purge the phishing message from all mailboxes",
            recover="Re-enable account access after MFA re-enrollment",
        ),
    ),
    ScenarioDef(
        scenario_id="insider_data_exfiltration",
        name="Insider Data Exfiltration",
        description="An employee with legitimate access exfiltrates engineering documents ahead of a "
        "resignation, via bulk download and an external share link.",
        steps=_steps(
            "insider_data_exfiltration",
            detect="Flag the anomalous bulk download via a DLP alert",
            contain="Suspend the insider's account credentials and revoke the active VPN session",
            eradicate="Revoke the external cloud-storage sharing links used for exfiltration",
            recover="Restore normal access controls after HR and legal sign-off",
        ),
    ),
    ScenarioDef(
        scenario_id="ddos_customer_portal",
        name="DDoS Against Customer-Facing Portal",
        description="A volumetric denial-of-service attack degrades the utility's customer-facing "
        "billing and outage-reporting portal.",
        steps=_steps(
            "ddos_customer_portal",
            detect="Confirm the volumetric traffic anomaly via network flow monitoring",
            contain="Enable upstream scrubbing and rate-limiting for the customer portal",
            eradicate="Block the identified attacking source ranges at the edge firewall",
            recover="Restore full portal capacity and confirm customer-facing availability",
        ),
    ),
    ScenarioDef(
        scenario_id="ot_scada_intrusion",
        name="Intrusion Attempt Against the OT/SCADA Segment",
        description="An intrusion attempt reaches the simulated OT/SCADA network segment through a "
        "compromised engineering workstation, targeting the historian and a PLC.",
        steps=_steps(
            "ot_scada_intrusion",
            detect="Identify anomalous engineering-workstation traffic into the OT historian via the "
            "segment IDS",
            contain="Isolate the OT/SCADA network segment from the corporate IT network",
            eradicate="Remove unauthorized remote-access tooling from the OT jump host",
            recover="Validate control-system integrity and restore OT network connectivity",
        ),
    ),
    ScenarioDef(
        scenario_id="vendor_compromise",
        name="Third-Party Vendor Compromise",
        description="A third-party vendor's own environment is compromised, and the compromise reaches "
        "the utility through the vendor's remote-access integration.",
        steps=_steps(
            "vendor_compromise",
            detect="Identify anomalous vendor VPN activity via third-party access log review",
            contain="Disable the compromised vendor's remote access credentials",
            eradicate="Rotate the shared secrets and API keys used by the vendor integration",
            recover="Reinstate vendor access after re-attestation of the vendor's security controls",
        ),
    ),
)

SCENARIO_BY_ID: dict[str, ScenarioDef] = {s.scenario_id: s for s in SCENARIOS}


def all_steps() -> tuple[PlaybookStepDef, ...]:
    steps: list[PlaybookStepDef] = []
    for scenario in SCENARIOS:
        steps.extend(scenario.steps)
    return tuple(steps)


STEP_BY_ID: dict[str, PlaybookStepDef] = {step.step_id: step for step in all_steps()}


def steps_for_scenario(scenario_id: str) -> tuple[PlaybookStepDef, ...]:
    return SCENARIO_BY_ID[scenario_id].steps


def step_for_phase(scenario_id: str, phase: str) -> PlaybookStepDef:
    for step in steps_for_scenario(scenario_id):
        if step.phase == phase:
            return step
    raise KeyError(f"no {phase} step for scenario {scenario_id}")
