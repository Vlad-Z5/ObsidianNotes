# Architecture Evolution

## Evolution Strategies

Architecture evolution is a systematic approach to transforming legacy systems and enabling continuous architectural improvement. This guide provides comprehensive strategies for legacy modernization, migration patterns, technical debt management, and evolutionary architecture principles.

### Legacy Modernization

Legacy modernization requires careful assessment, strategic planning, and systematic execution to transform aging systems while maintaining business continuity.

#### Legacy System Assessment Framework

```python
import asyncio
import json
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import ast
import subprocess
import os
import logging

class TechnicalDebtSeverity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class ModernizationStrategy(Enum):
    REWRITE = "REWRITE"
    REFACTOR = "REFACTOR"
    REPLACE = "REPLACE"
    RETIRE = "RETIRE"
    RETAIN = "RETAIN"

@dataclass
class LegacyComponent:
    name: str
    type: str
    language: str
    version: str
    dependencies: List[str] = field(default_factory=list)
    lines_of_code: int = 0
    complexity_score: float = 0.0
    last_modified: Optional[datetime] = None
    business_value: str = "UNKNOWN"
    technical_debt_score: float = 0.0
    modernization_priority: int = 0

@dataclass
class AssessmentReport:
    component: LegacyComponent
    findings: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)
    recommended_strategy: Optional[ModernizationStrategy] = None
    estimated_effort_months: float = 0.0
    business_impact: str = "MEDIUM"

class LegacySystemAnalyzer:
    """Comprehensive legacy system analysis and modernization planning"""
    
    def __init__(self, root_path: str):
        self.root_path = root_path
        self.components: Dict[str, LegacyComponent] = {}
        self.assessment_reports: List[AssessmentReport] = []
        self.logger = logging.getLogger(__name__)
        
        # Technology modernization mapping
        self.technology_mapping = {
            'java': {
                'legacy_versions': ['1.4', '1.5', '1.6', '1.7', '8'],
                'current_version': '17',
                'frameworks': {
                    'legacy': ['struts', 'spring-2', 'hibernate-3'],
                    'modern': ['spring-boot', 'spring-cloud', 'microprofile']
                }
            },
            'dotnet': {
                'legacy_versions': ['2.0', '3.5', '4.0', '4.5'],
                'current_version': '6.0',
                'frameworks': {
                    'legacy': ['webforms', 'wcf', 'asmx'],
                    'modern': ['asp.net-core', 'blazor', 'minimal-apis']
                }
            },
            'python': {
                'legacy_versions': ['2.7', '3.5', '3.6'],
                'current_version': '3.11',
                'frameworks': {
                    'legacy': ['django-1.x', 'flask-0.x'],
                    'modern': ['fastapi', 'django-4.x', 'flask-2.x']
                }
            }
        }
    
    async def analyze_system(self) -> Dict[str, Any]:
        """Perform comprehensive legacy system analysis"""
        
        # Discover system components
        await self._discover_components()
        
        # Analyze each component
        for component_name, component in self.components.items():
            report = await self._assess_component(component)
            self.assessment_reports.append(report)
        
        # Generate dependency analysis
        dependency_analysis = await self._analyze_dependencies()
        
        # Calculate modernization roadmap
        roadmap = await self._generate_modernization_roadmap()
        
        return {
            'system_overview': {
                'total_components': len(self.components),
                'total_lines_of_code': sum(c.lines_of_code for c in self.components.values()),
                'average_complexity': sum(c.complexity_score for c in self.components.values()) / len(self.components),
                'high_risk_components': len([r for r in self.assessment_reports if r.business_impact == "HIGH"])
            },
            'components': [
                {
                    'name': comp.name,
                    'type': comp.type,
                    'language': comp.language,
                    'technical_debt_score': comp.technical_debt_score,
                    'modernization_priority': comp.modernization_priority
                }
                for comp in self.components.values()
            ],
            'assessment_reports': [
                {
                    'component_name': report.component.name,
                    'recommended_strategy': report.recommended_strategy.value if report.recommended_strategy else None,
                    'estimated_effort_months': report.estimated_effort_months,
                    'key_findings': report.findings[:3],  # Top 3 findings
                    'critical_risks': [r for r in report.risks if 'critical' in r.lower()]
                }
                for report in self.assessment_reports
            ],
            'dependency_analysis': dependency_analysis,
            'modernization_roadmap': roadmap
        }
    
    async def _discover_components(self) -> None:
        """Discover all components in the legacy system"""
        
        for root, dirs, files in os.walk(self.root_path):
            # Skip common non-source directories
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', 'bin', 'obj']]
            
            for file in files:
                file_path = os.path.join(root, file)
                component = await self._analyze_file(file_path)
                
                if component:
                    # Group files into logical components
                    component_key = self._determine_component_group(file_path)
                    
                    if component_key not in self.components:
                        self.components[component_key] = component
                    else:
                        # Merge file analysis into existing component
                        existing = self.components[component_key]
                        existing.lines_of_code += component.lines_of_code
                        existing.complexity_score = max(existing.complexity_score, component.complexity_score)
                        existing.dependencies.extend(component.dependencies)
                        existing.dependencies = list(set(existing.dependencies))  # Remove duplicates
    
    async def _analyze_file(self, file_path: str) -> Optional[LegacyComponent]:
        """Analyze individual file for legacy characteristics"""
        
        _, ext = os.path.splitext(file_path)
        language_map = {
            '.java': 'java',
            '.cs': 'dotnet',
            '.py': 'python',
            '.js': 'javascript',
            '.php': 'php',
            '.rb': 'ruby',
            '.cpp': 'cpp',
            '.c': 'c'
        }
        
        language = language_map.get(ext.lower())
        if not language:
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Basic metrics
            lines_of_code = len([line for line in content.split('\n') if line.strip() and not line.strip().startswith('//')])
            
            # Get file modification time
            stat = os.stat(file_path)
            last_modified = datetime.fromtimestamp(stat.st_mtime)
            
            # Analyze dependencies
            dependencies = self._extract_dependencies(content, language)
            
            # Calculate complexity score
            complexity_score = self._calculate_complexity(content, language)
            
            # Determine version
            version = self._detect_version(content, language)
            
            component_name = os.path.basename(file_path)
            
            return LegacyComponent(
                name=component_name,
                type=self._determine_component_type(file_path),
                language=language,
                version=version,
                dependencies=dependencies,
                lines_of_code=lines_of_code,
                complexity_score=complexity_score,
                last_modified=last_modified,
                technical_debt_score=self._calculate_technical_debt(content, language, last_modified)
            )
            
        except Exception as e:
            self.logger.warning(f"Error analyzing file {file_path}: {e}")
            return None
    
    def _extract_dependencies(self, content: str, language: str) -> List[str]:
        """Extract dependencies from source code"""
        dependencies = []
        
        if language == 'java':
            # Java imports
            import_pattern = r'import\s+([a-zA-Z0-9_.]+);'
            dependencies.extend(re.findall(import_pattern, content))
            
        elif language == 'python':
            # Python imports
            import_patterns = [
                r'import\s+([a-zA-Z0-9_.]+)',
                r'from\s+([a-zA-Z0-9_.]+)\s+import'
            ]
            for pattern in import_patterns:
                dependencies.extend(re.findall(pattern, content))
                
        elif language == 'dotnet':
            # C# using statements
            using_pattern = r'using\s+([a-zA-Z0-9_.]+);'
            dependencies.extend(re.findall(using_pattern, content))
            
        elif language == 'javascript':
            # JavaScript requires/imports
            patterns = [
                r'require\([\'"]([^\'\"]+)[\'"]\)',
                r'import.*from\s+[\'"]([^\'\"]+)[\'"]'
            ]
            for pattern in patterns:
                dependencies.extend(re.findall(pattern, content))
        
        return list(set(dependencies))  # Remove duplicates
    
    def _calculate_complexity(self, content: str, language: str) -> float:
        """Calculate cyclomatic complexity"""
        
        # Simple complexity based on control flow keywords
        complexity_keywords = {
            'java': ['if', 'else', 'while', 'for', 'switch', 'case', 'catch', 'try'],
            'python': ['if', 'elif', 'else', 'while', 'for', 'try', 'except', 'finally'],
            'dotnet': ['if', 'else', 'while', 'for', 'foreach', 'switch', 'case', 'catch', 'try'],
            'javascript': ['if', 'else', 'while', 'for', 'switch', 'case', 'catch', 'try']
        }
        
        keywords = complexity_keywords.get(language, [])
        complexity_score = 1  # Base complexity
        
        for keyword in keywords:
            # Count occurrences of complexity-inducing keywords
            pattern = r'\b' + keyword + r'\b'
            complexity_score += len(re.findall(pattern, content, re.IGNORECASE))
        
        # Normalize by lines of code
        lines = len(content.split('\n'))
        return complexity_score / max(lines, 1) * 100
    
    def _detect_version(self, content: str, language: str) -> str:
        """Detect technology version from source code"""
        
        version_patterns = {
            'java': [
                r'java\.version.*?([0-9]+\.[0-9]+)',
                r'target.*?([0-9]+\.[0-9]+)',
                r'source.*?([0-9]+\.[0-9]+)'
            ],
            'python': [
                r'python_requires.*?([0-9]+\.[0-9]+)',
                r'version.*?([0-9]+\.[0-9]+\.[0-9]+)'
            ],
            'dotnet': [
                r'TargetFramework.*?([0-9]+\.[0-9]+)',
                r'netstandard([0-9]+\.[0-9]+)',
                r'netcoreapp([0-9]+\.[0-9]+)'
            ]
        }
        
        patterns = version_patterns.get(language, [])
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "unknown"
    
    def _calculate_technical_debt(self, content: str, language: str, last_modified: datetime) -> float:
        """Calculate technical debt score"""
        
        debt_score = 0.0
        
        # Age-based debt (older code = higher debt)
        age_years = (datetime.now() - last_modified).days / 365.25
        debt_score += min(age_years * 10, 50)  # Cap at 50 points
        
        # Code smell detection
        code_smells = {
            'long_method': r'def\s+\w+.*?\n(.*?\n){50,}',  # Methods > 50 lines
            'large_class': r'class\s+\w+.*?\n(.*?\n){500,}',  # Classes > 500 lines
            'magic_numbers': r'\b\d{4,}\b',  # Numbers with 4+ digits
            'dead_code': r'#.*TODO|//.*TODO|/\*.*TODO',  # TODO comments
            'duplicated_code': r'(\w+.*?\n)(.*?\n){2,}\1'  # Simple duplication detection
        }
        
        for smell_name, pattern in code_smells.items():
            matches = len(re.findall(pattern, content, re.MULTILINE | re.DOTALL))
            debt_score += matches * 5
        
        # Technology version debt
        version = self._detect_version(content, language)
        if language in self.technology_mapping:
            legacy_versions = self.technology_mapping[language]['legacy_versions']
            if version in legacy_versions:
                debt_score += 30
        
        return min(debt_score, 100)  # Cap at 100
    
    async def _assess_component(self, component: LegacyComponent) -> AssessmentReport:
        """Assess component and determine modernization strategy"""
        
        report = AssessmentReport(component=component)
        
        # Analyze findings
        if component.technical_debt_score > 70:
            report.findings.append("High technical debt detected")
        
        if component.complexity_score > 20:
            report.findings.append("High complexity - consider refactoring")
        
        if component.last_modified and (datetime.now() - component.last_modified).days > 365:
            report.findings.append("Component not modified in over a year")
        
        # Analyze risks
        if component.language in self.technology_mapping:
            tech_info = self.technology_mapping[component.language]
            if component.version in tech_info['legacy_versions']:
                report.risks.append(f"Using legacy {component.language} version {component.version}")
        
        if component.lines_of_code > 10000:
            report.risks.append("Large component - high migration risk")
        
        if len(component.dependencies) > 50:
            report.risks.append("High dependency count - complex migration")
        
        # Identify opportunities
        if component.technical_debt_score < 30:
            report.opportunities.append("Low technical debt - good modernization candidate")
        
        if component.complexity_score < 10:
            report.opportunities.append("Low complexity - easier to modernize")
        
        # Determine strategy
        report.recommended_strategy = self._determine_strategy(component)
        
        # Estimate effort
        report.estimated_effort_months = self._estimate_effort(component)
        
        # Determine business impact
        report.business_impact = self._assess_business_impact(component)
        
        # Set modernization priority
        component.modernization_priority = self._calculate_priority(component, report)
        
        return report
    
    def _determine_strategy(self, component: LegacyComponent) -> ModernizationStrategy:
        """Determine the best modernization strategy for a component"""
        
        # Decision matrix based on technical debt, complexity, and business value
        if component.technical_debt_score > 80:
            if component.lines_of_code < 1000:
                return ModernizationStrategy.REWRITE
            else:
                return ModernizationStrategy.REPLACE
        
        elif component.technical_debt_score > 50:
            if component.complexity_score < 15:
                return ModernizationStrategy.REFACTOR
            else:
                return ModernizationStrategy.REPLACE
        
        elif component.technical_debt_score > 20:
            return ModernizationStrategy.REFACTOR
        
        else:
            return ModernizationStrategy.RETAIN
    
    def _estimate_effort(self, component: LegacyComponent) -> float:
        """Estimate modernization effort in months"""
        
        base_effort = component.lines_of_code / 1000  # 1 month per 1000 LOC
        
        # Adjust for complexity
        complexity_multiplier = 1 + (component.complexity_score / 100)
        
        # Adjust for technical debt
        debt_multiplier = 1 + (component.technical_debt_score / 100)
        
        # Adjust for dependencies
        dependency_multiplier = 1 + (len(component.dependencies) / 100)
        
        total_effort = base_effort * complexity_multiplier * debt_multiplier * dependency_multiplier
        
        return round(total_effort, 1)
    
    def _assess_business_impact(self, component: LegacyComponent) -> str:
        """Assess business impact of modernizing component"""
        
        # This would typically integrate with business stakeholder input
        # For now, use heuristics based on technical characteristics
        
        if component.lines_of_code > 5000:
            return "HIGH"
        elif component.lines_of_code > 1000:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _calculate_priority(self, component: LegacyComponent, report: AssessmentReport) -> int:
        """Calculate modernization priority (1-10, 10 being highest)"""
        
        priority = 5  # Base priority
        
        # Increase priority for high technical debt
        if component.technical_debt_score > 70:
            priority += 3
        elif component.technical_debt_score > 50:
            priority += 2
        
        # Increase priority for high business impact
        if report.business_impact == "HIGH":
            priority += 2
        elif report.business_impact == "MEDIUM":
            priority += 1
        
        # Decrease priority for high effort
        if report.estimated_effort_months > 12:
            priority -= 2
        elif report.estimated_effort_months > 6:
            priority -= 1
        
        # Increase priority for critical risks
        critical_risks = [r for r in report.risks if 'critical' in r.lower()]
        priority += len(critical_risks)
        
        return max(1, min(10, priority))
    
    async def _analyze_dependencies(self) -> Dict[str, Any]:
        """Analyze component dependencies and identify bottlenecks"""
        
        dependency_graph = {}
        circular_dependencies = []
        
        for component_name, component in self.components.items():
            dependency_graph[component_name] = {
                'depends_on': [],
                'depended_by': []
            }
        
        # Build dependency relationships
        for component_name, component in self.components.items():
            for dep in component.dependencies:
                # Find internal dependencies (components within the system)
                matching_components = [name for name in self.components.keys() if dep in name]
                
                for matching_comp in matching_components:
                    if matching_comp != component_name:
                        dependency_graph[component_name]['depends_on'].append(matching_comp)
                        dependency_graph[matching_comp]['depended_by'].append(component_name)
        
        # Detect circular dependencies (simplified)
        for component_name in dependency_graph:
            if self._has_circular_dependency(component_name, dependency_graph, set()):
                circular_dependencies.append(component_name)
        
        # Identify highly coupled components
        high_coupling = []
        for component_name, deps in dependency_graph.items():
            total_coupling = len(deps['depends_on']) + len(deps['depended_by'])
            if total_coupling > 10:  # Threshold for high coupling
                high_coupling.append({
                    'component': component_name,
                    'coupling_score': total_coupling
                })
        
        return {
            'dependency_graph': dependency_graph,
            'circular_dependencies': circular_dependencies,
            'high_coupling_components': sorted(high_coupling, key=lambda x: x['coupling_score'], reverse=True),
            'total_dependencies': sum(len(deps['depends_on']) for deps in dependency_graph.values())
        }
    
    def _has_circular_dependency(self, component: str, graph: Dict, visited: set) -> bool:
        """Detect circular dependencies using DFS"""
        if component in visited:
            return True
        
        visited.add(component)
        
        for dependent in graph.get(component, {}).get('depends_on', []):
            if self._has_circular_dependency(dependent, graph, visited.copy()):
                return True
        
        return False
    
    async def _generate_modernization_roadmap(self) -> Dict[str, Any]:
        """Generate prioritized modernization roadmap"""
        
        # Sort components by priority
        sorted_components = sorted(
            self.assessment_reports,
            key=lambda r: r.component.modernization_priority,
            reverse=True
        )
        
        # Group into phases
        phases = {
            'Phase 1 (0-6 months)': [],
            'Phase 2 (6-12 months)': [],
            'Phase 3 (12-18 months)': [],
            'Phase 4 (18+ months)': []
        }
        
        cumulative_effort = 0
        
        for report in sorted_components:
            cumulative_effort += report.estimated_effort_months
            
            if cumulative_effort <= 6:
                phase = 'Phase 1 (0-6 months)'
            elif cumulative_effort <= 12:
                phase = 'Phase 2 (6-12 months)'
            elif cumulative_effort <= 18:
                phase = 'Phase 3 (12-18 months)'
            else:
                phase = 'Phase 4 (18+ months)'
            
            phases[phase].append({
                'component': report.component.name,
                'strategy': report.recommended_strategy.value,
                'effort_months': report.estimated_effort_months,
                'priority': report.component.modernization_priority,
                'business_impact': report.business_impact
            })
        
        return {
            'phases': phases,
            'total_effort_months': cumulative_effort,
            'high_priority_count': len([r for r in sorted_components if r.component.modernization_priority >= 8]),
            'quick_wins': [
                {
                    'component': r.component.name,
                    'effort_months': r.estimated_effort_months
                }
                for r in sorted_components
                if r.estimated_effort_months <= 2 and r.component.modernization_priority >= 7
            ]
        }
    
    def _determine_component_group(self, file_path: str) -> str:
        """Determine logical component grouping for a file"""
        
        # Group by directory structure
        relative_path = os.path.relpath(file_path, self.root_path)
        path_parts = relative_path.split(os.sep)
        
        if len(path_parts) > 1:
            # Use first two levels of directory structure
            return os.path.join(path_parts[0], path_parts[1] if len(path_parts) > 1 else '')
        else:
            return path_parts[0]
    
    def _determine_component_type(self, file_path: str) -> str:
        """Determine component type based on file characteristics"""
        
        filename = os.path.basename(file_path).lower()
        
        if 'controller' in filename or 'servlet' in filename:
            return 'web_controller'
        elif 'service' in filename or 'business' in filename:
            return 'business_service'
        elif 'repository' in filename or 'dao' in filename or 'data' in filename:
            return 'data_access'
        elif 'model' in filename or 'entity' in filename or 'dto' in filename:
            return 'data_model'
        elif 'util' in filename or 'helper' in filename:
            return 'utility'
        elif 'test' in filename:
            return 'test'
        else:
            return 'application'
```

