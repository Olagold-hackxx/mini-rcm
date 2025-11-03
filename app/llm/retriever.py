"""RAG retriever for rule documents using LangChain with enhanced semantic coverage."""
from typing import List, Dict
from config import get_settings
from llm.vector_store import VectorStore
from utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


class RuleRetriever:
    """Retrieves relevant adjudication and approval rules from ChromaDB via LangChain."""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.vector_store = VectorStore(tenant_id) if settings.USE_RAG else None

    async def retrieve_relevant_rules(self, claim: Dict) -> List[Dict]:
        """
        Retrieve relevant rules for a claim using multi-query semantic RAG.
        Ensures coverage for service, diagnosis, approval, encounter type, and facility rules.
        """
        if not settings.USE_RAG or not self.vector_store:
            return []

        all_results = []
        seen_hashes = set()

        try:
            # Build diverse, focused queries
            queries = self._build_multiple_queries(claim)

            n_results_per_query = max(settings.TOP_K_RETRIEVAL or 30, 30)

            # Execute all queries and combine deduplicated results
            for query in queries:
                results = await self.vector_store.search(
                    query=query,
                    n_results=n_results_per_query,
                    filter_metadata={"tenant_id": self.tenant_id},
                )

                for result in results:
                    content = result.get("content", "")
                    content_hash = hash(content[:200])
                    if content_hash not in seen_hashes:
                        seen_hashes.add(content_hash)
                        all_results.append(result)

            # Broader fallback if insufficient results
            if len(all_results) < 20:
                logger.warning(
                    f"[RAG] Only retrieved {len(all_results)} rules, performing broader fallback search."
                )
                general_results = await self.vector_store.search(
                    query="medical claims validation adjudication rules service diagnosis encounter eligibility approval requirements",
                    n_results=n_results_per_query * 2,
                    filter_metadata={"tenant_id": self.tenant_id},
                )

                for result in general_results:
                    content = result.get("content", "")
                    content_hash = hash(content[:200])
                    if content_hash not in seen_hashes:
                        seen_hashes.add(content_hash)
                        all_results.append(result)

            # Safety fallback: ensure at least one encounter-type rule
            if not any(
                "inpatient" in r.get("content", "").lower()
                or "outpatient" in r.get("content", "").lower()
                for r in all_results
            ):
                logger.warning(
                    f"[RAG] No encounter-type rules found for claim {claim.get('claim_id')}, adding fallback rule."
                )
                all_results.append({
                    "content": (
                        "Encounter-type restriction rule: "
                        "Each service code must match its allowed encounter type. "
                        "If a service is inpatient-only, it cannot be used for outpatient encounters, and vice versa."
                    ),
                    "metadata": {"rule_type": "encounter_type_fallback"}
                })

            logger.info(
                f"[RAG] Retrieved {len(all_results)} unique rules for claim {claim.get('claim_id')} "
                f"from {len(queries)} queries."
            )

            # Return up to 5× TOP_K for comprehensive context
            max_results = settings.TOP_K_RETRIEVAL * 5 if settings.TOP_K_RETRIEVAL else 150
            return all_results[:max_results]

        except Exception as e:
            logger.error(f"[RAG] Rule retrieval failed: {e}")
            return []

    # ---------------------------------------------------------------------- #
    # Query Construction Helpers
    # ---------------------------------------------------------------------- #

    def _build_multiple_queries(self, claim: Dict) -> List[str]:
        """Build multiple targeted queries to capture all rule dimensions."""
        queries = []

        service_code = claim.get("service_code")
        diagnosis_codes = claim.get("diagnosis_codes")
        encounter_type = claim.get("encounter_type", "").lower()
        facility_id = claim.get("facility_id")

        # ------------------------------
        # 1. Service-specific queries
        # ------------------------------
        if service_code:
            queries += [
                f"service code {service_code} rules requirements eligibility",
                f"service {service_code} allowed not allowed restrictions",
                f"service code {service_code} approval authorization required",
                f"service code {service_code} required diagnosis codes",
                f"what diagnosis codes are required for service {service_code}",
                f"service {service_code} encounter eligibility inpatient outpatient",
            ]

        # ------------------------------
        # 2. Diagnosis-specific queries
        # ------------------------------
        if diagnosis_codes:
            codes = diagnosis_codes if isinstance(diagnosis_codes, list) else [diagnosis_codes]
            for code in codes[:5]:
                queries += [
                    f"diagnosis code {code} requirements approval eligibility",
                    f"diagnosis {code} allowed not allowed restrictions",
                    f"diagnosis code {code} authorization prior approval",
                    f"diagnosis {code} requiring approval rules",
                ]

        # ------------------------------
        # 3. Service + Diagnosis combos
        # ------------------------------
        if service_code and diagnosis_codes:
            codes = diagnosis_codes if isinstance(diagnosis_codes, list) else [diagnosis_codes]
            for code in codes[:5]:
                queries += [
                    f"service code {service_code} requires diagnosis code {code}",
                    f"service {service_code} with diagnosis {code} eligibility requirements",
                    f"service {service_code} diagnosis {code} approval required",
                    f"service {service_code} diagnosis {code} allowed not allowed",
                ]

        # ------------------------------
        # 4. Approval requirement rules
        # ------------------------------
        queries += [
            "approval requirement prior authorization services diagnoses",
            "services requiring approval diagnosis codes requiring approval",
        ]
        if service_code:
            queries += [
                f"approval required service code {service_code}",
                f"service {service_code} prior authorization approval",
                f"service {service_code} approval requirement",
            ]
        if diagnosis_codes:
            codes = diagnosis_codes if isinstance(diagnosis_codes, list) else [diagnosis_codes]
            for code in codes[:5]:
                queries += [
                    f"diagnosis code {code} requires approval authorization",
                    f"diagnosis {code} approval requirement",
                ]

        # ------------------------------
        # 5. Encounter-type restriction rules
        # ------------------------------
        if encounter_type:
            queries += [
                f"{encounter_type} encounter service eligibility inpatient outpatient",
                f"{encounter_type} encounter type rules restrictions allowed services",
                f"encounter type {encounter_type} service code eligibility restrictions",
                f"which services are allowed for {encounter_type} encounters",
                f"services not allowed for {encounter_type} encounters",
                f"{encounter_type}-only service rules and restrictions",
            ]

        # ------------------------------
        # 6. Facility-specific rules
        # ------------------------------
        if facility_id:
            queries += [
                f"facility {facility_id} eligibility service type",
                f"facility {facility_id} allowed services restrictions",
            ]

        # ------------------------------
        # 7. Mutually exclusive diagnoses
        # ------------------------------
        if diagnosis_codes and isinstance(diagnosis_codes, list) and len(diagnosis_codes) > 1:
            queries += [
                "mutually exclusive diagnosis codes conflict rules",
                f"diagnosis codes {', '.join(diagnosis_codes[:3])} mutually exclusive conflict",
            ]

        # ------------------------------
        # 8. Paid amount / threshold rules
        # ------------------------------
        if claim.get("paid_amount_aed"):
            queries += [
                "paid amount threshold limit maximum minimum rules",
                "claim amount rules validation paid amount requirements",
            ]

        # ------------------------------
        # 9. General adjudication / fallback rules
        # ------------------------------
        queries += [
            "medical adjudication rules service diagnosis encounter facility eligibility",
            "medical rules validation service code diagnosis code requirements",
            "claims validation rules medical adjudication eligibility",
            "healthcare claims rules service diagnosis encounter facility",
            "eligibility rules service diagnosis facility encounter",
            "validation rules requirements restrictions allowed not allowed",
        ]

        # Deduplicate while preserving order
        seen = set()
        unique_queries = [q for q in queries if not (q in seen or seen.add(q))]
        return unique_queries or ["medical claims validation rules"]

    # ---------------------------------------------------------------------- #
    # Short semantic query for simple vector search (fallback)
    # ---------------------------------------------------------------------- #

    def _build_search_query(self, claim: Dict) -> str:
        """Build concise semantic query from claim context for vector retrieval."""
        service_code = claim.get("service_code")
        diagnosis_codes = claim.get("diagnosis_codes")
        encounter_type = claim.get("encounter_type", "").lower()
        error_type = claim.get("error_type", "").lower()

        query_parts = []

        # Core fields
        if service_code:
            query_parts.append(f"rule for service code {service_code}")
        if diagnosis_codes:
            codes = diagnosis_codes if isinstance(diagnosis_codes, list) else [diagnosis_codes]
            query_parts.append(f"diagnosis codes {', '.join(codes)}")
        if encounter_type:
            query_parts.append(f"{encounter_type} encounter rule")

        # Add semantic emphasis
        query_parts += [
            "approval requirement facility eligibility",
            "inpatient outpatient encounter eligibility rules",
            "service-encounter restrictions inpatient-only outpatient-only not allowed",
        ]

        # Error context
        if "technical" in error_type:
            query_parts.append("technical claim validation")
        elif "medical" in error_type:
            query_parts.append("medical rule compliance")
        else:
            query_parts.append("claim adjudication guidelines")

        query = ". ".join(query_parts)
        logger.debug(f"[RAG] Built semantic query: {query}")
        return query or "medical claims validation rules"
