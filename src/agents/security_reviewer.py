"""
Security Reviewer Agent - Analyzes code for security vulnerabilities.
"""

from typing import Optional
from src.llm.gateway import LLMGateway


SECURITY_SYSTEM_PROMPT = """You are an expert security code reviewer. Your job is to analyze code for security vulnerabilities and potential risks.

Focus on:
1. Injection vulnerabilities (SQL, Command, XSS)
2. Authentication and authorization issues
3. Sensitive data exposure
4. Insecure cryptographic practices
5. Input validation problems
6. Hardcoded secrets or credentials
7. Insecure dependencies patterns
8. Race conditions and concurrency issues

For each issue found:
- Describe the vulnerability
- Explain the potential impact
- Suggest a fix

Be concise but thorough. If no security issues are found, say so clearly.
Respond in the same language as the code comments or in English if no comments exist."""


class SecurityReviewer:
    """Agent that reviews code for security vulnerabilities."""
    
    def __init__(self, llm_gateway: Optional[LLMGateway] = None):
        self.llm = llm_gateway or LLMGateway()
        self.name = "Security Reviewer"
    
    async def review(self, code: str, language: Optional[str] = None) -> dict:
        """
        Review code for security vulnerabilities.
        
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
                system_prompt=SECURITY_SYSTEM_PROMPT
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
        return f"""Please review the following code for security vulnerabilities{lang_hint}:

```
{code}
```

Provide a detailed security analysis."""
