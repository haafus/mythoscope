# Thin wrappers over fabfile.py; see docs/deployment.md §2.
#
#   make deploy
#   make push-outputs ZIP=mythoscope-export-20260803.zip
#   make logs N=200
#   make deploy HOST=203.0.113.7      # by IP while DNS propagates

DOMAIN      ?= mythoscope.io
HOST        ?= $(DOMAIN)
DEPLOY_USER ?= ubuntu
FAB         ?= fab
ZIP         ?=
N           ?= 100

# fabfile.py reads these too; exporting keeps its asserts and Caddyfile in step
# with the -H given here.
export MYTHO_DEPLOY_DOMAIN := $(DOMAIN)
export MYTHO_DEPLOY_USER   := $(DEPLOY_USER)

AS_DEPLOY := $(FAB) -H $(DEPLOY_USER)@$(HOST)

.DEFAULT_GOAL := help
.PHONY: help bootstrap deploy push-outputs rollback-outputs status logs restart smoke

help:
	@echo "make bootstrap          once per server, as root"
	@echo "make deploy             code: rsync, uv sync, restart, smoke"
	@echo "make push-outputs       data: stage and swap outputs/ [ZIP=bundle.zip]"
	@echo "make rollback-outputs   swap outputs.prev back in"
	@echo "make status | logs [N=100] | restart | smoke"
	@echo "Overrides: HOST=$(HOST) DOMAIN=$(DOMAIN) DEPLOY_USER=$(DEPLOY_USER)"

bootstrap:
	$(FAB) -H root@$(HOST) bootstrap

deploy:
	$(AS_DEPLOY) deploy

push-outputs:
	$(AS_DEPLOY) push-outputs $(if $(ZIP),--from-zip=$(ZIP))

rollback-outputs:
	$(AS_DEPLOY) rollback-outputs

status:
	$(AS_DEPLOY) status

logs:
	$(AS_DEPLOY) logs --n=$(N)

restart:
	$(AS_DEPLOY) restart

smoke:
	$(AS_DEPLOY) smoke
