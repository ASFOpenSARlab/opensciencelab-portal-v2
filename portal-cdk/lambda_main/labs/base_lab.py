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
    ip_country_status: dict = field(
        default_factory=lambda: {"limited": [], "prohibited": []}
    )
    enabled: str = None
    accessibility: str = None
    users: list = field(default_factory=lambda: [])
