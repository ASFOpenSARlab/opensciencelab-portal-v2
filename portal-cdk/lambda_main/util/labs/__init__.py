from .base_lab import BaseLab, daac_limited_restricted_status

import os
import requests

PROD_LABS = {
    "smce-prod-opensarlab": BaseLab(
        short_lab_name="smce-prod-opensarlab",
        friendly_name="OpenSARLab (ASF DAAC)",
        description="""
        <p>NASA JupyterHub operated by the Alaska Satellite Facility</p> <p>Users not affiliated with NASA should apply for access here: <a href="https://forms.gle/LNBCwe8JohYitvfy6">OpenSARLab Access Application</a></p> <p style="color: orangered;">User storage is permanently deleted after 30 days of inactivity. Users can request a temporary extension by contacting the OSL Admins.</p> <hr style="border-top: 1px solid grey;"> <div style="font-size: 12px;margin: 10px 0 0 0;text-align: justify;">
            <p>By accessing and using this information system, you acknowledge and consent to the following:</p>
            <p>You are accessing a U.S. Government information system, which includes: (1) this computer; (2) this computer network; (3) all computers connected to
            this network including end user systems; (4) all devices and storage media attached to this network or to any computer on this network; and
            (5) cloud and remote information services. </p>
            <p>This information system is provided for U.S. Government-authorized use only. You have no reasonable expectation of privacy regarding any
            communication transmitted through or data stored on this information system. At any time, and for any lawful purpose, the U.S. Government may monitor,
            intercept, search, and seize any communication or data transiting, stored on, or traveling to or from this information system.
            You are NOT authorized to process classified information on this information system. Unauthorized or improper use of this system may
            result in suspension or loss of access privileges, disciplinary action, and civil and/or criminal penalties. </p>
        </div>
        """,
        deployment_url="https://smce-prod-1240379463.us-west-2.elb.amazonaws.com",
        logo="ASFLogo-Blue2.png",
        about_page_url="https://opensarlab-docs.asf.alaska.edu/",
        about_page_button_label="Info",
        ip_country_status=daac_limited_restricted_status,
        accessibility="protected",
        allowed_profiles=[
            "t3a.medium - Dask User",
            "m6a.large",
            "m6a.large - Spot",
            "SAR 1 - Max",
            "Debug Server Profile",
            "SAR 2",
            "SAR 2 - Max",
            "SAR 2 - Max - Spot",
            "SERVIR 1",
            "m6a.xlarge",
            "VDAP m6a.large",
            "OPERA",
            "noistio",
            "sudo",
        ],
        crypto_remediation_role_arn="arn:aws:iam::381492216607:role/service-role/cryptomining-remediation-role-b4sw3o86",
        default_profiles=["m6a.large", "m6a.xlarge"],
    ),
    "azdwr-prod-opensarlab": BaseLab(
        short_lab_name="azdwr-prod-opensarlab",
        friendly_name="AZ Department of Water Resources",
        description="OpenSARLab Deployment",
        deployment_url="https://azdwr-prod-54597698.us-west-2.elb.amazonaws.com",
        logo="azdwr_logo_web.jpg",
        accessibility="private",
        allowed_profiles=[
            "AZDWR SAR 1",
            "Debug Profile",
            "AZDWR SAR 2",
            "AZDWR SAR 3",
            "AZDWR SAR 4",
            "AZDWR SAR 5",
            "sudo",
        ],
        default_profiles=[
            "AZDWR SAR 1",
            "Debug Profile",
            "AZDWR SAR 2",
            "AZDWR SAR 3",
            "AZDWR SAR 4",
            "AZDWR SAR 5",
        ],
    ),
    "avo-prod": BaseLab(
        short_lab_name="avo-prod",
        friendly_name="AVO",
        description="Alaska Volcano Observatory deployment, powered by ASF OpenScienceLab",
        deployment_url="https://avo-prod-1501047584.us-west-2.elb.amazonaws.com",
        accessibility="private",
        allowed_profiles=[
            "SAR 1",
            "SAR 2",
            "SAR 3",
            "Debug Server Profile",
            "sudo",
        ],
        default_profiles=["SAR 1", "SAR 2", "SAR 3", "Debug Server Profile"],
    ),
    "geos636-2025": BaseLab(
        short_lab_name="geos636-2025",
        friendly_name="GEOS 636 - Programming and Automation for Geoscientists",
        description="""
        <p>
            Basic concepts of computer programming and effective task automation for computers,
            with an emphasis on tools and problems common to the geosciences and other physical sciences.
            Use of Python, Jupyter Notebooks, shell scripting and command line tools,
            making scientific figures, maps and visualizations. Provided asynchronously remotely.
        </p> <p>
            Class lab, powered by ASF OpenScienceLab.
        </p>
        """,
        deployment_url="http://geos636-224946823.us-west-2.elb.amazonaws.com",
        # about_page_url="",
        # about_page_button_label="Course",
        accessibility="private",
        allowed_profiles=[
            "Debug Server Profile",
            "m6a.large",
            "sudo",
        ],
        default_profiles=["m6a.large"],
    ),
}

