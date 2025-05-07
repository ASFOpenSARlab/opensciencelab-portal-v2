"""AWS Lambda function to handle HTTP requests and return formatted HTML responses."""

from portal import routes
from static import get_static_object
from portal_formatting import portal_template, basic_html

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler.api_gateway import APIGatewayHttpResolver
from aws_lambda_powertools.logging import correlation_paths

logger = Logger(service="APP")

# Rest is V1, HTTP is V2
app = APIGatewayHttpResolver()

# Add portal routes
for prefix, router in routes.items():
    app.include_router(router, prefix=prefix)


@app.get("/")
def root():
    return basic_html(portal_template("Welcome to OpenScienceLab"))


@app.get("/login")
def login():
    return basic_html(portal_template("Add login form here."))


@app.get("/logout")
def logout():
    return basic_html(portal_template("You have been logged out"))


@app.get("/register")
def register():
    return basic_html(portal_template("Register a new user here"))


@app.get("/static/.+")
def static():
    logger.info("Path is %s", app.current_event.path)
    return get_static_object(app.current_event)


@app.not_found
def handle_not_found(error):
    body = f"""
    <h3>Not Found:</h3>
    <pre>{app.current_event.request_context}</pre>
    """

    return basic_html(portal_template(body))


@logger.inject_lambda_context(
    correlation_id_path=correlation_paths.API_GATEWAY_HTTP,
    log_event=True,
)
def lambda_handler(event, context):
    # print(json.dumps({"Event": event, "Context": context}, default=str))
    return app.resolve(event, context)
