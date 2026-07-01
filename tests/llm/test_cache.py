"""Unit tests for LLM cache layer — LLMCacheKey, LLMCache, InMemoryCache (LLM-02)."""

import pytest

from kir.llm.cache import InMemoryCache, LLMCache, LLMCacheKey

class TestLLMCacheKey:
    def test_build_returns_colon_delimited_key(self) -> None:
        key = LLMCacheKey().build(
            "sha256abc", "extract_v1", "1", "anthropic:claude-sonnet-4-6"
        )
        assert key == "sha256abc:extract_v1:1:anthropic:claude-sonnet-4-6"

    @pytest.mark.parametrize(
        "checksum,prompt_version,schema_version,model_id",
        [
            ("", "extract_v1", "1", "fake:v0"),
            ("sha256abc", "", "1", "fake:v0"),
            ("sha256abc", "extract_v1", "", "fake:v0"),
            ("sha256abc", "extract_v1", "1", ""),
        ],
        ids=["empty_checksum", "empty_prompt_version", "empty_schema_version", "empty_model_id"],
    )
    def test_missing_cache_key_component_raises(
        self, checksum: str, prompt_version: str, schema_version: str, model_id: str
    ) -> None:
        with pytest.raises(ValueError):
            LLMCacheKey().build(checksum, prompt_version, schema_version, model_id)

    def test_none_cache_key_component_raises(self) -> None:
        with pytest.raises((ValueError, TypeError)):
            LLMCacheKey().build(None, "extract_v1", "1", "fake:v0")  # type: ignore[arg-type]

class TestLLMCache:
    def test_llm_cache_miss_returns_none(self) -> None:
        cache = LLMCache(InMemoryCache())
        result = cache.get(
            checksum="sha256abc",
            prompt_version="extract_v1",
            schema_version="1",
            model_id="fake:v0",
        )
        assert result is None

    def test_llm_cache_set_then_get_roundtrips(self) -> None:
        cache = LLMCache(InMemoryCache())
        value = {"concepts": ["foo"]}
        cache.set(
            checksum="sha256abc",
            prompt_version="extract_v1",
            schema_version="1",
            model_id="fake:v0",
            value=value,
        )
        result = cache.get(
            checksum="sha256abc",
            prompt_version="extract_v1",
            schema_version="1",
            model_id="fake:v0",
        )
        assert result == value

    def test_llm_cache_different_keys_do_not_collide(self) -> None:
        cache = LLMCache(InMemoryCache())
        cache.set(
            checksum="doc_a_sha",
            prompt_version="extract_v1",
            schema_version="1",
            model_id="fake:v0",
            value="doc_a_result",
        )
        result = cache.get(
            checksum="doc_b_sha",
            prompt_version="extract_v1",
            schema_version="1",
            model_id="fake:v0",
        )
        assert result is None
