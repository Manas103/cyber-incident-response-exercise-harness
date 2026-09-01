"""The fixed exercise timeline: 30 injects, exactly 5 per scenario, each
injected at a timestamp (minutes from that scenario's exercise start).
An inject is the simulated event a responder reacts to; the response it
requires is the 4-step playbook of its own scenario (see scenarios.py),
not a bespoke step of its own, which is why 30 injects can be measured
against only 24 named playbook steps: several injects in a scenario
legitimately call for the same named step (for example, two ransomware
injects both call for the same "isolate affected hosts" contain step)."""

from dataclasses import dataclass

from .scenarios import SCENARIO_BY_ID


@dataclass(frozen=True)
class InjectDef:
    inject_id: str
    scenario_id: str
    order_index: int
    name: str
    timestamp_minutes: int


def _injects(scenario_id: str, entries: list[tuple[str, int]]) -> tuple[InjectDef, ...]:
    return tuple(
        InjectDef(
            inject_id=f"{scenario_id}.inject{index + 1}",
            scenario_id=scenario_id,
            order_index=index,
            name=name,
            timestamp_minutes=timestamp,
        )
        for index, (name, timestamp) in enumerate(entries)
    )


INJECTS: tuple[InjectDef, ...] = (
    _injects(
        "ransomware_corporate_it",
        [
            ("Encrypted file extensions observed on the Finance file share", 0),
            ("Ransom note dropped on the HR department shared drive", 15),
            ("EDR alert fires for mass file-rename activity on a second file server", 35),
            ("Backup server reports a failed nightly job coincident with the encryption spread", 55),
            ("Help desk reports multiple users unable to open shared documents", 70),
        ],
    )
    + _injects(
        "phishing_credential_compromise",
        [
            ("A user reports a suspicious 'password expiring' email with an external link", 0),
            ("The email gateway flags 40 recipients of the same phishing template", 10),
            ("SSO logs show an impossible-travel login for one flagged recipient", 25),
            ("The compromised account sends internal phishing replies from an inbox rule", 40),
            ("Help desk receives a report of unauthorized calendar invites from the account", 55),
        ],
    )
    + _injects(
        "insider_data_exfiltration",
        [
            ("A DLP alert fires for a 4 GB download from the engineering document repository", 0),
            ("The same account shares a folder link externally minutes later", 12),
            ("VPN logs show the user connecting from an unrecognized residential ISP", 30),
            ("The user's manager reports the employee resigned effective today", 50),
            ("The cloud storage audit log shows a second, larger export attempt", 65),
        ],
    )
    + _injects(
        "ddos_customer_portal",
        [
            ("Customer portal latency spikes and load balancer health checks begin failing", 0),
            ("Network flow monitoring shows a 40x baseline spike in inbound UDP traffic", 5),
            ("The CDN provider opens an automated abuse ticket citing volumetric traffic", 15),
            ("The support queue fills with customer reports of portal timeouts", 20),
            ("A second traffic vector (HTTP flood) begins against the login endpoint", 35),
        ],
    )
    + _injects(
        "ot_scada_intrusion",
        [
            ("The OT segment IDS logs an unexpected engineering-workstation connection to the historian", 0),
            ("The historian shows a login from a service account outside its maintenance window", 10),
            ("Unusual read commands are observed against a PLC via the engineering workstation", 25),
            ("The OT firewall logs an attempted outbound connection from the historian to an external IP", 40),
            ("A control-room operator reports an unexpected HMI screen refresh anomaly", 55),
        ],
    )
    + _injects(
        "vendor_compromise",
        [
            ("Third-party access logs show the vendor's service account authenticating outside contracted hours", 0),
            ("The vendor integration API begins making requests outside its documented scope", 10),
            ("The vendor confirms by phone that its own environment was compromised", 25),
            ("An internal system shows a new API key created under the vendor's integration", 35),
            ("The SOC receives an alert for data egress correlated with the vendor's access window", 50),
        ],
    )
)

INJECT_BY_ID: dict[str, InjectDef] = {inject.inject_id: inject for inject in INJECTS}


def injects_for_scenario(scenario_id: str) -> tuple[InjectDef, ...]:
    if scenario_id not in SCENARIO_BY_ID:
        raise KeyError(f"unknown scenario_id: {scenario_id}")
    return tuple(i for i in INJECTS if i.scenario_id == scenario_id)
