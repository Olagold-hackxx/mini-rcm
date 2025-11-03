"""RAG retriever for rule documents using LangChain."""
from typing import List, Dict
from config import get_settings
from llm.vector_store import VectorStore
from utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class RuleRetriever:
    """Retrieves relevant adjudication or approval rules from ChromaDB via LangChain."""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.vector_store = VectorStore(tenant_id) if settings.USE_RAG else None

    async def retrieve_relevant_rules(self, claim: Dict) -> List[Dict]:
        """
        Retrieve relevant rules for a claim using RAG.
        Uses multiple focused queries to ensure comprehensive coverage.
        """
        if not settings.USE_RAG or not self.vector_store:
            return []
        
        all_results = []
        seen_ids = set()
        
        try:
            # Build multiple focused queries for different rule types
            queries = self._build_multiple_queries(claim)
            
            # Execute all queries and combine results
            # Use higher n_results per query to ensure comprehensive coverage
            n_results_per_query = max(settings.TOP_K_RETRIEVAL or 30, 30)
            
            for query in queries:
                results = await self.vector_store.search(
                    query=query,
                    n_results=n_results_per_query,
                    filter_metadata={"tenant_id": self.tenant_id},
                )
                
                # Deduplicate by content hash (use more chars for better uniqueness)
                for result in results:
                    content = result.get('content', '')
                    # Use first 200 chars for better uniqueness detection
                    content_hash = hash(content[:200])
                    if content_hash not in seen_ids:
                        seen_ids.add(content_hash)
                        all_results.append(result)
            
            # If we still don't have enough rules, do a broader search
            if len(all_results) < 20:
                logger.warning(
                    f"[RAG] Only retrieved {len(all_results)} rules, performing broader search"
                )
                # Do a very general search to get more rules
                general_results = await self.vector_store.search(
                    query="medical claims validation rules adjudication eligibility requirements",
                    n_results=n_results_per_query * 2,
                    filter_metadata={"tenant_id": self.tenant_id},
                )
                
                for result in general_results:
                    content = result.get('content', '')
                    content_hash = hash(content[:200])
                    if content_hash not in seen_ids:
                        seen_ids.add(content_hash)
                        all_results.append(result)
            
            logger.info(
                f"[RAG] Retrieved {len(all_results)} unique rules for claim {claim.get('claim_id')} "
                f"from {len(queries)} queries"
            )
            # Return up to 3x TOP_K for very comprehensive coverage
            max_results = settings.TOP_K_RETRIEVAL * 3 if settings.TOP_K_RETRIEVAL else 90
            return all_results[:max_results]
        except Exception as e:
            logger.error(f"[RAG] Rule retrieval failed: {e}")
            return []
    
    def _build_multiple_queries(self, claim: Dict) -> List[str]:
        """
        Build multiple focused queries to ensure comprehensive rule retrieval.
        This ensures we get rules for all aspects: approval, facility, service-diagnosis, etc.
        """
        queries = []
        
        service_code = claim.get("service_code")
        diagnosis_codes = claim.get("diagnosis_codes")
        encounter_type = claim.get("encounter_type", "").lower()
        facility_id = claim.get("facility_id")
        
        # Query 1: Service-specific rules (very specific)
        if service_code:
            queries.append(f"service code {service_code} rules requirements eligibility")
            queries.append(f"service {service_code} allowed not allowed restrictions")
            queries.append(f"service code {service_code} approval authorization required")
        
        # Query 2: Diagnosis-specific rules (very specific)
        if diagnosis_codes:
            if isinstance(diagnosis_codes, list):
                for code in diagnosis_codes[:5]:  # Increased to 5 to get more coverage
                    queries.append(f"diagnosis code {code} requirements approval eligibility")
                    queries.append(f"diagnosis {code} allowed not allowed restrictions")
                    queries.append(f"diagnosis code {code} authorization prior approval")
            else:
                queries.append(f"diagnosis code {diagnosis_codes} requirements approval eligibility")
                queries.append(f"diagnosis {diagnosis_codes} allowed not allowed restrictions")
        
        # Query 3: Service-Diagnosis combination rules (CRITICAL - must be checked first)
        if service_code and diagnosis_codes:
            if isinstance(diagnosis_codes, list):
                for code in diagnosis_codes[:5]:  # Increased to 5 to ensure we get all diagnosis combinations
                    queries.append(f"service code {service_code} requires diagnosis code {code}")
                    queries.append(f"service code {service_code} diagnosis code {code} combination rules")
                    queries.append(f"service {service_code} with diagnosis {code} eligibility requirements")
                    queries.append(f"service {service_code} allowed diagnosis codes required")
                    queries.append(f"diagnosis code {code} allowed service codes requirements")
            else:
                queries.append(f"service code {service_code} requires diagnosis code {diagnosis_codes}")
                queries.append(f"service code {service_code} diagnosis code {diagnosis_codes} combination rules")
                queries.append(f"service {service_code} with diagnosis {diagnosis_codes} eligibility requirements")
                queries.append(f"service {service_code} allowed diagnosis codes required")
        
        # Query 3b: Service requirement rules (what diagnoses/services are required)
        if service_code:
            queries.append(f"service code {service_code} required diagnosis codes")
            queries.append(f"service {service_code} diagnosis requirements")
            queries.append(f"what diagnosis codes are required for service {service_code}")
        
        # Query 4: Approval requirements (CRITICAL - must be comprehensive)
        queries.append("approval requirement prior authorization services diagnoses")
        queries.append("services requiring approval diagnosis codes requiring approval")
        if service_code:
            queries.append(f"approval required service code {service_code}")
            queries.append(f"service {service_code} prior authorization approval")
            queries.append(f"does service {service_code} require approval")
            queries.append(f"service {service_code} approval requirement")
        if diagnosis_codes:
            if isinstance(diagnosis_codes, list):
                for code in diagnosis_codes[:5]:  # Increased to 5 to ensure all diagnoses checked
                    queries.append(f"diagnosis code {code} requires approval authorization")
                    queries.append(f"does diagnosis {code} require approval")
                    queries.append(f"diagnosis {code} approval requirement")
            else:
                queries.append(f"diagnosis code {diagnosis_codes} requires approval authorization")
                queries.append(f"does diagnosis {diagnosis_codes} require approval")
                queries.append(f"diagnosis {diagnosis_codes} approval requirement")
        
        # Query 4b: Combined service-diagnosis approval check
        if service_code and diagnosis_codes:
            if isinstance(diagnosis_codes, list):
                for code in diagnosis_codes[:3]:
                    queries.append(f"service {service_code} diagnosis {code} approval required")
            else:
                queries.append(f"service {service_code} diagnosis {diagnosis_codes} approval required")
        
        # Query 5: Encounter type rules (comprehensive)
        if encounter_type:
            queries.append(f"{encounter_type} encounter service eligibility inpatient outpatient")
            queries.append(f"{encounter_type} encounter type rules restrictions allowed services")
            queries.append(f"encounter type {encounter_type} service code eligibility")
        
        # Query 6: Facility rules
        if facility_id:
            queries.append(f"facility {facility_id} eligibility service type")
            queries.append(f"facility {facility_id} allowed services restrictions")
        
        # Query 7: Service-Encounter type combination
        if service_code and encounter_type:
            queries.append(f"service code {service_code} {encounter_type} encounter eligibility")
            queries.append(f"service {service_code} allowed for {encounter_type} encounter type")
        
        # Query 8: General medical adjudication rules (multiple variations)
        queries.append("medical adjudication rules service diagnosis encounter facility eligibility")
        queries.append("medical rules validation service code diagnosis code requirements")
        queries.append("claims validation rules medical adjudication eligibility")
        queries.append("healthcare claims rules service diagnosis encounter facility")
        
        # Query 9: Mutually exclusive diagnoses (if multiple diagnoses)
        if diagnosis_codes and isinstance(diagnosis_codes, list) and len(diagnosis_codes) > 1:
            queries.append("mutually exclusive diagnosis codes conflict")
            queries.append(f"diagnosis codes {', '.join(diagnosis_codes[:3])} mutually exclusive conflict")
        
        # Query 10: Service amount/paid amount rules
        if claim.get("paid_amount_aed"):
            queries.append("paid amount threshold limit maximum minimum rules")
            queries.append("claim amount rules validation paid amount requirements")
        
        # Query 11: General eligibility rules (catch-all)
        queries.append("eligibility rules service diagnosis facility encounter")
        queries.append("validation rules requirements restrictions allowed not allowed")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_queries = []
        for q in queries:
            if q not in seen:
                seen.add(q)
                unique_queries.append(q)
        
        return unique_queries if unique_queries else ["medical claims validation rules"]

    def _build_search_query(self, claim: Dict) -> str:
        """
        Build short, semantically meaningful search queries from claim context.
        This produces much better vector similarity results than long concatenations.
        """
        service_code = claim.get("service_code")
        diagnosis_codes = claim.get("diagnosis_codes")
        encounter_type = claim.get("encounter_type", "").lower()
        error_type = claim.get("error_type", "").lower()

        query_parts = []

        # ---- 1. Primary relationships
        if service_code:
            query_parts.append(f"rule for service code {service_code}")
        if diagnosis_codes:
            if isinstance(diagnosis_codes, list):
                diagnosis_codes = ", ".join(diagnosis_codes)
            query_parts.append(f"diagnosis {diagnosis_codes}")
        if encounter_type:
            query_parts.append(f"{encounter_type} encounter rule")

        # ---- 2. Common adjudication keywords
        query_parts.append("approval requirement facility eligibility")

        # ---- 3. Contextual emphasis based on error type
        if "technical" in error_type:
            query_parts.append("technical claim validation")
        elif "medical" in error_type:
            query_parts.append("medical rule compliance")
        else:
            query_parts.append("claim adjudication guidelines")

        # ---- 4. Flatten into concise sentence
        query = ". ".join(query_parts)
        logger.debug(f"[RAG] Built search query: {query}")
        return query or "medical claims validation rules"
