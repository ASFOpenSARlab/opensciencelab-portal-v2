

define HELP

Makefile commands:

    help:            List makefile commands

    local-build:     Build image for local development

    local-run:       Run container for local development

endef
export HELP

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
