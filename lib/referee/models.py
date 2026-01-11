"""
Core data models for The Referee technology comparison tool.

This module defines all the data structures used throughout the system,
including request models, technology profiles, and output formats.
"""

from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, validator


class BudgetLevel(str, Enum):
    """Budget constraint levels for project requirements."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class TimelineLevel(str, Enum):
    """Timeline constraint levels for project requirements."""
    TIGHT = "TIGHT"
    MODERATE = "MODERATE"
    FLEXIBLE = "FLEXIBLE"


class ScaleLevel(str, Enum):
    """Scalability requirement levels."""
    SMALL = "SMALL"
    MEDIUM = "MEDIUM"
    LARGE = "LARGE"


class ExpertiseLevel(str, Enum):
    """Team expertise levels."""
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    EXPERT = "EXPERT"


class ConfidenceLevel(str, Enum):
    """Confidence levels for recommendations."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class MaturityLevel(str, Enum):
    """Technology maturity levels."""
    EXPERIMENTAL = "EXPERIMENTAL"
    STABLE = "STABLE"
    MATURE = "MATURE"


class ProjectRequirements(BaseModel):
    """Project requirements and constraints."""
    team_size: int = Field(..., ge=1, description="Number of team members")
    budget: BudgetLevel = Field(..., description="Budget constraint level")
    timeline: TimelineLevel = Field(..., description="Timeline constraint level")
    scalability_needs: ScaleLevel = Field(..., description="Scalability requirements")
    expertise_level: ExpertiseLevel = Field(..., description="Team expertise level")


class DimensionScore(BaseModel):
    """Score for a specific dimension with explanation."""
    score: float = Field(..., ge=0, le=5, description="Numerical score (0-5)")
    explanation: str = Field(..., min_length=1, description="Reasoning for the score")


class TechnologyMetadata(BaseModel):
    """Metadata about a technology."""
    maturity: MaturityLevel = Field(..., description="Technology maturity level")
    license: str = Field(..., min_length=1, description="License type")
    maintainer: str = Field(..., min_length=1, description="Primary maintainer")


class TechnologyProfile(BaseModel):
    """Complete profile of a technology including scores and characteristics."""
    name: str = Field(..., min_length=1, description="Technology name")
    category: str = Field(..., min_length=1, description="Technology category")
    dimensions: Dict[str, DimensionScore] = Field(
        ..., 
        description="Scores across different dimensions"
    )
    pros: List[str] = Field(..., min_items=1, description="Specific advantages")
    cons: List[str] = Field(..., min_items=1, description="Specific disadvantages")
    best_for: List[str] = Field(..., min_items=1, description="Ideal use cases")
    metadata: TechnologyMetadata = Field(..., description="Technology metadata")

    @validator('dimensions')
    def validate_required_dimensions(cls, v):
        """Ensure all required dimensions are present."""
        required_dimensions = {'cost', 'scalability', 'complexity', 'ecosystem', 'performance'}
        missing = required_dimensions - set(v.keys())
        if missing:
            raise ValueError(f"Missing required dimensions: {missing}")
        return v


class OutputPreferences(BaseModel):
    """User preferences for output formatting."""
    include_matrix: bool = Field(default=True, description="Include trade-off matrix")
    include_recommendation: bool = Field(default=True, description="Include recommendation")
    max_technologies: int = Field(default=5, ge=2, le=5, description="Maximum technologies to compare")


class ComparisonRequest(BaseModel):
    """Request for technology comparison analysis."""
    technologies: List[str] = Field(
        ..., 
        min_items=2, 
        max_items=5, 
        description="Technologies to compare (2-5)"
    )
    project_requirements: ProjectRequirements = Field(
        ..., 
        description="Project requirements and constraints"
    )
    custom_dimensions: Optional[List[str]] = Field(
        default=None, 
        description="Additional comparison criteria"
    )
    output_preferences: OutputPreferences = Field(
        default_factory=OutputPreferences,
        description="Output formatting preferences"
    )

    @validator('technologies')
    def validate_unique_technologies(cls, v):
        """Ensure all technologies are unique."""
        if len(v) != len(set(v)):
            raise ValueError("All technologies must be unique")
        return v

    @validator('custom_dimensions')
    def validate_custom_dimensions(cls, v):
        """Ensure custom dimensions don't conflict with standard ones."""
        if v is None:
            return v
        
        standard_dimensions = {'cost', 'scalability', 'complexity', 'ecosystem', 'performance'}
        conflicts = set(v) & standard_dimensions
        if conflicts:
            raise ValueError(f"Custom dimensions conflict with standard dimensions: {conflicts}")
        return v


