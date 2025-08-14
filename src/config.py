import os
from langchain_openai import ChatOpenAI

# This configuration sets up the language model for the Moonshot POC.
llm = ChatOpenAI(
    base_url="https://api.moonshot.cn/v1",
    api_key=os.getenv("MOONSHOT_API_KEY"),
    model="kimi-k2-instruct",
    temperature=0.7,
    max_tokens=2000,
)