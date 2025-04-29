# How to Test

CDK has three main ways to test your code. Using SAM for lambda, using unit testing for making sure the synthed template has specific features (i.e lambda functions can only have specific runtimes), and snapshot testing.

Snapshot testing is just saving a synthed template, and erroring if that template changes. It's useful if you have a stable project and you're about to refactor, but NOT when you're in the development phase. We'll focus on the other two options.

## SAM Testing

- If you haven't, [here's the install instructions](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html#install-sam-cli-instructions).
- [Here's a high-level guide](https://docs.aws.amazon.com/cdk/v2/guide/testing-locally-getting-started.html) in testing lambda functions locally.

## Unit Testing

To run unit testing, use:

```bash
cd portal-cdk
pytest
```

There's more flags we can add to pytest, like threads. We also need to decide when to automate running tests. It does NOT stop synthing by itself.
