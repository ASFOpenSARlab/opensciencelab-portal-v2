from dataclasses import dataclass, field
import requests
from aws_lambda_powertools import Logger
from json import JSONDecodeError

from util.log_timer import measure_time
from data import RESTRICTED_COUNTRIES

logger = Logger(child=True)

@dataclass
class BaseLabConfig:
    friendly_name: str
    short_lab_name: str
    accessibility: str
    allowed_profiles: list
    deployment_url: str
    calendar_url: str | None = None
    description: str | None = None
    logo: str | None = None
    about_page_url: str | None = None
    about_page_button_label: str | None = None
    ip_country_status: dict = field(
        default_factory=lambda: {
            "limited": [],
            "prohibited": [
                "KP",
                "SY",
                "IR",
            ],
        }
    )
    crypto_remediation_role_arn: str | None = None
    default_profiles: list = field(default_factory=lambda: [])
    application_questions: list[dict] = field(default_factory=lambda: [])
    application_description: str | None = None
    allows_tokens: bool = False

    def is_healthy(self) -> bool:
        try:
            with measure_time(
                service="healthcheck", action=f"ping {self.short_lab_name}"
            ):
                ret = requests.get(
                    url=f"{self.deployment_url}/lab/{self.short_lab_name}/hub/health",
                    timeout=0.1,
                    verify=False,
                )
        except requests.exceptions.ReadTimeout:
            return False
        except requests.exceptions.ConnectionError:
            return False
        return ret.status_code == 200

    def get_version(self) -> str:
        try:
            with measure_time(
                service="get_version", action=f"get {self.short_lab_name} version"
            ):
                ret = requests.get(
                    url=f"{self.deployment_url}/lab/{self.short_lab_name}/hub/static/version.json",
                    timeout=0.1,
                    verify=False,
                )
        except requests.exceptions.ReadTimeout:
            return "Timeout"
        except requests.exceptions.ConnectionError:
            return "Version Not Supported"

        if ret.status_code < 200 or ret.status_code > 299:
            return f"Endpoint Error: {ret.status_code}"

        try:
            cluster_version = ret.json().get("cluster_version", "Unknown version")
            deploy_date = ret.json().get("deploy_date", "Unknown deploy date")
        except JSONDecodeError as e:
            logger.error(f"Error decoding cluster version JSON: {e}")
            return "Broken JSON"

        if cluster_version.startswith("v"):
            return cluster_version
        else:
            return f"{cluster_version} ({deploy_date})"


def get_daac_country_status() -> dict:
    """
    Country type mapping to access
    https://github.com/ASFOpenSARlab/.github-private/tree/main/add_users#who-we-can-deal-with

    Returns: Dict with lists of "limited" (type 1&4) and "prohibited" (type 2&4)

    """
    # Country type triggers
    limited = {1, 4}
    prohibited = {2, 3}

    rc_items = RESTRICTED_COUNTRIES.items()
    return {
        "limited": [
            c
            for c, d in rc_items
            if (
                limited & set(d["restrictions"])
                and not prohibited & set(d["restrictions"])
            )
        ],
        "prohibited": [c for c, d in rc_items if prohibited & set(d["restrictions"])],
    }
