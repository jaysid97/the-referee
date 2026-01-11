"""
Input parser for The Referee CLI tool.

This module handles command-line argument parsing, validation, and conversion
to internal data structures for technology comparison requests.
"""

import argparse
import sys
from typing import List, Optional, Dict, Any
from .models import (
    ComparisonRequest, ProjectRequirements, OutputPreferences,
    BudgetLevel, TimelineLevel, ScaleLevel, ExpertiseLevel
)


class InputValidationError(Exception):
    """Raised when input validation fails."""
    pass


class InputParser:
    """Parses and validates command-line input for technology comparisons."""
    
    def __init__(self):
        """Initialize the input parser with argument definitions."""
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create and configure the argument parser."""
        parser = argparse.ArgumentParser(
            prog='referee',
            description='Compare technology stacks and get tailored recommendations',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  referee --technologies "REST API" "GraphQL" --team-size 3 --budget MEDIUM
  referee -t "AWS Lambda" "EC2" "Google Cloud Functions" --timeline TIGHT --scalability LARGE
  referee --technologies "React" "Vue" --custom-dimensions "TypeScript Support" "Bundle Size"
            """
        )
        
        # Required arguments
        parser.add_argument(
            '--technologies', '-t',
            nargs='+',
            required=True,
            help='Technologies to compare (2-5 options). Use quotes for multi-word names.'
        )
        
        # Project requirements
        parser.add_argument(
            '--team-size',
            type=int,
            default=3,
            help='Number of team members (default: 3)'
        )
        
        parser.add_argument(
            '--budget',
            choices=[level.value for level in BudgetLevel],
            default=BudgetLevel.MEDIUM.value,
            help='Budget constraint level (default: MEDIUM)'
        )
        
        parser.add_argument(
            '--timeline',
            choices=[level.value for level in TimelineLevel],
            default=TimelineLevel.MODERATE.value,
            help='Timeline constraint level (default: MODERATE)'
        )
        
        parser.add_argument(
            '--scalability',
            choices=[level.value for level in ScaleLevel],
            default=ScaleLevel.MEDIUM.value,
            help='Scalability requirements (default: MEDIUM)'
        )
        
        parser.add_argument(
            '--expertise',
            choices=[level.value for level in ExpertiseLevel],
            default=ExpertiseLevel.INTERMEDIATE.value,
            help='Team expertise level (default: INTERMEDIATE)'
        )
        
        # Optional features
        parser.add_argument(
            '--custom-dimensions',
            nargs='*',
            help='Additional comparison dimensions beyond the standard set'
        )
        
        # Output preferences
        parser.add_argument(
            '--no-matrix',
            action='store_true',
            help='Exclude trade-off matrix from output'
        )
        
        parser.add_argument(
            '--no-recommendation',
            action='store_true',
            help='Exclude recommendation section from output'
        )
        
        parser.add_argument(
            '--max-technologies',
            type=int,
            default=5,
            help='Maximum number of technologies to include (default: 5)'
        )
        
        return parser
    
    def parse_args(self, args: Optional[List[str]] = None) -> ComparisonRequest:
        """
        Parse command-line arguments and return a validated ComparisonRequest.
        
        Args:
            args: Optional list of arguments (uses sys.argv if None)
            
        Returns:
            ComparisonRequest: Validated comparison request
            
        Raises:
            InputValidationError: If validation fails
        """
        try:
            parsed_args = self.parser.parse_args(args)
            return self._convert_to_comparison_request(parsed_args)
        except argparse.ArgumentError as e:
            raise InputValidationError(f"Argument parsing failed: {e}")
        except SystemExit:
            # argparse calls sys.exit on error, we want to handle this gracefully
            raise InputValidationError("Invalid command-line arguments")
    
    def _convert_to_comparison_request(self, args: argparse.Namespace) -> ComparisonRequest:
        """
        Convert parsed arguments to a ComparisonRequest object.
        
        Args:
            args: Parsed command-line arguments
            
        Returns:
            ComparisonRequest: Validated comparison request
            
        Raises:
            InputValidationError: If validation fails
        """
        # Validate technology count
        self._validate_technology_count(args.technologies)
        
        # Validate team size
        self._validate_team_size(args.team_size)
        
        # Validate custom dimensions
        if args.custom_dimensions:
            self._validate_custom_dimensions(args.custom_dimensions)
        
        # Validate max technologies
        self._validate_max_technologies(args.max_technologies)
        
        try:
            # Create project requirements
            project_requirements = ProjectRequirements(
                team_size=args.team_size,
                budget=BudgetLevel(args.budget),
                timeline=TimelineLevel(args.timeline),
                scalability_needs=ScaleLevel(args.scalability),
                expertise_level=ExpertiseLevel(args.expertise)
            )
            
            # Create output preferences
            output_preferences = OutputPreferences(
                include_matrix=not args.no_matrix,
                include_recommendation=not args.no_recommendation,
                max_technologies=args.max_technologies
            )
            
            # Create comparison request
            return ComparisonRequest(
                technologies=args.technologies,
                project_requirements=project_requirements,
                custom_dimensions=args.custom_dimensions if args.custom_dimensions else None,
                output_preferences=output_preferences
            )
            
        except Exception as e:
            raise InputValidationError(f"Failed to create comparison request: {e}")
    
    def _validate_technology_count(self, technologies: List[str]) -> None:
        """
        Validate that the number of technologies is within acceptable range.
        
        Args:
            technologies: List of technology names
            
        Raises:
            InputValidationError: If technology count is invalid
        """
        if len(technologies) < 2:
            raise InputValidationError(
                f"At least 2 technologies are required for comparison, got {len(technologies)}. "
                f"Please provide 2-5 technologies to compare."
            )
        
        if len(technologies) > 5:
            raise InputValidationError(
                f"Maximum 5 technologies can be compared, got {len(technologies)}. "
                f"Please limit your comparison to 5 technologies or fewer."
            )
        
        # Check for duplicates
        unique_technologies = set(tech.lower().strip() for tech in technologies)
        if len(unique_technologies) != len(technologies):
            raise InputValidationError(
                "Duplicate technologies detected. Each technology must be unique. "
                f"Technologies provided: {technologies}"
            )
    
    def _validate_team_size(self, team_size: int) -> None:
        """
        Validate team size is reasonable.
        
        Args:
            team_size: Number of team members
            
        Raises:
            InputValidationError: If team size is invalid
        """
        if team_size < 1:
            raise InputValidationError(
                f"Team size must be at least 1, got {team_size}"
            )
        
        if team_size > 1000:
            raise InputValidationError(
                f"Team size seems unreasonably large: {team_size}. "
                f"Please verify this is correct or use a smaller number."
            )
    
    def _validate_custom_dimensions(self, custom_dimensions: List[str]) -> None:
        """
        Validate custom dimensions don't conflict with standard ones.
        
        Args:
            custom_dimensions: List of custom dimension names
            
        Raises:
            InputValidationError: If custom dimensions are invalid
        """
        standard_dimensions = {'cost', 'scalability', 'complexity', 'ecosystem', 'performance'}
        
        # Check for conflicts with standard dimensions (case-insensitive)
        conflicts = []
        for dimension in custom_dimensions:
            if dimension.lower().strip() in standard_dimensions:
                conflicts.append(dimension)
        
        if conflicts:
            raise InputValidationError(
                f"Custom dimensions conflict with standard dimensions: {conflicts}. "
                f"Standard dimensions are: {sorted(standard_dimensions)}. "
                f"Please choose different names for your custom dimensions."
            )
        
        # Check for duplicates in custom dimensions
        unique_dimensions = set(dim.lower().strip() for dim in custom_dimensions)
        if len(unique_dimensions) != len(custom_dimensions):
            raise InputValidationError(
                f"Duplicate custom dimensions detected: {custom_dimensions}. "
                f"Each custom dimension must be unique."
            )
        
        # Check for empty or whitespace-only dimensions
        for dimension in custom_dimensions:
            if not dimension.strip():
                raise InputValidationError(
                    "Custom dimensions cannot be empty or contain only whitespace"
                )
    
    def _validate_max_technologies(self, max_technologies: int) -> None:
        """
        Validate max technologies setting.
        
        Args:
            max_technologies: Maximum number of technologies to include
            
        Raises:
            InputValidationError: If max technologies is invalid
        """
        if max_technologies < 2:
            raise InputValidationError(
                f"Maximum technologies must be at least 2, got {max_technologies}"
            )
        
        if max_technologies > 5:
            raise InputValidationError(
                f"Maximum technologies cannot exceed 5, got {max_technologies}"
            )
    
    def get_help_text(self) -> str:
        """
        Get formatted help text for the CLI.
        
        Returns:
            str: Formatted help text
        """
        return self.parser.format_help()
    
    def suggest_similar_technologies(self, unknown_tech: str) -> List[str]:
        """
        Suggest similar technology names for unknown technologies.
        
        Args:
            unknown_tech: The unrecognized technology name
            
        Returns:
            List[str]: List of suggested similar technology names
        """
        # Common technology names that users might misspell or abbreviate
        known_technologies = [
            "REST API", "GraphQL", "gRPC",
            "AWS Lambda", "AWS EC2", "Google Cloud Functions", "Azure Functions",
            "React", "Vue", "Angular", "Svelte",
            "PostgreSQL", "MongoDB", "MySQL", "Redis",
            "Docker", "Kubernetes", "Terraform",
            "Node.js", "Python", "Java", "Go", "Rust",
            "Express", "FastAPI", "Spring Boot", "Django"
        ]
        
        # Simple similarity matching (could be enhanced with fuzzy matching)
        suggestions = []
        unknown_lower = unknown_tech.lower()
        
        for tech in known_technologies:
            tech_lower = tech.lower()
            # Check for partial matches or common abbreviations
            if (unknown_lower in tech_lower or 
                tech_lower in unknown_lower or
                self._check_abbreviation_match(unknown_lower, tech_lower)):
                suggestions.append(tech)
        
        return suggestions[:3]  # Return top 3 suggestions
    
    def _check_abbreviation_match(self, abbrev: str, full_name: str) -> bool:
        """
        Check if an abbreviation might match a full technology name.
        
        Args:
            abbrev: Potential abbreviation
            full_name: Full technology name
            
        Returns:
            bool: True if there's a potential match
        """
        # Simple abbreviation matching
        if len(abbrev) < 2:
            return False
        
        # Check if abbreviation matches first letters of words
        words = full_name.lower().split()
        if len(words) >= 2:
            first_letters = ''.join(word[0] for word in words)
            if abbrev == first_letters:
                return True
        
        return False


def create_parser() -> InputParser:
    """
    Factory function to create an InputParser instance.
    
    Returns:
        InputParser: Configured input parser
    """
    return InputParser()