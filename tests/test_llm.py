import json

import httpx
import pytest

from procurement_screening.llm import CachedProvider, LLMError, OllamaProvider


def make_provider(handler):
    client = httpx.Client(base_url="http://x", transport=httpx.MockTransport(handler))
    return OllamaProvider("m", client=client)


def test_request_shape_and_schema():
    seen = {}

    def handler(req: httpx.Request):
        seen.update(json.loads(req.content))
        return httpx.Response(200, json={"response": '{"a": 1}'})

    schema = {"type": "object"}
    out = make_provider(handler).generate("hi", system="sys", schema=schema)
    assert out == '{"a": 1}'
    assert seen["format"] == schema
    assert seen["system"] == "sys"
    assert seen["stream"] is False
    assert seen["options"]["temperature"] == 0


def test_http_error_wrapped():
    p = make_provider(lambda req: httpx.Response(500))
    with pytest.raises(LLMError):
        p.generate("hi")


def test_malformed_response_wrapped():
    p = make_provider(lambda req: httpx.Response(200, json={"nope": 1}))
    with pytest.raises(LLMError):
        p.generate("hi")


def test_cache_hits_and_key_sensitivity(tmp_path):
    calls = []

    def handler(req):
        calls.append(1)
        return httpx.Response(200, json={"response": f"r{len(calls)}"})

    c = CachedProvider(make_provider(handler), tmp_path)
    assert c.generate("p") == "r1"
    assert c.generate("p") == "r1"
    assert (c.hits, c.misses, len(calls)) == (1, 1, 1)
    assert c.generate("p", system="s") == "r2"
    assert c.generate("p", schema={"type": "object"}) == "r3"
    assert c.generate("other") == "r4"


def test_cache_persists_across_instances(tmp_path):
    p1 = CachedProvider(make_provider(lambda r: httpx.Response(200, json={"response": "x"})), tmp_path)
    p1.generate("p")

    def boom(req):
        raise AssertionError("should not call backend")

    p2 = CachedProvider(make_provider(boom), tmp_path)
    assert p2.generate("p") == "x"


def test_corrupt_cache_entry_regenerates(tmp_path):
    p = CachedProvider(make_provider(lambda r: httpx.Response(200, json={"response": "ok"})), tmp_path)
    p.generate("p")
    for f in tmp_path.glob("*.json"):
        f.write_text("not json")
    assert p.generate("p") == "ok"


def test_errors_not_cached(tmp_path):
    state = {"fail": True}

    def handler(req):
        if state["fail"]:
            return httpx.Response(500)
        return httpx.Response(200, json={"response": "ok"})

    p = CachedProvider(make_provider(handler), tmp_path)
    with pytest.raises(LLMError):
        p.generate("p")
    state["fail"] = False
    assert p.generate("p") == "ok"
