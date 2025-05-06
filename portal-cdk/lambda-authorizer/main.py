
def lambda_handler(event, context):
    # event['headers']['x-origin-verify']
    ## We're using Lambda Response v2.0:
    # https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-lambda-authorizer.html#http-api-lambda-authorizer.payload-format-response
    return {
        "isAuthorized": True,
        # We can pass what ever we want in context later:
        # "context": {},
    }