NON_PROD_LABS = {
    "smce-test-opensarlab": BaseLab(
        short_lab_name="smce-test-opensarlab",
        friendly_name="SMCE Test (US Unrestricted, Lab Protected)",
        description="""
            <p>NASA JupyterHub operated by the Alaska Satellite Facility</p> <hr style="border-top: 1px solid grey;"> <div style="font-size: 12px;margin: 10px 0 0 0;text-align: justify;">
            <p>By accessing and using this information system, you acknowledge and consent to the following:</p>
            <p>You are accessing a U.S. Government information system, which includes: (1) this computer; (2) this computer network; (3) all computers connected to
            this network including end user systems; (4) all devices and storage media attached to this network or to any computer on this network; and
            (5) cloud and remote information services. </p>
            <p>This information system is provided for U.S. Government-authorized use only. You have no reasonable expectation of privacy regarding any
            communication transmitted through or data stored on this information system. At any time, and for any lawful purpose, the U.S. Government may monitor,
            intercept, search, and seize any communication or data transiting, stored on, or traveling to or from this information system.
            You are NOT authorized to process classified information on this information system. Unauthorized or improper use of this system may
            result in suspension or loss of access privileges, disciplinary action, and civil and/or criminal penalties. </p>
        </div>
        """,
        deployment_url="http://smce-test-1433554573.us-west-2.elb.amazonaws.com",
        logo="ASFLogo-Blue2.png",
        about_page_url="https://opensarlab-docs.asf.alaska.edu/",
        about_page_button_label="Info",
        ip_country_status=daac_limited_restricted_status,
        accessibility="private",
        allowed_profiles=[
            "SAR 1",
            "t3a.medium - Dask User",
            "SAR 1 - Max",
            "Debug Server Profile",
            "SAR 2",
            "SAR 2 - Max",
            "SERVIR 1",
            "m6a.xlarge",
            "m6a.large",
            "m6a.large - Desktop",
            "sudo",
        ],
        crypto_remediation_role_arn="arn:aws:iam::381492216607:role/service-role/cryptomining-remediation-role-b4sw3o86",
        default_profiles=["m6a.large", "m6a.xlarge"],
    ),
    "test_protected": BaseLab(
        short_lab_name="test_protected",
        friendly_name="Test Protected Lab",
        description="",
        logo="NASA_logo.svg",
        deployment_url="http://smce-test-1433554573.us-west-2.elb.amazonaws.com",
        accessibility="protected",
        allowed_profiles=[],
        default_profiles=["m6a.large", "m6a.xlarge"],
    ),
    "test_prohibited": BaseLab(
        short_lab_name="test_prohibited",
        friendly_name="Test Prohibited Lab",
        description="",
        logo="OpenSARLab_logo.png",
        deployment_url="http://smce-test-1433554573.us-west-2.elb.amazonaws.com",
        ip_country_status={
            "limited": [],
            "prohibited": [
                "US",
            ],
        },
        accessibility="protected",
        allowed_profiles=[],
        default_profiles=["m6a.large", "m6a.xlarge"],
    ),
}

if os.getenv("IS_PROD", "false").lower() == "true":
    LABS: dict[str, BaseLab] = PROD_LABS
else:
    LABS: dict[str, BaseLab] = NON_PROD_LABS

def is_lab_healthy(lab: BaseLab) -> bool:
    ret = requests.get(
        url = f"{lab.deployment_url}/lab/{lab.short_lab_name}/hub/health"
    )
    return ret.status_code == 200
