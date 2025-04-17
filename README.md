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

While development maturity can be deployment manually via [`Docker`](./Fix-Me-When-Avaiable.Dockerfile) 
& [`Makefile`](./Makefile), it may be easier and more consistent to rely on the GitHub action. 
However, when necessary, developer deployments can be completed using the following steps:

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

