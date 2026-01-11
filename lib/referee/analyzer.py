"""
Technology analyzer with knowledge base for The Referee.

This module provides the TechnologyAnalyzer class that maintains a knowledge base
of technology profiles and provides analysis capabilities for technology comparison.
"""

import difflib
from typing import Dict, List, Optional, Set, Tuple
from referee.models import (
    TechnologyProfile,
    DimensionScore,
    TechnologyMetadata,
    MaturityLevel
)


class TechnologyNotFoundError(Exception):
    """Raised when a requested technology is not found in the knowledge base."""
    
    def __init__(self, technology: str, suggestions: Optional[List[str]] = None):
        self.technology = technology
        self.suggestions = suggestions or []
        
        message = f"Technology '{technology}' not found in knowledge base"
        if self.suggestions:
            message += f". Did you mean: {', '.join(self.suggestions[:3])}?"
        
        super().__init__(message)


class AnalysisError(Exception):
    """Raised when technology analysis fails."""
    pass


class TechnologyAnalyzer:
    """
    Analyzes technologies and maintains a knowledge base of technology profiles.
    
    Provides functionality to:
    - Retrieve technology profiles from the knowledge base
    - Evaluate technologies across standard dimensions
    - Identify and categorize known technologies
    """
    
    def __init__(self):
        """Initialize the analyzer with the technology knowledge base."""
        self._knowledge_base = self._build_knowledge_base()
    
    def _build_knowledge_base(self) -> Dict[str, TechnologyProfile]:
        """
        Build the comprehensive technology knowledge base.
        
        Returns:
            Dictionary mapping technology names to their profiles
        """
        knowledge_base = {}
        
        # REST API
        knowledge_base["REST"] = TechnologyProfile(
            name="REST",
            category="API",
            dimensions={
                "cost": DimensionScore(
                    score=4.5,
                    explanation="Low implementation cost, uses standard HTTP infrastructure"
                ),
                "scalability": DimensionScore(
                    score=4.0,
                    explanation="Scales well with caching and CDNs, stateless nature helps"
                ),
                "complexity": DimensionScore(
                    score=4.5,
                    explanation="Simple to understand and implement, follows HTTP conventions"
                ),
                "ecosystem": DimensionScore(
                    score=5.0,
                    explanation="Mature ecosystem with extensive tooling and library support"
                ),
                "performance": DimensionScore(
                    score=3.5,
                    explanation="Good performance but can be chatty with multiple round trips"
                )
            },
            pros=[
                "Simple and intuitive HTTP-based design",
                "Excellent caching capabilities",
                "Wide tooling and client library support",
                "Stateless architecture enables easy scaling",
                "Human-readable URLs and responses"
            ],
            cons=[
                "Can require multiple requests for complex data",
                "Over-fetching or under-fetching of data",
                "Limited real-time capabilities without additional protocols",
                "Versioning can become complex over time"
            ],
            best_for=[
                "CRUD operations and resource-based APIs",
                "Public APIs with broad client compatibility",
                "Simple to moderate complexity applications",
                "Teams new to API development",
                "Applications requiring strong caching"
            ],
            metadata=TechnologyMetadata(
                maturity=MaturityLevel.MATURE,
                license="Standard",
                maintainer="W3C/IETF Standards"
            )
        )
        
        # GraphQL
        knowledge_base["GraphQL"] = TechnologyProfile(
            name="GraphQL",
            category="API",
            dimensions={
                "cost": DimensionScore(
                    score=3.0,
                    explanation="Higher implementation complexity increases development costs"
                ),
                "scalability": DimensionScore(
                    score=4.5,
                    explanation="Excellent query optimization and single endpoint scaling"
                ),
                "complexity": DimensionScore(
                    score=2.5,
                    explanation="Steep learning curve, complex schema design and resolver logic"
                ),
                "ecosystem": DimensionScore(
                    score=4.0,
                    explanation="Growing ecosystem with good tooling, but less mature than REST"
                ),
                "performance": DimensionScore(
                    score=4.5,
                    explanation="Efficient data fetching, reduces over-fetching significantly"
                )
            },
            pros=[
                "Single endpoint for all data needs",
                "Eliminates over-fetching and under-fetching",
                "Strong type system and introspection",
                "Excellent developer tooling and debugging",
                "Real-time subscriptions built-in"
            ],
            cons=[
                "Complex caching strategies required",
                "Steep learning curve for teams",
                "Potential for expensive queries without proper limits",
                "Less suitable for simple CRUD operations"
            ],
            best_for=[
                "Complex data relationships and queries",
                "Mobile applications with bandwidth constraints",
                "Rapid frontend development with changing requirements",
                "Applications requiring real-time features",
                "Teams with strong backend expertise"
            ],
            metadata=TechnologyMetadata(
                maturity=MaturityLevel.STABLE,
                license="MIT",
                maintainer="GraphQL Foundation"
            )
        )
        
        # AWS Lambda
        knowledge_base["AWS Lambda"] = TechnologyProfile(
            name="AWS Lambda",
            category="Cloud Service",
            dimensions={
                "cost": DimensionScore(
                    score=4.0,
                    explanation="Pay-per-execution model, cost-effective for variable workloads"
                ),
                "scalability": DimensionScore(
                    score=5.0,
                    explanation="Automatic scaling to handle any load, virtually unlimited"
                ),
                "complexity": DimensionScore(
                    score=3.0,
                    explanation="Serverless paradigm requires different thinking, cold start considerations"
                ),
                "ecosystem": DimensionScore(
                    score=4.5,
                    explanation="Rich AWS ecosystem integration, extensive third-party support"
                ),
                "performance": DimensionScore(
                    score=3.5,
                    explanation="Good performance but cold starts can impact latency"
                )
            },
            pros=[
                "No server management required",
                "Automatic scaling and high availability",
                "Pay only for actual execution time",
                "Seamless integration with AWS services",
                "Built-in monitoring and logging"
            ],
            cons=[
                "Cold start latency for infrequent functions",
                "15-minute maximum execution time limit",
                "Vendor lock-in to AWS ecosystem",
                "Complex debugging and local development",
                "Limited control over runtime environment"
            ],
            best_for=[
                "Event-driven architectures",
                "Microservices with variable load",
                "Data processing and ETL pipelines",
                "API backends with unpredictable traffic",
                "Startups wanting to minimize infrastructure overhead"
            ],
            metadata=TechnologyMetadata(
                maturity=MaturityLevel.MATURE,
                license="Proprietary",
                maintainer="Amazon Web Services"
            )
        )
        
        # AWS EC2
        knowledge_base["EC2"] = TechnologyProfile(
            name="EC2",
            category="Cloud Service",
            dimensions={
                "cost": DimensionScore(
                    score=3.0,
                    explanation="Predictable costs but requires capacity planning and optimization"
                ),
                "scalability": DimensionScore(
                    score=4.0,
                    explanation="Good scaling with auto-scaling groups, but requires configuration"
                ),
                "complexity": DimensionScore(
                    score=2.5,
                    explanation="Requires server management, security patching, and infrastructure knowledge"
                ),
                "ecosystem": DimensionScore(
                    score=4.5,
                    explanation="Mature ecosystem with extensive AWS integration and tooling"
                ),
                "performance": DimensionScore(
                    score=4.5,
                    explanation="Excellent performance with full control over compute resources"
                )
            },
            pros=[
                "Full control over server environment",
                "Consistent performance without cold starts",
                "Wide variety of instance types and configurations",
                "Mature tooling and deployment options",
                "No execution time limits"
            ],
            cons=[
                "Requires server management and maintenance",
                "Always-on costs even during idle periods",
                "Manual scaling configuration needed",
                "Security and patching responsibilities",
                "More complex deployment processes"
            ],
            best_for=[
                "Long-running applications and services",
                "Applications requiring specific server configurations",
                "High-performance computing workloads",
                "Legacy applications with specific requirements",
                "Teams with strong DevOps capabilities"
            ],
            metadata=TechnologyMetadata(
                maturity=MaturityLevel.MATURE,
                license="Proprietary",
                maintainer="Amazon Web Services"
            )
        )
        
        # React
        knowledge_base["React"] = TechnologyProfile(
            name="React",
            category="Frontend Framework",
            dimensions={
                "cost": DimensionScore(
                    score=4.5,
                    explanation="Free and open-source with large talent pool reducing costs"
                ),
                "scalability": DimensionScore(
                    score=4.0,
                    explanation="Scales well for large applications with proper architecture"
                ),
                "complexity": DimensionScore(
                    score=3.5,
                    explanation="Moderate learning curve, requires understanding of modern JS concepts"
                ),
                "ecosystem": DimensionScore(
                    score=5.0,
                    explanation="Largest ecosystem with extensive libraries and community support"
                ),
                "performance": DimensionScore(
                    score=4.0,
                    explanation="Good performance with virtual DOM, requires optimization for large apps"
                )
            },
            pros=[
                "Huge community and ecosystem",
                "Excellent developer tools and debugging",
                "Component-based architecture promotes reusability",
                "Strong job market and talent availability",
                "Backed by Meta with long-term support"
            ],
            cons=[
                "Rapid ecosystem changes can cause fatigue",
                "JSX syntax has a learning curve",
                "Requires additional libraries for full functionality",
                "Can become complex with state management needs"
            ],
            best_for=[
                "Large-scale single-page applications",
                "Teams with strong JavaScript expertise",
                "Projects requiring extensive third-party integrations",
                "Applications with complex user interfaces",
                "Startups needing fast development and hiring"
            ],
            metadata=TechnologyMetadata(
                maturity=MaturityLevel.MATURE,
                license="MIT",
                maintainer="Meta (Facebook)"
            )
        )
        
        # Vue
        knowledge_base["Vue"] = TechnologyProfile(
            name="Vue",
            category="Frontend Framework",
            dimensions={
                "cost": DimensionScore(
                    score=4.5,
                    explanation="Free and open-source with growing talent pool"
                ),
                "scalability": DimensionScore(
                    score=4.0,
                    explanation="Scales well with good architecture, excellent for medium-large apps"
                ),
                "complexity": DimensionScore(
                    score=4.5,
                    explanation="Gentle learning curve, intuitive template syntax"
                ),
                "ecosystem": DimensionScore(
                    score=3.5,
                    explanation="Growing ecosystem but smaller than React, good official tooling"
                ),
                "performance": DimensionScore(
                    score=4.5,
                    explanation="Excellent performance with efficient reactivity system"
                )
            },
            pros=[
                "Gentle learning curve and intuitive syntax",
                "Excellent official documentation and tooling",
                "Progressive adoption possible in existing projects",
                "Great performance out of the box",
                "Strong TypeScript support"
            ],
            cons=[
                "Smaller ecosystem compared to React",
                "Less job market demand",
                "Fewer large-scale enterprise examples",
                "Smaller community for complex problem solving"
            ],
            best_for=[
                "Teams new to modern frontend frameworks",
                "Small to medium-sized applications",
                "Progressive enhancement of existing applications",
                "Rapid prototyping and development",
                "Projects prioritizing developer experience"
            ],
            metadata=TechnologyMetadata(
                maturity=MaturityLevel.STABLE,
                license="MIT",
                maintainer="Evan You / Vue Team"
            )
        )
        
        # PostgreSQL
        knowledge_base["PostgreSQL"] = TechnologyProfile(
            name="PostgreSQL",
            category="Database",
            dimensions={
                "cost": DimensionScore(
                    score=5.0,
                    explanation="Free and open-source with no licensing costs"
                ),
                "scalability": DimensionScore(
                    score=4.0,
                    explanation="Good vertical scaling, horizontal scaling requires additional setup"
                ),
                "complexity": DimensionScore(
                    score=3.0,
                    explanation="Rich feature set requires learning, but well-documented"
                ),
                "ecosystem": DimensionScore(
                    score=4.5,
                    explanation="Mature ecosystem with extensive extensions and tooling"
                ),
                "performance": DimensionScore(
                    score=4.5,
                    explanation="Excellent performance for complex queries and ACID compliance"
                )
            },
            pros=[
                "ACID compliance and strong consistency",
                "Rich data types including JSON, arrays, and custom types",
                "Powerful query capabilities and indexing",
                "Extensive extension ecosystem",
                "Strong community and enterprise support"
            ],
            cons=[
                "Can be overkill for simple applications",
                "Requires more memory than simpler databases",
                "Horizontal scaling requires additional complexity",
                "Steeper learning curve for advanced features"
            ],
            best_for=[
                "Applications requiring complex queries and transactions",
                "Data integrity critical applications",
                "Applications with varied data types",
                "Analytics and reporting workloads",
                "Teams with database expertise"
            ],
            metadata=TechnologyMetadata(
                maturity=MaturityLevel.MATURE,
                license="PostgreSQL License",
                maintainer="PostgreSQL Global Development Group"
            )
        )
        
        # MongoDB
        knowledge_base["MongoDB"] = TechnologyProfile(
            name="MongoDB",
            category="Database",
            dimensions={
                "cost": DimensionScore(
                    score=3.5,
                    explanation="Free community version, but enterprise features require licensing"
                ),
                "scalability": DimensionScore(
                    score=5.0,
                    explanation="Excellent horizontal scaling with built-in sharding"
                ),
                "complexity": DimensionScore(
                    score=4.0,
                    explanation="Easy to get started, but requires understanding of NoSQL concepts"
                ),
                "ecosystem": DimensionScore(
                    score=4.0,
                    explanation="Good ecosystem with strong driver support across languages"
                ),
                "performance": DimensionScore(
                    score=4.0,
                    explanation="Good performance for read-heavy workloads and flexible schemas"
                )
            },
            pros=[
                "Flexible schema design and rapid development",
                "Excellent horizontal scaling capabilities",
                "Native JSON document storage",
                "Strong aggregation pipeline for analytics",
                "Good performance for read-heavy applications"
            ],
            cons=[
                "Eventual consistency can complicate some use cases",
                "Less mature tooling compared to relational databases",
                "Can lead to data duplication and inconsistency",
                "Memory usage can be higher than relational databases"
            ],
            best_for=[
                "Rapid prototyping and agile development",
                "Applications with evolving data schemas",
                "Content management and catalog systems",
                "Real-time analytics and logging",
                "Microservices with independent data models"
            ],
            metadata=TechnologyMetadata(
                maturity=MaturityLevel.MATURE,
                license="SSPL",
                maintainer="MongoDB Inc."
            )
        )
        
        return knowledge_base
    
    def get_technology_profile(self, technology_name: str) -> Optional[TechnologyProfile]:
        """
        Retrieve a technology profile from the knowledge base.
        
        Args:
            technology_name: Name of the technology to retrieve
            
        Returns:
            TechnologyProfile if found, None otherwise
        """
        if not technology_name or not technology_name.strip():
            return None
            
        # Try exact match first
        profile = self._knowledge_base.get(technology_name)
        if profile:
            return profile
        
        # Try case-insensitive match
        for known_tech, profile in self._knowledge_base.items():
            if known_tech.lower() == technology_name.lower():
                return profile
        
        # Try partial matches for common abbreviations
        normalized_input = technology_name.lower().strip()
        for known_tech, profile in self._knowledge_base.items():
            known_lower = known_tech.lower()
            
            # Check if input is contained in known tech name
            if normalized_input in known_lower or known_lower in normalized_input:
                return profile
            
            # Check for common abbreviations
            if self._is_abbreviation_match(normalized_input, known_lower):
                return profile
        
        return None
    
    def get_technology_profile_with_fallback(self, technology_name: str) -> TechnologyProfile:
        """
        Retrieve a technology profile with fallback to generic profile if not found.
        
        Args:
            technology_name: Name of the technology to retrieve
            
        Returns:
            TechnologyProfile (either from knowledge base or generic fallback)
            
        Raises:
            TechnologyNotFoundError: If technology not found and no fallback possible
        """
        profile = self.get_technology_profile(technology_name)
        if profile:
            return profile
        
        # Generate suggestions for similar technologies
        suggestions = self.suggest_similar_technologies(technology_name)
        
        # Create a generic fallback profile with neutral scores
        try:
            fallback_profile = self._create_fallback_profile(technology_name)
            return fallback_profile
        except Exception as e:
            raise TechnologyNotFoundError(technology_name, suggestions) from e
    
    def is_known_technology(self, technology_name: str) -> bool:
        """
        Check if a technology is in the knowledge base.
        
        Args:
            technology_name: Name of the technology to check
            
        Returns:
            True if technology is known, False otherwise
        """
        return technology_name in self._knowledge_base
    
    def get_known_technologies(self) -> List[str]:
        """
        Get list of all known technology names.
        
        Returns:
            List of technology names in the knowledge base
        """
        return list(self._knowledge_base.keys())
    
    def get_technologies_by_category(self, category: str) -> List[str]:
        """
        Get all technologies in a specific category.
        
        Args:
            category: Category to filter by (e.g., "API", "Database")
            
        Returns:
            List of technology names in the specified category
        """
        return [
            name for name, profile in self._knowledge_base.items()
            if profile.category == category
        ]
    
    def get_available_categories(self) -> Set[str]:
        """
        Get all available technology categories.
        
        Returns:
            Set of category names
        """
        return {profile.category for profile in self._knowledge_base.values()}
    
    def evaluate_dimension(self, technology_name: str, dimension: str) -> Optional[DimensionScore]:
        """
        Evaluate a specific dimension for a technology.
        
        Args:
            technology_name: Name of the technology
            dimension: Dimension to evaluate (e.g., "cost", "scalability")
            
        Returns:
            DimensionScore if technology and dimension exist, None otherwise
        """
        profile = self.get_technology_profile(technology_name)
        if profile and dimension in profile.dimensions:
            return profile.dimensions[dimension]
        return None
    
    def suggest_similar_technologies(self, unknown_tech: str) -> List[str]:
        """
        Suggest similar technology names for unknown technologies using fuzzy matching.
        
        Args:
            unknown_tech: The unrecognized technology name
            
        Returns:
            List[str]: List of suggested similar technology names (up to 5)
        """
        if not unknown_tech or not unknown_tech.strip():
            return []
        
        known_technologies = list(self._knowledge_base.keys())
        
        # Use difflib for fuzzy string matching
        suggestions = difflib.get_close_matches(
            unknown_tech, 
            known_technologies, 
            n=5,  # Return up to 5 suggestions
            cutoff=0.3  # Minimum similarity threshold
        )
        
        # If no close matches, try partial matching
        if not suggestions:
            unknown_lower = unknown_tech.lower()
            partial_matches = []
            
            for tech in known_technologies:
                tech_lower = tech.lower()
                
                # Check for partial matches
                if (unknown_lower in tech_lower or 
                    tech_lower in unknown_lower or
                    self._is_abbreviation_match(unknown_lower, tech_lower)):
                    partial_matches.append(tech)
            
            suggestions = partial_matches[:5]
        
        return suggestions
    
    def _is_abbreviation_match(self, abbrev: str, full_name: str) -> bool:
        """
        Check if an abbreviation might match a full technology name.
        
        Args:
            abbrev: Potential abbreviation
            full_name: Full technology name
            
        Returns:
            bool: True if there's a potential match
        """
        if len(abbrev) < 2:
            return False
        
        # Check if abbreviation matches first letters of words
        words = full_name.lower().split()
        if len(words) >= 2:
            first_letters = ''.join(word[0] for word in words if word)
            if abbrev == first_letters:
                return True
        
        # Check for common technology abbreviations
        abbreviation_map = {
            'js': 'javascript',
            'ts': 'typescript', 
            'py': 'python',
            'pg': 'postgresql',
            'mongo': 'mongodb',
            'k8s': 'kubernetes',
            'aws': 'amazon web services'
        }
        
        return abbrev in abbreviation_map and abbreviation_map[abbrev] in full_name.lower()
    
    def _create_fallback_profile(self, technology_name: str) -> TechnologyProfile:
        """
        Create a generic fallback profile for unknown technologies.
        
        Args:
            technology_name: Name of the unknown technology
            
        Returns:
            TechnologyProfile: Generic profile with neutral scores
        """
        # Determine likely category based on name patterns
        category = self._guess_technology_category(technology_name)
        
        # Create neutral dimension scores
        neutral_dimensions = {
            'cost': DimensionScore(
                score=3.0,
                explanation=f"No specific cost data available for {technology_name}"
            ),
            'scalability': DimensionScore(
                score=3.0,
                explanation=f"No specific scalability data available for {technology_name}"
            ),
            'complexity': DimensionScore(
                score=3.0,
                explanation=f"No specific complexity data available for {technology_name}"
            ),
            'ecosystem': DimensionScore(
                score=3.0,
                explanation=f"No specific ecosystem data available for {technology_name}"
            ),
            'performance': DimensionScore(
                score=3.0,
                explanation=f"No specific performance data available for {technology_name}"
            )
        }
        
        return TechnologyProfile(
            name=technology_name,
            category=category,
            dimensions=neutral_dimensions,
            pros=[f"Technology choice for {category.lower()} needs"],
            cons=["Limited analysis data available"],
            best_for=[f"Projects requiring {category.lower()} solutions"],
            metadata=TechnologyMetadata(
                maturity=MaturityLevel.STABLE,  # Assume stable if unknown
                license="Unknown",
                maintainer="Unknown"
            )
        )
    
    def _guess_technology_category(self, technology_name: str) -> str:
        """
        Guess the technology category based on name patterns.
        
        Args:
            technology_name: Name of the technology
            
        Returns:
            str: Guessed category
        """
        name_lower = technology_name.lower()
        
        # Database indicators
        if any(keyword in name_lower for keyword in ['db', 'database', 'sql', 'mongo', 'redis', 'elastic']):
            return "Database"
        
        # API indicators  
        if any(keyword in name_lower for keyword in ['api', 'rest', 'graphql', 'grpc']):
            return "API"
        
        # Cloud service indicators
        if any(keyword in name_lower for keyword in ['aws', 'azure', 'gcp', 'cloud', 'lambda', 'function']):
            return "Cloud Service"
        
        # Frontend framework indicators
        if any(keyword in name_lower for keyword in ['react', 'vue', 'angular', 'svelte', 'frontend', 'ui']):
            return "Frontend Framework"
        
        # Backend framework indicators
        if any(keyword in name_lower for keyword in ['express', 'django', 'flask', 'spring', 'fastapi']):
            return "Backend Framework"
        
        # Default to generic technology
        return "Technology"
    def get_knowledge_base(self) -> Dict[str, TechnologyProfile]:
        """
        Get the complete knowledge base.
        
        Returns:
            Dictionary mapping technology names to profiles
        """
        return self._knowledge_base.copy()
    
    def validate_technology_data(self, technology_name: str) -> Tuple[bool, List[str]]:
        """
        Validate that a technology has complete and consistent data.
        
        Args:
            technology_name: Name of the technology to validate
            
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        profile = self.get_technology_profile(technology_name)
        if not profile:
            return False, [f"Technology '{technology_name}' not found"]
        
        issues = []
        
        # Check required dimensions
        required_dimensions = {'cost', 'scalability', 'complexity', 'ecosystem', 'performance'}
        missing_dimensions = required_dimensions - set(profile.dimensions.keys())
        if missing_dimensions:
            issues.append(f"Missing dimensions: {', '.join(missing_dimensions)}")
        
        # Check dimension scores are in valid range
        for dim_name, dim_score in profile.dimensions.items():
            if not (0 <= dim_score.score <= 5):
                issues.append(f"Invalid score for {dim_name}: {dim_score.score} (must be 0-5)")
            
            if not dim_score.explanation.strip():
                issues.append(f"Empty explanation for {dim_name}")
        
        # Check that pros, cons, and best_for are not empty
        if not profile.pros:
            issues.append("No pros listed")
        if not profile.cons:
            issues.append("No cons listed")
        if not profile.best_for:
            issues.append("No best_for scenarios listed")
        
        return len(issues) == 0, issues