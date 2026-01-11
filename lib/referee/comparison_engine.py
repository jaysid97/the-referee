"""
Comparison engine for The Referee technology comparison tool.

This module provides the ComparisonEngine class that orchestrates the comparison
process by combining technology profiles with weighted requirements to generate
structured comparisons and trade-off matrices.
"""

from typing import Dict, List, Optional, Tuple
from referee.models import (
    TechnologyProfile,
    WeightedCriteria,
    TradeoffMatrix,
    TradeoffHighlight,
    CompatibilityScore
)


class ComparisonError(Exception):
    """Raised when comparison generation fails."""
    pass


class InsufficientDataError(Exception):
    """Raised when there's insufficient data for meaningful comparison."""
    pass


class ComparisonEngine:
    """
    Orchestrates the comparison process by combining technology profiles with weighted requirements.
    
    Provides functionality to:
    - Generate side-by-side comparisons with pros/cons analysis
    - Create trade-off matrices with dimensional scoring
    - Calculate compatibility scores between technologies and requirements
    - Support custom dimensions integration
    """
    
    def __init__(self):
        """Initialize the comparison engine."""
        pass
    
    def generate_comparison(
        self, 
        technologies: List[TechnologyProfile], 
        weighted_criteria: WeightedCriteria,
        custom_dimensions: Optional[List[str]] = None
    ) -> Dict[str, any]:
        """
        Generate a comprehensive comparison of technologies based on weighted criteria.
        
        Args:
            technologies: List of technology profiles to compare
            weighted_criteria: Weighted criteria based on project requirements
            custom_dimensions: Optional list of custom dimensions to include
            
        Returns:
            Dictionary containing comparison results with technologies, matrix, and scores
            
        Raises:
            ComparisonError: If comparison cannot be generated
            InsufficientDataError: If there's insufficient data for meaningful comparison
        """
        # Validate inputs
        self._validate_comparison_inputs(technologies, weighted_criteria, custom_dimensions)
        
        try:
            # Create trade-off matrix with error handling
            dimensions = self._get_comparison_dimensions(technologies, custom_dimensions)
            tradeoff_matrix = self.create_tradeoff_matrix(technologies, dimensions)
            
            # Calculate compatibility scores for each technology with fallback
            compatibility_scores = []
            for tech in technologies:
                try:
                    score = self.calculate_compatibility(tech, weighted_criteria)
                    compatibility_scores.append(score)
                except Exception as e:
                    # Create fallback score if calculation fails
                    fallback_score = self._create_fallback_compatibility_score(tech, str(e))
                    compatibility_scores.append(fallback_score)
            
            # Generate side-by-side comparison data
            comparison_data = self._generate_side_by_side_data(technologies)
            
            return {
                'technologies': [tech.name for tech in technologies],
                'comparison_data': comparison_data,
                'tradeoff_matrix': tradeoff_matrix,
                'compatibility_scores': compatibility_scores,
                'weighted_criteria': weighted_criteria
            }
            
        except Exception as e:
            raise ComparisonError(f"Failed to generate comparison: {str(e)}") from e
    
    def create_tradeoff_matrix(
        self, 
        technologies: List[TechnologyProfile], 
        dimensions: List[str]
    ) -> TradeoffMatrix:
        """
        Create a trade-off matrix showing technology comparisons across dimensions.
        
        Args:
            technologies: List of technology profiles
            dimensions: List of dimensions to compare across
            
        Returns:
            TradeoffMatrix with scores, explanations, and highlights
            
        Raises:
            ComparisonError: If matrix creation fails
        """
        try:
            self._validate_matrix_inputs(technologies, dimensions)
            
            tech_names = [tech.name for tech in technologies]
            
            # Build scores and explanations matrices with error handling
            scores = []
            explanations = []
            
            for tech in technologies:
                tech_scores = []
                tech_explanations = []
                
                for dimension in dimensions:
                    try:
                        if dimension in tech.dimensions:
                            # Standard dimension from technology profile
                            dim_score = tech.dimensions[dimension]
                            tech_scores.append(dim_score.score)
                            tech_explanations.append(dim_score.explanation)
                        else:
                            # Custom dimension - use default scoring
                            tech_scores.append(3.0)  # Neutral score
                            tech_explanations.append(f"No specific data available for {dimension}")
                    except Exception as e:
                        # Fallback for any dimension scoring errors
                        tech_scores.append(2.5)  # Slightly below neutral
                        tech_explanations.append(f"Error evaluating {dimension}: {str(e)}")
                
                scores.append(tech_scores)
                explanations.append(tech_explanations)
            
            # Identify key differentiators (highlights) with error handling
            try:
                highlights = self._identify_highlights(technologies, dimensions, scores)
            except Exception as e:
                # Fallback to empty highlights if identification fails
                highlights = []
            
            return TradeoffMatrix(
                technologies=tech_names,
                dimensions=dimensions,
                scores=scores,
                explanations=explanations,
                highlights=highlights
            )
            
        except Exception as e:
            raise ComparisonError(f"Failed to create trade-off matrix: {str(e)}") from e
    
    def calculate_compatibility(
        self, 
        technology: TechnologyProfile, 
        weighted_criteria: WeightedCriteria
    ) -> CompatibilityScore:
        """
        Calculate compatibility score between a technology and project requirements.
        
        Args:
            technology: Technology profile to evaluate
            weighted_criteria: Weighted criteria based on project requirements
            
        Returns:
            CompatibilityScore with overall score and reasoning
            
        Raises:
            ComparisonError: If compatibility calculation fails
        """
        try:
            # Validate inputs
            if not technology or not weighted_criteria:
                raise ValueError("Technology and weighted criteria must be provided")
            
            if not weighted_criteria.dimension_weights:
                raise ValueError("Weighted criteria must contain dimension weights")
            
            # Calculate weighted score across all dimensions
            total_weighted_score = 0.0
            total_weight = 0.0
            dimension_contributions = []
            
            for dimension, weight in weighted_criteria.dimension_weights.items():
                if weight <= 0:
                    continue  # Skip dimensions with zero or negative weight
                
                try:
                    if dimension in technology.dimensions:
                        dim_score = technology.dimensions[dimension].score
                        # Normalize score to 0-1 range (assuming scores are 0-5)
                        normalized_score = max(0, min(1, dim_score / 5.0))
                        weighted_contribution = normalized_score * weight
                        total_weighted_score += weighted_contribution
                        total_weight += weight
                        
                        dimension_contributions.append({
                            'dimension': dimension,
                            'score': dim_score,
                            'weight': weight,
                            'contribution': weighted_contribution
                        })
                    else:
                        # Missing dimension - use neutral score with reduced weight
                        neutral_score = 0.5  # Neutral in 0-1 range
                        weighted_contribution = neutral_score * weight * 0.5  # Reduce impact
                        total_weighted_score += weighted_contribution
                        total_weight += weight * 0.5
                        
                        dimension_contributions.append({
                            'dimension': dimension,
                            'score': 2.5,  # Neutral in 0-5 range
                            'weight': weight,
                            'contribution': weighted_contribution
                        })
                except Exception as e:
                    # Skip this dimension if there's an error, but log it
                    continue
            
            # Normalize by total weight to get final score
            if total_weight > 0:
                final_score = total_weighted_score / total_weight
            else:
                # Fallback if no valid weights
                final_score = 0.5  # Neutral score
            
            # Generate reasoning based on top contributing factors
            reasoning = self._generate_compatibility_reasoning(
                technology, dimension_contributions, weighted_criteria, final_score
            )
            
            return CompatibilityScore(
                technology=technology.name,
                score=max(0, min(1, final_score)),  # Ensure score is in valid range
                reasoning=reasoning
            )
            
        except Exception as e:
            raise ComparisonError(f"Failed to calculate compatibility for {technology.name}: {str(e)}") from e
    
    def _get_comparison_dimensions(
        self, 
        technologies: List[TechnologyProfile], 
        custom_dimensions: Optional[List[str]] = None
    ) -> List[str]:
        """
        Get the list of dimensions to use for comparison.
        
        Args:
            technologies: List of technology profiles
            custom_dimensions: Optional custom dimensions to include
            
        Returns:
            List of dimension names for comparison
        """
        # Start with standard dimensions
        standard_dimensions = ['cost', 'scalability', 'complexity', 'ecosystem', 'performance']
        
        # Add custom dimensions if provided
        dimensions = standard_dimensions.copy()
        if custom_dimensions:
            # Validate that custom dimensions don't conflict with standard ones
            conflicts = set(custom_dimensions) & set(standard_dimensions)
            if conflicts:
                raise ValueError(f"Custom dimensions conflict with standard dimensions: {conflicts}")
            
            dimensions.extend(custom_dimensions)
        
        return dimensions
    
    def _generate_side_by_side_data(self, technologies: List[TechnologyProfile]) -> Dict[str, any]:
        """
        Generate side-by-side comparison data for technologies.
        
        Args:
            technologies: List of technology profiles
            
        Returns:
            Dictionary with structured comparison data
        """
        comparison_data = {}
        
        for tech in technologies:
            comparison_data[tech.name] = {
                'category': tech.category,
                'pros': tech.pros,
                'cons': tech.cons,
                'best_for': tech.best_for,
                'dimensions': {
                    dim_name: {
                        'score': dim_score.score,
                        'explanation': dim_score.explanation
                    }
                    for dim_name, dim_score in tech.dimensions.items()
                },
                'metadata': {
                    'maturity': tech.metadata.maturity.value,
                    'license': tech.metadata.license,
                    'maintainer': tech.metadata.maintainer
                }
            }
        
        return comparison_data
    
    def _identify_highlights(
        self, 
        technologies: List[TechnologyProfile], 
        dimensions: List[str], 
        scores: List[List[float]]
    ) -> List[TradeoffHighlight]:
        """
        Identify key differentiators (highlights) in the trade-off matrix.
        
        Args:
            technologies: List of technology profiles
            dimensions: List of dimension names
            scores: 2D array of scores [tech_index][dimension_index]
            
        Returns:
            List of TradeoffHighlight objects showing key differentiators
        """
        highlights = []
        
        # For each dimension, find the technology with the highest score
        # and check if it's significantly better than others
        for dim_idx, dimension in enumerate(dimensions):
            dim_scores = [scores[tech_idx][dim_idx] for tech_idx in range(len(technologies))]
            
            # Find max score and corresponding technology
            max_score = max(dim_scores)
            max_tech_idx = dim_scores.index(max_score)
            leader_tech = technologies[max_tech_idx].name
            
            # Check if this is a significant lead (at least 0.5 points better than second best)
            sorted_scores = sorted(dim_scores, reverse=True)
            if len(sorted_scores) > 1 and (sorted_scores[0] - sorted_scores[1]) >= 0.5:
                # Get explanation from the leading technology's profile
                if dimension in technologies[max_tech_idx].dimensions:
                    explanation = technologies[max_tech_idx].dimensions[dimension].explanation
                else:
                    explanation = f"Leads in {dimension} with score of {max_score:.1f}"
                
                highlights.append(TradeoffHighlight(
                    dimension=dimension,
                    leader=leader_tech,
                    explanation=explanation
                ))
        
        return highlights
    
    def _validate_comparison_inputs(
        self,
        technologies: List[TechnologyProfile],
        weighted_criteria: WeightedCriteria,
        custom_dimensions: Optional[List[str]]
    ) -> None:
        """
        Validate inputs for comparison generation.
        
        Args:
            technologies: List of technology profiles
            weighted_criteria: Weighted criteria
            custom_dimensions: Optional custom dimensions
            
        Raises:
            ValueError: If inputs are invalid
            InsufficientDataError: If there's insufficient data
        """
        if not technologies:
            raise ValueError("At least one technology must be provided for comparison")
        
        if len(technologies) < 2:
            raise ValueError("At least two technologies must be provided for comparison")
        
        if len(technologies) > 5:
            raise ValueError("Maximum of 5 technologies can be compared simultaneously")
        
        if not weighted_criteria or not weighted_criteria.dimension_weights:
            raise InsufficientDataError("Weighted criteria with dimension weights must be provided")
        
        # Check if technologies have sufficient data
        insufficient_data_count = 0
        for tech in technologies:
            if not tech.dimensions or len(tech.dimensions) < 3:
                insufficient_data_count += 1
        
        if insufficient_data_count > len(technologies) / 2:
            raise InsufficientDataError(
                f"More than half of the technologies ({insufficient_data_count}/{len(technologies)}) "
                "have insufficient dimension data for meaningful comparison"
            )
    
    def _validate_matrix_inputs(
        self,
        technologies: List[TechnologyProfile],
        dimensions: List[str]
    ) -> None:
        """
        Validate inputs for matrix creation.
        
        Args:
            technologies: List of technology profiles
            dimensions: List of dimensions
            
        Raises:
            ValueError: If inputs are invalid
        """
        if not technologies:
            raise ValueError("At least one technology must be provided")
        
        if not dimensions:
            raise ValueError("At least one dimension must be provided")
        
        if len(dimensions) > 10:
            raise ValueError("Maximum of 10 dimensions can be compared simultaneously")
    
    def _create_fallback_compatibility_score(
        self,
        technology: TechnologyProfile,
        error_message: str
    ) -> CompatibilityScore:
        """
        Create a fallback compatibility score when calculation fails.
        
        Args:
            technology: Technology profile
            error_message: Error that occurred during calculation
            
        Returns:
            CompatibilityScore with neutral score and error explanation
        """
        return CompatibilityScore(
            technology=technology.name,
            score=0.5,  # Neutral score
            reasoning=f"Compatibility calculation failed ({error_message}). Using neutral score for comparison."
        )
    
    def _generate_compatibility_reasoning(
        self,
        technology: TechnologyProfile,
        dimension_contributions: List[Dict],
        weighted_criteria: WeightedCriteria,
        final_score: float
    ) -> str:
        """
        Generate reasoning for compatibility score.
        
        Args:
            technology: Technology profile
            dimension_contributions: List of dimension contribution data
            weighted_criteria: Weighted criteria
            final_score: Final calculated score
            
        Returns:
            Reasoning string explaining the score
        """
        reasoning_parts = []
        
        # Add score context
        score_percentage = int(final_score * 100)
        reasoning_parts.append(f"Overall compatibility: {score_percentage}%")
        
        # Sort by contribution to identify most important factors
        dimension_contributions.sort(key=lambda x: x['contribution'], reverse=True)
        
        # Highlight top contributing dimensions (up to 3)
        top_contributions = dimension_contributions[:3]
        strengths = []
        weaknesses = []
        
        for contrib in top_contributions:
            dim_name = contrib['dimension']
            score = contrib['score']
            weight = contrib['weight']
            
            if weight > 0.2:  # Significant weight
                if score >= 4.0:
                    strengths.append(f"excellent {dim_name}")
                elif score <= 2.0:
                    weaknesses.append(f"limited {dim_name}")
        
        if strengths:
            reasoning_parts.append(f"Key strengths: {', '.join(strengths)}")
        
        if weaknesses:
            reasoning_parts.append(f"Areas of concern: {', '.join(weaknesses)}")
        
        # Add priority alignment if available
        if weighted_criteria.priority_factors:
            top_priority = weighted_criteria.priority_factors[0]
            reasoning_parts.append(f"Evaluated against priority: {top_priority}")
        
        return ". ".join(reasoning_parts) if reasoning_parts else "Standard evaluation across all dimensions"