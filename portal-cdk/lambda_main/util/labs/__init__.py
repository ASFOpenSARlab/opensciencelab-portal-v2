from .base_lab import BaseLab

import os

if os.getenv("IS_PROD", "false").lower() == "true":
    LABS = {
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
            about_page_url="https://opensarlab-docs.asf.alaska.edu/user/",
            ip_country_status={
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
                ],
            },
            enabled=True,
            accessibility="protected",
        ),
        "azdwr-prod-opensarlab": BaseLab(
            short_lab_name="azdwr-prod-opensarlab",
            friendly_name="AZ Department of Water Resources",
            description="OpenSARLab Deployment",
            deployment_url="https://azdwr-prod-1046268859.us-west-2.elb.amazonaws.com",
            logo="azdwr_logo_web.jpg",
            enabled=True,
            accessibility="private",
        ),
        "avo-prod": BaseLab(
            short_lab_name="avo-prod",
            friendly_name="AVO",
            description="Alaska Volcano Observatory deployment, powered by ASF OpenScienceLab",
            deployment_url="https://avo-prod-53819398.us-west-2.elb.amazonaws.com/",
            enabled=True,
            accessibility="private",
        ),
        "osl-grapenthin": BaseLab(
            short_lab_name="osl-grapenthin",
            friendly_name="GEOS 631",
            description="Foundations of Geophysics",
            deployment_url="https://osl-grapenthin-657937316.us-west-2.elb.amazonaws.com",
            about_page_url="https://catalog.uaf.edu/courses/geos/",
            about_page_button_label="Course",
            enabled=True,
            accessibility="private",
        ),
        "geos657": BaseLab(
            short_lab_name="geos657",
            friendly_name="GEOS 657",
            description="Microwave Remote Sensing",
            deployment_url="https://geos657-579303888.us-west-2.elb.amazonaws.com",
            about_page_url="https://radar.community.uaf.edu/",
            about_page_button_label="Course",
            enabled=True,
            accessibility="private",
        ),
        "geos419": BaseLab(
            short_lab_name="geos419",
            friendly_name="GEOS 419",
            description="Solid Earth Geophysics",
            deployment_url="https://geos419-402278678.us-west-2.elb.amazonaws.com",
            about_page_url="https://catalog.uaf.edu/courses/geos/",
            about_page_button_label="Course",
            enabled=True,
            accessibility="private",
        ),
        "ssbw": BaseLab(
            short_lab_name="ssbw",
            friendly_name="Seismology Skill Building Workshop - 1",
            description="EarthScope Training, powered by ASF OpenScienceLab.",
            deployment_url="https://ssbw-2104246316.us-west-2.elb.amazonaws.com",
            # logo="ssbw_summer_2024_logo.png",
            about_page_url="https://moodle.glg.miamioh.edu/glgmoodle/login/index.php",
            about_page_button_label="Course",
            enabled=True,
            accessibility="private",
        ),
        "ssbw2": BaseLab(
            short_lab_name="ssbw2",
            friendly_name="Seismology Skill Building Workshop - 2",
            description="EarthScope Training, powered by ASF OpenScienceLab.",
            deployment_url="https://ssbw2-1404950528.us-west-2.elb.amazonaws.com",
            # logo="ssbw_summer_2024_logo.png",
            about_page_url="https://moodle.glg.miamioh.edu/glgmoodle/login/index.php",
            about_page_button_label="Course",
            enabled=True,
            accessibility="private",
        ),
        "insar2025": BaseLab(
            short_lab_name="insar2025",
            friendly_name="2025 EarthScope InSAR Workshop",
            description="EarthScope Training, powered by ASF OpenScienceLab.",
            deployment_url="http://insar25-1684469926.us-west-2.elb.amazonaws.com",
            logo="earthscope-cort.png",
            # about_page_url="",
            # about_page_button_label="Course",
            enabled=True,
            accessibility="private",
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
            deployment_url="http://geos636-224946823.us-west-2.elb.amazonaws.com/",
            # about_page_url="",
            # about_page_button_label="Course",
            enabled=True,
            accessibility="private",
        ),
    }
else:
    LABS: dict[str, BaseLab] = {
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
            # about_page_url="",
            # about_page_button_label="Course",
            ip_country_status={
                "limited": [],
                "prohibited": ["KP", "IR", "SY"],
            },
            enabled=True,
            accessibility="private",
            notifications="https://calendar.google.com/calendar/ical/c_3704674759bada5ab28ed5f66686b932bbabe955ecc440bd2aeed0982d5cd34a%40group.calendar.google.com/public/basic.ics",
        ),
        "test_protected": BaseLab(
            short_lab_name="test_protected",
            friendly_name="Test Protected Lab",
            description="",
            deployment_url="http://smce-test-1433554573.us-west-2.elb.amazonaws.com",
            enabled=True,
            accessibility="protected",
        ),
        "test_prohibited": BaseLab(
            short_lab_name="test_prohibited",
            friendly_name="Test Prohibited Lab",
            description="",
            deployment_url="http://smce-test-1433554573.us-west-2.elb.amazonaws.com",
            ip_country_status={
                "limited": [],
                "prohibited": [
                    "US",
                ],
            },
            enabled=True,
            accessibility="protected",
        ),
    }
