"""
Main CLI application for The Referee technology comparison tool.

This module provides the command-line interface that wires together all
components to create complete technology comparison reports.
"""

import sys
from typing import Optional, List
from .input_parser import InputParser, InputValidationError
from .analyzer import TechnologyAnalyzer, TechnologyNotFoundError, AnalysisError
from .requirements_processor import RequirementsProcessor, RequirementsProcessingError, ConflictingRequirementsError
from .comparison_engine import ComparisonEngine, ComparisonError, InsufficientDataError
from .recommendation_engine import RecommendationEngine
from .formatter import MarkdownFormatter


class ApplicationError(Exception):
    """Base exception for application-level errors."""
    pass


class GracefulDegradationError(Exception):
    """Raised when the application can continue with reduced functionality."""
    
    def __init__(self, message: str, fallback_available: bool = True):
        self.fallback_available = fallback_available
        super().__init__(message)


class RefereeApplication:
    """Main application class that orchestrates the comparison process."""
    
    def __init__(self):
        """Initialize the application with all required components."""
        self.input_parser = InputParser()
        self.technology_analyzer = TechnologyAnalyzer()
        self.requirements_processor = RequirementsProcessor()
        self.comparison_engine = ComparisonEngine()
        self.recommendation_engine = RecommendationEngine()
        self.formatter = MarkdownFormatter()
    
    def run(self, args: Optional[List[str]] = None) -> int:
        """
        Run the complete comparison workflow.
        
        Args:
            args: Optional command-line arguments (uses sys.argv if None)
            
        Returns:
            int: Exit code (0 for success, 1 for error)
        """
        try:
            # Parse and validate input
            comparison_request = self.input_parser.parse_args(args)
            
            # Process project requirements into weighted criteria with conflict detection
            try:
                weighted_criteria = self.requirements_processor.process_requirements(
                    comparison_request.project_requirements
                )
            except ConflictingRequirementsError as e:
                # Handle conflicting requirements gracefully
                print("Warning: Conflicting requirements detected:", file=sys.stderr)
                for conflict in e.conflicts:
                    print(f"  - {conflict}", file=sys.stderr)
                
                # Get suggestions for resolution
                conflict_analysis = self.requirements_processor.get_requirement_conflicts_with_suggestions(
                    comparison_request.project_requirements
                )
                
                if conflict_analysis['suggestions']:
                    print("\nSuggestions:", file=sys.stderr)
                    for suggestion in conflict_analysis['suggestions']:
                        print(f"  - {suggestion}", file=sys.stderr)
                
                print("\nProceeding with analysis, but recommendations may be suboptimal.\n", file=sys.stderr)
                
                # Continue with processing despite conflicts by creating a modified processor
                # that bypasses the conflict check
                try:
                    # Temporarily disable conflict detection
                    original_detect = self.requirements_processor._detect_requirement_conflicts
                    self.requirements_processor._detect_requirement_conflicts = lambda req: []
                    
                    weighted_criteria = self.requirements_processor.process_requirements(
                        comparison_request.project_requirements
                    )
                    
                    # Restore original method
                    self.requirements_processor._detect_requirement_conflicts = original_detect
                    
                except Exception as fallback_error:
                    print(f"Error: Could not process requirements even with conflict bypass: {fallback_error}", file=sys.stderr)
                    return 1
            
            # Analyze each technology with enhanced error handling
            technology_profiles = []
            unknown_technologies = []
            fallback_technologies = []
            
            for tech_name in comparison_request.technologies:
                try:
                    # Try to get the technology profile
                    profile = self.technology_analyzer.get_technology_profile(tech_name)
                    if profile is None:
                        # Try with fallback
                        try:
                            profile = self.technology_analyzer.get_technology_profile_with_fallback(tech_name)
                            fallback_technologies.append(tech_name)
                            technology_profiles.append(profile)
                        except TechnologyNotFoundError as e:
                            unknown_technologies.append(tech_name)
                            print(f"Warning: Unknown technology '{tech_name}'", file=sys.stderr)
                            
                            # Show suggestions if available
                            if e.suggestions:
                                print(f"Did you mean one of these? {', '.join(e.suggestions)}", file=sys.stderr)
                    else:
                        technology_profiles.append(profile)
                        
                except Exception as e:
                    print(f"Error analyzing technology '{tech_name}': {e}", file=sys.stderr)
                    unknown_technologies.append(tech_name)
            
            # Check if we have enough technologies to compare
            if len(technology_profiles) < 2:
                if len(technology_profiles) == 1 and unknown_technologies:
                    print("Error: Need at least 2 technologies for comparison.", file=sys.stderr)
                    print(f"Found 1 valid technology, but {len(unknown_technologies)} were unrecognized.", file=sys.stderr)
                elif len(technology_profiles) == 0:
                    print("Error: No recognized technologies found for comparison.", file=sys.stderr)
                else:
                    print("Error: Need at least 2 technologies for comparison.", file=sys.stderr)
                
                if unknown_technologies:
                    print(f"Unrecognized technologies: {', '.join(unknown_technologies)}", file=sys.stderr)
                    print("Use --help to see supported technologies or check spelling.", file=sys.stderr)
                
                return 1
            
            # Warn about fallback technologies
            if fallback_technologies:
                print(f"Note: Using generic profiles for: {', '.join(fallback_technologies)}", file=sys.stderr)
                print("Analysis may be less accurate for these technologies.\n", file=sys.stderr)
            
            # Generate comparison analysis with error handling
            try:
                comparison_result = self.comparison_engine.generate_comparison(
                    technology_profiles,
                    weighted_criteria,
                    comparison_request.custom_dimensions
                )
            except InsufficientDataError as e:
                print(f"Warning: {e}", file=sys.stderr)
                print("Proceeding with limited analysis.\n", file=sys.stderr)
                
                # Try with reduced functionality
                comparison_result = self._generate_fallback_comparison(
                    technology_profiles, weighted_criteria, comparison_request.custom_dimensions
                )
            except ComparisonError as e:
                print(f"Error generating comparison: {e}", file=sys.stderr)
                return 1
            
            # Generate recommendations if requested
            recommendation = None
            if comparison_request.output_preferences.include_recommendation:
                try:
                    recommendation = self.recommendation_engine.generate_recommendation(
                        technology_profiles,
                        comparison_result['compatibility_scores'],
                        weighted_criteria,
                        comparison_result['comparison_data']
                    )
                except Exception as e:
                    print(f"Warning: Could not generate recommendations: {e}", file=sys.stderr)
                    print("Proceeding without recommendation section.\n", file=sys.stderr)
                    recommendation = None
            
            # Format and output the results with error handling
            try:
                if comparison_request.output_preferences.include_matrix and comparison_request.output_preferences.include_recommendation:
                    # Include everything
                    markdown_output = self.formatter.format_comparison(
                        technology_profiles,
                        comparison_result['comparison_data'],
                        comparison_result['tradeoff_matrix'],
                        comparison_result['compatibility_scores'],
                        recommendation
                    )
                else:
                    # Custom formatting based on preferences
                    markdown_output = self._format_custom_output(
                        technology_profiles,
                        comparison_result,
                        recommendation,
                        comparison_request.output_preferences
                    )
                
                print(markdown_output)
                
            except Exception as e:
                print(f"Error formatting output: {e}", file=sys.stderr)
                # Try basic fallback formatting
                try:
                    basic_output = self._generate_basic_output(technology_profiles, comparison_result)
                    print(basic_output)
                except Exception as fallback_error:
                    print(f"Critical error: Could not generate any output: {fallback_error}", file=sys.stderr)
                    return 1
            
            # Summary warnings
            warnings_shown = False
            if unknown_technologies:
                print(f"\nNote: {len(unknown_technologies)} technology(ies) were not recognized and excluded from analysis.", file=sys.stderr)
                warnings_shown = True
            
            if fallback_technologies:
                print(f"Note: Generic analysis used for: {', '.join(fallback_technologies)}", file=sys.stderr)
                warnings_shown = True
            
            if warnings_shown:
                print("Consider checking technology names or consulting documentation for supported technologies.", file=sys.stderr)
            
            return 0
            
        except InputValidationError as e:
            print(f"Input Error: {e}", file=sys.stderr)
            print("\nUse --help for usage information.", file=sys.stderr)
            return 1
            
        except RequirementsProcessingError as e:
            print(f"Requirements Error: {e}", file=sys.stderr)
            print("Please check your project requirements and try again.", file=sys.stderr)
            return 1
            
        except Exception as e:
            print(f"Unexpected Error: {e}", file=sys.stderr)
            print("Please report this issue if it persists.", file=sys.stderr)
            return 1
    
    def show_help(self) -> None:
        """Display help information."""
        print(self.input_parser.get_help_text())
    
    def show_version(self) -> None:
        """Display version information."""
        from . import __version__
        print(f"The Referee v{__version__}")
        print("Technology comparison tool for informed decision-making")
    
    def _format_custom_output(
        self,
        technology_profiles,
        comparison_result,
        recommendation,
        output_preferences
    ) -> str:
        """Format output based on custom preferences."""
        sections = []
        
        # Title and overview (always included)
        tech_names = [tech.name for tech in technology_profiles]
        title = f"# Technology Comparison: {' vs '.join(tech_names)}"
        sections.append(title)
        sections.append("")
        
        # Overview section (always included)
        sections.append("## Overview")
        sections.append("")
        sections.append(f"This report compares {len(technology_profiles)} technology options across multiple dimensions to help guide your technical decision-making.")
        sections.append("")
        
        # Side-by-side comparison (always included)
        sections.append("## Side-by-Side Comparison")
        sections.append("")
        sections.extend(self.formatter._format_side_by_side_comparison(technology_profiles, comparison_result['comparison_data']))
        sections.append("")
        
        # Trade-off matrix (conditional)
        if output_preferences.include_matrix:
            sections.append("## Trade-off Matrix")
            sections.append("")
            sections.extend(self.formatter.format_tradeoff_matrix(comparison_result['tradeoff_matrix']))
            sections.append("")
        
        # Compatibility scores (always included)
        sections.append("## Compatibility Analysis")
        sections.append("")
        sections.extend(self.formatter._format_compatibility_scores(comparison_result['compatibility_scores']))
        sections.append("")
        
        # Recommendation (conditional)
        if output_preferences.include_recommendation and recommendation:
            sections.append("## Recommendation")
            sections.append("")
            sections.extend(self.formatter.format_recommendation(recommendation))
            sections.append("")
        
        return "\n".join(sections)


