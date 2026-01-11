"""
The Referee - Technology Comparison Tool

A command-line tool that generates structured technology comparison reports.
"""

__version__ = "0.1.0"
__author__ = "The Referee Team"

from .models import (
    ComparisonRequest,
    TechnologyProfile,
    TradeoffMatrix,
    Recommendation,
    ProjectRequirements,
    WeightedCriteria,
    DimensionScore,
    CompatibilityScore,
    BudgetLevel,
    TimelineLevel,
    ScaleLevel,
    ExpertiseLevel,
    ConfidenceLevel,
    MaturityLevel,
)
from .analyzer import TechnologyAnalyzer
from .requirements_processor import RequirementsProcessor
from .comparison_engine import ComparisonEngine
from .recommendation_engine import RecommendationEngine
from .formatter import MarkdownFormatter
from .input_parser import InputParser

__all__ = [
    "ComparisonRequest",
    "TechnologyProfile", 
    "TradeoffMatrix",
    "Recommendation",
    "ProjectRequirements",
    "WeightedCriteria",
    "DimensionScore",
    "CompatibilityScore",
    "BudgetLevel",
    "TimelineLevel",
    "ScaleLevel",
    "ExpertiseLevel",
    "ConfidenceLevel",
    "MaturityLevel",
    "TechnologyAnalyzer",
    "RequirementsProcessor",
    "ComparisonEngine",
    "RecommendationEngine",
    "MarkdownFormatter",
    "InputParser",
]