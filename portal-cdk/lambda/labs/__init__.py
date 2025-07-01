from .base_lab import BaseLab

labs_dict = {
    "shortname": BaseLab(
            friendly_name="testlab",
            short_lab_name="shortname",
            description= "A test lab for testing",
            logo= "favicon.ico",
            about_page_url= "google.com",
            about_page_button_label= "Not Google",
            deployment_url= "labdeployment.com",
            ip_country_status= {
                "limited": ["BH", "BT", "EG", "IL", "JO", "KW", "OM", "PK", "QA", "SA", "AE", "YE", "EH"],
                "prohibited": ["AF", "BY", "MM", "KH", "CT", "CN", "CD", "CU", "CY", "ER", "ET", "HT", "IR", "IQ", "KP", "LB", "LY", "NI", "SO", "SS", "SU", "SY", "VE", "ZW", "RU", "TW"],
            },
            enabled= True,
            accessibility= "protected",
        ),
    "shortname2": BaseLab(
            friendly_name="testlab2",
            short_lab_name="shortname2",
            description= "A test lab for testing",
            logo= "favicon.ico",
            about_page_url= "google.com",
            about_page_button_label= "Not Google",
            deployment_url= "labdeployment.com",
            enabled= True,
            accessibility= "protected",
        )
}