def main() -> int:
    """
    Main entry point for the CLI application.
    
    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    # Handle special cases first
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--help', '-h']:
            app = RefereeApplication()
            app.show_help()
            return 0
        elif sys.argv[1] in ['--version', '-v']:
            app = RefereeApplication()
            app.show_version()
            return 0
    
    # Run the main application
    app = RefereeApplication()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
    
    def _generate_fallback_comparison(
        self,
        technology_profiles,
        weighted_criteria,
        custom_dimensions
    ):
        """
        Generate a fallback comparison when normal comparison fails.
        
        Args:
            technology_profiles: List of technology profiles
            weighted_criteria: Weighted criteria
            custom_dimensions: Optional custom dimensions
            
        Returns:
            Simplified comparison result
        """
        try:
            # Create a simplified trade-off matrix with only standard dimensions
            standard_dimensions = ['cost', 'scalability', 'complexity', 'ecosystem', 'performance']
            tradeoff_matrix = self.comparison_engine.create_tradeoff_matrix(
                technology_profiles, standard_dimensions
            )
            
            # Generate basic compatibility scores
            compatibility_scores = []
            for tech in technology_profiles:
                try:
                    score = self.comparison_engine.calculate_compatibility(tech, weighted_criteria)
                    compatibility_scores.append(score)
                except Exception:
                    # Create minimal fallback score
                    fallback_score = self.comparison_engine._create_fallback_compatibility_score(
                        tech, "Calculation failed"
                    )
                    compatibility_scores.append(fallback_score)
            
            # Generate basic comparison data
            comparison_data = self.comparison_engine._generate_side_by_side_data(technology_profiles)
            
            return {
                'technologies': [tech.name for tech in technology_profiles],
                'comparison_data': comparison_data,
                'tradeoff_matrix': tradeoff_matrix,
                'compatibility_scores': compatibility_scores,
                'weighted_criteria': weighted_criteria
            }
            
        except Exception as e:
            raise ApplicationError(f"Even fallback comparison failed: {str(e)}")
    
    def _generate_basic_output(self, technology_profiles, comparison_result):
        """
        Generate basic text output when Markdown formatting fails.
        
        Args:
            technology_profiles: List of technology profiles
            comparison_result: Comparison result data
            
        Returns:
            Basic text output string
        """
        lines = []
        
        # Title
        tech_names = [tech.name for tech in technology_profiles]
        lines.append(f"Technology Comparison: {' vs '.join(tech_names)}")
        lines.append("=" * 50)
        lines.append("")
        
        # Basic technology info
        lines.append("Technologies:")
        for tech in technology_profiles:
            lines.append(f"- {tech.name} ({tech.category})")
        lines.append("")
        
        # Compatibility scores
        lines.append("Compatibility Scores:")
        for score in comparison_result['compatibility_scores']:
            percentage = f"{score.score:.1%}"
            lines.append(f"- {score.technology}: {percentage}")
        lines.append("")
        
        # Basic pros/cons
        lines.append("Key Points:")
        for tech in technology_profiles:
            lines.append(f"\n{tech.name}:")
            lines.append(f"  Pros: {', '.join(tech.pros[:2])}")  # First 2 pros
            lines.append(f"  Cons: {', '.join(tech.cons[:2])}")  # First 2 cons
        
        return "\n".join(lines)