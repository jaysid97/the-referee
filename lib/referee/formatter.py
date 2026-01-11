"""
Markdown formatter for The Referee technology comparison tool.

This module provides the MarkdownFormatter class that converts analysis results
into highly scannable Markdown output with proper formatting for tables,
bullet points, and visual hierarchy.
"""

from typing import Dict, List, Optional, Any
from referee.models import (
    TechnologyProfile,
    TradeoffMatrix,
    Recommendation,
    CompatibilityScore
)


class MarkdownFormatter:
    """
    Converts analysis results into highly scannable Markdown output.
    
    Provides functionality to:
    - Format side-by-side comparisons using tables with clear headers
    - Create trade-off matrices with aligned columns and consistent spacing
    - Apply bullet points and visual hierarchy for pros/cons sections
    - Ensure compatibility with standard Markdown renderers
    """
    
    def __init__(self):
        """Initialize the Markdown formatter."""
        pass
    
    def format_comparison(
        self,
        technologies: List[TechnologyProfile],
        comparison_data: Dict[str, Any],
        tradeoff_matrix: TradeoffMatrix,
        compatibility_scores: List[CompatibilityScore],
        recommendation: Optional[Recommendation] = None
    ) -> str:
        """
        Format a complete comparison report in Markdown.
        
        Args:
            technologies: List of technology profiles
            comparison_data: Side-by-side comparison data
            tradeoff_matrix: Trade-off matrix with scores and explanations
            compatibility_scores: Compatibility scores for each technology
            recommendation: Optional recommendation with ranked choices
            
        Returns:
            Complete Markdown-formatted comparison report
        """
        if not technologies:
            raise ValueError("At least one technology must be provided")
        
        sections = []
        
        # Title and overview
        tech_names = [tech.name for tech in technologies]
        title = f"# Technology Comparison: {' vs '.join(tech_names)}"
        sections.append(title)
        sections.append("")
        
        # Overview section
        sections.append("## Overview")
        sections.append("")
        sections.append(f"This report compares {len(technologies)} technology options across multiple dimensions to help guide your technical decision-making.")
        sections.append("")
        
        # Side-by-side comparison
        sections.append("## Side-by-Side Comparison")
        sections.append("")
        sections.extend(self._format_side_by_side_comparison(technologies, comparison_data))
        sections.append("")
        
        # Trade-off matrix
        sections.append("## Trade-off Matrix")
        sections.append("")
        sections.extend(self.format_tradeoff_matrix(tradeoff_matrix))
        sections.append("")
        
        # Compatibility scores
        sections.append("## Compatibility Analysis")
        sections.append("")
        sections.extend(self._format_compatibility_scores(compatibility_scores))
        sections.append("")
        
        # Recommendation (if provided)
        if recommendation:
            sections.append("## Recommendation")
            sections.append("")
            sections.extend(self.format_recommendation(recommendation))
            sections.append("")
        
        return "\n".join(sections)
    
    def format_tradeoff_matrix(self, matrix: TradeoffMatrix) -> List[str]:
        """
        Format a trade-off matrix as a Markdown table.
        
        Args:
            matrix: TradeoffMatrix with technologies, dimensions, and scores
            
        Returns:
            List of strings representing the formatted table
        """
        if not matrix.technologies or not matrix.dimensions:
            raise ValueError("Matrix must have at least one technology and one dimension")
        
        lines = []
        
        # Create header row
        header = ["Technology"] + matrix.dimensions
        lines.append("| " + " | ".join(header) + " |")
        
        # Create separator row
        separator = [":---"] + [":---:" for _ in matrix.dimensions]
        lines.append("| " + " | ".join(separator) + " |")
        
        # Create data rows
        for i, tech in enumerate(matrix.technologies):
            row = [tech]
            for j, dimension in enumerate(matrix.dimensions):
                score = matrix.scores[i][j]
                # Format score with consistent scale representation
                formatted_score = self._format_score(score)
                row.append(formatted_score)
            lines.append("| " + " | ".join(row) + " |")
        
        # Add highlights section if available
        if matrix.highlights:
            lines.append("")
            lines.append("### Key Differentiators")
            lines.append("")
            for highlight in matrix.highlights:
                lines.append(f"- **{highlight.dimension.title()}**: {highlight.leader} - {highlight.explanation}")
        
        return lines
    
    def format_recommendation(self, recommendation: Recommendation) -> List[str]:
        """
        Format a recommendation with ranked choices and reasoning.
        
        Args:
            recommendation: Recommendation with ranked choices and decision factors
            
        Returns:
            List of strings representing the formatted recommendation
        """
        lines = []
        
        # Ranked choices
        lines.append("### Recommended Choice")
        lines.append("")
        
        if recommendation.ranked_choices:
            top_choice = recommendation.ranked_choices[0]
            lines.append(f"**{top_choice.technology}** (Score: {top_choice.score:.1%}, Confidence: {top_choice.confidence.value})")
            lines.append("")
            lines.append(top_choice.reasoning)
            lines.append("")
        
        # Full ranking if multiple options
        if len(recommendation.ranked_choices) > 1:
            lines.append("### Complete Ranking")
            lines.append("")
            for i, choice in enumerate(recommendation.ranked_choices, 1):
                lines.append(f"{i}. **{choice.technology}** - {choice.score:.1%} compatibility")
                lines.append(f"   - Confidence: {choice.confidence.value}")
                lines.append(f"   - {choice.reasoning}")
                lines.append("")
        
        # Key decision factors
        if recommendation.key_decision_factors:
            lines.append("### Key Decision Factors")
            lines.append("")
            for factor in recommendation.key_decision_factors:
                lines.append(f"- {factor}")
            lines.append("")
        
        # Caveats
        if recommendation.caveats:
            lines.append("### Important Considerations")
            lines.append("")
            for caveat in recommendation.caveats:
                lines.append(f"- {caveat}")
            lines.append("")
        
        # Alternative scenarios
        if recommendation.alternative_scenarios:
            lines.append("### Alternative Scenarios")
            lines.append("")
            for scenario in recommendation.alternative_scenarios:
                lines.append(f"**{scenario.scenario}**: {scenario.recommended_tech}")
                lines.append(f"- {scenario.explanation}")
                lines.append("")
        
        return lines
    
    def _format_side_by_side_comparison(
        self,
        technologies: List[TechnologyProfile],
        comparison_data: Dict[str, Any]
    ) -> List[str]:
        """
        Format side-by-side comparison with pros, cons, and best-for sections.
        
        Args:
            technologies: List of technology profiles
            comparison_data: Comparison data dictionary
            
        Returns:
            List of strings representing the formatted comparison
        """
        lines = []
        
        # Create sections for each comparison aspect
        sections = [
            ("Pros", "pros"),
            ("Cons", "cons"),
            ("Best For", "best_for")
        ]
        
        for section_title, section_key in sections:
            lines.append(f"### {section_title}")
            lines.append("")
            
            # Create table header
            tech_names = [tech.name for tech in technologies]
            header = "| " + " | ".join(tech_names) + " |"
            lines.append(header)
            
            # Create separator
            separator = "| " + " | ".join([":---" for _ in tech_names]) + " |"
            lines.append(separator)
            
            # Find maximum number of items across all technologies
            max_items = 0
            for tech in technologies:
                tech_data = comparison_data.get(tech.name, {})
                items = tech_data.get(section_key, [])
                max_items = max(max_items, len(items))
            
            # Create rows
            for i in range(max_items):
                row_items = []
                for tech in technologies:
                    tech_data = comparison_data.get(tech.name, {})
                    items = tech_data.get(section_key, [])
                    if i < len(items):
                        # Format as bullet point
                        item = items[i].strip()
                        if not item.startswith("•") and not item.startswith("-"):
                            item = f"• {item}"
                        row_items.append(item)
                    else:
                        row_items.append("")
                
                row = "| " + " | ".join(row_items) + " |"
                lines.append(row)
            
            lines.append("")
        
        return lines
    
    def _format_compatibility_scores(self, compatibility_scores: List[CompatibilityScore]) -> List[str]:
        """
        Format compatibility scores as a summary table.
        
        Args:
            compatibility_scores: List of compatibility scores
            
        Returns:
            List of strings representing the formatted scores
        """
        lines = []
        
        # Sort by score (highest first)
        sorted_scores = sorted(compatibility_scores, key=lambda x: x.score, reverse=True)
        
        # Create table
        lines.append("| Technology | Compatibility Score | Analysis |")
        lines.append("| :--- | :---: | :--- |")
        
        for score in sorted_scores:
            percentage = f"{score.score:.1%}"
            lines.append(f"| {score.technology} | {percentage} | {score.reasoning} |")
        
        return lines
    
    def _format_score(self, score: float) -> str:
        """
        Format a numerical score with consistent scale representation.
        
        Args:
            score: Numerical score (typically 0-5)
            
        Returns:
            Formatted score string with visual representation
        """
        # Convert to 0-5 scale if needed and create visual representation
        if score < 0:
            score = 0
        elif score > 5:
            score = 5
        
        # Create star rating (★ for filled, ☆ for empty)
        filled_stars = int(round(score))
        empty_stars = 5 - filled_stars
        
        stars = "★" * filled_stars + "☆" * empty_stars
        
        return f"{score:.1f} {stars}"