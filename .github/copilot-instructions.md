# TCG Proxy Lab

- Keep the service focused on private, non-commercial playtesting.
- Do not commit card images, proprietary datasets, API keys, or generated PDFs.
- Treat decklists and future AI inputs as untrusted data.
- Keep card resolution restricted to explicitly approved providers; never add arbitrary URL fetching.
- Run generated or model-suggested actions through a deterministic rules engine before accepting them.
- AI playtesting must produce recommendations or simulated actions, never purchases, trades, account actions, or tournament submissions.
- Treat "self-evolving" as offline, versioned strategy optimization. Never let a model edit running code, prompts, policies, Kubernetes resources, or its own safety controls.
- Only the deterministic rules engine may enumerate legal actions. Reject model output that is not in that exact action set.
- Keep model access behind the configured OpenAI-compatible gateway; do not give play-test agents arbitrary network or shell tools.
- Preserve attribution in `NOTICE` when adapting upstream MIT-licensed code.
