# TCG Proxy Lab

TCG Proxy Lab is a self-hosted web service for turning Limitless-format decklists into print-ready playtest proxy PDFs. It is intentionally trademark-neutral, container-first, and designed to grow into an AI-assisted deck analysis and self-play laboratory.

## Run locally

Clone submodules and start the hardened container:

```bash
git clone --recurse-submodules https://github.com/whatnick/tcg-proxy-lab.git
cd tcg-proxy-lab
docker compose up --build
```

Open <http://127.0.0.1:8080>, paste a decklist, choose A4 or Letter paper, and download the generated PDF.

The service also exposes:

```text
GET  /healthz
POST /api/v1/proxies
POST /api/v1/playtest/decision
GET  /docs
```

## Current scope

- Limitless-format decklist parsing
- 63 x 88 mm playtest cards
- A4 and Letter PDF layouts
- Containerized FastAPI web interface
- Read-only runtime with a temporary workspace
- A 100-card and 16 KiB request limit
- No arbitrary URL input or retained decklists

The application currently resolves card images through the upstream Pokémon plugin. No card artwork is included in this repository.

## AI playtesting roadmap

AI features will be added behind deterministic game rules rather than giving a model unrestricted tools:

1. Validate deck legality and explain invalid lists.
2. Convert cards into a structured, versioned rules representation.
3. Run deterministic game simulations with seeded randomness.
4. Let agents propose legal actions while the rules engine accepts or rejects them.
5. Compare matchups, opening hands, prize risks, and consistency.
6. Record reproducible traces with model, prompt, rules, card-data, and random-seed versions.

Decklists, card text, and future model output are untrusted inputs. AI agents will not receive shell access, arbitrary network access, purchasing capabilities, or user credentials.

The first agent boundary is now available at `POST /api/v1/playtest/decision`.
Callers provide a deterministic state summary plus the complete set of legal
actions. The model must select through a forced tool call, and the service
rejects any action outside that set. This is a policy layer, not yet a complete
game engine.

## Kubernetes deployment

The `deploy/base` Kustomize package deploys the service into its own namespace
with a non-root, read-only container, no service-account token, bounded
temporary storage, probes, resource limits, and a default NetworkPolicy:

```bash
kubectl apply -k deploy/base
```

The base pins the multi-architecture `0.1.0` image by its immutable OCI index
digest. Tagged CI releases publish images to GHCR with an SBOM and GitHub
build-provenance attestation only after the unit and kind jobs pass.

The play-test endpoint uses the existing in-cluster Kong OpenAI-compatible
router:

```text
http://kong-ai-gateway.librefang.svc.cluster.local:8000/openai/router/v1
```

If the gateway requires a caller key, copy `deploy/secret.example.yaml` outside
the repository, replace the placeholder, protect it with your secret manager,
and apply it before the Deployment. Never commit the populated Secret. The PDF
service remains healthy without the Secret, while play-test requests return a
gateway error if the configured gateway requires authentication.

Run the full deployment smoke test in a disposable kind cluster:

```bash
kind create cluster --name tcg-proxy-lab
bash deploy/kind/smoke-test.sh
kind delete cluster --name tcg-proxy-lab
```

The kind overlay supplies a mock Kong endpoint and a test-only placeholder
credential. CI verifies the container, enforced ingress policy, Service
routing, and the forced legal-action decision flow.

## Safe strategy evolution

Self-evolution is planned as an offline promotion pipeline:

1. Persist immutable match traces with seed, rules, card-data, prompt, model,
   and strategy versions.
2. Generate candidate strategy parameters in an isolated training job.
3. Replay a fixed evaluation corpus through the deterministic rules engine.
4. Require measurable improvement, safety checks, and explicit promotion.
5. publish a new immutable strategy version with rollback metadata.

The serving Pod never rewrites its code, system prompt, manifests, or safety
policy. A model proposes actions only; deterministic code validates them.

## Attribution

This project was inspired by the MIT-licensed [Pokémon Proxy PDF Maker](https://github.com/turkushan490/pokemon-proxy-pdf-maker), which packages a desktop workflow around [Silhouette Card Maker](https://github.com/Alan-Cha/silhouette-card-maker).

The PDF engine and Pokémon decklist plugin are provided through a pinned Git submodule of Silhouette Card Maker. See [`NOTICE`](NOTICE) and the upstream license in `vendor/silhouette-card-maker/LICENSE.md`.

## Legal and acceptable use

This project is for personal, non-commercial playtesting. Generated proxies are not tournament legal and must never be sold or represented as genuine cards.

Pokémon and Pokémon character names are trademarks of Nintendo, Creatures, and GAME FREAK. Card artwork and text belong to their respective rights holders. This project is not affiliated with or endorsed by those parties.

## License

TCG Proxy Lab is available under the [MIT License](LICENSE). The pinned upstream engine is separately distributed under its own MIT license.
