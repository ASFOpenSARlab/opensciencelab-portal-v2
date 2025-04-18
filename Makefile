define HELP

Makefile commands:

    help:                   List makefile commands

    lint:                   Run linting commands

    cdk-image:              Create CDK Build environment Docker image

    cdk-shell:              Enter CDK enviroment Docker Image

    manual-cdk-bootstrap:   Bootstrap an account for CDK

    cdk-deploy:             Deploy CDK project

    cdk-synth:              Synth CDK project

    aws-whoami:             Get AWS account info    

endef
export HELP

# work in BASH
SHELL:=/bin/bash

# Get terminal colors
_SUCCESS := "\033[32m%s\033[0m %s\n" # Green text for "printf"
_DANGER := "\033[31m%s\033[0m %s\n" # Red text for "printf"

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
		-v ${PROJECT_DIR}/oidc-cdk/:/oidc/ \
		-v ${PROJECT_DIR}/Makefile:/Makefile \
		-e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY \
		-e AWS_DEFAULT_PROFILE -e AWS_PROFILE \
		-e AWS_DEFAULT_REGION -e AWS_REGION \
		-e AWS_DEFAULT_ACCOUNT \
		-e DEPLOY_PREFIX \
		${IMAGE_NAME}:latest

.PHONY := manual-cdk-bootstrap
manual-cdk-bootstrap:
	# This needs to be run once per account.
	if [ -z "${AWS_DEFAULT_PROFILE}" ]; then echo "AWS_DEFAULT_PROFILE is not set"; fi ; && \
	export AWS_DEFAULT_ACCOUNT=`aws sts get-caller-identity --query 'Account' --output=text` ; && \
	export AWS_DEFAULT_REGION="${AWS_REGION}" ; && \
	if [ -z "$$AWS_DEFAULT_ACCOUNT" ]; then echo "⚠️  Can't infer AWS credentials from AWS_DEFAULT_ACCOUNT! ⚠️" && exit; fi && \
	echo "Make sure we bootstrap credentials manually once per AWS account" ; && \
	read -p "Are you sure? [y/N] " ans && ans=$${ans:-N} ; && \
	if [ $${ans} = y ] || [ $${ans} = Y ]; then \
		printf $(_SUCCESS) "Running: \`cdk bootstrap aws://$$AWS_DEFAULT_ACCOUNT/${AWS_DEFAULT_REGION}\`..." ; && \
		cdk bootstrap aws://$$AWS_DEFAULT_ACCOUNT/${AWS_DEFAULT_REGION} --public-access-block-configuration false ; \
	else \
		printf $(_DANGER) "Aborted" ; \
	fi

.PHONY := cdk-deploy
cdk-deploy:
	echo "Deploying ${PROJECT_NAME}"
	cdk --require-approval never deploy 

.PHONY := cdk-synth
cdk-synth:
	echo "Synthesizing ${PROJECT_NAME}"
	cdk synth

.PHONY := aws-whoami
aws-whoami:
	aws sts get-caller-identity \
		--query "$${query:-Arn}" \
		--output text