### Migration Patterns

Migration patterns provide proven approaches for safely transitioning from legacy systems to modern architectures while minimizing business disruption.

#### Strangler Fig Pattern Implementation

```python
import asyncio
import aiohttp
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import logging
import time

class MigrationPhase(Enum):
    PLANNING = "PLANNING"
    PILOT = "PILOT"
    GRADUAL_MIGRATION = "GRADUAL_MIGRATION"
    LEGACY_RETIREMENT = "LEGACY_RETIREMENT"
    COMPLETE = "COMPLETE"

class RouteStrategy(Enum):
    LEGACY_ONLY = "LEGACY_ONLY"
    NEW_ONLY = "NEW_ONLY"
    CANARY = "CANARY"
    AB_TEST = "AB_TEST"
    FEATURE_FLAG = "FEATURE_FLAG"

@dataclass
class MigrationRule:
    pattern: str
    strategy: RouteStrategy
    new_service_url: str
    legacy_service_url: str
    traffic_percentage: int = 0  # Percentage to route to new service
    enabled: bool = True
    conditions: Dict[str, Any] = field(default_factory=dict)
    rollback_triggers: List[str] = field(default_factory=list)

@dataclass
class MigrationMetrics:
    rule_pattern: str
    requests_total: int = 0
    requests_legacy: int = 0
    requests_new: int = 0
    errors_legacy: int = 0
    errors_new: int = 0
    latency_legacy_ms: float = 0.0
    latency_new_ms: float = 0.0
    success_rate_legacy: float = 100.0
    success_rate_new: float = 100.0
    last_updated: datetime = field(default_factory=datetime.utcnow)

class StranglerFigProxy:
    """Strangler Fig Pattern implementation for gradual system migration"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.migration_rules: List[MigrationRule] = []
        self.metrics: Dict[str, MigrationMetrics] = {}
        self.feature_flags: Dict[str, bool] = {}
        self.circuit_breakers: Dict[str, 'CircuitBreaker'] = {}
        self.logger = logging.getLogger(__name__)
        
        # Load migration rules from configuration
        self._load_migration_rules()
        
        # Initialize circuit breakers for both legacy and new services
        self._initialize_circuit_breakers()
    
    async def route_request(
        self, 
        request_path: str, 
        request_method: str,
        request_headers: Dict[str, str],
        request_body: Optional[str] = None,
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Route request based on migration rules and strategies"""
        
        # Find matching migration rule
        matching_rule = self._find_matching_rule(request_path, request_method)
        
        if not matching_rule:
            # No migration rule found, route to legacy by default
            return await self._route_to_legacy(request_path, request_method, request_headers, request_body)
        
        # Update metrics
        self._update_request_metrics(matching_rule.pattern)
        
        # Determine routing based on strategy
        if matching_rule.strategy == RouteStrategy.LEGACY_ONLY:
            return await self._route_to_legacy(request_path, request_method, request_headers, request_body, matching_rule)
        
        elif matching_rule.strategy == RouteStrategy.NEW_ONLY:
            return await self._route_to_new_service(request_path, request_method, request_headers, request_body, matching_rule)
        
        elif matching_rule.strategy == RouteStrategy.CANARY:
            return await self._route_canary(request_path, request_method, request_headers, request_body, matching_rule)
        
        elif matching_rule.strategy == RouteStrategy.AB_TEST:
            return await self._route_ab_test(request_path, request_method, request_headers, request_body, matching_rule, user_context)
        
        elif matching_rule.strategy == RouteStrategy.FEATURE_FLAG:
            return await self._route_feature_flag(request_path, request_method, request_headers, request_body, matching_rule, user_context)
        
        else:
            # Default to legacy
            return await self._route_to_legacy(request_path, request_method, request_headers, request_body, matching_rule)
    
    async def _route_canary(
        self,
        request_path: str,
        request_method: str,
        request_headers: Dict[str, str],
        request_body: Optional[str],
        rule: MigrationRule
    ) -> Dict[str, Any]:
        """Route request using canary deployment strategy"""
        
        # Determine if request should go to new service based on traffic percentage
        import random
        should_route_to_new = random.randint(1, 100) <= rule.traffic_percentage
        
        if should_route_to_new:
            # Check circuit breaker for new service
            circuit_breaker = self.circuit_breakers.get(f"new_{rule.pattern}")
            
            if circuit_breaker and circuit_breaker.is_open():
                self.logger.warning(f"Circuit breaker open for new service {rule.pattern}, routing to legacy")
                return await self._route_to_legacy(request_path, request_method, request_headers, request_body, rule)
            
            try:
                response = await self._route_to_new_service(request_path, request_method, request_headers, request_body, rule)
                
                # Check response quality
                if await self._is_response_acceptable(response, rule):
                    return response
                else:
                    # Fallback to legacy if response quality is poor
                    self.logger.warning(f"Poor response quality from new service {rule.pattern}, falling back to legacy")
                    return await self._route_to_legacy(request_path, request_method, request_headers, request_body, rule)
                    
            except Exception as e:
                self.logger.error(f"Error routing to new service {rule.pattern}: {e}")
                # Fallback to legacy on error
                return await self._route_to_legacy(request_path, request_method, request_headers, request_body, rule)
        else:
            return await self._route_to_legacy(request_path, request_method, request_headers, request_body, rule)
    
    async def _route_to_legacy(
        self,
        request_path: str,
        request_method: str,
        request_headers: Dict[str, str],
        request_body: Optional[str],
        rule: Optional[MigrationRule] = None
    ) -> Dict[str, Any]:
        """Route request to legacy service"""
        
        start_time = time.perf_counter()
        
        try:
            legacy_url = rule.legacy_service_url if rule else self.config['default_legacy_url']
            full_url = f"{legacy_url.rstrip('/')}{request_path}"
            
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=request_method,
                    url=full_url,
                    headers=request_headers,
                    data=request_body,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    response_data = await response.text()
                    response_headers = dict(response.headers)
                    
                    # Update metrics
                    if rule:
                        self._update_response_metrics(rule.pattern, 'legacy', 
                                                    time.perf_counter() - start_time, 
                                                    response.status < 400)
                    
                    return {
                        'status_code': response.status,
                        'headers': response_headers,
                        'body': response_data,
                        'source': 'legacy',
                        'rule_pattern': rule.pattern if rule else 'default'
                    }
                    
        except Exception as e:
            self.logger.error(f"Error routing to legacy service: {e}")
            
            if rule:
                self._update_response_metrics(rule.pattern, 'legacy', 
                                            time.perf_counter() - start_time, False)
            
            return {
                'status_code': 500,
                'headers': {},
                'body': json.dumps({'error': 'Legacy service unavailable'}),
                'source': 'legacy',
                'error': str(e)
            }
    
    async def _route_to_new_service(
        self,
        request_path: str,
        request_method: str,
        request_headers: Dict[str, str],
        request_body: Optional[str],
        rule: MigrationRule
    ) -> Dict[str, Any]:
        """Route request to new service"""
        
        start_time = time.perf_counter()
        
        try:
            full_url = f"{rule.new_service_url.rstrip('/')}{request_path}"
            
            # Transform request if needed (for API compatibility)
            transformed_headers = await self._transform_request_headers(request_headers, rule)
            transformed_body = await self._transform_request_body(request_body, rule)
            
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=request_method,
                    url=full_url,
                    headers=transformed_headers,
                    data=transformed_body,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    response_data = await response.text()
                    response_headers = dict(response.headers)
                    
                    # Transform response if needed
                    transformed_response = await self._transform_response(response_data, response_headers, rule)
                    
                    # Update metrics
                    self._update_response_metrics(rule.pattern, 'new', 
                                                time.perf_counter() - start_time, 
                                                response.status < 400)
                    
                    return {
                        'status_code': response.status,
                        'headers': transformed_response['headers'],
                        'body': transformed_response['body'],
                        'source': 'new',
                        'rule_pattern': rule.pattern
                    }
                    
        except Exception as e:
            self.logger.error(f"Error routing to new service {rule.pattern}: {e}")
            
            self._update_response_metrics(rule.pattern, 'new', 
                                        time.perf_counter() - start_time, False)
            
            # Circuit breaker logic
            circuit_breaker = self.circuit_breakers.get(f"new_{rule.pattern}")
            if circuit_breaker:
                circuit_breaker.record_failure()
            
            raise e
    
    def _find_matching_rule(self, request_path: str, request_method: str) -> Optional[MigrationRule]:
        """Find migration rule that matches the request"""
        
        for rule in self.migration_rules:
            if not rule.enabled:
                continue
            
            # Simple pattern matching (could be enhanced with regex)
            if rule.pattern in request_path:
                # Check method-specific conditions if configured
                if 'methods' in rule.conditions:
                    if request_method.upper() not in rule.conditions['methods']:
                        continue
                
                return rule
        
        return None
    
    async def _is_response_acceptable(self, response: Dict[str, Any], rule: MigrationRule) -> bool:
        """Check if response from new service meets quality criteria"""
        
        # Check status code
        if response['status_code'] >= 500:
            return False
        
        # Check response time (if configured)
        if 'max_response_time_ms' in rule.conditions:
            # This would need to be tracked separately in actual implementation
            pass
        
        # Check response format/content if needed
        if 'response_validation' in rule.conditions:
            # Implement custom response validation logic
            pass
        
        return True
    
    async def _transform_request_headers(self, headers: Dict[str, str], rule: MigrationRule) -> Dict[str, str]:
        """Transform request headers for new service compatibility"""
        
        transformed = headers.copy()
        
        # Add any required headers for new service
        if 'header_transformations' in rule.conditions:
            transformations = rule.conditions['header_transformations']
            
            for header_name, transformation in transformations.items():
                if transformation['action'] == 'add':
                    transformed[header_name] = transformation['value']
                elif transformation['action'] == 'remove':
                    transformed.pop(header_name, None)
                elif transformation['action'] == 'rename':
                    if header_name in transformed:
                        transformed[transformation['new_name']] = transformed.pop(header_name)
        
        return transformed
    
    async def _transform_request_body(self, body: Optional[str], rule: MigrationRule) -> Optional[str]:
        """Transform request body for new service compatibility"""
        
        if not body or 'body_transformations' not in rule.conditions:
            return body
        
        # Implement body transformation logic based on rule configuration
        # This could include JSON field mapping, format conversion, etc.
        
        return body
    
    async def _transform_response(
        self, 
        response_body: str, 
        response_headers: Dict[str, str], 
        rule: MigrationRule
    ) -> Dict[str, Any]:
        """Transform response from new service to match legacy format"""
        
        # Default - no transformation
        transformed = {
            'body': response_body,
            'headers': response_headers
        }
        
        if 'response_transformations' in rule.conditions:
            # Implement response transformation logic
            # This could include JSON field mapping, format conversion, etc.
            pass
        
        return transformed
    
    def _update_request_metrics(self, pattern: str) -> None:
        """Update request metrics for a pattern"""
        if pattern not in self.metrics:
            self.metrics[pattern] = MigrationMetrics(rule_pattern=pattern)
        
        self.metrics[pattern].requests_total += 1
        self.metrics[pattern].last_updated = datetime.utcnow()
    
    def _update_response_metrics(
        self, 
        pattern: str, 
        service_type: str, 
        response_time: float, 
        success: bool
    ) -> None:
        """Update response metrics for a pattern and service"""
        
        if pattern not in self.metrics:
            self.metrics[pattern] = MigrationMetrics(rule_pattern=pattern)
        
        metrics = self.metrics[pattern]
        response_time_ms = response_time * 1000
        
        if service_type == 'legacy':
            metrics.requests_legacy += 1
            if success:
                # Update rolling average latency
                if metrics.latency_legacy_ms == 0:
                    metrics.latency_legacy_ms = response_time_ms
                else:
                    metrics.latency_legacy_ms = (metrics.latency_legacy_ms * 0.9) + (response_time_ms * 0.1)
            else:
                metrics.errors_legacy += 1
            
            # Calculate success rate
            total_legacy = metrics.requests_legacy
            success_legacy = total_legacy - metrics.errors_legacy
            metrics.success_rate_legacy = (success_legacy / total_legacy) * 100 if total_legacy > 0 else 100
            
        elif service_type == 'new':
            metrics.requests_new += 1
            if success:
                # Update rolling average latency
                if metrics.latency_new_ms == 0:
                    metrics.latency_new_ms = response_time_ms
                else:
                    metrics.latency_new_ms = (metrics.latency_new_ms * 0.9) + (response_time_ms * 0.1)
            else:
                metrics.errors_new += 1
            
            # Calculate success rate
            total_new = metrics.requests_new
            success_new = total_new - metrics.errors_new
            metrics.success_rate_new = (success_new / total_new) * 100 if total_new > 0 else 100
        
        metrics.last_updated = datetime.utcnow()
    
    def _load_migration_rules(self) -> None:
        """Load migration rules from configuration"""
        
        rules_config = self.config.get('migration_rules', [])
        
        for rule_config in rules_config:
            rule = MigrationRule(
                pattern=rule_config['pattern'],
                strategy=RouteStrategy(rule_config['strategy']),
                new_service_url=rule_config['new_service_url'],
                legacy_service_url=rule_config['legacy_service_url'],
                traffic_percentage=rule_config.get('traffic_percentage', 0),
                enabled=rule_config.get('enabled', True),
                conditions=rule_config.get('conditions', {}),
                rollback_triggers=rule_config.get('rollback_triggers', [])
            )
            
            self.migration_rules.append(rule)
    
    def _initialize_circuit_breakers(self) -> None:
        """Initialize circuit breakers for services"""
        
        for rule in self.migration_rules:
            # Circuit breaker for new service
            self.circuit_breakers[f"new_{rule.pattern}"] = CircuitBreaker(
                failure_threshold=5,
                timeout_seconds=60,
                expected_exception=Exception
            )
            
            # Circuit breaker for legacy service
            self.circuit_breakers[f"legacy_{rule.pattern}"] = CircuitBreaker(
                failure_threshold=10,  # Higher threshold for legacy (more tolerant)
                timeout_seconds=60,
                expected_exception=Exception
            )
    
    async def get_migration_status(self) -> Dict[str, Any]:
        """Get comprehensive migration status and metrics"""
        
        status = {
            'migration_rules': [
                {
                    'pattern': rule.pattern,
                    'strategy': rule.strategy.value,
                    'traffic_percentage': rule.traffic_percentage,
                    'enabled': rule.enabled
                }
                for rule in self.migration_rules
            ],
            'metrics': {
                pattern: {
                    'requests_total': metrics.requests_total,
                    'requests_legacy': metrics.requests_legacy,
                    'requests_new': metrics.requests_new,
                    'success_rate_legacy': metrics.success_rate_legacy,
                    'success_rate_new': metrics.success_rate_new,
                    'latency_legacy_ms': metrics.latency_legacy_ms,
                    'latency_new_ms': metrics.latency_new_ms,
                    'migration_percentage': (metrics.requests_new / metrics.requests_total * 100) if metrics.requests_total > 0 else 0
                }
                for pattern, metrics in self.metrics.items()
            },
            'circuit_breakers': {
                name: {
                    'state': cb.state,
                    'failure_count': cb.failure_count,
                    'last_failure_time': cb.last_failure_time.isoformat() if cb.last_failure_time else None
                }
                for name, cb in self.circuit_breakers.items()
            },
            'overall_migration_progress': self._calculate_overall_progress()
        }
        
        return status
    
    def _calculate_overall_progress(self) -> float:
        """Calculate overall migration progress as percentage"""
        
        if not self.metrics:
            return 0.0
        
        total_requests = sum(metrics.requests_total for metrics in self.metrics.values())
        total_new_requests = sum(metrics.requests_new for metrics in self.metrics.values())
        
        return (total_new_requests / total_requests * 100) if total_requests > 0 else 0.0

class CircuitBreaker:
    """Simple circuit breaker implementation"""
    
    def __init__(self, failure_threshold: int = 5, timeout_seconds: int = 60, expected_exception: type = Exception):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def is_open(self) -> bool:
        """Check if circuit breaker is open"""
        
        if self.state == 'OPEN':
            # Check if timeout has passed
            if self.last_failure_time and (datetime.utcnow() - self.last_failure_time).seconds >= self.timeout_seconds:
                self.state = 'HALF_OPEN'
                return False
            return True
        
        return False
    
    def record_success(self) -> None:
        """Record successful request"""
        self.failure_count = 0
        self.state = 'CLOSED'
    
    def record_failure(self) -> None:
        """Record failed request"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
```

This comprehensive Architecture Evolution guide provides production-ready implementations for legacy system assessment, strangler fig migration patterns, evolutionary architecture principles, and technical debt management. Each component is designed to enable safe, systematic transformation of legacy systems while maintaining business continuity.