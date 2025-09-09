import main

SWAGGER_EXCLUDED_ENDPOINTS = {
    "root": [
        ("GET", "/"),
        ("GET", "/auth"),
        ("GET", "/logout"),
        ("GET", "/register"),
        ("GET", "/static/.+"),
    ],
    "portal_root": [
        ("GET", "/portal"),
    ],
    "access": [
        ("GET", "/portal/access/manage/{shortname}"),
    ],
}


SWAGGER_INCLUDED_ENDPOINTS = {
    "access": [
        ("GET", "/portal/access"),
        ("GET", "/portal/access/add_lab"),
        ("GET", "/portal/access/lab"),
        ("GET", "/portal/access/lab/{lab}"),
        ("GET", "/portal/access/labs/{username}"),
        ("GET", "/portal/access/users/{shortname}"),
        ("PUT", "/portal/access/labs/{username}"),
        ("DELETE", "/portal/access/labs/{username}"),
    ],
}


class TestPortalAuth:
    def test_excluded_endpoints_in_swagger_ai(self, helpers, lambda_context):
        event = helpers.get_event(path="/api")
        ret = main.lambda_handler(event, lambda_context)
        for _, router in SWAGGER_EXCLUDED_ENDPOINTS.items():
            for exclude in router:
                path = f"{exclude[0]} {exclude[1]}"
                excluded = f'"summary": "{path}"'
                assert ret["body"].find(excluded) == -1, (
                    f"Found excluded '{path}' in swagger"
                )

    def test_included_endpoints_in_swagger_ai(self, helpers, lambda_context):
        event = helpers.get_event(path="/api")
        ret = main.lambda_handler(event, lambda_context)
        for _, router in SWAGGER_INCLUDED_ENDPOINTS.items():
            for include in router:
                path = f"{include[0]} {include[1]}"
                included = f'"summary": "{path}"'
                assert ret["body"].find(included) != -1, (
                    f"Couldn't find included '{path}' in swagger"
                )
