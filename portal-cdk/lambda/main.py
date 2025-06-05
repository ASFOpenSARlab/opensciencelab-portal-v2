"""AWS Lambda function to handle HTTP requests and return formatted HTML responses."""

import os
import datetime

from portal import routes
from util.format import (
    portal_template,
    request_context_string,
    render_template,
)
from util.responses import wrap_response
from util.auth import (
    get_set_cookie_headers,
    validate_code,
    process_auth,
    delete_cookies,
    validate_jwt,
)
from util.exceptions import GenericFatalError
from util.session import current_session
from util.user import User

from static import get_static_object

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
from aws_lambda_powertools.logging import correlation_paths


should_debug = os.getenv("DEBUG", "false").lower() == "true"

## Root logger, others will inherit from this:
# https://docs.powertools.aws.dev/lambda/python/latest/core/logger/#child-loggers
logger = Logger(log_uncaught_exceptions=should_debug)


# Rest is V1, HTTP is V2
app = APIGatewayHttpResolver()

##############
### Routes ###
##############

# Add portal routes
for prefix, router in routes.items():
    app.include_router(router, prefix=prefix)


@app.get("/")
@portal_template(title="OpenScience", name="logged-out.j2")
def root():
    return "Welcome to OpenScienceLab"


@app.get("/logout")
def logout():
    return wrap_response(
        render_template(
            content="You have been logged out",
            title="Logged Out",
            name="logged-out.j2",
        ),
        code=200,
        cookies=delete_cookies(),
    )


@app.get("/register")
@portal_template(title="Register New User", name="logged-out.j2")
def register():
    return "Register a new user here"


@app.get("/auth")
def auth_code():
    code = app.current_event.query_string_parameters.get("code")
    if not code:
        return wrap_response(render_template(content="No return Code found."), code=401)

    # FIXME: inbound_host must match the origin of initial cognito login request.
    #        This value needs to be more dynamically detected. Right now, the CF
    #        endpoint (or _actual_ host) is not embedded in the request.
    # inbound_host = app.current_event.request_context.domain_name
    inbound_host = os.getenv("CLOUDFRONT_ENDPOINT")
    token_payload = validate_code(code, inbound_host)
    if not token_payload:
        return wrap_response(
            render_template(content="Could not complete token exchange"), code=401
        )

    set_cookie_headers = get_set_cookie_headers(token_payload)
    state = app.current_event.query_string_parameters.get("state", "/portal")

    ## Update User last_cookie_assignment
    # Get username from token
    access_token_jwt = token_payload["access_token"]
    access_token_decoded = validate_jwt(access_token_jwt)
    # make sure the JWT validated
    if access_token_decoded:
        username = access_token_decoded.get("username", "Unknown")
        user = User(username)
        user.last_cookie_assignment = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    else:
        logger.info("Failed to set user last_cookie_assignment")

    # Send the newly logged in user to the Portal
    return wrap_response(
        render_template(content=f"Redirecting to {state}"),
        code=302,
        cookies=set_cookie_headers,
        headers={"Location": state},
    )


@app.get("/static/.+")
def static():
    logger.debug("Path is %s", app.current_event.path)
    return get_static_object(app.current_event)


######################
### Error Handling ###
######################


@app.not_found
@portal_template(title="Request Not Found", name="logged-out.j2", response=404)
def handle_not_found(error):
    body = f"""
    <h3>Not Found: '{app.current_event.request_context.http.path}'<h3>
    <hr>
    <pre>{request_context_string(app)}</pre>
    """
    return body


# https://docs.powertools.aws.dev/lambda/python/1.25.3/core/event_handler/api_gateway/#exception-handling
@app.exception_handler(GenericFatalError)
def handle_generic_fatal_error(exception):
    return wrap_response(
        render_template(content=exception.message),
        code=exception.error_code,
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
