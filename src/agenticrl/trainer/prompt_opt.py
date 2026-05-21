"""Prompt-level optimization (DSPy-style).

Instead of updating model weights, this optimizer searches for the optimal
system prompt using evolutionary algorithms. Each generation evaluates a
population of prompt candidates on the environment and selects the best
performers for mutation and crossover.
"""

from __future__ import annotations

import copy
import random
from typing import Any

from agenticrl.config import PromptOptConfig
from agenticrl.trajectory.collector import TrajectoryCollector

# Mutation operators for text prompts
_MUTATION_TEMPLATES = [
    "Be more concise and direct.",
    "Think step by step before answering.",
    "Consider multiple perspectives.",
    "Double-check your reasoning.",
    "Provide detailed explanations.",
    "Use examples to illustrate.",
    "Be creative and think outside the box.",
    "Focus on accuracy over speed.",
    "Break down complex problems into smaller parts.",
    "Always verify your final answer.",
]


class PromptCandidate:
    """A single prompt candidate with a fitness score.

    Args:
        prompt: The system prompt string.
        score: Fitness score (higher is better). Defaults to 0.0.
    """

    def __init__(self, prompt: str, score: float = 0.0) -> None:
        self.prompt = prompt
        self.score = score


class PromptOptimizer:
    """Evolve prompts using an evolutionary algorithm.

    Maintains a population of prompt candidates, evaluates them on the
    environment, and iteratively selects and mutates the best performers.

    Args:
        collector: TrajectoryCollector for running rollouts.
        config: Prompt optimization configuration.
        seed: Random seed.

    Example:
        >>> from agenticrl.trainer import PromptOptimizer
        >>> from agenticrl.config import PromptOptConfig
        >>> 
        >>> opt = PromptOptimizer(collector, PromptOptConfig(population_size=10))
        >>> best = opt.optimize(agent)
        >>> print(best.prompt)
    """

    def __init__(
        self,
        collector: TrajectoryCollector,
        config: PromptOptConfig | None = None,
        seed: int | None = None,
    ) -> None:
        self.collector = collector
        self.config = config or PromptOptConfig()
        self._rng = random.Random(seed)
        self._population: list[PromptCandidate] = []
        self._history: list[dict[str, Any]] = []

    def _initialize_population(self) -> list[PromptCandidate]:
        """Create initial population from seed prompts or defaults.

        Returns:
            List of PromptCandidate objects.
        """
        population: list[PromptCandidate] = []

        # Use provided seed prompts
        for prompt in self.config.initial_prompts:
            population.append(PromptCandidate(prompt))

        # Pad with default prompts if needed
        default_prompts = [
            "You are a helpful AI assistant.",
            "You are an expert problem solver. Think step by step.",
            "You are a precise and accurate AI. Verify your answers.",
            "You are a creative AI. Explore multiple solutions.",
            "You are a concise AI. Give direct answers.",
        ]
        while len(population) < self.config.population_size:
            idx = len(population) % len(default_prompts)
            base = default_prompts[idx]
            # Add variation
            if self._rng.random() < 0.5:
                mutation = self._rng.choice(_MUTATION_TEMPLATES)
                base = f"{base} {mutation}"
            population.append(PromptCandidate(base))

        return population[: self.config.population_size]

    def _evaluate_candidate(
        self, candidate: PromptCandidate, agent: Any
    ) -> float:
        """Evaluate a single prompt candidate.

        Temporarily sets the agent's system prompt and runs rollouts.

        Args:
            candidate: The prompt candidate to evaluate.
            agent: Agent instance (must have config.system_prompt attribute).

        Returns:
            Mean total reward across rollouts.
        """
        # Save original prompt
        original_prompt = getattr(agent.config, "system_prompt", "")
        agent.config.system_prompt = candidate.prompt

        try:
            trajectories = self.collector.run_rollouts(
                agent, num_rollouts=self.config.num_rollouts_per_prompt
            )
            total_rewards = [t["total_reward"] for t in trajectories]
            score = sum(total_rewards) / len(total_rewards) if total_rewards else 0.0
        finally:
            # Restore original prompt
            agent.config.system_prompt = original_prompt

        candidate.score = score
        return score

    def _mutate(self, prompt: str) -> str:
        """Apply a random mutation to a prompt.

        Args:
            prompt: Original prompt string.

        Returns:
            Mutated prompt string.
        """
        if self._rng.random() > self.config.mutation_rate:
            return prompt

        mutation = self._rng.choice(_MUTATION_TEMPLATES)
        # Prepend, append, or insert mutation
        op = self._rng.choice(["prepend", "append", "replace_last"])
        if op == "prepend":
            return f"{mutation} {prompt}"
        elif op == "append":
            return f"{prompt} {mutation}"
        else:
            sentences = prompt.split(". ")
            if len(sentences) > 1:
                sentences[-1] = mutation
                return ". ".join(sentences)
            return f"{prompt} {mutation}"

    def _crossover(
        self, parent1: str, parent2: str
    ) -> str:
        """Perform crossover between two prompts.

        Splits both prompts in half and combines them.

        Args:
            parent1: First parent prompt.
            parent2: Second parent prompt.

        Returns:
            Child prompt.
        """
        words1 = parent1.split()
        words2 = parent2.split()

        if len(words1) < 2 or len(words2) < 2:
            return parent1 if self._rng.random() < 0.5 else parent2

        split1 = self._rng.randint(1, len(words1) - 1)
        split2 = self._rng.randint(1, len(words2) - 1)

        child = " ".join(words1[:split1] + words2[split2:])
        return child

    def optimize(self, agent: Any) -> PromptCandidate:
        """Run the full evolutionary optimization loop.

        Args:
            agent: Agent to evaluate prompts with.

        Returns:
            The best PromptCandidate found.
        """
        # Initialize
        self._population = self._initialize_population()

        best_candidate = self._population[0]

        for iteration in range(self.config.num_iterations):
            # Evaluate all candidates
            for candidate in self._population:
                self._evaluate_candidate(candidate, agent)

            # Sort by fitness
            self._population.sort(key=lambda c: c.score, reverse=True)
            current_best = self._population[0]
            if current_best.score > best_candidate.score:
                best_candidate = copy.deepcopy(current_best)

            mean_score = sum(c.score for c in self._population) / len(self._population)
            print(
                f"[Gen {iteration+1}/{self.config.num_iterations}] "
                f"Best: {current_best.score:.3f} (\"{current_best.prompt[:60]}...\") "
                f"Mean: {mean_score:.3f}"
            )

            self._history.append({
                "iteration": iteration + 1,
                "best_score": current_best.score,
                "best_prompt": current_best.prompt,
                "mean_score": mean_score,
            })

            # Selection: keep top-k
            elite = [
                copy.deepcopy(c) for c in self._population[: self.config.top_k]
            ]
            new_population = elite[:]

            # Fill the rest with mutated/crossed candidates
            while len(new_population) < self.config.population_size:
                parent1 = self._rng.choice(elite).prompt
                parent2 = self._rng.choice(elite).prompt

                if self._rng.random() < self.config.crossover_rate:
                    child_prompt = self._crossover(parent1, parent2)
                else:
                    child_prompt = parent1

                child_prompt = self._mutate(child_prompt)
                new_population.append(PromptCandidate(child_prompt))

            self._population = new_population

        if best_candidate is not None:
            agent.config.system_prompt = best_candidate.prompt

        return best_candidate

    def get_history(self) -> list[dict[str, Any]]:
        """Return optimization history for analysis."""
        return self._history
