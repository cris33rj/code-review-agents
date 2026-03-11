"""
Orchestrator Agent - Coordinates the code review workflow using LangGraph.
"""

import asyncio
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

from src.llm.gateway import LLMGateway
from src.agents.security_reviewer import SecurityReviewer
from src.agents.style_reviewer import StyleReviewer
from src.agents.summarizer import Summarizer
from src.config import settings


class ReviewState(TypedDict):
    """State object passed through the review workflow."""
    code: str
    language: Optional[str]
    security_result: Optional[dict]
    style_result: Optional[dict]
    summary_result: Optional[dict]
    error: Optional[str]


class Orchestrator:
    """
    Orchestrates the code review workflow.
    Uses LangGraph to coordinate multiple agents.
    """

    def __init__(self, llm_gateway: Optional[LLMGateway] = None):
        self.llm = llm_gateway or LLMGateway()
        self.security_reviewer = SecurityReviewer(self.llm)
        self.style_reviewer = StyleReviewer(self.llm)
        self.summarizer = Summarizer(self.llm)
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(ReviewState)

        workflow.add_node("run_security", self._security_review_node)
        workflow.add_node("run_style", self._style_review_node)
        workflow.add_node("run_summary", self._summarize_node)

        workflow.set_entry_point("run_security")
        workflow.add_edge("run_security", "run_style")
        workflow.add_edge("run_style", "run_summary")
        workflow.add_edge("run_summary", END)

        return workflow.compile()

    async def _security_review_node(self, state: ReviewState) -> dict:
        """Execute security review."""
        result = await self.security_reviewer.review(
            code=state["code"],
            language=state.get("language")
        )
        return {"security_result": result}

    async def _style_review_node(self, state: ReviewState) -> dict:
        """Execute style review."""
        result = await self.style_reviewer.review(
            code=state["code"],
            language=state.get("language")
        )
        return {"style_result": result}

    async def _summarize_node(self, state: ReviewState) -> dict:
        """Summarize all reviews."""
        reviews = []

        if state.get("security_result"):
            reviews.append(state["security_result"])

        if state.get("style_result"):
            reviews.append(state["style_result"])

        result = await self.summarizer.summarize(
            reviews=reviews,
            code=state["code"]
        )
        return {"summary_result": result}

    async def review(self, code: str, language: Optional[str] = None) -> dict:
        """
        Execute the full code review workflow.

        Args:
            code: Source code to review
            language: Optional programming language hint

        Returns:
            Complete review results from all agents
        """
        if len(code) > settings.max_code_length:
            return {
                "status": "error",
                "error": f"Code exceeds maximum length of {settings.max_code_length} characters"
            }

        initial_state: ReviewState = {
            "code": code,
            "language": language,
            "security_result": None,
            "style_result": None,
            "summary_result": None,
            "error": None
        }

        try:
            final_state = await self.workflow.ainvoke(initial_state)

            return {
                "status": "success",
                "security_review": final_state.get("security_result"),
                "style_review": final_state.get("style_result"),
                "summary": final_state.get("summary_result"),
                "llm_provider": self.llm.get_provider_info()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "llm_provider": self.llm.get_provider_info()
            }

    async def review_parallel(self, code: str, language: Optional[str] = None) -> dict:
        """
        Execute reviews in parallel for faster results.
        Security and Style reviews run concurrently, then summarize.

        Args:
            code: Source code to review
            language: Optional programming language hint

        Returns:
            Complete review results from all agents
        """
        if len(code) > settings.max_code_length:
            return {
                "status": "error",
                "error": f"Code exceeds maximum length of {settings.max_code_length} characters"
            }

        try:
            security_task = self.security_reviewer.review(code, language)
            style_task = self.style_reviewer.review(code, language)

            security_result, style_result = await asyncio.gather(
                security_task,
                style_task
            )

            summary_result = await self.summarizer.summarize(
                reviews=[security_result, style_result],
                code=code
            )

            return {
                "status": "success",
                "security_review": security_result,
                "style_review": style_result,
                "summary": summary_result,
                "llm_provider": self.llm.get_provider_info()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "llm_provider": self.llm.get_provider_info()
            }