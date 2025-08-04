from .base_lab import BaseLab

from dataclasses import dataclass

all_labs = {
    "shortname": BaseLab(
        friendly_name="testlab",
        short_lab_name="shortname",
        description="A test lab for testing",
        logo="favicon.ico",
        about_page_url="https://google.com",
        about_page_button_label="Learn Testlab",
        deployment_url="labdeployment.com",
        enabled=True,
        accessibility="protected",
    ),
    "shortname2": BaseLab(
        friendly_name="testlab2",
        short_lab_name="shortname2",
        description="A test lab for testing",
        logo="favicon.ico",
        about_page_url="https://google.com",
        about_page_button_label="Not Google",
        deployment_url="labdeployment.com",
        enabled=True,
        accessibility="protected",
    ),
    "secret-lab": BaseLab(
        friendly_name="Secret Lab",
        short_lab_name="secret-lab",
        description="A secret test lab for testing",
        logo="favicon.ico",
        about_page_url="https://google.com",
        about_page_button_label="About",
        deployment_url="labdeployment.com",
        enabled=True,
        accessibility="protected",
    ),
}


@dataclass
class LabAccessInfo:
    lab: BaseLab
    can_user_access_lab: bool
    can_user_see_lab_card: bool
