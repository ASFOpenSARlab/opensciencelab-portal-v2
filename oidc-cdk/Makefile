# Respect pathing
export PWD=$(dir $(realpath $(firstword $(MAKEFILE_LIST))))
PROJECT_DIR := $(if $(CI_PROJECT_DIR),$(CI_PROJECT_DIR:/=),$(PWD:/=/../..))
DOCKER_TAG ?= test

# If we're doing TAG_COMMIT, use MATURITY ("prod"), otherwise use DOCKER_TAG
PROJECT_NAME ?= oidc-provider

# # Read in all the variables from AWS/Makefile
# export EXPORT_STRING := $(shell cd .. && make set-env | base64 -w 0 )

# # Cherry pick the variables we care about from AWS/Makefile, don't overwrite variables supplied by GitHub Secrets/Actions
# export AWS_ACCOUNT_NUMBER ?= $(shell echo $(EXPORT_STRING) | base64 --decode | grep ^AWS_ACCOUNT_NUMBER= | sed -n -e 's/^[[:alnum:]_]*\=//p' )

# Config make
SHELL:=/bin/bash
.DEFAULT_GOAL := all
.SILENT:
# .ONESHELL:

.PHONY := cdk-shell
cdk-shell:
	echo "Starting CDK Shell"
	cd ../../build && \
	make cdk-shell PROJ=oidc-cdk/

.PHONY := cdk-deploy
cdk-deploy:
	echo "Deploying ${PROJECT_NAME}"
	cdk --require-approval never deploy 

.PHONY := cdk-synth
cdk-synth:
	echo "Synthesizing ${PROJECT_NAME}"
	cdk synth

