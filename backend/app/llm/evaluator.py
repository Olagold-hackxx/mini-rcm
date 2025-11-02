"""LLM evaluation engine for claims."""
from typing import Dict, Any, Optional
from app.config import get_settings
from app.llm.prompt_templates import get_validation_prompt
from app.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class LLMEvaluator:
    """Evaluates claims using LLM with RAG support."""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.use_rag = settings.USE_RAG

    async def evaluate_claim(self, claim: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a claim using LLM.
        
        Args:
            claim: Claim dictionary with validation errors
            
        Returns:
            Dictionary with LLM evaluation results
        """
        try:
            # Retrieve relevant rules if RAG is enabled
            retrieved_rules = []
            if self.use_rag:
                from app.llm.retriever import RuleRetriever
                retriever = RuleRetriever(self.tenant_id)
                retrieved_rules = await retriever.retrieve_relevant_rules(claim)
            
            # Build prompt
            prompt = get_validation_prompt(claim, retrieved_rules)
            
            # Call LLM
            response = await self._call_llm(prompt)
            
            return {
                "confidence_score": response.get("confidence_score", 0.5),
                "explanation": response.get("explanation", ""),
                "enhanced_explanation": response.get("enhanced_explanation", ""),
                "recommended_action": response.get("recommended_action", ""),
                "retrieved_rules": retrieved_rules,
            }
        except Exception as e:
            logger.error(f"LLM evaluation failed: {e}")
            return {
                "confidence_score": 0.0,
                "explanation": f"LLM evaluation failed: {str(e)}",
                "enhanced_explanation": "",
                "recommended_action": "",
                "retrieved_rules": [],
            }

    async def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """Call LLM API."""
        if settings.USE_LANGCHAIN:
            return await self._call_langchain(prompt)
        else:
            return await self._call_direct(prompt)

    async def _call_direct(self, prompt: str) -> Dict[str, Any]:
        """Call LLM directly via Anthropic API."""
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            
            message = await client.messages.create(
                model=settings.LLM_MODEL,
                max_tokens=settings.LLM_MAX_TOKENS,
                temperature=settings.LLM_TEMPERATURE,
                messages=[{"role": "user", "content": prompt}],
            )
            
            response_text = message.content[0].text
            
            # Parse structured response
            return self._parse_llm_response(response_text)
        except Exception as e:
            logger.error(f"Direct LLM call failed: {e}")
            return {
                "confidence_score": 0.0,
                "explanation": f"LLM call failed: {str(e)}",
                "enhanced_explanation": "",
                "recommended_action": "",
            }

    async def _call_langchain(self, prompt: str) -> Dict[str, Any]:
        """Call LLM via LangChain."""
        try:
            from langchain_anthropic import ChatAnthropic
            from langchain_core.prompts import ChatPromptTemplate
            
            llm = ChatAnthropic(
                model=settings.LLM_MODEL,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
            )
            
            template = ChatPromptTemplate.from_messages([
                ("system", "You are a medical claims validation expert."),
                ("user", "{prompt}"),
            ])
            
            chain = template | llm
            response = await chain.ainvoke({"prompt": prompt})
            
            return self._parse_llm_response(response.content)
        except Exception as e:
            logger.error(f"LangChain LLM call failed: {e}")
            return await self._call_direct(prompt)

    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response into structured format."""
        # Simple parsing - can be enhanced with structured output
        return {
            "confidence_score": 0.8,
            "explanation": response_text[:500],
            "enhanced_explanation": response_text,
            "recommended_action": "Review the claim details carefully.",
        }

