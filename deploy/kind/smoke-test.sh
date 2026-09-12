#!/usr/bin/env bash
set -euo pipefail

cluster_name="${KIND_CLUSTER_NAME:-tcg-proxy-lab}"
image="${TCG_PROXY_LAB_IMAGE:-tcg-proxy-lab:kind}"

docker build --tag "${image}" .
kind load docker-image --name "${cluster_name}" "${image}"
kubectl apply -k deploy/kind
kubectl -n librefang rollout status deployment/kong-ai-gateway --timeout=120s
kubectl -n tcg-proxy-lab rollout status deployment/tcg-proxy-lab --timeout=180s

kubectl -n tcg-proxy-lab run allowed-ingress-probe \
  --image=python:3.12-alpine \
  --restart=Never \
  --rm \
  --attach \
  --command -- \
  python -c "import urllib.request; urllib.request.urlopen('http://tcg-proxy-lab/healthz', timeout=5)"

if kubectl -n librefang run denied-ingress-probe \
  --image=python:3.12-alpine \
  --restart=Never \
  --rm \
  --attach \
  --command -- \
  python -c "import urllib.request; urllib.request.urlopen('http://tcg-proxy-lab.tcg-proxy-lab.svc.cluster.local/healthz', timeout=5)"
then
  echo "NetworkPolicy allowed cross-namespace ingress unexpectedly" >&2
  exit 1
fi

kubectl -n tcg-proxy-lab port-forward service/tcg-proxy-lab 18080:80 \
  >"${RUNNER_TEMP:-/tmp}/tcg-proxy-lab-port-forward.log" 2>&1 &
port_forward_pid=$!
trap 'kill "${port_forward_pid}" 2>/dev/null || true' EXIT

for _ in $(seq 1 30); do
  if curl --fail --silent http://127.0.0.1:18080/healthz >/dev/null; then
    break
  fi
  sleep 1
done

curl --fail --silent http://127.0.0.1:18080/healthz |
  python -c 'import json,sys; assert json.load(sys.stdin) == {"status": "ok"}'

curl --fail --silent \
  --header 'Content-Type: application/json' \
  --data '{
    "match_id": "kind-smoke",
    "turn": 1,
    "seed": 7,
    "strategy_version": "baseline-v1",
    "state_summary": "Opening turn with one legal action.",
    "legal_actions": [
      {"id": "pass", "description": "End the turn."}
    ]
  }' \
  http://127.0.0.1:18080/api/v1/playtest/decision |
  python -c 'import json,sys; value=json.load(sys.stdin); assert value["action_id"] == "pass"; assert value["model"] == "kind-mock-model"'
