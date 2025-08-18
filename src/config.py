import os
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_ollama import ChatOllama


def get_llm(provider: str, model: str):
    """Return an LLM client for the given provider and model."""
    provider = provider.lower()
    if provider == "openai":
        return ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), model=model)
    if provider == "anthropic":
        return ChatAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"), model=model)
    if provider == "kimi":
        return ChatOpenAI(
            base_url="https://api.moonshot.cn/v1",
            api_key=os.getenv("MOONSHOT_API_KEY"),
            model=model,
            temperature=0.7,
            max_tokens=2000,
        )
    if provider == "ollama":
        base_url = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        return ChatOllama(model=model, base_url=base_url)
    raise ValueError(f"Unsupported provider: {provider}")
