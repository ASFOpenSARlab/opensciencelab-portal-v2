"""AWS Lambda function to handle HTTP requests and return formatted HTML responses."""

import os
import json

from portal import routes

# Tmp for deprecated email endpoint:
from portal.hub import swagger_email_options, send_user_email

from util.format import (
    portal_template,
    request_context_string,
    render_template,
)
from util.responses import wrap_response
from util.auth import (
    parse_token,
    validate_code,
    process_auth,
    delete_cookies,
    revoke_refresh_token,
    refresh_map_del,
)
from util.exceptions import GenericFatalError
from util.session import current_session
from util.user import User

from static import get_static_object

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.event_handler import content_types

# If IS_PROD is somehow set to "asdf" or something, default to non-prod (True)
is_not_prod = os.getenv("IS_PROD", "false").lower() != "true"
# If DEBUG is somehow set to "asdf" or something, default to False (lock-down)
should_debug = os.getenv("DEBUG", "false").lower() == "true"

## Root logger, others will inherit from this:
# https://docs.powertools.aws.dev/lambda/python/latest/core/logger/#child-loggers
logger = Logger(log_uncaught_exceptions=should_debug)

# Rest is V1, HTTP is V2
# debug: https://docs.powertools.aws.dev/lambda/python/latest/core/event_handler/api_gateway/#debug-mode
app = APIGatewayHttpResolver(debug=should_debug)

#####################
### Swagger Stuff ###
#####################
# # Debug is based on the maturity, use that to enable open_api:
if is_not_prod:
    ## All the params can be found at:
    # https://docs.powertools.aws.dev/lambda/python/latest/core/event_handler/api_gateway/#enabling-swaggerui
    # https://docs.powertools.aws.dev/lambda/python/latest/core/event_handler/api_gateway/#customizing-swagger-ui
    app.enable_swagger(
        title="OpenScienceLab Portal - API docs",
        path="/api",
        description="API documentation for OpenScienceLab's portal",
        version="0.0.1",
    )

##############
### Routes ###
##############

# Add portal routes
for prefix, router in routes.items():
    app.include_router(router, prefix=prefix)


@app.get("/", include_in_schema=False)
def root():
    # Forward to portal if they are logged in
    if current_session.user:
        return wrap_response(
            body="Redirecting to Portal",
            headers={"Location": "/portal"},
            code=302,
        )

    return wrap_response(
        render_template(
            content="Welcome to OpenScienceLab",
            title="OpenScience",
            name="landing.j2",
        )
    )


# This endpoint exists primarily for dumping to html
@app.get("/error", include_in_schema=False)
def error():
    return wrap_response(
        render_template(
            content="An unexpected error has occurred",
            name="error.j2",
            title="OpenScienceLab: Something went wrong",
        ),
        code=401,
    )


@app.get("/logout", include_in_schema=False)
def logout():
    # Revoke this refresh token, kill session
    if current_session.auth.cognito.raw:
        revoke_refresh_token(current_session.auth.cognito.raw)
        refresh_map_del(current_session.auth.cognito.raw)

    return wrap_response(
        body="You have been logged out",
        headers={"Location": "/"},
        code=302,
        cookies=delete_cookies(),
    )


@app.get("/register", include_in_schema=False)
@portal_template(title="Register New User", name="logged-out.j2")
def register():
    return "Register a new user here"


@app.get("/auth", include_in_schema=False)
def auth_code():
    code = app.current_event.query_string_parameters.get("code")
    if not code:
        return wrap_response(render_template(content="No return Code found."), code=401)

    inbound_host = os.getenv("DEPLOYMENT_HOSTNAME")
    token_payload = validate_code(code, inbound_host)
    if not token_payload:
        return wrap_response(
            render_template(content="Could not complete token exchange"), code=401
        )

    token_dict = parse_token(token_payload)
    state = app.current_event.query_string_parameters.get("state", "/portal")

    user = User(token_dict["username"])
    user.update_last_cookie_assignment()

    # Send the newly logged in user to the Portal
    return wrap_response(
        render_template(content=f"Redirecting to {state}"),
        code=302,
        cookies=token_dict["cookie_headers"],
        headers={"Location": state},
    )


@app.get("/static/.+", include_in_schema=False)
def static():
    logger.debug("Path is %s", app.current_event.path)
    return get_static_object(app.current_event)


@app.post(
    "/user/email/send",
    **swagger_email_options,
    deprecated=True,
    description="Forwards everything to `/portal/hub/user/email`.",
)
def send_user_email_deprecated():
    return send_user_email()


######################
### Error Handling ###
######################


@app.not_found
@portal_template(title="Request Not Found", name="logged-out.j2", response=404)
def handle_not_found(error):
    # Don't dump context in prod
    if os.getenv("IS_PROD", "false").lower() != "true":
        # Dump request context in non-prod
        debug_info = f"<pre>{request_context_string(app)}</pre>"
    else:
        debug_info = "<a href='/portal'>Return to portal Home</a>"

    body = f"""
    <h3>Not Found: '{app.current_event.request_context.http.path}'<h3>
    <hr>
    {debug_info}
    """
    return body


# https://docs.powertools.aws.dev/lambda/python/1.25.3/core/event_handler/api_gateway/#exception-handling
# THIS SHOULD BE THE ONLY ONE! Other exceptions inherit from this one:
@app.exception_handler(GenericFatalError)
def handle_generic_fatal_error(exception):
    return wrap_response(
        json.dumps(
            {
                "error": exception.message,
                "extra_info": exception.extra_info,
            }
        ),
        code=exception.error_code,
        content_type=content_types.APPLICATION_JSON,
    )


############
### MAIN ###
############
@logger.inject_lambda_context(
    correlation_id_path=correlation_paths.API_GATEWAY_HTTP,
    log_event=should_debug,
)
@process_auth
def lambda_handler(event, context):
    current_session.app = app  # Pass app into downstream functions
    return app.resolve(event, context)
