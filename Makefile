-include .project-gallery.mk

WEB_PORT ?= 8000
DOCKER_CONTEXT ?= default

.PHONY: start stop
start:
	@COMPOSE_PROJECT_NAME=recording WEB_PORT=$(WEB_PORT) docker --context $(DOCKER_CONTEXT) compose up -d --build
	@i=0; until curl -fsS http://127.0.0.1:$(WEB_PORT)/api/health >/dev/null; do i=$$((i + 1)); if [ $$i -ge 120 ]; then echo "Recording service did not become ready on port $(WEB_PORT)."; exit 1; fi; sleep 1; done

stop:
	@COMPOSE_PROJECT_NAME=recording WEB_PORT=$(WEB_PORT) docker --context $(DOCKER_CONTEXT) compose down
