"""
Summarizer Agent - Consolidates reviews from other agents into a final report.
"""

from typing import Optional, List
from src.llm.gateway import LLMGateway


SUMMARIZER_SYSTEM_PROMPT = """You are a senior tech lead responsible for consolidating code review feedback.

Your job is to:
1. Synthesize findings from multiple reviewers (security, style, etc.)
2. Prioritize issues by severity (Critical, High, Medium, Low)
3. Remove duplicates and consolidate related issues
4. Provide a clear executive summary
5. List actionable next steps

Output format:
## Summary
Brief overview of code quality (1-2 sentences)

## Critical Issues
List any critical/blocking issues

## Improvements Needed
Prioritized list of suggested improvements

## Positive Aspects
What the code does well

## Action Items
Concrete next steps for the developer

Be concise, actionable, and constructive."""


class Summarizer:
    """Agent that consolidates reviews into a final report."""
    
    def __init__(self, llm_gateway: Optional[LLMGateway] = None):
        self.llm = llm_gateway or LLMGateway()
        self.name = "Summarizer"
    
    async def summarize(self, reviews: List[dict], code: Optional[str] = None) -> dict:
        """
        Consolidate multiple review results into a final report.
        
        Args:
            reviews: List of review results from other agents
            code: Optional original code for context
        
        Returns:
            Dictionary with consolidated review
        """
        prompt = self._build_prompt(reviews, code)
        
        try:
            response = await self.llm.generate(
                prompt=prompt,
                system_prompt=SUMMARIZER_SYSTEM_PROMPT
            )
            
            return {
                "agent": self.name,
                "status": "success",
                "summary": response,
                "reviews_processed": len(reviews),
                "provider": self.llm.get_provider_info()
            }
        except Exception as e:
            return {
                "agent": self.name,
                "status": "error",
                "error": str(e),
                "provider": self.llm.get_provider_info()
            }
    
    def _build_prompt(self, reviews: List[dict], code: Optional[str] = None) -> str:
        reviews_text = ""
        
        for review in reviews:
            agent_name = review.get("agent", "Unknown Agent")
            status = review.get("status", "unknown")
            
            if status == "success":
                findings = review.get("findings", "No findings")
                reviews_text += f"\n### {agent_name}\n{findings}\n"
            else:
                error = review.get("error", "Unknown error")
                reviews_text += f"\n### {agent_name}\nError: {error}\n"
        
        prompt = f"""Please consolidate the following code review findings into a final report:

{reviews_text}
"""
        
        if code:
            prompt += f"""
For reference, here is the original code:
```
{code[:2000]}{'...(truncated)' if len(code) > 2000 else ''}
```
"""
        
        return prompt
