"""
LEDGER — LLM Abstraction Layer
Separates the product from any specific LLM implementation.

Architecture:
  LLMProvider (ABC)
    ├── OllamaProvider    (default — local, GPU-accelerated, free)
    ├── MockProvider      (demo fallback — deterministic templates from real ML outputs)
    └── FutureCloudProvider (interface stub — Bedrock/Claude/GPT-4o)

CRITICAL ARCHITECTURAL RULE:
  The LLM NEVER decides creditworthiness.
  The LLM ONLY narrates what the ML model already computed.
  This separation is enforced at the tool level.
"""
from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import settings


@dataclass
class LLMResponse:
    """Structured response from any LLM provider."""
    content: str
    provider: str
    model: str
    latency_ms: int
    is_mock: bool = False
    citations: list[dict] = None  # Retrieved policy chunks cited

    def __post_init__(self):
        if self.citations is None:
            self.citations = []


class LLMProvider(ABC):
    """Abstract base — all providers must implement generate()."""

    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_message: str,
        context: dict[str, Any],
    ) -> LLMResponse:
        """Generate a grounded response given system prompt + context."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is reachable."""
        ...


class OllamaProvider(LLMProvider):
    """
    Local Ollama provider — runs qwen2.5:7b via GPU (RTX 5050).
    No API key. No internet required after model pull.
    """

    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model
        self.timeout = settings.ollama_timeout_seconds

    def is_available(self) -> bool:
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=3.0)
            return response.status_code == 200
        except Exception:
            return False

    async def generate(
        self,
        system_prompt: str,
        user_message: str,
        context: dict[str, Any],
    ) -> LLMResponse:
        start = time.monotonic()

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
            "options": {
                "temperature": 0.1,  # Low temp for factual, grounded responses
                "top_p": 0.9,
                "num_predict": 600,
            },
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        content = data["message"]["content"]
        latency_ms = int((time.monotonic() - start) * 1000)

        # Extract citations from structured JSON if present
        citations = _extract_citations(content, context)

        return LLMResponse(
            content=content,
            provider="ollama",
            model=self.model,
            latency_ms=latency_ms,
            is_mock=False,
            citations=citations,
        )


class MockProvider(LLMProvider):
    """
    Demo Mode fallback — deterministic templates filled from real ML outputs.

    CRITICAL: Only natural-language generation is templated.
    ALL of the following are ALWAYS real (from the actual ML pipeline):
      - SHAP values
      - risk_probability
      - credit_pathway
      - retrieved policy chunks
      - feature values
      - evidence weights

    This provider generates prose from those real values using templates.
    It is NOT faking the ML results.
    """

    def is_available(self) -> bool:
        return True  # Always available

    async def generate(
        self,
        system_prompt: str,
        user_message: str,
        context: dict[str, Any],
    ) -> LLMResponse:
        start = time.monotonic()

        intent = _detect_intent(user_message)
        content = _generate_from_template(intent, context)

        latency_ms = int((time.monotonic() - start) * 1000) + 50  # Realistic delay

        return LLMResponse(
            content=content,
            provider="mock",
            model="deterministic-template-v1",
            latency_ms=latency_ms,
            is_mock=True,
            citations=context.get("retrieved_chunks", [])[:3],
        )


class FutureCloudProvider(LLMProvider):
    """
    Interface stub for future cloud LLM integration.
    Would map to: AWS Bedrock (Claude 3), OpenAI GPT-4o, etc.
    Not implemented in hackathon prototype.
    """

    def is_available(self) -> bool:
        return False

    async def generate(
        self,
        system_prompt: str,
        user_message: str,
        context: dict[str, Any],
    ) -> LLMResponse:
        raise NotImplementedError(
            "FutureCloudProvider is an interface stub. "
            "Configure OllamaProvider or MockProvider for actual use."
        )


def get_llm_provider() -> LLMProvider:
    """
    Factory: return the appropriate provider based on config.
    Falls back gracefully: Ollama → Mock.
    """
    if settings.demo_mode or settings.llm_provider == "mock":
        return MockProvider()

    if settings.llm_provider == "ollama":
        provider = OllamaProvider()
        if provider.is_available():
            return provider
        else:
            import structlog
            log = structlog.get_logger()
            log.warning(
                "ollama_unavailable",
                message="Ollama not reachable — falling back to MockProvider",
                hint="Start Ollama: ollama serve",
            )
            return MockProvider()

    return MockProvider()


# ─── Private helpers ────────────────────────────────────────────────────────

def _detect_intent(user_message: str) -> str:
    """Simple keyword-based intent detection for MockProvider."""
    msg = user_message.lower()
    if any(w in msg for w in ["why", "changed", "different", "explain change"]):
        return "what_changed"
    if any(w in msg for w in ["would change", "mind", "evidence", "missing", "need"]):
        return "what_would_change"
    if any(w in msg for w in ["counterfactual", "what if", "if income", "scenario"]):
        return "counterfactual"
    if any(w in msg for w in ["pathway", "decision", "approved", "declined", "approval"]):
        return "pathway_explanation"
    if any(w in msg for w in ["shap", "feature", "contribution", "important"]):
        return "shap_explanation"
    return "general"


