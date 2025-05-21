"""AWS Lambda function to handle HTTP requests and return formatted HTML responses."""

import os
import json

from portal import routes
from util.format import (
    portal_template,
    request_context_string,
    render_template,
)
from util.responses import basic_html, wrap_response
from util.auth import get_set_cookie_headers, validate_code, process_auth
from util.exceptions import GenericFatalError
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
    router.app = app


@app.get("/")
@portal_template(app, title="OpenScience", name="logged-out.j2")
def root():
    return "Welcome to OpenScienceLab"


@app.get("/login")
@portal_template(app, title="Please Log In", name="logged-out.j2")
def login():
    return "Add login form here."


@app.get("/logout")
@portal_template(app, title="Logged Out", name="logged-out.j2")
def logout():
    # TODO: Remove cookies here.
    return "You have been logged out"


@app.get("/test")
@basic_html(code=200)
@portal_template(app, name="logged-out.j2", response=None)
def test():
    # Another way to use basic_html & portal_template
    return """
    <h3>This is a test html</h3>
    """


@app.get("/register")
@portal_template(app, title="Register New User", name="logged-out.j2")
def register():
    return "Register a new user here"


@app.get("/auth")
def auth_code():
    code = app.current_event.query_string_parameters.get("code")
    if not code:
        return wrap_response(
            render_template(app, content="No return Code found."), code=401
        )

    # FIXME: inbound_host must match the origin of initial cognito login request.
    #        This value needs to be more dynamically detected. Right now, the CF
    #        endpoint (or _actual_ host) is not embedded in the request.
    # inbound_host = app.current_event.request_context.domain_name
    inbound_host = os.getenv("CLOUDFRONT_ENDPOINT")
    token_payload = validate_code(code, inbound_host)
    if not token_payload:
        return wrap_response(
            render_template(app, content="Could not complete token exchange"), code=401
        )

    set_cookie_headers = get_set_cookie_headers(token_payload)
    state = app.current_event.query_string_parameters.get("state", "/portal")

    # Send the newly logged in user to the Portal
    return wrap_response(
        render_template(app, content=f"Redirecting to {state}"),
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
@portal_template(app, title="Request Not Found", name="logged-out.j2", response=404)
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
        render_template(app, content=exception.message),
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
    print(json.dumps({"Event": event, "Context": context}, default=str))
    return app.resolve(event, context)
