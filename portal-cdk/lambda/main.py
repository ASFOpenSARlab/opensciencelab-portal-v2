# Example from: https://docs.powertools.aws.dev/lambda/python/latest/tutorial/#simplifying-with-logger

from portal_formatting import portal_template, basic_html

from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler.api_gateway import APIGatewayHttpResolver
from aws_lambda_powertools.logging import correlation_paths

logger = Logger(service="APP")

# Rest is V1, HTTP is V2
app = APIGatewayHttpResolver()


@app.get("/hello/<name>")
def hello_name(name):
    logger.info(f"Request from {name} received")
    return basic_html(portal_template(f"hello {name}!"))


@app.get("/hello")
def hello():
    logger.info("Request from unknown received")
    return basic_html(portal_template("Hello Unknown"))


@logger.inject_lambda_context(
    correlation_id_path=correlation_paths.API_GATEWAY_HTTP,
    log_event=True,
)
def lambda_handler(event, context):
    return app.resolve(event, context)
