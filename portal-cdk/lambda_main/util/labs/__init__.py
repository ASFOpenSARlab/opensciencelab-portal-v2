from objs.base_lab_config import BaseLabConfig, get_daac_country_status

import os

PROD_LAB_CONFIGS = {
    "smce-prod-opensarlab": BaseLabConfig(
        short_lab_name="smce-prod-opensarlab",
        friendly_name="OpenSARLab (ASF DAAC)",
        description="""
            <p>NASA JupyterHub operated by the Alaska Satellite Facility</p>
            <p>Users with a valid science need can apply for access by clicking the "Apply for Access" button below (if present).</p>
            <p style="color: orangered;">User storage is permanently deleted after 30 days of inactivity. Users can request a temporary extension by contacting the OSL Admins.</p> <hr style="border-top: 1px solid grey;"> <div style="font-size: 12px;margin: 10px 0 0 0;text-align: justify;">
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
        logo="ASF_and_NASA.svg",
        about_page_url="https://opensarlab-docs.asf.alaska.edu/",
        about_page_button_label="Info",
        ip_country_status=get_daac_country_status(),
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
            "OpenSARLab Test Image",
            "r6i.4xlarge",
        ],
        crypto_remediation_role_arn="arn:aws:iam::381492216607:role/service-role/cryptomining-remediation-role-b4sw3o86",
        default_profiles=["m6a.large", "m6a.xlarge"],
        application_questions=[
            {
                "name": "sar_experience",
                "question": "Tell us about your SAR-related experience and the length of time you have worked in the field.",
                "type": "text",
                "rendering_options": "multi-line",
                "placeholder": "Your Answer",
            },
            {
                "name": "osl_experience",
                "question": "Have you used OpenSARLab before? If so, tell us what you used it for and what you produced / developed / delivered with it.",
                "type": "text",
                "rendering_options": "multi-line",
                "placeholder": "Your Answer",
            },
            {
                "name": "use_case",
                "question": "What do you want to use OpenSARLab for?",
                "type": "text",
                "rendering_options": "multi-line",
                "placeholder": "Your Answer",
            },
            {
                "name": "personal_impacts",
                "question": "If you were given access to OpenSARLab, what would be the impact for you?",
                "type": "text",
                "rendering_options": "multi-line",
                "placeholder": "Your Answer",
            },
            {
                "name": "community_impacts",
                "question": "What would be the impact for your community?",
                "type": "text",
                "rendering_options": "multi-line",
                "placeholder": "Your Answer",
            },
            {
                "name": "research_impacts",
                "question": "What would be the impact for the field of research you are contributing to?",
                "type": "text",
                "rendering_options": "multi-line",
                "placeholder": "Your Answer",
            },
        ],
        application_description=(
            'Access to "OpenSARLab (ASF DAAC)" is month-to-month as budget allows. If your access is set to be revoked, '
            "we will get in touch to ensure that you are able to download any workflows and results "
            "before you lose access.<br><br>"
            "Applications are approved on a weekly basis. If timeliness is a significant factor for your application, "
            'please email <a href="mailto:uaf-jupyterhub-asf@alaska.edu">uaf-jupyterhub-asf@alaska.edu</a> '
            "to advise us of your circumstances."
        ),
    ),
    "azdwr-prod-opensarlab": BaseLabConfig(
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
        allows_tokens=True,
    ),
    "avo-prod": BaseLabConfig(
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
        allows_tokens=True,
    ),
}

NON_PROD_LAB_CONFIGS = {
    "test": BaseLabConfig(
        short_lab_name="test",
        friendly_name="Cluster v2 - test",
        description="""
            <p>Cluster v2 access to test auth.</p>
        """,
        deployment_url="http://eks-cluster-test-3ad17d630b8f26fc.elb.us-west-2.amazonaws.com",
        accessibility="protected",
        allowed_profiles=[
            "SAR 1",
            "SAR 1 - Max",
            "Debug Server Profile",
            "m6a.xlarge",
            "m6a.large",
            "sudo",
        ],
        default_profiles=["m6a.large", "m6a.xlarge"],
    ),
    "ssbw26": BaseLabConfig(
        short_lab_name="ssbw26",
        friendly_name="SSBW 2026",
        description="Seismology Skill Building Workshop for Summer 2026, powered by ASF OpenScienceLab",
        about_page_url="https://www.earthscope.org/education/skill-building-learning/courses/ssbw/",
        about_page_button_label="Course",
        ip_country_status={"limited": [], "prohibited": []},
        deployment_url="http://ssbw26-1741361599.us-west-2.elb.amazonaws.com",
        accessibility="private",
        allowed_profiles=[
            "SSBW Workspace 1",
            "SSBW Workspace 2",
            "SSBW Workspace 1 - Test",
            "Debug Server Profile",
            "sudo",
        ],
        default_profiles=["SSBW Workspace 1"],
        allows_tokens=True,
    ),
    "smce-test-opensarlab": BaseLabConfig(
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
        logo="ASF_and_NASA.svg",
        about_page_url="https://opensarlab-docs.asf.alaska.edu/",
        about_page_button_label="Info",
        ip_country_status=get_daac_country_status(),
        accessibility="protected",
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
            "r6i.4xlarge",
        ],
        crypto_remediation_role_arn="arn:aws:iam::381492216607:role/service-role/cryptomining-remediation-role-b4sw3o86",
        default_profiles=["m6a.large", "m6a.xlarge"],
        application_questions=[
            {
                "name": "sar_experience",
                "question": "Tell us about your SAR-related experience and the length of time you have worked in the field.",
                "type": "text",
                "rendering_options": "multi-line",
                "placeholder": "Your Answer",
            },
            {
                "name": "osl_experience",
                "question": "Have you used OpenSARLab before? If so, tell us what you used it for and what you produced / developed / delivered with it.",
                "type": "text",
                "rendering_options": "multi-line",
                "placeholder": "Your Answer",
            },
            {
                "name": "use_case",
                "question": "What do you want to use OpenSARLab for?",
                "type": "text",
                "rendering_options": "multi-line",
                "placeholder": "Your Answer",
            },
            {
                "name": "personal_impacts",
                "question": "If you were given access to OpenSARLab, what would be the impact for you?",
                "type": "text",
                "rendering_options": "multi-line",
                "placeholder": "Your Answer",
            },
            {
                "name": "community_impacts",
                "question": "What would be the impact for your community?",
                "type": "text",
                "rendering_options": "multi-line",
                "placeholder": "Your Answer",
            },
            {
                "name": "research_impacts",
                "question": "What would be the impact for the field of research you are contributing to?",
                "type": "text",
                "rendering_options": "multi-line",
                "placeholder": "Your Answer",
            },
        ],
        application_description=(
            'Access to "OpenSARLab (ASF DAAC)" is month-to-month as budget allows. If your access is set to be revoked, '
            "we will get in touch to ensure that you are able to download any workflows and results "
            "before you lose access.<br><br>"
            "Applications are approved on a weekly basis. If timeliness is a significant factor for your application, "
            'please email <a href="mailto:uaf-jupyterhub-asf@alaska.edu">uaf-jupyterhub-asf@alaska.edu</a> '
            "to advise us of your circumstances."
        ),
    ),
    "test_protected": BaseLabConfig(
        short_lab_name="test_protected",
        friendly_name="Test Protected Lab",
        description="",
        logo="NASA_logo.svg",
        deployment_url="http://smce-test-1433554573.us-west-2.elb.amazonaws.com",
        accessibility="protected",
        allowed_profiles=[],
        default_profiles=["m6a.large", "m6a.xlarge"],
        application_questions=[
            {
                "name": "why",
                "question": "Why do you want access?",
                "type": "text",
                "rendering_options": "multi-line",
                "placeholder": "Your Answer",
            },
        ],
        allows_tokens=True,
    ),
    "test_prohibited": BaseLabConfig(
        short_lab_name="test_prohibited",
        friendly_name="Test Prohibited Lab",
        description="",
        logo="OpenSARLab_logo.png",
        deployment_url="https://smce-test-1433554573.us-west-2.elb.amazonaws.com",
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
    LAB_CONFIGS: dict[str, BaseLabConfig] = PROD_LAB_CONFIGS
else:
    LAB_CONFIGS: dict[str, BaseLabConfig] = NON_PROD_LAB_CONFIGS