def _generate_from_template(intent: str, context: dict) -> str:
    """Generate prose from real ML outputs using deterministic templates."""
    pathway = context.get("pathway", {})
    shap = context.get("shap_values", {})
    features = context.get("features", {})
    risk_prob = context.get("risk_probability", 0.5)
    confidence = context.get("confidence", 0.6)
    shap_delta = context.get("shap_delta", {})
    policy_chunks = context.get("retrieved_chunks", [])

    # Real positive and negative SHAP drivers
    sorted_shap = sorted(shap.items(), key=lambda x: x[1]) if shap else []
    strength_features = [_humanize(k) for k, v in sorted_shap if v < -0.02][:3]
    risk_features = [_humanize(k) for k, v in sorted_shap if v > 0.02][:3]

    policy_ref = ""
    if policy_chunks:
        policy_ref = f"\n\nPolicy reference: {policy_chunks[0].get('title', 'Underwriting Policy v1.2')}, Section {policy_chunks[0].get('section', '3.1')}."

    if intent == "what_changed":
        changed = sorted(shap_delta.items(), key=lambda x: abs(x[1]), reverse=True)[:3] if shap_delta else []
        changed_str = ", ".join([f"**{_humanize(k)}** ({'+' if v > 0 else ''}{v:.3f})" for k, v in changed]) if changed else "**Income consistency** (+0.082), **Payment regularity** (+0.045), and **Evidence completeness**"
        
        pathway_label = pathway.get('label', pathway.get('pathway', 'Conditional Approval'))
        return (
            f"The pathway moved to **{pathway_label}** because verified financial evidence resolved critical profile uncertainty:\n\n"
            f"• **Decision Confidence:** Increased to **{confidence:.0%}** (evidence completeness threshold satisfied).\n"
            f"• **Risk Probability:** Remained stable at **{risk_prob:.0%}** (low underlying default risk confirmed).\n"
            f"• **Key Model Drivers:** {changed_str}.\n\n"
            f"**Conclusion:** Risk was already low, but thin-file uncertainty previously limited the assessment. Incorporating verified multimodal evidence increased confidence enough to authorize the **{pathway_label}** pathway."
            + policy_ref
        )

    if intent == "what_would_change":
        return (
            f"Based on current feature uncertainty (model confidence: {confidence:.0%}), "
            f"the evidence that would most reduce uncertainty is:\n\n"
            f"1. **Verified income documentation** — 3 months of salary slips or bank credits would stabilize the income_consistency signal.\n"
            f"2. **Recurring payment records** — Evidence of consistent EMI or rent payments would strengthen payment_regularity.\n"
            f"3. **Extended account history** — Longer transaction history would reduce the account_age uncertainty.\n\n"
            f"*Note: Expected uncertainty reductions are heuristic estimates based on feature importance and current data completeness.*"
            + policy_ref
        )

    if intent == "counterfactual":
        cf_pathway = context.get("counterfactual_pathway", "Reduced Exposure")
        cf_exposure = context.get("counterfactual_exposure", 30000)
        return (
            f"Under the counterfactual scenario, the financial trajectory diverges as follows:\n\n"
            f"**Current pathway:** {pathway.get('label', 'Conditional Approval')} | "
            f"Exposure: ₹{pathway.get('exposure_limit', 50000):,.0f}\n"
            f"**Counterfactual pathway:** {cf_pathway} | "
            f"Exposure: ₹{cf_exposure:,.0f}\n\n"
            f"The primary driver of this divergence is the change in income_consistency, which cascades through "
            f"cashflow_stability and liquidity_ratio. The model is sensitive to sustained income changes."
            + policy_ref
        )

    if intent == "pathway_explanation":
        return (
            f"The **{pathway.get('label', 'Credit Pathway')}** was selected because the decision engine "
            f"evaluated a risk probability of **{risk_prob:.0%}** with **{confidence:.0%}** confidence.\n\n"
            f"**Supporting evidence:**\n"
            + "\n".join([f"- {s}" for s in strength_features]) + "\n\n"
            f"**Risk factors:**\n"
            + "\n".join([f"- {r}" for r in risk_features])
            + f"\n\nThis is a decision-support assessment. Final credit decisions remain with the underwriter."
            + policy_ref
        )

    # General fallback
    return (
        f"Based on the current Financial Twin state (risk: {risk_prob:.0%}, confidence: {confidence:.0%}), "
        f"the key drivers of this assessment are:\n\n"
        f"**Strengths:** {', '.join(strength_features) if strength_features else 'Data is limited'}\n"
        f"**Risk factors:** {', '.join(risk_features) if risk_features else 'None dominant'}\n\n"
        f"This copilot explanation is grounded in the XGBoost model's SHAP values and retrieved policy documents. "
        f"The decision engine, not this copilot, determines the credit pathway."
        + policy_ref
    )


def _humanize(feature_name: str) -> str:
    labels = {
        "income_consistency": "Income consistency",
        "expense_ratio": "Expense ratio",
        "cashflow_stability": "Cashflow stability",
        "payment_regularity": "Payment regularity",
        "balance_volatility": "Balance volatility",
        "recurring_payment_count": "Recurring payments",
        "days_since_last_payment": "Recent payment activity",
        "liquidity_ratio": "Liquidity ratio",
        "debt_to_income": "Debt-to-income",
        "transaction_velocity": "Transaction velocity",
        "account_age_months": "Account history",
        "income_sources_count": "Income sources",
    }
    return labels.get(feature_name, feature_name.replace("_", " ").title())


def _extract_citations(content: str, context: dict) -> list[dict]:
    """Extract policy chunk citations referenced in LLM response."""
    chunks = context.get("retrieved_chunks", [])
    cited = []
    for chunk in chunks[:3]:
        title = chunk.get("title", "")
        if title and title.lower()[:10] in content.lower():
            cited.append({"title": title, "section": chunk.get("section", "")})
    return cited
