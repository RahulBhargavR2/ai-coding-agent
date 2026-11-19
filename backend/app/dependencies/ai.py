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

from app.tools.tool_service import ToolService
from app.security.policy import CODING_POLICY


from app.coding.editing.editor import CodeEditor
from app.coding.review.change_reviewer import ChangeReviewer
from app.coding.changes.change_resolver import ChangeResolver
from app.coding.review.reviewer_coinfig import ChangeReviewerConfig

from app.core.config import settings

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

def get_tool_service() -> ToolService:
    return ToolService()

def get_executor_agent(
    tool_servie : ToolService = Depends(get_tool_service)
) -> ExecutorAgent:
    return ExecutorAgent(
        tool_service=tool_servie,
        policy=CODING_POLICY
    )

def get_change_reviewer() -> ChangeReviewer:
    config = ChangeReviewerConfig(
        max_files=settings.CHANGE_REVIEWER_MAX_FILES,
        max_change_size=settings.CHANGE_REVIEWER_MAX_CHANGE_SIZE
    )
    return ChangeReviewer(config)

def get_change_resolver()-> ChangeResolver:
    return ChangeResolver()

def get_editor()-> CodeEditor:
    return CodeEditor


def get_coding_workflow(
    planner: PlannerAgent = Depends(get_planner_agent),
    retriever: RetrieverAgent = Depends(get_retriever_agent),
    coder: CoderAgent = Depends(get_coder_agent),
    reviewer: ReviewerAgent = Depends(get_reviewer_agent),
    critic: CriticAgent = Depends(get_critic_agent),
    executor: ExecutorAgent = Depends(get_executor_agent),
    summarizer: SummarizerAgent = Depends(get_summarizer_agent),
    change_reviewer: ChangeReviewer = Depends(get_change_reviewer),
    change_resolver: ChangeResolver = Depends(get_change_resolver),
    editor: CodeEditor = Depends(get_editor)
) -> CodingWorkflow:
    return CodingWorkflow(
        planner=planner,
        retriever=retriever,
        coder=coder,
        reviewer=reviewer,
        critic=critic,
        executor=executor,
        summarizer=summarizer,
        change_reviewer=change_reviewer,
        change_resolver=change_resolver,
        editor=editor
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
