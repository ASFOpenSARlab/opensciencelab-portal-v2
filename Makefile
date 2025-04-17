define HELP

Makefile commands:

    help:            List makefile commands

    local-build:     Build image for local development

    local-run:       Run container for local development

    lint:            Run linting commands

    cdk-image:       Create CDK Build environment Docker image

    cdk-shell:       Enter CDK enviroment Docker Image

    cdk-bootstrap:   Bootstrap an account for CDK

endef
export HELP

# work in BASH
SHELL:=/bin/bash

# Respect pathing
export PWD=$(dir $(realpath $(firstword $(MAKEFILE_LIST))))
PROJECT_DIR := $(if $(CI_PROJECT_DIR),$(CI_PROJECT_DIR:/=),$(PWD:/=/))

# If we're doing TAG_COMMIT, use MATURITY ("prod"), otherwise use DOCKER_TAG
DOCKER_TAG ?= local
DEPLOY_PREFIX ?= $(if $(TAG_COMMIT),$(MATURITY),$(DOCKER_TAG))

IMAGE_NAME ?= cdk-env
AWS_DEFAULT_PROFILE := $(AWS_DEFAULT_PROFILE)
AWS_REGION ?= us-west-2

.PHONY := all
all: help

.PHONY := help
help:
	@echo "$$HELP"

.PHONY := local-build
local-build:
	docker build -f local-build.Dockerfile -t localhost:5000/portalv2:local-build .

.PHONY := local-run
local-run:
	docker run -it --rm -v $$(pwd)/portal-cdk:/tmp/portal-cdk --user $$(id -u) localhost:5000/portalv2:local-build bash

.PHONY := lint
lint:
	echo "Starting Docker Shell..."
	echo ""
	docker run \
		-v "$$(pwd):/code" \
		-it \
		--rm \
		--pull always \
		ghcr.io/asfopensarlab/osl-utils:v0.0.9 \
		make all && \
	echo "### All Linting Passed ###" || \
	echo "⚠️⚠️⚠️ Linting was not successful ⚠️⚠️⚠️"

### CDK Environment
.PHONY := cdk-image
cdk-image:
	cd ${PROJECT_DIR} && pwd && docker build --pull -t ${IMAGE_NAME}:latest -f ./build/cdk.Dockerfile .

.PHONY := cdk-shell
cdk-shell:
	export AWS_DEFAULT_ACCOUNT=`aws sts get-caller-identity --query 'Account' --output=text` && \
	export AWS_DEFAULT_REGION="${AWS_REGION}" && \
		if [ -z "$$AWS_DEFAULT_ACCOUNT" ]; then echo "⚠️  Can't infer AWS credentials! ⚠️"; fi && \
	mkdir -p /tmp/cdkawscli/cache && \
	docker run --rm -it \
		-v ~/.aws/:/root/.aws/:ro \
		-v /tmp/cdkawscli/cache:/root/.aws/cli/cache/ \
		-v ${PROJECT_DIR}/portal-cdk/:/cdk/ \
		-v ${PROJECT_DIR}/build/:/build/ \
		-e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY \
		-e AWS_DEFAULT_PROFILE -e AWS_PROFILE \
		-e AWS_DEFAULT_REGION -e AWS_REGION \
		-e AWS_DEFAULT_ACCOUNT \
		-e DEPLOY_PREFIX \
		${IMAGE_NAME}:latest

.PHONY := cdk-bootstrap
cdk-bootstrap:
	# This needs to be run once per account.
	if [ -z "${AWS_DEFAULT_PROFILE}" ]; then echo "AWS_DEFAULT_PROFILE is not set"; fi
	if [ -z "$$AWS_DEFAULT_ACCOUNT" ]; then echo "Could not get AWS account number" && exit 13; fi && \
	if [ -z "$$AWS_DEFAULT_REGION" ]; then echo "Could not get AWS Region" && exit 6; fi && \
	echo "Running: \`cdk bootstrap aws://$$AWS_DEFAULT_ACCOUNT/${AWS_DEFAULT_REGION}\`..."
	cdk bootstrap aws://$$AWS_DEFAULT_ACCOUNT/${AWS_DEFAULT_REGION} --public-access-block-configuration false