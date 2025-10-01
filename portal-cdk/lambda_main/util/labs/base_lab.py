from dataclasses import dataclass, field


@dataclass
class BaseLab:
    friendly_name: str = None
    short_lab_name: str = None
    description: str = None
    logo: str = None
    about_page_url: str = None
    about_page_button_label: str = None
    deployment_url: str = None
    allowed_profiles: list = field(default_factory=list)
    ip_country_status: dict = field(
        default_factory=lambda: {
            "limited": [
                "BH",
                "BT",
                "EG",
                "IL",
                "JO",
                "KW",
                "OM",
                "PK",
                "QA",
                "SA",
                "AE",
                "YE",
                "EH",
            ],
            "prohibited": [
                "AF",
                "BY",
                "MM",
                "KH",
                "CT",
                "CN",
                "CD",
                "CU",
                "CY",
                "ER",
                "ET",
                "HT",
                "IR",
                "IQ",
                "KP",
                "LB",
                "LY",
                "NI",
                "SO",
                "SS",
                "SU",
                "SY",
                "VE",
                "ZW",
                "RU",
                "TW",
            ],
        }
    )
    enabled: str = None
    accessibility: str = None
    users: list = field(default_factory=lambda: [])
    notifications: str = None
