from pathlib import Path

from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import InMemorySaver

from tools import (
    current_date,
    save_search_results,
    scrape_website,
    search_database,
    web_search,
)

system_prompt = Path(__file__).with_name("prompt.md").read_text(encoding="utf-8")

agent = create_agent(
    model=ChatOllama(model="gemma4:e2b", temperature=0),
    tools=[
        current_date,
        search_database,
        web_search,
        scrape_website,
        save_search_results,
    ],
    system_prompt=system_prompt,
    checkpointer=InMemorySaver(),
)


def answer(query: str) -> str:
    result = None
    for step in agent.stream(
        {"messages": [{"role": "user", "content": query}]},
        {"configurable": {"thread_id": "cli"}},
        stream_mode="values",
    ):
        result = step
    if result is None:
        return "No result"
    called = {
        call["name"]
        for message in result["messages"]
        for call in (getattr(message, "tool_calls", None) or [])
    }
    if (
        "web_search" in called
        and "save_search_results" not in called
    ):
        print(save_search_results.invoke({}))
    return result["messages"][-1].content
