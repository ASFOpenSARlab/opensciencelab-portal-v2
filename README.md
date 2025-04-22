# opensciencelab-portal-v2

## Architecture

At the most basic level, the new portal is a Python Lambda app, back-ended by AWS DynamoDB, and 
front-ended by API Gateway and CloudFront. 

![Architecture Diagram](./docs/Portal%20V2.png)

## Deployments

### AWS Accounts

| Maturity | Environment | AWS Account  |
| -- | -- |--------------|
| `dev` | Non-prod | 97********89 |
| `test` | Non-Prod | 97********89 |
| `prod` | Prod | 16********27 |

### Maturities

* Non-`main` branches with specified prefix/suffix (eg `ab/ticket.feature`) will deploy a matched
prefix (ie `ab`) dev maturity ( and `dev` GitHub environment!) deployment. 
* Merges into `main` branch will create/update the `test` maturity deployment.
* Symantic Tags (where `v#.#.#` is `v[Major].[Minor].[Patch]`) will deploy to Prod.

#### `Dev`/Development

While development maturity can be deployment manually via [`Docker`](./build/cdk.Dockerfile) 
& [`Makefile`](./Makefile), it may be easier and more consistent to rely on the GitHub action. 
However, when necessary, developer deployments can be completed using the following steps:

##### Deploying a Personal Stack

You can deploy a new stack without conflicting with any others, with:

```bash
# Just synthing locally:
make synth-portal -e DEPLOY_PREFIX=cs
# Or deploying:
make deploy-portal -e DEPLOY_PREFIX=cs
# (Will default to the 'dev' MATURITY, no need to set that too.)
```

##### Clone Repo

Clone the portal repo to your local work station

##### Ensure AWS credentials a present 

The Makefile + Docker process will need to communicate with AWS. In actions, this is done through an
OIDC Provider in AWS and requires no authentication. Locally however, a profile must be present in 
`~/.aws/credentials` and the `AWS_DEFAULT_PROFILE` env var needs to be set accordingly, ***OR*** 
`AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` must be set. Either solution works, and will get 
automagically populated into the dockerized build/deploy environment.

##### Start CDK Shell 

From the root of the cloned repo, run `make cdk-image` to build the image:
```shell
user@Mac-mini opensciencelab-portal-v2 % make cdk-image
cd /Users/user/PycharmProjects/opensciencelab-portal-v2/ && pwd && docker build --pull -t cdk-env:latest -f ./build/cdk.Dockerfile .
/Users/user/PycharmProjects/opensciencelab-portal-v2
[+] Building 67.3s (15/15) FINISHED                                                                                                                                               docker:desktop-linux
 => [internal] load[.yamllint.yaml](.yamllint.yaml) build definition from cdk.Dockerfile                                                                                                                                          0.0s
[....clipped.....]                                                                                                                                0.7s
 => [10/10] COPY ./build /build                                                                                                                                                                   0.0s
 => exporting to image                                                                                                                                                                            3.9s
 => => exporting layers                                                                                                                                                                           3.9s
 => => writing image sha256:4ce2799f6aed653350571169671645ea591af787b7ab60ad0efbc3c5984781b6                                                                                                      0.0s
 => => naming to docker.io/library/cdk-env:latest                         
```

That step can be skipped if the image is already cashed. Next start the container:

```shell
user@Mac-mini opensciencelab-portal-v2 % make cdk-shell
[ root@a7a585db4d88:/cdk ]# 

```

##### Deploy via CDK

```shell
[ root@a7a585db4d88:/cdk ]# make cdk-synth

[ root@a7a585db4d88:/cdk ]# make cdk-deploy
```

##### Linting

Before committing changes, the code can be easily linted by utilizing the `lint` 
target of the Makefile. This will call the same linting routines used by the 
GitHub actions. 

#### **`Test`**

**`Test`** is intended to be the stable integration/validation environment. ONLY complete, tested code
should be released to **`Test`**. `Dev` and `Test` exist in the same AWS account. 

#### **`Prod`**

The **`Prod`** environment is isolated in its own AWS account to reduce blast radius. `Prod` 
should **never** be released by any mechanism other than GitHub actions.

### Automation

#### GitHub Actions

* [`lint.yaml`](.github/workflows/lint.yaml) - Automate code linting and formatting enforcement
* [`on-pull-request-notify.yaml`](.github/workflows/on-pull-request-notify.yaml) - Alert SES 
mattermost channel about new and modified non-draft pull requests.

## CDK Tech

**_Information about CDK stack(s)_**

