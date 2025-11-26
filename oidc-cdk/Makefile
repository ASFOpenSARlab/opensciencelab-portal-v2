# Project name for the stack
PROJECT_NAME ?= oidc-provider

# Config make
SHELL:=/bin/bash
.DEFAULT_GOAL := all
.SILENT:

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
