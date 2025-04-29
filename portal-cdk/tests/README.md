# How to Test

CDK has three main ways to test your code. Using SAM for lambda, using unit testing for making sure the synthed template has specific features (i.e lambda functions can only have specific runtimes), and snapshot testing.

Snapshot testing is just saving a synthed template, and erroring if that template changes. It's useful if you have a stable project and you're about to refactor, but NOT when you're in the development phase. We'll focus on the other two options.

## SAM Testing

- If you haven't, [here's the install instructions](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html#install-sam-cli-instructions).
- [Here's a high-level guide](https://docs.aws.amazon.com/cdk/v2/guide/testing-locally-getting-started.html) in testing lambda functions locally.
- [And a slightly more in-depth guide](https://docs.aws.amazon.com/cdk/v2/guide/testing-locally-with-sam-cli.html) on testing lambda functions locally.

For example, what I was able to get to work:

1) Go to `portal-cdk/cdk.out/<StackName>-<DeployPrefix>.template.json`. Make note of that file, AND ALSO ctrl-f inside it for your lambda function name. Mine ended up being `testlambdadynamodbstackLambdaFunctionDA383F07`. Note that too.

2) With those two arguments, run in the root of the project:

```bash
sam local invoke <FUNCTION_NAME> --event ./portal-cdk/tests/events/basic-api-gateway.json -t ./portal-cdk/cdk.out/<StackName>-<DeployPrefix>.template.json
# For me it'd be:
sam local invoke testlambdadynamodbstackLambdaFunctionDA383F07 --event ./portal-cdk/tests/events/basic-api-gateway.json -t ./portal-cdk/cdk.out/PortalCdkStack-cs.template.json
```

NOTE: To get the `./portal-cdk/tests/events/basic-api-gateway.json`, I had to add `print(json.dumps({"Event": event, "Context": context}, default=str))` to the lambda and copy it out of the cloudwatch logs. When I tried to use the built-in lambda one, it'd only return 404's, but maybe I was just selecting the wrong event pattern? Since we have one that works, if we need to expand it, we can modify the existing one for now.

## Unit Testing

If you HAVEN'T synth/deployed yet, you'll have to generate the files for one of the lambda's:

```bash
make bundle-deps
```

To run unit testing, use:

```bash
cd portal-cdk
pytest
```

There's more flags we can add to pytest, like threads. We also need to decide when to automate running tests. It does NOT stop synthing by itself.
