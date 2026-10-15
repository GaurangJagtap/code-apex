from typing import Dict, Any, List

class CuriosityEngine:
    """
    Explainable Prioritization Engine that ranks exploration journeys and test cases
    based on Impact, Uncertainty, Novelty, and Coverage Gaps.
    """
    def __init__(
        self,
        impact_weight: float = 0.35,
        uncertainty_weight: float = 0.25,
        novelty_weight: float = 0.20,
        coverage_weight: float = 0.20,
        cost_penalty_weight: float = 0.05
    ):
        self.impact_weight = impact_weight
        self.uncertainty_weight = uncertainty_weight
        self.novelty_weight = novelty_weight
        self.coverage_weight = coverage_weight
        self.cost_penalty_weight = cost_penalty_weight
        self.visited_paths: set = set()
        self.tested_features: set = set()

    def evaluate_candidate(
        self,
        candidate_id: str,
        title: str,
        category: str,
        path: str,
        description: str,
        business_criticality: float = 0.5,
        known_failures: bool = False,
        estimated_steps: int = 4
    ) -> Dict[str, Any]:
        """
        Computes a normalized score [0.0 - 1.0] and generates an explainable rationale.
        """
        # 1. Impact: Business criticality + core transaction weight (cart/checkout/auth have higher impact)
        path_lower = path.lower()
        title_lower = title.lower()
        
        is_transactional = any(k in path_lower or k in title_lower for k in ["cart", "checkout", "order", "login", "auth", "register", "payment"])
        impact = 0.90 if is_transactional else (0.50 + 0.40 * business_criticality)
        
        # 2. Novelty: High if path has not been explored in the current run
        is_visited = path in self.visited_paths
        novelty = 0.20 if is_visited else 0.95
        
        # 3. Uncertainty: High if it's a boundary condition, previous failure observed, or complex input
        is_boundary_or_negative = any(k in title_lower for k in ["invalid", "boundary", "empty", "duplicate", "missing", "unauthenticated", "failure"])
        if known_failures:
            uncertainty = 0.95
        elif is_boundary_or_negative:
            uncertainty = 0.85
        else:
            uncertainty = 0.40

        # 4. Coverage Gap: High if this feature category has low execution coverage so far
        category_count = sum(1 for f in self.tested_features if f == category)
        coverage_gap = max(0.1, 1.0 - (category_count * 0.3))

        # 5. Cost Penalty: Higher steps incur slight penalty
        cost_penalty = min(0.15, (estimated_steps / 20.0) * self.cost_penalty_weight)

        # Compute combined weighted priority score
        raw_score = (
            (self.impact_weight * impact) +
            (self.uncertainty_weight * uncertainty) +
            (self.novelty_weight * novelty) +
            (self.coverage_weight * coverage_gap) -
            cost_penalty
        )
        final_score = round(max(0.05, min(1.0, raw_score)), 3)

        # Generate Explainable Heuristic Reasoning
        reasons = []
        if is_transactional:
            reasons.append("touches critical business transactional workflows")
        if not is_visited:
            reasons.append("explores previously unvisited application state")
        if is_boundary_or_negative:
            reasons.append("tests edge-case / negative validation boundaries with elevated risk")
        if category_count == 0:
            reasons.append(f"closes an untested coverage gap in '{category}'")

        if not reasons:
            reasons.append("standard functional sanity verification")

        reasoning = f"{title} was prioritized (score: {final_score}) because it " + " and ".join(reasons) + "."

        return {
            "impact": round(impact, 2),
            "uncertainty": round(uncertainty, 2),
            "novelty": round(novelty, 2),
            "coverage_gap": round(coverage_gap, 2),
            "priority_score": final_score,
            "reasoning": reasoning
        }

    def record_selection(self, path: str, category: str):
        """Updates internal state after a test journey is executed."""
        self.visited_paths.add(path)
        self.tested_features.add(category)