class WeightedCriteria(BaseModel):
    """Weighted criteria based on project requirements."""
    dimension_weights: Dict[str, float] = Field(
        ..., 
        description="Weights for each dimension (0-1)"
    )
    priority_factors: List[str] = Field(
        ..., 
        description="Prioritized factors based on requirements"
    )

    @validator('dimension_weights')
    def validate_weights(cls, v):
        """Ensure all weights are between 0 and 1."""
        for dimension, weight in v.items():
            if not 0 <= weight <= 1:
                raise ValueError(f"Weight for {dimension} must be between 0 and 1, got {weight}")
        return v


class TradeoffHighlight(BaseModel):
    """Key differentiator in trade-off analysis."""
    dimension: str = Field(..., min_length=1, description="Dimension name")
    leader: str = Field(..., min_length=1, description="Leading technology")
    explanation: str = Field(..., min_length=1, description="Explanation of leadership")


class TradeoffMatrix(BaseModel):
    """Trade-off matrix showing technology comparisons across dimensions."""
    technologies: List[str] = Field(..., min_items=2, description="Technology names")
    dimensions: List[str] = Field(..., min_items=1, description="Comparison dimensions")
    scores: List[List[float]] = Field(..., description="2D array: [tech_index][dimension_index]")
    explanations: List[List[str]] = Field(..., description="Reasoning for each score")
    highlights: List[TradeoffHighlight] = Field(..., description="Key differentiators")

    @validator('scores')
    def validate_scores_dimensions(cls, v, values):
        """Ensure scores matrix matches technologies and dimensions."""
        if 'technologies' in values and 'dimensions' in values:
            expected_rows = len(values['technologies'])
            expected_cols = len(values['dimensions'])
            
            if len(v) != expected_rows:
                raise ValueError(f"Scores must have {expected_rows} rows, got {len(v)}")
            
            for i, row in enumerate(v):
                if len(row) != expected_cols:
                    raise ValueError(f"Row {i} must have {expected_cols} columns, got {len(row)}")
        return v

    @validator('explanations')
    def validate_explanations_dimensions(cls, v, values):
        """Ensure explanations matrix matches technologies and dimensions."""
        if 'technologies' in values and 'dimensions' in values:
            expected_rows = len(values['technologies'])
            expected_cols = len(values['dimensions'])
            
            if len(v) != expected_rows:
                raise ValueError(f"Explanations must have {expected_rows} rows, got {len(v)}")
            
            for i, row in enumerate(v):
                if len(row) != expected_cols:
                    raise ValueError(f"Explanation row {i} must have {expected_cols} columns, got {len(row)}")
        return v


class CompatibilityScore(BaseModel):
    """Compatibility score between technology and requirements."""
    technology: str = Field(..., min_length=1, description="Technology name")
    score: float = Field(..., ge=0, le=1, description="Compatibility score (0-1)")
    reasoning: str = Field(..., min_length=1, description="Explanation of score")


class RankedChoice(BaseModel):
    """Ranked technology choice with scoring details."""
    technology: str = Field(..., min_length=1, description="Technology name")
    score: float = Field(..., ge=0, le=1, description="Overall score (0-1)")
    confidence: ConfidenceLevel = Field(..., description="Confidence in recommendation")
    reasoning: str = Field(..., min_length=1, description="Detailed reasoning")


class AlternativeScenario(BaseModel):
    """Alternative recommendation for different scenarios."""
    scenario: str = Field(..., min_length=1, description="Scenario description")
    recommended_tech: str = Field(..., min_length=1, description="Recommended technology")
    explanation: str = Field(..., min_length=1, description="Explanation for recommendation")


class Recommendation(BaseModel):
    """Final recommendation with ranked choices and reasoning."""
    ranked_choices: List[RankedChoice] = Field(
        ..., 
        min_items=1, 
        description="Technologies ranked by suitability"
    )
    key_decision_factors: List[str] = Field(
        ..., 
        min_items=1, 
        description="Primary factors influencing decision"
    )
    caveats: List[str] = Field(..., description="Important limitations or warnings")
    alternative_scenarios: Optional[List[AlternativeScenario]] = Field(
        default=None,
        description="Recommendations for different scenarios"
    )

    @validator('ranked_choices')
    def validate_unique_technologies_in_ranking(cls, v):
        """Ensure all ranked technologies are unique."""
        technologies = [choice.technology for choice in v]
        if len(technologies) != len(set(technologies)):
            raise ValueError("All technologies in ranking must be unique")
        return v

    @validator('ranked_choices')
    def validate_score_ordering(cls, v):
        """Ensure technologies are ranked by score (highest first)."""
        scores = [choice.score for choice in v]
        if scores != sorted(scores, reverse=True):
            raise ValueError("Technologies must be ranked by score (highest first)")
        return v