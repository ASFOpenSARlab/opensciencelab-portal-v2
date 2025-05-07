"""AWS Lambda function to handle HTTP requests and return formatted HTML responses."""

from portal import routes
from portal.format import portal_template
from portal.responses import basic_html
from static import get_static_object

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
@basic_html()
@portal_template(app, title="OpenScience", name="logged-out.j2")
def root():
    return "Welcome to OpenScienceLab"


@app.get("/login")
@basic_html()
@portal_template(app, title="Please Log In", name="logged-out.j2")
def login():
    return "Add login form here."


@app.get("/logout")
@basic_html()
@portal_template(app, title="Logged Out", name="logged-out.j2")
def logout():
    return "You have been logged out"


@app.get("/test")
@basic_html()
@portal_template(app, name="logged-out.j2")
def test():
    return """
    <h3>This is a test html</h3>
    """


@app.get("/register")
@basic_html()
@portal_template(app, title="Register New User", name="logged-out.j2")
def register():
    return "Register a new user here"


@app.get("/static/.+")
def static():
    logger.info("Path is %s", app.current_event.path)
    return get_static_object(app.current_event)


@app.not_found
@basic_html(code=404)
@portal_template(app, title="Request Not Found", name="logged-out.j2")
def handle_not_found(error):
    body = f"""
    <h3>Not Found:</h3>
    <pre>{app.current_event.request_context}</pre>
    """

    return body


@logger.inject_lambda_context(
    correlation_id_path=correlation_paths.API_GATEWAY_HTTP,
    log_event=True,
)
def lambda_handler(event, context):
    # print(json.dumps({"Event": event, "Context": context}, default=str))
    return app.resolve(event, context)
