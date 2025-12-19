from dataclasses import dataclass, field
from os import getenv
import requests



@dataclass
class BaseLab:
    friendly_name: str
    short_lab_name: str
    accessibility: str
    allowed_profiles: list
    deployment_url: str
    description: str = None
    logo: str = None
    about_page_url: str = None
    about_page_button_label: str = None
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
    crypto_remediation_role_arn: str = None
    default_profiles: list = field(default_factory=lambda: [])

    def is_healthy(self) -> bool:
        try:
            ret = requests.get(
                url=f"{getenv('DEPLOYMENT_HOSTNAME')}/lab/{self.short_lab_name}/hub/health",
                timeout=0.1,
            )
        except requests.exceptions.ReadTimeout:
            return False
        return ret.status_code == 200


daac_limited_restricted_status = {
    "limited": [
        "AE",
        "BH",
        "BT",
        "EG",
        "IL",
        "JO",
        "KW",
        "MO",
        "OM",
        "PK",
        "QA",
        "SA",
        "YE",
        "MO",
    ],
    "prohibited": [
        "AF",
        "BY",
        "CD",
        "CN",
        "CT",
        "CU",
        "ER",
        "ET",
        "HT",
        "IQ",
        "IR",
        "KH",
        "KP",
        "LB",
        "LY",
        "MM",
        "NI",
        "SO",
        "SS",
        "SU",
        "SY",
        "VE",
        "ZW",
        "TW",
        "RU",
        "CY",
    ],
}
