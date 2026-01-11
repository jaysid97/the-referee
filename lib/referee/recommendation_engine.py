"""
Recommendation engine for The Referee technology comparison tool.

This module provides the RecommendationEngine class that generates intelligent
recommendations based on technology compatibility scores and project requirements.
"""

from typing import List, Dict, Optional, Tuple
from referee.models import (
    TechnologyProfile,
    WeightedCriteria,
    CompatibilityScore,
    Recommendation,
    RankedChoice,
    AlternativeScenario,
    ConfidenceLevel
)


class RecommendationEngine:
    """
    Generates intelligent recommendations based on weighted analysis.
    
    Provides functionality to:
    - Rank technologies by compatibility with project requirements
    - Generate reasoning explanations based on requirements
    - Identify key decision factors for close matches
    - Calculate confidence levels for recommendations
    """
    
    def __init__(self):
        """Initialize the recommendation engine."""
        pass
    
    def generate_recommendation(
        self,
        technologies: List[TechnologyProfile],
        compatibility_scores: List[CompatibilityScore],
        weighted_criteria: WeightedCriteria,
        comparison_data: Optional[Dict] = None
    ) -> Recommendation:
        """
        Generate a comprehensive recommendation based on compatibility analysis.
        
        Args:
            technologies: List of technology profiles
            compatibility_scores: Compatibility scores for each technology
            weighted_criteria: Weighted criteria based on project requirements
            comparison_data: Optional additional comparison data
            
        Returns:
            Recommendation with ranked choices and reasoning
        """
        if not technologies:
            raise ValueError("At least one technology must be provided")
        
        if len(compatibility_scores) != len(technologies):
            raise ValueError("Number of compatibility scores must match number of technologies")
        
        # Create ranked choices
        ranked_choices = self._create_ranked_choices(
            technologies, compatibility_scores, weighted_criteria
        )
        
        # Identify key decision factors
        key_decision_factors = self._identify_decision_factors(
            technologies, compatibility_scores, weighted_criteria
        )
        
        # Generate caveats and warnings
        caveats = self._generate_caveats(technologies, compatibility_scores, weighted_criteria)
        
        # Generate alternative scenarios if applicable
        alternative_scenarios = self._generate_alternative_scenarios(
            technologies, compatibility_scores, weighted_criteria
        )
        
        return Recommendation(
            ranked_choices=ranked_choices,
            key_decision_factors=key_decision_factors,
            caveats=caveats,
            alternative_scenarios=alternative_scenarios
        )
    
    def _create_ranked_choices(
        self,
        technologies: List[TechnologyProfile],
        compatibility_scores: List[CompatibilityScore],
        weighted_criteria: WeightedCriteria
    ) -> List[RankedChoice]:
        """
        Create ranked technology choices with detailed reasoning.
        
        Args:
            technologies: List of technology profiles
            compatibility_scores: Compatibility scores for each technology
            weighted_criteria: Weighted criteria based on project requirements
            
        Returns:
            List of RankedChoice objects sorted by score (highest first)
        """
        # Create technology lookup for easy access
        tech_lookup = {tech.name: tech for tech in technologies}
        
        # Sort compatibility scores by score (highest first)
        sorted_scores = sorted(compatibility_scores, key=lambda x: x.score, reverse=True)
        
        ranked_choices = []
        
        for i, comp_score in enumerate(sorted_scores):
            technology = tech_lookup[comp_score.technology]
            
            # Calculate confidence level
            confidence = self._calculate_confidence(comp_score, sorted_scores, i)
            
            # Generate detailed reasoning
            reasoning = self._generate_detailed_reasoning(
                technology, comp_score, weighted_criteria, i + 1
            )
            
            ranked_choice = RankedChoice(
                technology=comp_score.technology,
                score=comp_score.score,
                confidence=confidence,
                reasoning=reasoning
            )
            
            ranked_choices.append(ranked_choice)
        
        return ranked_choices
    
    def _calculate_confidence(
        self,
        comp_score: CompatibilityScore,
        all_scores: List[CompatibilityScore],
        rank: int
    ) -> ConfidenceLevel:
        """
        Calculate confidence level for a recommendation.
        
        Args:
            comp_score: Compatibility score for the technology
            all_scores: All compatibility scores sorted by rank
            rank: Rank of this technology (0-based)
            
        Returns:
            ConfidenceLevel indicating confidence in the recommendation
        """
        score = comp_score.score
        
        # For top choice, consider both absolute score and competition
        if rank == 0 and len(all_scores) > 1:
            second_score = all_scores[1].score
            
            if second_score > 0:
                # Calculate percentage gap relative to second place score
                percentage_gap = (score - second_score) / second_score
                
                # Very close competition (within 2% difference) - should be low confidence
                if percentage_gap <= 0.02:
                    return ConfidenceLevel.LOW
                # Close competition (within 5% difference) 
                elif percentage_gap <= 0.05:
                    # If score is very high (>= 0.85), can still have medium confidence
                    if score >= 0.85:
                        return ConfidenceLevel.MEDIUM
                    else:
                        return ConfidenceLevel.LOW
                # Moderate competition (within 15% difference)
                elif percentage_gap <= 0.15:
                    if score >= 0.8:
                        return ConfidenceLevel.HIGH
                    elif score >= 0.6:
                        return ConfidenceLevel.MEDIUM
                    else:
                        return ConfidenceLevel.LOW
                # Significant lead (more than 15% better)
                else:
                    if score >= 0.7:
                        return ConfidenceLevel.HIGH
                    elif score >= 0.5:
                        return ConfidenceLevel.MEDIUM
                    else:
                        return ConfidenceLevel.LOW
            else:
                # If second score is 0, use absolute score
                if score >= 0.8:
                    return ConfidenceLevel.HIGH
                elif score >= 0.6:
                    return ConfidenceLevel.MEDIUM
                else:
                    return ConfidenceLevel.LOW
        
        # For non-top choices or single technology, use absolute score
        if score >= 0.8:
            return ConfidenceLevel.HIGH
        elif score >= 0.6:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    def _generate_detailed_reasoning(
        self,
        technology: TechnologyProfile,
        comp_score: CompatibilityScore,
        weighted_criteria: WeightedCriteria,
        rank: int
    ) -> str:
        """
        Generate detailed reasoning for a technology recommendation.
        
        Args:
            technology: Technology profile
            comp_score: Compatibility score
            weighted_criteria: Weighted criteria
            rank: Rank of this technology (1-based)
            
        Returns:
            Detailed reasoning string
        """
        reasoning_parts = []
        
        # Add rank context
        if rank == 1:
            reasoning_parts.append("Top choice based on compatibility analysis.")
        elif rank == 2:
            reasoning_parts.append("Strong second option with good alignment.")
        else:
            reasoning_parts.append(f"Ranked #{rank} among the compared options.")
        
        # Add score context
        score_percentage = int(comp_score.score * 100)
        reasoning_parts.append(f"Overall compatibility score: {score_percentage}%.")
        
        # Analyze strengths based on high-weighted dimensions
        strengths = []
        weaknesses = []
        
        for dimension, weight in weighted_criteria.dimension_weights.items():
            if dimension in technology.dimensions and weight > 0.2:  # High weight
                dim_score = technology.dimensions[dimension].score
                if dim_score >= 4.0:
                    strengths.append(f"excellent {dimension}")
                elif dim_score <= 2.0:
                    weaknesses.append(f"limited {dimension}")
        
        if strengths:
            reasoning_parts.append(f"Key strengths include {', '.join(strengths)}.")
        
        if weaknesses:
            reasoning_parts.append(f"Areas of concern: {', '.join(weaknesses)}.")
        
        # Add priority alignment
        if weighted_criteria.priority_factors:
            top_priority = weighted_criteria.priority_factors[0]
            reasoning_parts.append(f"Alignment with top priority ({top_priority}) considered in ranking.")
        
        # Add use case fit
        if technology.best_for:
            reasoning_parts.append(f"Best suited for: {technology.best_for[0]}.")
        
        return " ".join(reasoning_parts)
    
    def _identify_decision_factors(
        self,
        technologies: List[TechnologyProfile],
        compatibility_scores: List[CompatibilityScore],
        weighted_criteria: WeightedCriteria
    ) -> List[str]:
        """
        Identify key decision factors that influence the recommendation.
        
        Args:
            technologies: List of technology profiles
            compatibility_scores: Compatibility scores for each technology
            weighted_criteria: Weighted criteria
            
        Returns:
            List of key decision factors
        """
        decision_factors = []
        
        # Add top weighted dimensions as decision factors
        sorted_weights = sorted(
            weighted_criteria.dimension_weights.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Include top 3 weighted dimensions
        for dimension, weight in sorted_weights[:3]:
            if weight > 0.15:  # Significant weight
                decision_factors.append(f"{dimension.title()} requirements (weight: {weight:.1%})")
        
        # Add priority factors
        if weighted_criteria.priority_factors:
            for factor in weighted_criteria.priority_factors[:2]:  # Top 2 priorities
                decision_factors.append(f"Project priority: {factor}")
        
        # Check for close competition
        sorted_scores = sorted(compatibility_scores, key=lambda x: x.score, reverse=True)
        if len(sorted_scores) >= 2:
            gap = sorted_scores[0].score - sorted_scores[1].score
            if gap < 0.1:  # Very close competition
                decision_factors.append("Close competition between top options")
        
        # Ensure we have at least one decision factor
        if not decision_factors:
            decision_factors.append("Overall compatibility with project requirements")
        
        return decision_factors
    
    def _generate_caveats(
        self,
        technologies: List[TechnologyProfile],
        compatibility_scores: List[CompatibilityScore],
        weighted_criteria: WeightedCriteria
    ) -> List[str]:
        """
        Generate caveats and warnings for the recommendation.
        
        Args:
            technologies: List of technology profiles
            compatibility_scores: Compatibility scores for each technology
            weighted_criteria: Weighted criteria
            
        Returns:
            List of caveat strings
        """
        caveats = []
        
        # Check for low overall scores
        max_score = max(score.score for score in compatibility_scores)
        if max_score < 0.6:
            caveats.append("All options show moderate compatibility - consider additional requirements analysis")
        
        # Check for experimental technologies
        tech_lookup = {tech.name: tech for tech in technologies}
        for score in compatibility_scores:
            tech = tech_lookup[score.technology]
            if tech.metadata.maturity.value == "EXPERIMENTAL" and score.score >= 0.7:
                caveats.append(f"{tech.name} is experimental technology - evaluate production readiness carefully")
        
        # Check for conflicting requirements
        high_weight_dims = [
            dim for dim, weight in weighted_criteria.dimension_weights.items()
            if weight > 0.3
        ]
        if len(high_weight_dims) >= 3:
            caveats.append("Multiple high-priority requirements may require trade-off decisions")
        
        # Check for close competition
        sorted_scores = sorted(compatibility_scores, key=lambda x: x.score, reverse=True)
        if len(sorted_scores) >= 2:
            gap = sorted_scores[0].score - sorted_scores[1].score
            if gap < 0.05:
                caveats.append("Top choices are very close - consider team preferences and existing expertise")
        
        # Add general caveat about changing requirements
        caveats.append("Recommendations may change if project requirements or constraints are updated")
        
        return caveats
    
    def _generate_alternative_scenarios(
        self,
        technologies: List[TechnologyProfile],
        compatibility_scores: List[CompatibilityScore],
        weighted_criteria: WeightedCriteria
    ) -> Optional[List[AlternativeScenario]]:
        """
        Generate alternative scenarios for different requirement changes.
        
        Args:
            technologies: List of technology profiles
            compatibility_scores: Compatibility scores for each technology
            weighted_criteria: Weighted criteria
            
        Returns:
            List of AlternativeScenario objects or None if not applicable
        """
        scenarios = []
        tech_lookup = {tech.name: tech for tech in technologies}
        
        # Scenario 1: If budget becomes a major constraint
        budget_focused_tech = None
        best_cost_score = 0
        
        for score in compatibility_scores:
            tech = tech_lookup[score.technology]
            if 'cost' in tech.dimensions:
                # Lower cost score is better, so invert for comparison
                cost_effectiveness = 5.0 - tech.dimensions['cost'].score
                if cost_effectiveness > best_cost_score:
                    best_cost_score = cost_effectiveness
                    budget_focused_tech = tech.name
        
        if budget_focused_tech:
            scenarios.append(AlternativeScenario(
                scenario="If budget becomes the primary constraint",
                recommended_tech=budget_focused_tech,
                explanation="This option offers the best cost-effectiveness for the project requirements"
            ))
        
        # Scenario 2: If scalability becomes critical
        scalability_focused_tech = None
        best_scale_score = 0
        
        for score in compatibility_scores:
            tech = tech_lookup[score.technology]
            if 'scalability' in tech.dimensions:
                scale_score = tech.dimensions['scalability'].score
                if scale_score > best_scale_score:
                    best_scale_score = scale_score
                    scalability_focused_tech = tech.name
        
        if scalability_focused_tech and scalability_focused_tech != compatibility_scores[0].technology:
            scenarios.append(AlternativeScenario(
                scenario="If scalability becomes the top priority",
                recommended_tech=scalability_focused_tech,
                explanation="This option provides the strongest scalability capabilities"
            ))
        
        # Scenario 3: If team expertise is limited
        simplicity_focused_tech = None
        best_simplicity_score = 6.0  # Start high since lower complexity is better
        
        for score in compatibility_scores:
            tech = tech_lookup[score.technology]
            if 'complexity' in tech.dimensions:
                complexity_score = tech.dimensions['complexity'].score
                if complexity_score < best_simplicity_score:
                    best_simplicity_score = complexity_score
                    simplicity_focused_tech = tech.name
        
        if simplicity_focused_tech and simplicity_focused_tech != compatibility_scores[0].technology:
            scenarios.append(AlternativeScenario(
                scenario="If team expertise is limited or learning curve is a concern",
                recommended_tech=simplicity_focused_tech,
                explanation="This option offers the lowest complexity and easiest learning curve"
            ))
        
        return scenarios if scenarios else None