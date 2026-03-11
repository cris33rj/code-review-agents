"""
Style Reviewer Agent - Analyzes code for style, best practices, and maintainability.
"""

from typing import Optional
from src.llm.gateway import LLMGateway


STYLE_SYSTEM_PROMPT = """You are an expert code reviewer focused on code quality, style, and best practices.

Focus on:
1. Code readability and clarity
2. Naming conventions (variables, functions, classes)
3. Function and class design (single responsibility, size)
4. Code duplication (DRY principle)
5. Error handling patterns
6. Documentation and comments quality
7. Type hints and annotations (if applicable)
8. Performance considerations
9. Testability of the code
10. SOLID principles adherence

For each issue found:
- Describe the problem
- Explain why it matters
- Suggest an improvement with example if helpful

Be constructive and educational. Highlight good practices too, not just problems.
Respond in the same language as the code comments or in English if no comments exist."""


class StyleReviewer:
    """Agent that reviews code for style and best practices."""
    
    def __init__(self, llm_gateway: Optional[LLMGateway] = None):
        self.llm = llm_gateway or LLMGateway()
        self.name = "Style Reviewer"
    
    async def review(self, code: str, language: Optional[str] = None) -> dict:
        """
        Review code for style and best practices.
        
        Args:
            code: The source code to review
            language: Optional programming language hint
        
        Returns:
            Dictionary with review results
        """
        prompt = self._build_prompt(code, language)
        
        try:
            response = await self.llm.generate(
                prompt=prompt,
                system_prompt=STYLE_SYSTEM_PROMPT
            )
            
            return {
                "agent": self.name,
                "status": "success",
                "findings": response,
                "provider": self.llm.get_provider_info()
            }
        except Exception as e:
            return {
                "agent": self.name,
                "status": "error",
                "error": str(e),
                "provider": self.llm.get_provider_info()
            }
    
    def _build_prompt(self, code: str, language: Optional[str] = None) -> str:
        lang_hint = f" (Language: {language})" if language else ""
        return f"""Please review the following code for style and best practices{lang_hint}:

```
{code}
```

Provide a detailed code quality analysis."""
