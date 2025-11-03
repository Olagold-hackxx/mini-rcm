"""LLM evaluation engine for claims."""
from typing import Dict, Any, Optional
from config import get_settings
from llm.prompt_templates import get_validation_prompt
from utils.logger import get_logger

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
                from llm.retriever import RuleRetriever
                retriever = RuleRetriever(self.tenant_id)
                retrieved_rules = await retriever.retrieve_relevant_rules(claim)
            
            # Build prompt
            prompt = get_validation_prompt(claim, retrieved_rules)
            
            # Call LLM (returns already parsed response)
            parsed_response = await self._call_llm(prompt)
            
            return {
                "confidence_score": parsed_response.get("confidence_score", 0.5),
                "explanation": parsed_response.get("explanation", ""),
                "enhanced_explanation": parsed_response.get("enhanced_explanation", parsed_response.get("explanation", "")),
                "recommended_action": parsed_response.get("recommended_action", ""),
                "executive_summary": parsed_response.get("executive_summary", ""),
                "notes": parsed_response.get("notes", ""),
                "retrieved_rules": retrieved_rules,
                "technical_validation_status": parsed_response.get("technical_validation_status"),
                "medical_validation_status": parsed_response.get("medical_validation_status"),
                "overall_status": parsed_response.get("overall_status"),
                "technical_rules_status": parsed_response.get("technical_rules_status", []),
                "medical_rules_status": parsed_response.get("medical_rules_status", []),
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
        """Call LLM directly via OpenAI API."""
        try:
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            
            response = await client.chat.completions.create(
                model=settings.LLM_MODEL,
                max_tokens=settings.LLM_MAX_TOKENS,
                temperature=settings.LLM_TEMPERATURE,
                messages=[{"role": "user", "content": prompt}],
            )
            
            response_text = response.choices[0].message.content
            
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
            from langchain_openai import ChatOpenAI
            from langchain_core.prompts import ChatPromptTemplate
            
            llm = ChatOpenAI(
                model=settings.LLM_MODEL,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.LLM_MAX_TOKENS,
                openai_api_key=settings.OPENAI_API_KEY,
            )
            
            template = ChatPromptTemplate.from_messages([
                ("system", "You are a medical claims validation expert. Provide clear, structured explanations."),
                ("user", "{prompt}"),
            ])
            
            chain = template | llm
            response = await chain.ainvoke({"prompt": prompt})
            
            return self._parse_llm_response(response.content)
        except Exception as e:
            logger.error(f"LangChain LLM call failed: {e}")
            # Fallback to direct API call
            if settings.OPENAI_API_KEY:
                return await self._call_direct(prompt)
            else:
                raise ValueError("LLM API key not configured")

    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response into structured format."""
        import re
        
        result = {
            "confidence_score": 0.5,
            "explanation": "",
            "enhanced_explanation": "",
            "recommended_action": "",
            "executive_summary": "",
            "notes": "",
            "technical_validation_status": None,  # "PASS" or "FAIL"
            "medical_validation_status": None,  # "PASS" or "FAIL"
            "overall_status": None,  # "VALID" or "INVALID"
            "technical_rules_status": [],  # List of {"rule": "...", "status": "PASS/FAIL", "reason": "..."}
            "medical_rules_status": [],  # List of {"rule": "...", "status": "PASS/FAIL", "reason": "..."}
        }
        
        if not response_text:
            return result
        
        # Extract executive summary
        exec_match = re.search(
            r'EXECUTIVE_SUMMARY:\s*(.*?)(?=DETAILED_EXPLANATION:|RECOMMENDATIONS:|CONFIDENCE:|NOTES:|$)', 
            response_text, 
            re.DOTALL | re.IGNORECASE
        )
        if exec_match:
            result["executive_summary"] = exec_match.group(1).strip()
        
        # Extract detailed explanation
        detail_match = re.search(
            r'DETAILED_EXPLANATION:\s*(.*?)(?=RECOMMENDATIONS:|CONFIDENCE:|NOTES:|$)', 
            response_text, 
            re.DOTALL | re.IGNORECASE
        )
        if detail_match:
            explanation = detail_match.group(1).strip()
            result["explanation"] = explanation[:500]  # Short version
            result["enhanced_explanation"] = explanation  # Full version
        
        # Extract recommendations
        rec_match = re.search(
            r'RECOMMENDATIONS:\s*(.*?)(?=CONFIDENCE:|NOTES:|$)', 
            response_text, 
            re.DOTALL | re.IGNORECASE
        )
        if rec_match:
            result["recommended_action"] = rec_match.group(1).strip()
        else:
            # Fallback: try to find any recommendation-like text
            rec_fallback = re.search(
                r'RECOMMENDATION:\s*(.*?)(?=CONFIDENCE:|NOTES:|$)', 
                response_text, 
                re.DOTALL | re.IGNORECASE
            )
            if rec_fallback:
                result["recommended_action"] = rec_fallback.group(1).strip()
        
        # Extract confidence score
        conf_match = re.search(
            r'CONFIDENCE:\s*([0-9]*\.?[0-9]+)', 
            response_text, 
            re.IGNORECASE
        )
        if conf_match:
            try:
                result["confidence_score"] = float(conf_match.group(1))
                # Clamp to 0-1 range
                result["confidence_score"] = max(0.0, min(1.0, result["confidence_score"]))
            except ValueError:
                pass
        
        # Extract notes
        notes_match = re.search(
            r'NOTES:\s*(.*?)$', 
            response_text, 
            re.DOTALL | re.IGNORECASE
        )
        if notes_match:
            result["notes"] = notes_match.group(1).strip()
        
        # Extract validation status section
        validation_status_match = re.search(
            r'VALIDATION_STATUS:\s*(.*?)(?=DETAILED_EXPLANATION:|TECHNICAL_RULES_STATUS:|RECOMMENDATIONS:|CONFIDENCE:|NOTES:|$)', 
            response_text, 
            re.DOTALL | re.IGNORECASE
        )
        if validation_status_match:
            status_text = validation_status_match.group(1)
            # Extract technical validation status
            tech_match = re.search(r'TECHNICAL_VALIDATION:\s*(PASS|FAIL)', status_text, re.IGNORECASE)
            if tech_match:
                result["technical_validation_status"] = tech_match.group(1).upper()
            # Extract medical validation status
            med_match = re.search(r'MEDICAL_VALIDATION:\s*(PASS|FAIL)', status_text, re.IGNORECASE)
            if med_match:
                result["medical_validation_status"] = med_match.group(1).upper()
            # Extract overall status
            overall_match = re.search(r'OVERALL_STATUS:\s*(VALID|INVALID)', status_text, re.IGNORECASE)
            if overall_match:
                result["overall_status"] = overall_match.group(1).upper()
        
        # Extract technical rules status
        tech_rules_match = re.search(
            r'TECHNICAL_RULES_STATUS:\s*(.*?)(?=MEDICAL_RULES_STATUS:|RECOMMENDATIONS:|CONFIDENCE:|NOTES:|$)', 
            response_text, 
            re.DOTALL | re.IGNORECASE
        )
        if tech_rules_match:
            tech_rules_text = tech_rules_match.group(1).strip()
            # Parse each rule line (format: "- Rule Name: PASS/FAIL - reason")
            for line in tech_rules_text.split('\n'):
                line = line.strip()
                if line.startswith('-'):
                    rule_match = re.match(r'-\s*(.+?):\s*(PASS|FAIL)\s*-\s*(.+)', line, re.IGNORECASE)
                    if rule_match:
                        result["technical_rules_status"].append({
                            "rule": rule_match.group(1).strip(),
                            "status": rule_match.group(2).upper(),
                            "reason": rule_match.group(3).strip()
                        })
        
        # Extract medical rules status
        med_rules_match = re.search(
            r'MEDICAL_RULES_STATUS:\s*(.*?)(?=RECOMMENDATIONS:|CONFIDENCE:|NOTES:|$)', 
            response_text, 
            re.DOTALL | re.IGNORECASE
        )
        if med_rules_match:
            med_rules_text = med_rules_match.group(1).strip()
            # Parse each rule line (format: "- Rule #N or Rule Name: PASS/FAIL - reason")
            for line in med_rules_text.split('\n'):
                line = line.strip()
                if line.startswith('-'):
                    rule_match = re.match(r'-\s*(.+?):\s*(PASS|FAIL)\s*-\s*(.+)', line, re.IGNORECASE)
                    if rule_match:
                        result["medical_rules_status"].append({
                            "rule": rule_match.group(1).strip(),
                            "status": rule_match.group(2).upper(),
                            "reason": rule_match.group(3).strip()
                        })
        
        # If no structured fields found, use the entire response
        if not result["explanation"] and not result["enhanced_explanation"]:
            result["enhanced_explanation"] = response_text
            result["explanation"] = response_text[:500]
        
        if not result["recommended_action"]:
            result["recommended_action"] = "Please review the detailed explanation for specific guidance."
        
        # Combine executive summary and detailed explanation for enhanced_explanation
        if result["executive_summary"] and result["enhanced_explanation"]:
            result["enhanced_explanation"] = (
                f"EXECUTIVE SUMMARY:\n{result['executive_summary']}\n\n"
                f"DETAILED EXPLANATION:\n{result['enhanced_explanation']}"
            )
        elif result["executive_summary"]:
            result["enhanced_explanation"] = (
                f"EXECUTIVE SUMMARY:\n{result['executive_summary']}\n\n"
                f"{response_text}"
            )
        
        return result

