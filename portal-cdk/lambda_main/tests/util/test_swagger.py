import main

SWAGGER_EXCLUDED_ENDPOINTS = {
    "hub": [
        ("GET", "/portal/hub"),
        ("GET", "/portal/hub/home"),
        ("GET", "/portal/hub/auth"),
        ("GET", "/portal/hub/login"),
    ],
    "portal_root": [
        ("GET", "/portal"),
    ],
    "profile": [
        ("GET", "/portal/profile"),
        ("GET", "/portal/profile/form/bob"),
        ("GET", "/portal/profile/form/{username}"),
        ("POST", "/portal/profile/form/{username}"),
    ],
    "root": [
        ("GET", "/"),
        ("GET", "/auth"),
        ("GET", "/logout"),
        ("GET", "/register"),
        ("GET", "/static/.+"),
    ],
    "access": [
        ("GET", "/portal/access"),
        ("GET", "/portal/access/add_lab"),
        ("GET", "/portal/access/manage/{shortname}"),
        ("GET", "/portal/access/manage/{shortname}/edituser"),
        ("GET", "/portal/access/lab"),
        ("GET", "/portal/access/lab/{lab}"),
    ],
    "user": [
        ("GET", "/portal/user"),
        ("POST", "/portal/user/delete/{username}"),
        ("POST", "/portal/user/lock/{username}"),
        ("POST", "/portal/user/unlock/{username}"),
    ],
}


SWAGGER_INCLUDED_ENDPOINTS = {
    "access": [
        ("GET", "/portal/access/users/{shortname}"),
        ("GET", "/portal/access/labs/{username}"),
        ("PUT", "/portal/access/labs/{username}"),
        ("DELETE", "/portal/access/labs/{username}"),
    ],
    "hub": [
        ("POST", "/portal/hub/auth"),
    ],
}

def get_operation_id(method, path) -> str:
    # Strip the leading slash, then turn the rest to underscores:
    path = path.lstrip("/").replace('/', '_')
    # Replace any placeholder brackets with underscores:
    path = path.replace('{', '_').replace('}', '_')
    # Finally combine everything into the ID:
    return f"wrapper_{path}_{method.lower()}"

class TestPortalAuth:
    def test_excluded_endpoints_in_swagger_ai(self, helpers, lambda_context):
        event = helpers.get_event(path="/api")
        ret = main.lambda_handler(event, lambda_context)
        for _, router in SWAGGER_EXCLUDED_ENDPOINTS.items():
            for exclude in router:
                operation_id = get_operation_id(exclude[0], exclude[1])
                excluded = f'"operationId": "{operation_id}"'
                assert ret["body"].find(excluded) == -1, (
                    f"Found excluded '{exclude[0]} {exclude[1]}' in swagger"
                )

    def test_included_endpoints_in_swagger_ai(self, helpers, lambda_context):
        event = helpers.get_event(path="/api")
        ret = main.lambda_handler(event, lambda_context)
        print(ret["body"])
        for _, router in SWAGGER_INCLUDED_ENDPOINTS.items():
            for include in router:
                operation_id = get_operation_id(include[0], include[1])
                included = f'"operationId": "{operation_id}"'
                assert ret["body"].find(included) != -1, (
                    f"Couldn't find included '{include[0]} {include[1]}' in swagger"
                )
