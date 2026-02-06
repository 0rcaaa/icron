"""Multi-model collaboration service for cross-provider discussions.

This module enables multiple LLM providers to collaborate on a task through
structured discussion phases: independent analysis, peer critique, and synthesis.
"""

import asyncio
from dataclasses import dataclass
from typing import Any

from loguru import logger

from icron.config.schema import Config
from icron.providers.base import LLMProvider
from icron.providers.openai_provider import OpenAIProvider
from icron.providers.anthropic_provider import AnthropicProvider
from icron.providers.gemini_provider import GeminiProvider


# Provider display info
PROVIDER_INFO: dict[str, dict[str, str]] = {
    "anthropic": {"name": "Claude", "emoji": "🟣", "model": "claude-sonnet-4-20250514"},
    "openrouter": {"name": "OpenRouter", "emoji": "🔀", "model": "anthropic/claude-sonnet-4-20250514"},
    "openai": {"name": "GPT", "emoji": "🟢", "model": "gpt-4o"},
    "together": {"name": "Together", "emoji": "🔵", "model": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"},
    "groq": {"name": "Groq", "emoji": "⚡", "model": "llama-3.3-70b-versatile"},
    "gemini": {"name": "Gemini", "emoji": "💎", "model": "gemini-2.0-flash"},
    "zhipu": {"name": "Zhipu", "emoji": "🇨🇳", "model": "glm-4-flash"},
}

# Provider priority for synthesis (higher = better)
PROVIDER_PRIORITY: dict[str, int] = {
    "anthropic": 100,
    "openrouter": 90,  # Usually hosts Claude
    "openai": 80,
    "gemini": 70,
    "together": 60,
    "groq": 50,
    "zhipu": 40,
}


@dataclass
class ProviderInstance:
    """A configured provider instance with metadata."""
    name: str
    emoji: str
    provider: LLMProvider
    model: str
    priority: int


@dataclass
class CollaborationResult:
    """Result of a multi-model collaboration."""
    task: str
    phases: list[dict[str, Any]]
    final_synthesis: str
    providers_used: list[str]
    success: bool
    error: str | None = None


class CollaborationService:
    """
    Multi-model collaboration service.
    
    Orchestrates structured discussions between multiple LLM providers
    using a three-phase approach for optimal results.
    """
    
    def __init__(self, config: Config):
        self.config = config
        self._providers: list[ProviderInstance] | None = None
    
    def get_configured_providers(self) -> list[ProviderInstance]:
        """
        Get all providers that have valid API keys configured.
        
        Returns:
            List of configured provider instances, sorted by priority.
        """
        if self._providers is not None:
            return self._providers
        
        providers: list[ProviderInstance] = []
        
        # Check each provider in config
        for provider_name in PROVIDER_INFO.keys():
            provider_config = getattr(self.config.providers, provider_name, None)
            if not provider_config:
                continue
            
            api_key = getattr(provider_config, "api_key", None)
            if not api_key:
                continue
            
            api_base = getattr(provider_config, "api_base", None)
            info = PROVIDER_INFO[provider_name]
            
            try:
                # Create provider instance based on type
                if provider_name == "anthropic":
                    llm = AnthropicProvider(
                        api_key=api_key,
                        api_base=api_base,
                        default_model=info["model"],
                    )
                elif provider_name == "gemini":
                    llm = GeminiProvider(
                        api_key=api_key,
                        api_base=api_base,
                        default_model=info["model"],
                    )
                else:
                    # OpenAI-compatible providers
                    base_urls = {
                        "openai": "https://api.openai.com/v1",
                        "openrouter": "https://openrouter.ai/api/v1",
                        "together": "https://api.together.xyz/v1",
                        "groq": "https://api.groq.com/openai/v1",
                        "zhipu": "https://open.bigmodel.cn/api/paas/v4/",
                    }
                    llm = OpenAIProvider(
                        api_key=api_key,
                        api_base=api_base or base_urls.get(provider_name),
                        default_model=info["model"],
                    )
                
                providers.append(ProviderInstance(
                    name=info["name"],
                    emoji=info["emoji"],
                    provider=llm,
                    model=info["model"],
                    priority=PROVIDER_PRIORITY.get(provider_name, 0),
                ))
                logger.debug(f"Collaboration: Found configured provider {info['name']}")
                
            except Exception as e:
                logger.warning(f"Failed to initialize {provider_name} for collaboration: {e}")
        
        # Sort by priority (highest first)
        providers.sort(key=lambda p: p.priority, reverse=True)
        self._providers = providers
        
        return providers
    
    def get_provider_count(self) -> int:
        """Get the number of configured providers."""
        return len(self.get_configured_providers())
    
    async def collaborate(
        self,
        task: str,
        callback: callable = None,
    ) -> CollaborationResult:
        """
        Run a multi-model collaboration on a task.
        
        Args:
            task: The task/question for the models to discuss.
            callback: Optional async function to call with progress updates.
                      Signature: async def callback(provider_name: str, phase: str, content: str)
        
        Returns:
            CollaborationResult with all phases and final synthesis.
        """
        providers = self.get_configured_providers()
        
        if len(providers) < 2:
            return CollaborationResult(
                task=task,
                phases=[],
                final_synthesis="",
                providers_used=[p.name for p in providers],
                success=False,
                error=f"Need at least 2 providers configured for collaboration. Found: {len(providers)}",
            )
        
        phases: list[dict[str, Any]] = []
        
        try:
            # Phase 1: Independent Analysis
            # Each model analyzes the task without seeing others' responses
            phase1_results = await self._run_phase1(task, providers, callback)
            phases.append({"phase": "analysis", "results": phase1_results})
            
            # Phase 2: Peer Critique
            # Each model reviews all Phase 1 responses
            phase2_results = await self._run_phase2(task, phase1_results, providers, callback)
            phases.append({"phase": "critique", "results": phase2_results})
            
            # Phase 3: Synthesis
            # Best model creates final answer incorporating all insights
            synthesis = await self._run_phase3(task, phase1_results, phase2_results, providers, callback)
            phases.append({"phase": "synthesis", "result": synthesis})
            
            return CollaborationResult(
                task=task,
                phases=phases,
                final_synthesis=synthesis,
                providers_used=[p.name for p in providers],
                success=True,
            )
            
        except Exception as e:
            logger.error(f"Collaboration failed: {e}")
            return CollaborationResult(
                task=task,
                phases=phases,
                final_synthesis="",
                providers_used=[p.name for p in providers],
                success=False,
                error=str(e),
            )
    
    async def _run_phase1(
        self,
        task: str,
        providers: list[ProviderInstance],
        callback: callable = None,
    ) -> dict[str, str]:
        """
        Phase 1: Independent Analysis.
        
        Each model analyzes the task independently without seeing others' responses.
        This prevents groupthink and encourages diverse perspectives.
        """
        prompt = f"""You are participating in a multi-model collaboration to solve a task.
This is Phase 1: Independent Analysis.

TASK: {task}

Provide your analysis and proposed solution. Be thorough and specific.
Consider:
- Key requirements and constraints
- Potential approaches and trade-offs
- Your recommended solution with reasoning

Other AI models will also analyze this task independently. Your response will be shared with them in the next phase."""

        results: dict[str, str] = {}
        
        # Run all providers in parallel for Phase 1
        async def get_response(p: ProviderInstance) -> tuple[str, str]:
            try:
                messages = [{"role": "user", "content": prompt}]
                response = await p.provider.chat(messages, model=p.model)
                content = response.get("content", "")
                return p.name, content
            except Exception as e:
                logger.error(f"Phase 1 error for {p.name}: {e}")
                return p.name, f"[Error: {e}]"
        
        tasks = [get_response(p) for p in providers]
        responses = await asyncio.gather(*tasks)
        
        for name, content in responses:
            results[name] = content
        
        # Send combined Phase 1 results
        if callback:
            combined = "\n\n---\n\n".join([
                f"{self._get_emoji(name)} **{name}'s Analysis**:\n{content}"
                for name, content in results.items()
            ])
            await callback("", "analysis", f"📊 **Phase 1: Independent Analyses**\n\n{combined}")
        
        return results
    
    def _get_emoji(self, provider_name: str) -> str:
        """Get emoji for a provider name."""
        for info in PROVIDER_INFO.values():
            if info["name"] == provider_name:
                return info["emoji"]
        return "🤖"
    
    async def _run_phase2(
        self,
        task: str,
        phase1_results: dict[str, str],
        providers: list[ProviderInstance],
        callback: callable = None,
    ) -> dict[str, str]:
        """
        Phase 2: Peer Critique.
        
        Each model reviews all Phase 1 responses, identifying strengths,
        weaknesses, and suggesting improvements.
        """
        # Build context with all Phase 1 responses
        proposals = "\n\n".join([
            f"=== {name}'s Analysis ===\n{content}"
            for name, content in phase1_results.items()
        ])
        
        results: dict[str, str] = {}
        
        async def get_critique(p: ProviderInstance) -> tuple[str, str]:
            prompt = f"""You are participating in a multi-model collaboration.
This is Phase 2: Peer Critique.

ORIGINAL TASK: {task}

Here are all the analyses from Phase 1:

{proposals}

Now provide your critique of ALL proposals (including your own):
1. **Strengths**: What good ideas or approaches do you see?
2. **Weaknesses**: What gaps, issues, or concerns do you identify?
3. **Improvements**: What specific improvements would you suggest?
4. **Best elements**: Which ideas from any proposal should definitely be included in the final solution?

Be constructive and specific. Your critique will help create an optimal final solution."""

            try:
                messages = [{"role": "user", "content": prompt}]
                response = await p.provider.chat(messages, model=p.model)
                content = response.get("content", "")
                return p.name, content
            except Exception as e:
                logger.error(f"Phase 2 error for {p.name}: {e}")
                return p.name, f"[Error: {e}]"
        
        tasks = [get_critique(p) for p in providers]
        responses = await asyncio.gather(*tasks)
        
        for name, content in responses:
            results[name] = content
        
        # Send combined Phase 2 results
        if callback:
            combined = "\n\n---\n\n".join([
                f"{self._get_emoji(name)} **{name}'s Critique**:\n{content}"
                for name, content in results.items()
            ])
            await callback("", "critique", f"🔍 **Phase 2: Peer Critiques**\n\n{combined}")
        
        return results
    
    async def _run_phase3(
        self,
        task: str,
        phase1_results: dict[str, str],
        phase2_results: dict[str, str],
        providers: list[ProviderInstance],
        callback: callable = None,
    ) -> str:
        """
        Phase 3: Synthesis.
        
        The highest-priority model synthesizes all insights into a final answer.
        """
        # Use highest priority provider for synthesis
        synthesizer = providers[0]
        
        proposals = "\n\n".join([
            f"=== {name}'s Analysis ===\n{content}"
            for name, content in phase1_results.items()
        ])
        
        critiques = "\n\n".join([
            f"=== {name}'s Critique ===\n{content}"
            for name, content in phase2_results.items()
        ])
        
        prompt = f"""You are the synthesizer in a multi-model collaboration.
This is Phase 3: Final Synthesis.

ORIGINAL TASK: {task}

=== PHASE 1: INDEPENDENT ANALYSES ===
{proposals}

=== PHASE 2: PEER CRITIQUES ===
{critiques}

Now create the FINAL SOLUTION that:
1. Incorporates the best ideas from all analyses
2. Addresses concerns raised in critiques
3. Provides a complete, actionable answer
4. Is better than any single proposal alone

Your synthesis should be comprehensive and represent the collective intelligence of all participating models. This is the answer that will be delivered to the user."""

        try:
            messages = [{"role": "user", "content": prompt}]
            response = await synthesizer.provider.chat(messages, model=synthesizer.model)
            content = response.get("content", "")
            
            if callback:
                await callback(synthesizer.name, "synthesis", f"✅ **Final Synthesis** (by {synthesizer.emoji} {synthesizer.name}):\n\n{content}")
            
            return content
            
        except Exception as e:
            logger.error(f"Phase 3 synthesis error: {e}")
            # Fallback: return combined phase 1 results
            return f"[Synthesis failed: {e}]\n\nBest proposals:\n{proposals}"
