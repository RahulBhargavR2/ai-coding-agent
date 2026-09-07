from functools import lru_cache
from fastapi import Depends
from typing import Annotated

from app.ai.agents.coder import CoderAgent
from app.ai.agents.critic import CriticAgent
from app.ai.agents.planner import PlannerAgent
from app.ai.agents.reviewer import ReviewerAgent
from app.ai.agents.summarizer import SummarizerAgent
from app.ai.agents.retriever import RetrieverAgent
from app.ai.agents.executor import ExecutorAgent


from app.ai.llm.provider import LLMProvider, MockLLMProvider

from app.dependencies.indexing import get_retriever
from app.retrieval.retriever import Retriever

from app.ai.workflows.graph import CodingWorkflow
from app.ai.workflows.coding_workflow import CodingWorkflowService


@lru_cache
def get_llm_provider() -> LLMProvider:
    return MockLLMProvider()


def get_planner_agent(
    llm: LLMProvider = Depends(get_llm_provider),
) -> PlannerAgent:
    return PlannerAgent(llm)


def get_coder_agent(
    llm: LLMProvider = Depends(get_llm_provider),
) -> CoderAgent:
    return CoderAgent(llm)


def get_reviewer_agent(
    llm: LLMProvider = Depends(get_llm_provider),
) -> ReviewerAgent:
    return ReviewerAgent(llm)


def get_critic_agent(
    llm: LLMProvider = Depends(get_llm_provider),
) -> CriticAgent:
    return CriticAgent(llm)


def get_summarizer_agent(
    llm: LLMProvider = Depends(get_llm_provider),
) -> SummarizerAgent:
    return SummarizerAgent(llm)


def get_retriever_agent(
    retriever: Retriever = Depends(get_retriever),
) -> RetrieverAgent:
    return RetrieverAgent(retriever=retriever)


def get_executor_agent() -> ExecutorAgent:
    return ExecutorAgent()


def get_coding_workflow(
    planner: PlannerAgent = Depends(get_planner_agent),
    retriever: RetrieverAgent = Depends(get_retriever_agent),
    coder: CoderAgent = Depends(get_coder_agent),
    reviewer: ReviewerAgent = Depends(get_reviewer_agent),
    critic: CriticAgent = Depends(get_critic_agent),
    executor: ExecutorAgent = Depends(get_executor_agent),
    summarizer: SummarizerAgent = Depends(get_summarizer_agent),
) -> CodingWorkflow:
    return CodingWorkflow(
        planner=planner,
        retriever=retriever,
        coder=coder,
        reviewer=reviewer,
        critic=critic,
        executor=executor,
        summarizer=summarizer,
    )


def get_coding_workflow_service(
    workflow: CodingWorkflow = Depends(get_coding_workflow),
) -> CodingWorkflowService:
    return CodingWorkflowService(
        workflow=workflow,
    )


CodingWorkflowServiceDep = Annotated[
    CodingWorkflowService,
    Depends(get_coding_workflow_service),
]
