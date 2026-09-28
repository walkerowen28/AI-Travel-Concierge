SHELL := /bin/bash

CLUSTER := travel
NS := travel
KUBECTL_VERSION := v1.34.12
KUBECTL := $(if $(wildcard .bin/kubectl),.bin/kubectl,kubectl)
K := $(KUBECTL) --context kind-$(CLUSTER) -n $(NS)

API_IMAGE := travel-api:dev
WEB_IMAGE := travel-web:dev
DB_IMAGE := postgres:16

.PHONY: k8s-tools k8s-cluster k8s-images k8s-secret k8s-apply k8s-migrate \
	k8s-up k8s-redeploy k8s-status k8s-lb k8s-logs k8s-down

## Download a kubectl that matches the kind node version into ./.bin
k8s-tools:
	@mkdir -p .bin
	curl -fsSLo .bin/kubectl "https://dl.k8s.io/release/$(KUBECTL_VERSION)/bin/$$(uname -s | tr A-Z a-z)/$$(uname -m | sed 's/x86_64/amd64/')/kubectl"
	chmod +x .bin/kubectl
	.bin/kubectl version --client

k8s-cluster:
	@kind get clusters 2>/dev/null | grep -qx $(CLUSTER) || kind create cluster --config k8s/kind-config.yaml

## kind nodes cannot see your local Docker images; they must be loaded in.
k8s-images:
	docker build -t $(API_IMAGE) backend
	docker build -t $(WEB_IMAGE) frontend
	docker pull -q $(DB_IMAGE)
	kind load docker-image --name $(CLUSTER) $(API_IMAGE) $(WEB_IMAGE) $(DB_IMAGE)

## Creates/updates api-secrets from OPENAI_API_KEY in .env (empty if missing).
k8s-secret:
	$(KUBECTL) --context kind-$(CLUSTER) apply -f k8s/namespace.yaml
	$(K) create secret generic api-secrets \
		--from-env-file=<(grep -E '^OPENAI_API_KEY=' .env 2>/dev/null || echo 'OPENAI_API_KEY=') \
		--dry-run=client -o yaml | $(K) apply -f -

k8s-apply:
	$(KUBECTL) --context kind-$(CLUSTER) apply -k k8s
	$(K) rollout status statefulset/db --timeout=180s

## Jobs are immutable, so delete the previous run before starting a new one.
k8s-migrate:
	$(K) delete job db-migrate --ignore-not-found
	$(K) apply -f k8s/jobs/db-migrate.yaml
	$(K) wait --for=condition=complete job/db-migrate --timeout=180s
	$(K) logs job/db-migrate

k8s-up: k8s-cluster k8s-images k8s-secret k8s-apply k8s-migrate
	$(K) rollout status deployment/api --timeout=180s
	$(K) rollout status deployment/web --timeout=180s
	@echo "App: http://localhost:8090"

## After code changes: rebuild + reload images, migrate, rolling restart.
k8s-redeploy: k8s-images k8s-secret k8s-migrate
	$(K) rollout restart deployment/api deployment/web
	$(K) rollout status deployment/api --timeout=180s
	$(K) rollout status deployment/web --timeout=180s

k8s-status:
	$(K) get pods,svc,jobs,pvc -o wide

## Hit the app a few times and show which web and api pod answered each request.
k8s-lb:
	@for i in $$(seq 1 8); do \
		curl -s -o /dev/null -D - http://localhost:8090/api/health/live \
			| tr -d '\r' | awk -F': ' 'tolower($$1)=="x-web-pod"{w=$$2} tolower($$1)=="x-api-pod"{a=$$2} END{printf "web=%-24s api=%s\n", w, a}'; \
	done

k8s-logs:
	$(K) logs -l app=api --prefix --tail=50

k8s-down:
	kind delete cluster --name $(CLUSTER)
