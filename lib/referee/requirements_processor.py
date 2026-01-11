"""
Requirements processor for The Referee technology comparison tool.

This module provides the RequirementsProcessor class that converts project
requirements and constraints into weighted criteria for technology comparison.
"""

from typing import Dict, List
from referee.models import (
    ProjectRequirements,
    WeightedCriteria,
    BudgetLevel,
    TimelineLevel,
    ScaleLevel,
    ExpertiseLevel
)


class RequirementsProcessingError(Exception):
    """Raised when requirements processing fails."""
    pass


class ConflictingRequirementsError(Exception):
    """Raised when project requirements contain conflicts."""
    
    def __init__(self, conflicts: List[str]):
        self.conflicts = conflicts
        message = f"Conflicting requirements detected: {'; '.join(conflicts)}"
        super().__init__(message)


class RequirementsProcessor:
    """
    Processes project requirements and converts them into weighted criteria.
    
    Maps project constraints to dimension weights:
    - Budget constraints → cost sensitivity weights
    - Timeline pressure → complexity/learning curve weights  
    - Scalability needs → performance dimension weights
    - Team expertise → complexity tolerance weights
    """
    
    def __init__(self):
        """Initialize the requirements processor."""
        pass
    
    def process_requirements(self, requirements: ProjectRequirements) -> WeightedCriteria:
        """
        Convert project requirements into weighted criteria for comparison.
        
        Args:
            requirements: Project requirements and constraints
            
        Returns:
            WeightedCriteria with dimension weights and priority factors
            
        Raises:
            RequirementsProcessingError: If processing fails
            ConflictingRequirementsError: If requirements contain conflicts
        """
        try:
            # Validate requirements first
            self._validate_requirements(requirements)
            
            # Check for conflicting requirements
            conflicts = self._detect_requirement_conflicts(requirements)
            if conflicts:
                raise ConflictingRequirementsError(conflicts)
            
            # Calculate base weights for all dimensions
            dimension_weights = self._calculate_dimension_weights(requirements)
            
            # Identify priority factors based on requirements
            priority_factors = self._identify_priority_factors(requirements)
            
            # Validate the resulting weights
            self._validate_weights(dimension_weights)
            
            return WeightedCriteria(
                dimension_weights=dimension_weights,
                priority_factors=priority_factors
            )
            
        except ConflictingRequirementsError:
            # Re-raise conflicts as-is
            raise
        except Exception as e:
            raise RequirementsProcessingError(f"Failed to process requirements: {str(e)}") from e
    
    def _calculate_dimension_weights(self, requirements: ProjectRequirements) -> Dict[str, float]:
        """
        Calculate weights for each dimension based on project requirements.
        
        Args:
            requirements: Project requirements and constraints
            
        Returns:
            Dictionary mapping dimension names to weights (0-1)
        """
        # Start with base weights (all dimensions equally important)
        base_weight = 0.2
        weights = {
            'cost': base_weight,
            'scalability': base_weight,
            'complexity': base_weight,
            'ecosystem': base_weight,
            'performance': base_weight
        }
        
        # Track which dimensions should be highlighted and their boost amounts
        dimension_boosts = {}
        
        # Budget constraints affect cost dimension
        if requirements.budget == BudgetLevel.LOW:
            dimension_boosts['cost'] = 0.15  # Strong emphasis on cost
        elif requirements.budget == BudgetLevel.MEDIUM:
            dimension_boosts['cost'] = 0.05  # Moderate emphasis on cost
        elif requirements.budget == BudgetLevel.HIGH:
            dimension_boosts['cost'] = -0.03  # De-emphasize cost
        
        # Timeline constraints affect complexity dimension
        if requirements.timeline == TimelineLevel.TIGHT:
            dimension_boosts['complexity'] = 0.15  # Strong emphasis on simplicity
        elif requirements.timeline == TimelineLevel.MODERATE:
            dimension_boosts['complexity'] = 0.06  # Moderate emphasis on simplicity
        elif requirements.timeline == TimelineLevel.FLEXIBLE:
            dimension_boosts['complexity'] = -0.06  # Less emphasis on simplicity
        
        # Expertise level modifies complexity boost
        if requirements.expertise_level == ExpertiseLevel.BEGINNER:
            current_complexity_boost = dimension_boosts.get('complexity', 0)
            dimension_boosts['complexity'] = current_complexity_boost + 0.10  # Beginners need simpler solutions
        elif requirements.expertise_level == ExpertiseLevel.EXPERT:
            current_complexity_boost = dimension_boosts.get('complexity', 0)
            dimension_boosts['complexity'] = current_complexity_boost - 0.05  # Experts can handle complexity
        
        # Scalability needs affect scalability and performance dimensions
        if requirements.scalability_needs == ScaleLevel.LARGE:
            dimension_boosts['scalability'] = 0.18  # Strong emphasis on scalability
            dimension_boosts['performance'] = 0.18   # Strong emphasis on performance (increased)
        elif requirements.scalability_needs == ScaleLevel.MEDIUM:
            dimension_boosts['scalability'] = 0.06  # Moderate emphasis
            dimension_boosts['performance'] = 0.05   # Moderate emphasis
        elif requirements.scalability_needs == ScaleLevel.SMALL:
            dimension_boosts['scalability'] = -0.04  # De-emphasize scalability
            dimension_boosts['performance'] = -0.03   # De-emphasize performance
        
        # Team characteristics affect ecosystem dimension
        # Larger teams benefit more from mature ecosystems
        size_boost = requirements.team_size * 0.015  # No cap, linear scaling
        
        # Less experienced teams need better ecosystem support
        if requirements.expertise_level == ExpertiseLevel.BEGINNER:
            expertise_ecosystem_boost = 0.12  # Need strong ecosystem support
        elif requirements.expertise_level == ExpertiseLevel.INTERMEDIATE:
            expertise_ecosystem_boost = 0.04  # Some ecosystem support helpful
        else:  # EXPERT
            expertise_ecosystem_boost = -0.04  # Can work with smaller ecosystems
        
        dimension_boosts['ecosystem'] = size_boost + expertise_ecosystem_boost
        
        # Apply boosts to base weights
        for dimension, boost in dimension_boosts.items():
            weights[dimension] += boost
        
        # Ensure no weight goes below 0.05 (minimum viable weight)
        for dimension in weights:
            weights[dimension] = max(0.05, weights[dimension])
        
        # Normalize weights to ensure they sum to 1.0
        total_weight = sum(weights.values())
        normalized_weights = {dim: weight / total_weight for dim, weight in weights.items()}
        
        # Final check: ensure the most important highlighted dimensions are above baseline
        baseline_threshold = 0.2
        highlighted_dimensions = [(dim, boost) for dim, boost in dimension_boosts.items() if boost > 0.02]
        
        # Sort by boost amount (most important first)
        highlighted_dimensions.sort(key=lambda x: x[1], reverse=True)
        
        # Special handling for scalability constraints - they should be prioritized even with competing constraints
        scalability_needs_large = requirements.scalability_needs == ScaleLevel.LARGE
        if scalability_needs_large:
            # Count competing high-priority constraints
            competing_high_priority = 0
            if requirements.budget == BudgetLevel.LOW:
                competing_high_priority += 1
            if requirements.timeline == TimelineLevel.TIGHT:
                competing_high_priority += 1
            if requirements.expertise_level == ExpertiseLevel.BEGINNER:
                competing_high_priority += 1
            
            # If there are many competing constraints, ensure at least one of scalability/performance is in top 3
            if competing_high_priority >= 2:
                # Force at least one of scalability or performance into top 3
                sorted_weights = sorted(normalized_weights.items(), key=lambda x: x[1], reverse=True)
                scalability_rank = next(i for i, (dim, _) in enumerate(sorted_weights) if dim == 'scalability')
                performance_rank = next(i for i, (dim, _) in enumerate(sorted_weights) if dim == 'performance')
                
                if min(scalability_rank, performance_rank) > 2:
                    # Neither is in top 3, boost the higher one
                    target_dim = 'scalability' if normalized_weights['scalability'] >= normalized_weights['performance'] else 'performance'
                    
                    # Find the 3rd highest weight and boost target above it
                    third_highest_weight = sorted_weights[2][1]
                    target_weight = third_highest_weight + 0.01
                    current_weight = normalized_weights[target_dim]
                    needed_boost = target_weight - current_weight
                    
                    # Take the boost from the lowest weighted dimensions
                    sorted_by_weight = sorted(normalized_weights.items(), key=lambda x: x[1])
                    remaining_boost = needed_boost
                    
                    for dim, weight in sorted_by_weight:
                        if dim != target_dim and remaining_boost > 0:
                            available_reduction = max(0, weight - 0.05)  # Don't go below 0.05
                            reduction = min(remaining_boost, available_reduction)
                            normalized_weights[dim] -= reduction
                            remaining_boost -= reduction
                            if remaining_boost <= 0:
                                break
                    
                    normalized_weights[target_dim] = target_weight
                    
                    # Re-normalize to ensure sum = 1.0
                    total = sum(normalized_weights.values())
                    normalized_weights = {dim: weight / total for dim, weight in normalized_weights.items()}
        
        # Try to ensure the top highlighted dimensions are above baseline
        # But we can only guarantee this for a reasonable number of dimensions
        max_highlights = min(3, len(highlighted_dimensions))  # At most 3 can be significantly above baseline
        
        for i, (dimension, boost) in enumerate(highlighted_dimensions[:max_highlights]):
            if normalized_weights[dimension] <= baseline_threshold:
                # This dimension should be highlighted but isn't - force it above baseline
                target_weight = baseline_threshold + 0.01
                current_weight = normalized_weights[dimension]
                needed_boost = target_weight - current_weight
                
                # Take the needed boost from non-highlighted dimensions first
                non_highlighted = [d for d in normalized_weights 
                                 if d not in [dim for dim, _ in highlighted_dimensions[:max_highlights]]]
                
                if non_highlighted:
                    total_non_highlighted_weight = sum(normalized_weights[d] for d in non_highlighted)
                    if total_non_highlighted_weight > needed_boost:
                        for other_dim in non_highlighted:
                            reduction_ratio = normalized_weights[other_dim] / total_non_highlighted_weight
                            reduction = needed_boost * reduction_ratio
                            normalized_weights[other_dim] = max(0.05, normalized_weights[other_dim] - reduction)
                        
                        normalized_weights[dimension] = target_weight
                        
                        # Re-normalize to ensure sum = 1.0
                        total = sum(normalized_weights.values())
                        normalized_weights = {dim: weight / total for dim, weight in normalized_weights.items()}
        
        return normalized_weights
    
    def _calculate_cost_weight_adjustment(self, budget: BudgetLevel) -> float:
        """
        Calculate cost dimension weight adjustment based on budget constraints.
        
        Args:
            budget: Budget constraint level
            
        Returns:
            Weight adjustment for cost dimension (-0.1 to +0.3)
        """
        if budget == BudgetLevel.LOW:
            return 0.3  # High cost sensitivity
        elif budget == BudgetLevel.MEDIUM:
            return 0.1  # Moderate cost sensitivity
        else:  # HIGH budget
            return -0.1  # Lower cost sensitivity
    
    def _calculate_complexity_weight_adjustment(
        self, 
        timeline: TimelineLevel, 
        expertise: ExpertiseLevel
    ) -> float:
        """
        Calculate complexity dimension weight adjustment based on timeline and expertise.
        
        Args:
            timeline: Timeline constraint level
            expertise: Team expertise level
            
        Returns:
            Weight adjustment for complexity dimension (-0.2 to +0.4)
        """
        # Base adjustment from timeline pressure
        timeline_adjustment = {
            TimelineLevel.TIGHT: 0.3,    # High complexity sensitivity
            TimelineLevel.MODERATE: 0.1, # Moderate complexity sensitivity
            TimelineLevel.FLEXIBLE: -0.1 # Lower complexity sensitivity
        }[timeline]
        
        # Expertise level modifier
        expertise_modifier = {
            ExpertiseLevel.BEGINNER: 0.1,     # Beginners need simpler solutions
            ExpertiseLevel.INTERMEDIATE: 0.0, # No adjustment
            ExpertiseLevel.EXPERT: -0.1       # Experts can handle complexity
        }[expertise]
        
        return timeline_adjustment + expertise_modifier
    
    def _calculate_scalability_weight_adjustment(self, scalability_needs: ScaleLevel) -> float:
        """
        Calculate scalability dimension weight adjustment based on scale requirements.
        
        Args:
            scalability_needs: Required scalability level
            
        Returns:
            Weight adjustment for scalability dimension (-0.1 to +0.3)
        """
        if scalability_needs == ScaleLevel.LARGE:
            return 0.3  # High scalability importance
        elif scalability_needs == ScaleLevel.MEDIUM:
            return 0.1  # Moderate scalability importance
        else:  # SMALL scale
            return -0.1  # Lower scalability importance
    
    def _calculate_ecosystem_weight_adjustment(
        self, 
        team_size: int, 
        expertise: ExpertiseLevel
    ) -> float:
        """
        Calculate ecosystem dimension weight adjustment based on team characteristics.
        
        Args:
            team_size: Number of team members
            expertise: Team expertise level
            
        Returns:
            Weight adjustment for ecosystem dimension (-0.1 to +0.2)
        """
        # Larger teams benefit more from mature ecosystems
        size_adjustment = min(0.1, team_size * 0.02)  # Cap at 0.1
        
        # Less experienced teams need better ecosystem support
        expertise_adjustment = {
            ExpertiseLevel.BEGINNER: 0.1,     # Need strong ecosystem support
            ExpertiseLevel.INTERMEDIATE: 0.05, # Some ecosystem support helpful
            ExpertiseLevel.EXPERT: -0.05      # Can work with smaller ecosystems
        }[expertise]
        
        return size_adjustment + expertise_adjustment
    
    def _identify_priority_factors(self, requirements: ProjectRequirements) -> List[str]:
        """
        Identify priority factors based on project requirements.
        
        Args:
            requirements: Project requirements and constraints
            
        Returns:
            List of priority factors in order of importance
        """
        factors = []
        
        # Budget-driven priorities
        if requirements.budget == BudgetLevel.LOW:
            factors.append("Cost optimization and budget constraints")
            factors.append("Open-source solutions preferred")
        elif requirements.budget == BudgetLevel.MEDIUM:
            factors.append("Balanced cost considerations")
        
        # Timeline-driven priorities
        if requirements.timeline == TimelineLevel.TIGHT:
            factors.append("Rapid development and deployment")
            factors.append("Minimal learning curve required")
            factors.append("Simple implementation approach")
        elif requirements.timeline == TimelineLevel.MODERATE:
            factors.append("Reasonable learning curve acceptable")
        
        # Scale-driven priorities
        if requirements.scalability_needs == ScaleLevel.LARGE:
            factors.append("Horizontal scalability requirements")
            factors.append("High performance optimization")
            factors.append("Enterprise-grade reliability")
        elif requirements.scalability_needs == ScaleLevel.MEDIUM:
            factors.append("Moderate scalability needs")
            factors.append("Performance considerations")
        
        # Team and expertise-driven priorities
        if requirements.team_size >= 5:
            factors.append("Team collaboration features")
            factors.append("Mature tooling ecosystem")
        
        if requirements.expertise_level == ExpertiseLevel.BEGINNER:
            factors.append("Strong ecosystem and community support")
            factors.append("Comprehensive documentation needed")
            factors.append("Gentle learning curve essential")
        elif requirements.expertise_level == ExpertiseLevel.INTERMEDIATE:
            factors.append("Good community support helpful")
        elif requirements.expertise_level == ExpertiseLevel.EXPERT:
            factors.append("Advanced customization capabilities")
            factors.append("Cutting-edge features available")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_factors = []
        for factor in factors:
            if factor not in seen:
                seen.add(factor)
                unique_factors.append(factor)
        
        return unique_factors
    
    def calculate_weights(self, constraints: Dict[str, any]) -> Dict[str, float]:
        """
        Calculate dimension weights from raw constraint dictionary.
        
        This is a convenience method for when constraints are provided
        as a dictionary rather than a ProjectRequirements object.
        
        Args:
            constraints: Dictionary of constraint values
            
        Returns:
            Dictionary mapping dimension names to weights
        """
        # Convert constraints dict to ProjectRequirements
        requirements = ProjectRequirements(
            team_size=constraints.get('team_size', 3),
            budget=BudgetLevel(constraints.get('budget', 'MEDIUM')),
            timeline=TimelineLevel(constraints.get('timeline', 'MODERATE')),
            scalability_needs=ScaleLevel(constraints.get('scalability_needs', 'MEDIUM')),
            expertise_level=ExpertiseLevel(constraints.get('expertise_level', 'INTERMEDIATE'))
        )
        
        weighted_criteria = self.process_requirements(requirements)
        return weighted_criteria.dimension_weights
    
    def _validate_requirements(self, requirements: ProjectRequirements) -> None:
        """
        Validate project requirements for consistency and reasonableness.
        
        Args:
            requirements: Project requirements to validate
            
        Raises:
            ValueError: If requirements are invalid
        """
        if not requirements:
            raise ValueError("Requirements must be provided")
        
        # Validate team size
        if requirements.team_size < 1:
            raise ValueError(f"Team size must be at least 1, got {requirements.team_size}")
        
        if requirements.team_size > 1000:
            raise ValueError(f"Team size seems unreasonably large: {requirements.team_size}")
        
        # Validate enum values (should be caught by Pydantic, but double-check)
        valid_budgets = {level.value for level in BudgetLevel}
        if requirements.budget.value not in valid_budgets:
            raise ValueError(f"Invalid budget level: {requirements.budget}")
        
        valid_timelines = {level.value for level in TimelineLevel}
        if requirements.timeline.value not in valid_timelines:
            raise ValueError(f"Invalid timeline level: {requirements.timeline}")
        
        valid_scales = {level.value for level in ScaleLevel}
        if requirements.scalability_needs.value not in valid_scales:
            raise ValueError(f"Invalid scalability level: {requirements.scalability_needs}")
        
        valid_expertise = {level.value for level in ExpertiseLevel}
        if requirements.expertise_level.value not in valid_expertise:
            raise ValueError(f"Invalid expertise level: {requirements.expertise_level}")
    
    def _detect_requirement_conflicts(self, requirements: ProjectRequirements) -> List[str]:
        """
        Detect conflicting requirements that may lead to poor recommendations.
        
        Args:
            requirements: Project requirements to check
            
        Returns:
            List of conflict descriptions (empty if no conflicts)
        """
        conflicts = []
        
        # Conflict 1: Low budget + Large scale + Tight timeline
        if (requirements.budget == BudgetLevel.LOW and 
            requirements.scalability_needs == ScaleLevel.LARGE and 
            requirements.timeline == TimelineLevel.TIGHT):
            conflicts.append(
                "Low budget, large scalability needs, and tight timeline create competing priorities"
            )
        
        # Conflict 2: Beginner expertise + Tight timeline + Large scale
        if (requirements.expertise_level == ExpertiseLevel.BEGINNER and
            requirements.timeline == TimelineLevel.TIGHT and
            requirements.scalability_needs == ScaleLevel.LARGE):
            conflicts.append(
                "Beginner expertise with tight timeline and large scale requirements may be unrealistic"
            )
        
        # Conflict 3: Low budget + Expert team (might be wasteful)
        if (requirements.budget == BudgetLevel.LOW and
            requirements.expertise_level == ExpertiseLevel.EXPERT and
            requirements.team_size >= 5):
            conflicts.append(
                "Low budget with large expert team suggests potential resource mismatch"
            )
        
        # Conflict 4: Small scale + Large team (over-engineering risk)
        if (requirements.scalability_needs == ScaleLevel.SMALL and
            requirements.team_size >= 8):
            conflicts.append(
                "Small scalability needs with large team may lead to over-engineering"
            )
        
        # Conflict 5: High budget + Tight timeline (rushed expensive project)
        if (requirements.budget == BudgetLevel.HIGH and
            requirements.timeline == TimelineLevel.TIGHT and
            requirements.expertise_level == ExpertiseLevel.BEGINNER):
            conflicts.append(
                "High budget with tight timeline and beginner team may indicate poor planning"
            )
        
        return conflicts
    
    def _validate_weights(self, weights: Dict[str, float]) -> None:
        """
        Validate that calculated weights are reasonable.
        
        Args:
            weights: Dictionary of dimension weights
            
        Raises:
            ValueError: If weights are invalid
        """
        if not weights:
            raise ValueError("Weights dictionary cannot be empty")
        
        required_dimensions = {'cost', 'scalability', 'complexity', 'ecosystem', 'performance'}
        missing_dimensions = required_dimensions - set(weights.keys())
        if missing_dimensions:
            raise ValueError(f"Missing required dimensions in weights: {missing_dimensions}")
        
        # Check individual weight values
        for dimension, weight in weights.items():
            if not isinstance(weight, (int, float)):
                raise ValueError(f"Weight for {dimension} must be numeric, got {type(weight)}")
            
            if not (0 <= weight <= 1):
                raise ValueError(f"Weight for {dimension} must be between 0 and 1, got {weight}")
        
        # Check that weights sum to approximately 1.0 (allow small floating point errors)
        total_weight = sum(weights.values())
        if not (0.95 <= total_weight <= 1.05):
            raise ValueError(f"Weights must sum to approximately 1.0, got {total_weight}")
        
        # Check that no single dimension dominates too much (> 60%)
        max_weight = max(weights.values())
        if max_weight > 0.6:
            dominant_dimension = next(dim for dim, weight in weights.items() if weight == max_weight)
            raise ValueError(
                f"Dimension '{dominant_dimension}' has excessive weight ({max_weight:.1%}). "
                "No single dimension should exceed 60% to ensure balanced comparison."
            )
        
        # Check that all dimensions have minimum viable weight (> 5%)
        min_weight = min(weights.values())
        if min_weight < 0.05:
            weak_dimension = next(dim for dim, weight in weights.items() if weight == min_weight)
            raise ValueError(
                f"Dimension '{weak_dimension}' has insufficient weight ({min_weight:.1%}). "
                "All dimensions should have at least 5% weight for meaningful comparison."
            )
    
    def get_requirement_conflicts_with_suggestions(self, requirements: ProjectRequirements) -> Dict[str, any]:
        """
        Get detailed conflict analysis with suggestions for resolution.
        
        Args:
            requirements: Project requirements to analyze
            
        Returns:
            Dictionary with conflicts and suggestions
        """
        conflicts = self._detect_requirement_conflicts(requirements)
        
        if not conflicts:
            return {
                'has_conflicts': False,
                'conflicts': [],
                'suggestions': []
            }
        
        suggestions = []
        
        # Generate suggestions based on detected conflicts
        if any('competing priorities' in conflict for conflict in conflicts):
            suggestions.append(
                "Consider relaxing one constraint: increase budget, extend timeline, or reduce scale requirements"
            )
        
        if any('beginner expertise' in conflict.lower() for conflict in conflicts):
            suggestions.append(
                "Consider adding experienced team members or extending timeline for learning"
            )
        
        if any('resource mismatch' in conflict for conflict in conflicts):
            suggestions.append(
                "Re-evaluate budget allocation or team composition for better alignment"
            )
        
        if any('over-engineering' in conflict for conflict in conflicts):
            suggestions.append(
                "Consider reducing team size or increasing scalability requirements to match effort"
            )
        
        if any('poor planning' in conflict for conflict in conflicts):
            suggestions.append(
                "Review project planning: tight timelines typically require experienced teams"
            )
        
        return {
            'has_conflicts': True,
            'conflicts': conflicts,
            'suggestions': suggestions
        }