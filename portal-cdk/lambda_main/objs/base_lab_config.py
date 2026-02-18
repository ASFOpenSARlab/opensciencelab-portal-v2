from dataclasses import dataclass, field
import requests

from util.log_timer import measure_time
from data import RESTRICTED_COUNTRIES


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
