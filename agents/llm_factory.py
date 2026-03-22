"""LLM factory — reads config.yaml and returns the right chat model."""
import logging
import yaml

logger = logging.getLogger("macsis.llm")

_llm_instance = None


def get_llm():
    """Lazy singleton — one LLM per process."""
    global _llm_instance
    if _llm_instance is not None:
        return _llm_instance

    with open("config.yaml") as f:
        config = yaml.safe_load(f)

    llm_config = config["llm"]
    provider = llm_config.get("provider", "openai")
    model = llm_config["model"]
    temperature = llm_config.get("temperature", 0.1)
    max_tokens = llm_config.get("max_tokens", 4096)

    if provider == "ollama":
        from langchain_ollama import ChatOllama

        _llm_instance = ChatOllama(
            model=model,
            temperature=temperature,
            num_ctx=max_tokens,
        )
        logger.info(f"Using Ollama with model: {model}")

    elif provider == "openai":
        from langchain_openai import ChatOpenAI

        _llm_instance = ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        logger.info(f"Using OpenAI with model: {model}")

    else:
        raise ValueError(f"Unknown LLM provider: {provider}. Use 'ollama' or 'openai'.")

    return _llm_instance


def reset_llm():
    """Clear the cached instance (useful for tests)."""
    global _llm_instance
    _llm_instance = None
