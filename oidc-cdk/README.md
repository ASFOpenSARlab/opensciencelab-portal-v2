# OIDC Provider Rules and CloudFormation

To facilitate credential-free deployemnts to AWS

## Adding Project Access roles

To add or update a role needed for CDK to deploy to AWS,
create or modify the entry in the Class [`roles`](oidc_provider.py#L30) object:

```python
roles = [
    "role_name_goes_here": {
        "description": "IAM Role for Fubar Project",
        "name": "FullLogAccessForFubar",      # Inline Policy Name
        "statements": [
            {
                "effect": "allow",            # or deny
                "actions": ["logs:*"],        # List of actions like s3:CreateBucket
                "resources": [                # List of Resources to allow access to
                    "arn:aws:logs:*:*:*"
                ]
            }
        ]
    }
]

```

## Building app

### Manual Build

#### Initialze Dockerized CDK Environment

```bash

# Navigate to this path
> pwd
/Path/To/Github_repo/oidc-cdk/                                                                                                                0.0s
<<< Output Clipped >>>
 => => exporting layers                                                                                                                                                      0.0s
 => => writing image sha256:32b8799e3caf3f902a087e8e60a8142292264a887884f06d8bad472d6726ada0                                                                                 0.0s
 => => naming to docker.io/library/dev-oidc-provider:latest
```

#### Using Dockerized CDK Environment

The following ENV VARS are exported to the docker run environemnt, but `AWS_DEFAULT_PROFILE` is the most critical.

- `AWS_DEFAULT_REGION='us-west-2'`
- `AWS_DEFAULT_PROFILE`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `PROJECT_NAME`
- `DEPLOY_PREFIX`
- `PROJECT_NAME`

```bash
# It is helpful to set a AWS Profile.
> export AWS_DEFAULT_PROFILE=portal-nonprod-profile

# To run the docker environment:
> make cdk-shell
bash-4.2#
```

Once we're shelled into the Dockerized environment, we can start working with CDK!

```bash
# AWS accounts need to be bootstrapped for each region (Once!)
bash-4.2# make cdk-bootstrap
 ⏳  Bootstrapping environment aws://000000000000/us-west-2...
Trusted accounts for deployment: (none)
Trusted accounts for lookup: (none)
Using default execution policy of 'arn:aws:iam::aws:policy/AdministratorAccess'. Pass '--cloudformation-execution-policies' to customize.
CDKToolkit: creating CloudFormation changeset...
 ✅  Environment aws://000000000000/us-west-2 bootstrapped.

# To see the synthesized template:
bash-4.2# make cdk-synth

# To Deploy the stack:
bash-4.2# make cdk-deploy
```
