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
}


class TestPortalAuth:
    def test_endpoints_in_swagger_ai(self, helpers, lambda_context):
        event = helpers.get_event(path="/api")
        ret = main.lambda_handler(event, lambda_context)

        for _, router in SWAGGER_EXCLUDED_ENDPOINTS.items():
            for exclude in router:
                path = f"{exclude[0]} {exclude[1]}"
                excluded = f'"summary": "{path}"'
                assert ret["body"].find(excluded) == -1, (
                    f"Found excluded '{path}' in swagger"
                )
