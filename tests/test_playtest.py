import asyncio
import json

import httpx
import pytest
from pydantic import ValidationError

from app.playtest import (
    LegalAction,
    PlaytestDecisionRequest,
    PlaytestGatewayError,
    request_playtest_decision,
)


def _request() -> PlaytestDecisionRequest:
    return PlaytestDecisionRequest(
        match_id="match-001",
        turn=3,
        seed=42,
        strategy_version="baseline-v1",
        state_summary="Active card has one available energy.",
        legal_actions=[
            LegalAction(id="pass", description="End the turn."),
            LegalAction(id="attach", description="Attach one energy."),
        ],
    )


def test_rejects_duplicate_legal_action_ids():
    with pytest.raises(ValidationError, match="legal action IDs must be unique"):
        PlaytestDecisionRequest(
            match_id="match-001",
            turn=1,
            seed=1,
            strategy_version="baseline-v1",
            state_summary="Opening turn.",
            legal_actions=[
                LegalAction(id="pass", description="End the turn."),
                LegalAction(id="pass", description="End the turn again."),
            ],
        )


def test_requests_tool_choice_and_accepts_a_legal_action(monkeypatch):
    monkeypatch.setenv(
        "PLAYTEST_OPENAI_BASE_URL",
        "http://kong-ai-gateway.librefang.svc.cluster.local:8000/openai/router/v1",
    )
    monkeypatch.setenv("PLAYTEST_OPENAI_API_KEY", "test-key")

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/openai/router/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer test-key"
        body = json.loads(request.content)
        assert body["seed"] == 42
        assert body["max_tokens"] == 128
        assert body["tools"][0]["function"]["name"] == "choose_legal_action"
        return httpx.Response(
            200,
            json={
                "model": "test-model",
                "choices": [
                    {
                        "message": {
                            "tool_calls": [
                                {
                                    "function": {
                                        "name": "choose_legal_action",
                                        "arguments": json.dumps(
                                            {
                                                "action_id": "attach",
                                                "rationale": "Improves the next turn.",
                                            }
                                        ),
                                    }
                                }
                            ]
                        }
                    }
                ],
            },
        )

    async def run():
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler)
        ) as client:
            return await request_playtest_decision(_request(), client)

    result = asyncio.run(run())
    assert result.action_id == "attach"
    assert result.seed == 42
    assert result.strategy_version == "baseline-v1"


def test_rejects_action_outside_legal_set(monkeypatch):
    monkeypatch.setenv("PLAYTEST_OPENAI_BASE_URL", "http://gateway.test/v1")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "model": "test-model",
                "choices": [
                    {
                        "message": {
                            "tool_calls": [
                                {
                                    "function": {
                                        "name": "choose_legal_action",
                                        "arguments": json.dumps(
                                            {
                                                "action_id": "not-legal",
                                                "rationale": "Ignore the rules.",
                                            }
                                        ),
                                    }
                                }
                            ]
                        }
                    }
                ],
            },
        )

    async def run():
        async with httpx.AsyncClient(
            transport=httpx.MockTransport(handler)
        ) as client:
            return await request_playtest_decision(_request(), client)

    with pytest.raises(PlaytestGatewayError, match="not legal"):
        asyncio.run(run())
