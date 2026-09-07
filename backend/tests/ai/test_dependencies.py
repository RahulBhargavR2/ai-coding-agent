
from app.ai.llm.provider import MockLLMProvider

from app.ai.agents.coder import CoderAgent
from app.ai.agents.critic import CriticAgent
from app.ai.agents.planner import PlannerAgent
from app.ai.agents.reviewer import ReviewerAgent
from app.ai.agents.summarizer import SummarizerAgent
from app.ai.agents.retriever import RetrieverAgent
from app.dependencies.ai import (
    get_coder_agent,
    get_critic_agent,
    get_planner_agent,
    get_reviewer_agent,
    get_summarizer_agent,
    get_retriever_agent,
    get_retriever,
    get_executor_agent,
    get_llm_provider
)
from app.ai.agents.executor import ExecutorAgent
from app.ai.workflows.graph import CodingWorkflow

def test_get_llm_provider_returns_provider() -> None:
    get_llm_provider.cache_clear()

    provider = get_llm_provider()

    assert isinstance(provider, MockLLMProvider)


def test_get_llm_provider_is_cached() -> None:
    get_llm_provider.cache_clear()

    first = get_llm_provider()
    second = get_llm_provider()

    assert first is second


def test_get_planner_agent() -> None:
    agent = get_planner_agent(llm=get_llm_provider())

    assert isinstance(agent, PlannerAgent)


def test_get_coder_agent() -> None:
    agent = get_coder_agent(llm=get_llm_provider())

    assert isinstance(agent, CoderAgent)


def test_get_reviewer_agent() -> None:
    agent = get_reviewer_agent(llm=get_llm_provider())

    assert isinstance(agent, ReviewerAgent)


def test_get_critic_agent() -> None:
    agent = get_critic_agent(llm=get_llm_provider())

    assert isinstance(agent, CriticAgent)


def test_get_summarizer_agent() -> None:
    agent = get_summarizer_agent(llm=get_llm_provider())

    assert isinstance(agent, SummarizerAgent)


def test_get_retriever_agent() -> None:
    retriever = get_retriever()

    agent = get_retriever_agent(
        retriever=retriever,
    )

    assert isinstance(agent, RetrieverAgent)


def test_get_executor_agent() -> None:
    agent = get_executor_agent()

    assert isinstance(agent, ExecutorAgent)
