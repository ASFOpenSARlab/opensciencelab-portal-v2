# Portal CDK Docs

## L3 Construct Notes

### Lambda and DynamoDB

I only looked briefly, but found one solid one:

<https://constructs.dev/packages/@aws-solutions-constructs/aws-lambda-dynamodb/v/2.84.0?lang=python>

It's created by the AWS CDK team, and supports python. It's labeled as `stable` too.

### Lambda and API Gateway

For this, I found two:

- <https://constructs.dev/packages/@aws-solutions-constructs/aws-apigateway-lambda/v/2.84.0?lang=python>
- <https://constructs.dev/packages/@aws-solutions-constructs/aws-openapigateway-lambda/v/2.84.0?lang=python>

Both are from the CDK team. The Open API Gateway is experimental, and I'm not sure what the difference between the two is.

### Lambda, Api Gateway, AND Cloudfront

Even better...

<https://constructs.dev/packages/@aws-solutions-constructs/aws-cloudfront-apigateway-lambda/v/2.84.0?lang=python>
