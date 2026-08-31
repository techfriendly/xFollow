from __future__ import annotations

import httpx
import pytest

from xfollow_api import llm
from xfollow_api.config import RuntimeConfig


class _Response:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("request failed", request=httpx.Request("GET", "http://llm.test"), response=httpx.Response(self.status_code))

    def json(self) -> dict:
        return self._payload


def test_openai_compatible_client_disables_thinking(monkeypatch: pytest.MonkeyPatch) -> None:
    recorded: dict = {}

    class Client:
        def __init__(self, **_: object) -> None:
            pass

        def __enter__(self) -> "Client":
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def get(self, *_: object, **__: object) -> _Response:
            return _Response({"data": [{"id": "llm2"}]})

        def post(self, _: str, **kwargs: object) -> _Response:
            recorded.update(kwargs)
            return _Response({"choices": [{"message": {"content": "respuesta"}}]})

    llm._STATUS_CACHE.clear()
    monkeypatch.setattr(llm.httpx, "Client", Client)
    config = RuntimeConfig(llm_base_url="http://llm.test/v1", llm_model="llm2", llm_max_output_tokens=256)

    assert llm.chat_text([{"role": "user", "content": "hola"}], config=config) == "respuesta"
    assert recorded["json"]["chat_template_kwargs"] == {"enable_thinking": False}
    assert recorded["json"]["model"] == "llm2"
    assert llm.status(config)["context_window"] == 128000


def test_openai_compatible_client_marks_network_errors_as_transient(monkeypatch: pytest.MonkeyPatch) -> None:
    class Client:
        def __init__(self, **_: object) -> None:
            pass

        def __enter__(self) -> "Client":
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def get(self, *_: object, **__: object) -> _Response:
            raise httpx.ConnectError("offline", request=httpx.Request("GET", "http://llm.test"))

    llm._STATUS_CACHE.clear()
    monkeypatch.setattr(llm.httpx, "Client", Client)
    config = RuntimeConfig(llm_base_url="http://llm.test/v1", llm_model="llm2")

    with pytest.raises(llm.LlmError, match="llm_unavailable") as error:
        llm.chat_text([{"role": "user", "content": "hola"}], config=config)
    assert error.value.transient is True
