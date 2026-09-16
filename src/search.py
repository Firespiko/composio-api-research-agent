import os

from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not TAVILY_API_KEY:
    raise RuntimeError("TAVILY_API_KEY is not set")

tavily = TavilyClient(api_key=TAVILY_API_KEY)


def search_web(query: str, max_results: int = 5):
    response = tavily.search(
        query=query,
        search_depth="advanced",
        max_results=max_results,
        include_answer=False,
    )

    return response.get("results", [])