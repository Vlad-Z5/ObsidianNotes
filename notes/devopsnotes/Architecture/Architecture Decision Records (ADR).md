# Architecture Decision Records (ADR)

## ADR Framework

Architecture Decision Records (ADRs) are a systematic way of documenting and tracking architectural decisions throughout a project's lifecycle. They provide transparency, accountability, and historical context for architectural choices, enabling teams to understand the reasoning behind decisions and their long-term consequences.

### ADR Structure

**Definition:** A standardized format for documenting architectural decisions that ensures consistency and completeness across all decision records.

#### Core ADR Template
```markdown
# ADR-XXX: [Decision Title]

## Status
[Proposed | Accepted | Rejected | Deprecated | Superseded by ADR-YYY]

## Context
[What is the issue that we're seeing that is motivating this decision or change?]

## Decision
[What is the change that we're proposing or have agreed to implement?]

## Consequences
[What becomes easier or more difficult to do and any risks introduced by this change?]

## Alternatives Considered
[What other options did we consider and why were they rejected?]

## References
[Links to supporting documentation, research, or related ADRs]
```

#### Implementation - ADR Management System
```python
import os
import re
import json
import yaml
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

class ADRStatus(Enum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DEPRECATED = "deprecated"
    SUPERSEDED = "superseded"

class ADRCategory(Enum):
    TECHNOLOGY = "technology"
    ARCHITECTURE = "architecture"
    PROCESS = "process"
    SECURITY = "security"
    PERFORMANCE = "performance"
    INTEGRATION = "integration"

@dataclass
class ADRMetadata:
    """Metadata for tracking and analysis"""
    author: str
    reviewers: List[str]
    stakeholders: List[str]
    created_date: datetime
    last_modified: datetime
    review_date: Optional[datetime] = None
    implementation_deadline: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    impact_level: str = "medium"  # low, medium, high, critical

@dataclass
class Alternative:
    """Alternative option considered"""
    name: str
    description: str
    pros: List[str]
    cons: List[str]
    cost_estimate: Optional[str] = None
    implementation_complexity: str = "medium"

@dataclass
class Consequence:
    """Consequence of the decision"""
    type: str  # positive, negative, neutral
    description: str
    impact_area: str  # performance, security, maintainability, cost, etc.
    likelihood: str = "medium"  # low, medium, high
    mitigation: Optional[str] = None

@dataclass
class ArchitectureDecisionRecord:
    """Complete ADR structure"""
    adr_id: str
    title: str
    status: ADRStatus
    context: str
    decision: str
    consequences: List[Consequence]
    alternatives: List[Alternative]
    metadata: ADRMetadata
    category: ADRCategory
    superseded_by: Optional[str] = None
    supersedes: Optional[str] = None
    references: List[str] = field(default_factory=list)

class ADRManager:
    """Comprehensive ADR management system"""
    
    def __init__(self, adr_directory: str = "./docs/adrs"):
        self.adr_directory = Path(adr_directory)
        self.adr_directory.mkdir(parents=True, exist_ok=True)
        self.adrs = {}
        self.load_existing_adrs()
    
    def create_adr(self, title: str, context: str, decision: str, 
                   author: str, category: ADRCategory) -> str:
        """Create a new ADR with proposed status"""
        adr_id = self._generate_adr_id()
        
        metadata = ADRMetadata(
            author=author,
            reviewers=[],
            stakeholders=[],
            created_date=datetime.utcnow(),
            last_modified=datetime.utcnow()
        )
        
        adr = ArchitectureDecisionRecord(
            adr_id=adr_id,
            title=title,
            status=ADRStatus.PROPOSED,
            context=context,
            decision=decision,
            consequences=[],
            alternatives=[],
            metadata=metadata,
            category=category
        )
        
        self.adrs[adr_id] = adr
        self._save_adr(adr)
        
        return adr_id
    
    def add_alternative(self, adr_id: str, alternative: Alternative):
        """Add alternative option to ADR"""
        if adr_id not in self.adrs:
            raise ValueError(f"ADR {adr_id} not found")
        
        self.adrs[adr_id].alternatives.append(alternative)
        self._update_modified_date(adr_id)
        self._save_adr(self.adrs[adr_id])
    
    def add_consequence(self, adr_id: str, consequence: Consequence):
        """Add consequence to ADR"""
        if adr_id not in self.adrs:
            raise ValueError(f"ADR {adr_id} not found")
        
        self.adrs[adr_id].consequences.append(consequence)
        self._update_modified_date(adr_id)
        self._save_adr(self.adrs[adr_id])
    
    def update_status(self, adr_id: str, new_status: ADRStatus, 
                     reviewer: str, comments: str = None):
        """Update ADR status with approval workflow"""
        if adr_id not in self.adrs:
            raise ValueError(f"ADR {adr_id} not found")
        
        adr = self.adrs[adr_id]
        old_status = adr.status
        
        # Validate status transition
        valid_transitions = {
            ADRStatus.PROPOSED: [ADRStatus.ACCEPTED, ADRStatus.REJECTED],
            ADRStatus.ACCEPTED: [ADRStatus.DEPRECATED, ADRStatus.SUPERSEDED],
            ADRStatus.REJECTED: [ADRStatus.PROPOSED],  # Can be reconsidered
            ADRStatus.DEPRECATED: [ADRStatus.SUPERSEDED],
            ADRStatus.SUPERSEDED: []  # Final state
        }
        
        if new_status not in valid_transitions.get(old_status, []):
            raise ValueError(f"Invalid status transition from {old_status.value} to {new_status.value}")
        
        adr.status = new_status
        if reviewer not in adr.metadata.reviewers:
            adr.metadata.reviewers.append(reviewer)
        
        self._update_modified_date(adr_id)
        self._save_adr(adr)
        
        # Log status change
        self._log_status_change(adr_id, old_status, new_status, reviewer, comments)
    
    def supersede_adr(self, old_adr_id: str, new_adr_id: str):
        """Mark an ADR as superseded by another"""
        if old_adr_id not in self.adrs or new_adr_id not in self.adrs:
            raise ValueError("Both ADRs must exist")
        
        self.adrs[old_adr_id].status = ADRStatus.SUPERSEDED
        self.adrs[old_adr_id].superseded_by = new_adr_id
        self.adrs[new_adr_id].supersedes = old_adr_id
        
        self._update_modified_date(old_adr_id)
        self._update_modified_date(new_adr_id)
        
        self._save_adr(self.adrs[old_adr_id])
        self._save_adr(self.adrs[new_adr_id])
    
    def search_adrs(self, query: str = None, status: ADRStatus = None, 
                   category: ADRCategory = None, author: str = None) -> List[ArchitectureDecisionRecord]:
        """Search ADRs by various criteria"""
        results = list(self.adrs.values())
        
        if query:
            query_lower = query.lower()
            results = [adr for adr in results 
                      if query_lower in adr.title.lower() 
                      or query_lower in adr.context.lower() 
                      or query_lower in adr.decision.lower()]
        
        if status:
            results = [adr for adr in results if adr.status == status]
        
        if category:
            results = [adr for adr in results if adr.category == category]
        
        if author:
            results = [adr for adr in results if adr.metadata.author == author]
        
        return sorted(results, key=lambda x: x.metadata.created_date, reverse=True)
    
    def generate_decision_report(self, include_proposed: bool = True) -> Dict:
        """Generate comprehensive decision report"""
        adrs_to_include = []
        
        for adr in self.adrs.values():
            if not include_proposed and adr.status == ADRStatus.PROPOSED:
                continue
            adrs_to_include.append(adr)
        
        # Statistics
        status_counts = {}
        category_counts = {}
        author_counts = {}
        
        for adr in adrs_to_include:
            # Status distribution
            status = adr.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Category distribution
            category = adr.category.value
            category_counts[category] = category_counts.get(category, 0) + 1
            
            # Author activity
            author = adr.metadata.author
            author_counts[author] = author_counts.get(author, 0) + 1
        
        # Recent activity
        recent_adrs = sorted(adrs_to_include, 
                           key=lambda x: x.metadata.last_modified, 
                           reverse=True)[:10]
        
        # Pending reviews
        pending_reviews = [adr for adr in adrs_to_include 
                          if adr.status == ADRStatus.PROPOSED]
        
        return {
            'summary': {
                'total_adrs': len(adrs_to_include),
                'status_distribution': status_counts,
                'category_distribution': category_counts,
                'author_activity': author_counts
            },
            'recent_activity': [
                {
                    'adr_id': adr.adr_id,
                    'title': adr.title,
                    'status': adr.status.value,
                    'last_modified': adr.metadata.last_modified.isoformat()
                }
                for adr in recent_adrs
            ],
            'pending_reviews': [
                {
                    'adr_id': adr.adr_id,
                    'title': adr.title,
                    'author': adr.metadata.author,
                    'created_date': adr.metadata.created_date.isoformat()
                }
                for adr in pending_reviews
            ],
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def export_to_markdown(self, adr_id: str) -> str:
        """Export ADR to markdown format"""
        if adr_id not in self.adrs:
            raise ValueError(f"ADR {adr_id} not found")
        
        adr = self.adrs[adr_id]
        
        markdown = f"""# {adr.adr_id}: {adr.title}

## Status
{adr.status.value.title()}"""
        
        if adr.superseded_by:
            markdown += f" (Superseded by {adr.superseded_by})"
        
        if adr.supersedes:
            markdown += f" (Supersedes {adr.supersedes})"
        
        markdown += f"""

## Metadata
- **Author:** {adr.metadata.author}
- **Category:** {adr.category.value.title()}
- **Created:** {adr.metadata.created_date.strftime('%Y-%m-%d')}
- **Last Modified:** {adr.metadata.last_modified.strftime('%Y-%m-%d')}
- **Impact Level:** {adr.metadata.impact_level.title()}
"""
        
        if adr.metadata.reviewers:
            markdown += f"- **Reviewers:** {', '.join(adr.metadata.reviewers)}\n"
        
        if adr.metadata.tags:
            markdown += f"- **Tags:** {', '.join(adr.metadata.tags)}\n"
        
        markdown += f"""
## Context
{adr.context}

## Decision
{adr.decision}
"""
        
        if adr.alternatives:
            markdown += "\n## Alternatives Considered\n"
            for i, alt in enumerate(adr.alternatives, 1):
                markdown += f"\n### {i}. {alt.name}\n"
                markdown += f"{alt.description}\n\n"
                markdown += "**Pros:**\n"
                for pro in alt.pros:
                    markdown += f"- {pro}\n"
                markdown += "\n**Cons:**\n"
                for con in alt.cons:
                    markdown += f"- {con}\n"
                if alt.cost_estimate:
                    markdown += f"\n**Cost Estimate:** {alt.cost_estimate}\n"
                markdown += f"**Implementation Complexity:** {alt.implementation_complexity}\n"
        
        if adr.consequences:
            markdown += "\n## Consequences\n"
            positive_consequences = [c for c in adr.consequences if c.type == "positive"]
            negative_consequences = [c for c in adr.consequences if c.type == "negative"]
            neutral_consequences = [c for c in adr.consequences if c.type == "neutral"]
            
            if positive_consequences:
                markdown += "\n### Positive\n"
                for cons in positive_consequences:
                    markdown += f"- **{cons.impact_area.title()}:** {cons.description}\n"
            
            if negative_consequences:
                markdown += "\n### Negative\n"
                for cons in negative_consequences:
                    markdown += f"- **{cons.impact_area.title()}:** {cons.description}\n"
                    if cons.mitigation:
                        markdown += f"  - *Mitigation:* {cons.mitigation}\n"
            
            if neutral_consequences:
                markdown += "\n### Neutral\n"
                for cons in neutral_consequences:
                    markdown += f"- **{cons.impact_area.title()}:** {cons.description}\n"
        
        if adr.references:
            markdown += "\n## References\n"
            for ref in adr.references:
                markdown += f"- {ref}\n"
        
        return markdown
    
    def _generate_adr_id(self) -> str:
        """Generate unique ADR ID"""
        existing_ids = [int(adr_id.split('-')[1]) for adr_id in self.adrs.keys()]
        next_id = max(existing_ids) + 1 if existing_ids else 1
        return f"ADR-{next_id:03d}"
    
    def _update_modified_date(self, adr_id: str):
        """Update last modified date"""
        self.adrs[adr_id].metadata.last_modified = datetime.utcnow()
    
    def _save_adr(self, adr: ArchitectureDecisionRecord):
        """Save ADR to file"""
        filename = f"{adr.adr_id.lower()}-{adr.title.lower().replace(' ', '-')}.md"
        filepath = self.adr_directory / filename
        
        markdown_content = self.export_to_markdown(adr.adr_id)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        # Also save metadata as JSON for programmatic access
        metadata_file = self.adr_directory / f"{adr.adr_id.lower()}.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self._adr_to_dict(adr), f, indent=2, default=str)
    
    def _adr_to_dict(self, adr: ArchitectureDecisionRecord) -> Dict:
        """Convert ADR to dictionary for JSON serialization"""
        return {
            'adr_id': adr.adr_id,
            'title': adr.title,
            'status': adr.status.value,
            'context': adr.context,
            'decision': adr.decision,
            'category': adr.category.value,
            'consequences': [
                {
                    'type': c.type,
                    'description': c.description,
                    'impact_area': c.impact_area,
                    'likelihood': c.likelihood,
                    'mitigation': c.mitigation
                }
                for c in adr.consequences
            ],
            'alternatives': [
                {
                    'name': a.name,
                    'description': a.description,
                    'pros': a.pros,
                    'cons': a.cons,
                    'cost_estimate': a.cost_estimate,
                    'implementation_complexity': a.implementation_complexity
                }
                for a in adr.alternatives
            ],
            'metadata': {
                'author': adr.metadata.author,
                'reviewers': adr.metadata.reviewers,
                'stakeholders': adr.metadata.stakeholders,
                'created_date': adr.metadata.created_date.isoformat(),
                'last_modified': adr.metadata.last_modified.isoformat(),
                'review_date': adr.metadata.review_date.isoformat() if adr.metadata.review_date else None,
                'tags': adr.metadata.tags,
                'impact_level': adr.metadata.impact_level
            },
            'superseded_by': adr.superseded_by,
            'supersedes': adr.supersedes,
            'references': adr.references
        }
    
    def load_existing_adrs(self):
        """Load existing ADRs from files"""
        for json_file in self.adr_directory.glob("adr-*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    adr_data = json.load(f)
                adr = self._dict_to_adr(adr_data)
                self.adrs[adr.adr_id] = adr
            except Exception as e:
                print(f"Error loading ADR from {json_file}: {e}")
    
    def _dict_to_adr(self, data: Dict) -> ArchitectureDecisionRecord:
        """Convert dictionary to ADR object"""
        metadata = ADRMetadata(
            author=data['metadata']['author'],
            reviewers=data['metadata']['reviewers'],
            stakeholders=data['metadata']['stakeholders'],
            created_date=datetime.fromisoformat(data['metadata']['created_date']),
            last_modified=datetime.fromisoformat(data['metadata']['last_modified']),
            review_date=datetime.fromisoformat(data['metadata']['review_date']) if data['metadata']['review_date'] else None,
            tags=data['metadata']['tags'],
            impact_level=data['metadata']['impact_level']
        )
        
        consequences = [
            Consequence(
                type=c['type'],
                description=c['description'],
                impact_area=c['impact_area'],
                likelihood=c['likelihood'],
                mitigation=c['mitigation']
            )
            for c in data['consequences']
        ]
        
        alternatives = [
            Alternative(
                name=a['name'],
                description=a['description'],
                pros=a['pros'],
                cons=a['cons'],
                cost_estimate=a['cost_estimate'],
                implementation_complexity=a['implementation_complexity']
            )
            for a in data['alternatives']
        ]
        
        return ArchitectureDecisionRecord(
            adr_id=data['adr_id'],
            title=data['title'],
            status=ADRStatus(data['status']),
            context=data['context'],
            decision=data['decision'],
            consequences=consequences,
            alternatives=alternatives,
            metadata=metadata,
            category=ADRCategory(data['category']),
            superseded_by=data.get('superseded_by'),
            supersedes=data.get('supersedes'),
            references=data.get('references', [])
        )
    
    def _log_status_change(self, adr_id: str, old_status: ADRStatus, 
                          new_status: ADRStatus, reviewer: str, comments: str = None):
        """Log status changes for audit trail"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'adr_id': adr_id,
            'old_status': old_status.value,
            'new_status': new_status.value,
            'reviewer': reviewer,
            'comments': comments
        }
        
        log_file = self.adr_directory / 'adr_changes.log'
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
```

### Decision Tracking

**Definition:** Systematic monitoring and management of architectural decisions throughout their lifecycle.

#### Decision Impact Assessment
```python
from typing import Dict, List, Set
from dataclasses import dataclass
from enum import Enum
import networkx as nx

class ImpactType(Enum):
    TECHNICAL = "technical"
    BUSINESS = "business"
    ORGANIZATIONAL = "organizational"
    SECURITY = "security"
    PERFORMANCE = "performance"
    COST = "cost"

@dataclass
class DecisionImpact:
    """Impact of an architectural decision"""
    decision_id: str
    impact_type: ImpactType
    affected_components: List[str]
    severity: str  # low, medium, high, critical
    description: str
    estimated_effort: str  # person-hours or story points
    risk_level: str  # low, medium, high
    timeline: str  # immediate, short-term, long-term

class DecisionTracker:
    """Tracks decisions and their impacts across the system"""
    
    def __init__(self, adr_manager: ADRManager):
        self.adr_manager = adr_manager
        self.decision_graph = nx.DiGraph()
        self.impact_registry = {}
        self.component_dependencies = {}
    
    def analyze_decision_impact(self, adr_id: str) -> List[DecisionImpact]:
        """Analyze the impact of a specific decision"""
        if adr_id not in self.adr_manager.adrs:
            raise ValueError(f"ADR {adr_id} not found")
        
        adr = self.adr_manager.adrs[adr_id]
        impacts = []
        
        # Analyze technical impacts
        technical_impacts = self._analyze_technical_impact(adr)
        impacts.extend(technical_impacts)
        
        # Analyze business impacts
        business_impacts = self._analyze_business_impact(adr)
        impacts.extend(business_impacts)
        
        # Analyze security impacts
        security_impacts = self._analyze_security_impact(adr)
        impacts.extend(security_impacts)
        
        # Store impacts for future reference
        self.impact_registry[adr_id] = impacts
        
        return impacts
    
    def track_decision_dependencies(self, adr_id: str, depends_on: List[str]):
        """Track dependencies between decisions"""
        self.decision_graph.add_node(adr_id)
        
        for dependency in depends_on:
            self.decision_graph.add_node(dependency)
            self.decision_graph.add_edge(dependency, adr_id)
    
    def get_decision_chain(self, adr_id: str) -> Dict:
        """Get the complete dependency chain for a decision"""
        if adr_id not in self.decision_graph:
            return {'upstream': [], 'downstream': []}
        
        # Get all decisions this one depends on (upstream)
        upstream = list(nx.ancestors(self.decision_graph, adr_id))
        
        # Get all decisions that depend on this one (downstream)
        downstream = list(nx.descendants(self.decision_graph, adr_id))
        
        return {
            'upstream': upstream,
            'downstream': downstream,
            'direct_dependencies': list(self.decision_graph.predecessors(adr_id)),
            'direct_dependents': list(self.decision_graph.successors(adr_id))
        }
    
    def detect_circular_dependencies(self) -> List[List[str]]:
        """Detect circular dependencies in decisions"""
        try:
            cycles = list(nx.simple_cycles(self.decision_graph))
            return cycles
        except nx.NetworkXError:
            return []
    
    def generate_impact_report(self, adr_id: str) -> Dict:
        """Generate comprehensive impact report for a decision"""
        if adr_id not in self.impact_registry:
            self.analyze_decision_impact(adr_id)
        
        impacts = self.impact_registry[adr_id]
        dependencies = self.get_decision_chain(adr_id)
        
        # Group impacts by type
        impact_by_type = {}
        for impact in impacts:
            impact_type = impact.impact_type.value
            if impact_type not in impact_by_type:
                impact_by_type[impact_type] = []
            impact_by_type[impact_type].append(impact)
        
        # Calculate overall risk score
        risk_score = self._calculate_risk_score(impacts)
        
        return {
            'adr_id': adr_id,
            'total_impacts': len(impacts),
            'impact_by_type': {
                impact_type: len(type_impacts) 
                for impact_type, type_impacts in impact_by_type.items()
            },
            'risk_score': risk_score,
            'dependencies': dependencies,
            'detailed_impacts': [
                {
                    'type': impact.impact_type.value,
                    'severity': impact.severity,
                    'description': impact.description,
                    'affected_components': impact.affected_components,
                    'estimated_effort': impact.estimated_effort,
                    'risk_level': impact.risk_level,
                    'timeline': impact.timeline
                }
                for impact in impacts
            ]
        }
    
    def _analyze_technical_impact(self, adr: ArchitectureDecisionRecord) -> List[DecisionImpact]:
        """Analyze technical impacts of a decision"""
        impacts = []
        
        # Analyze based on category
        if adr.category == ADRCategory.TECHNOLOGY:
            impacts.append(DecisionImpact(
                decision_id=adr.adr_id,
                impact_type=ImpactType.TECHNICAL,
                affected_components=self._extract_affected_components(adr),
                severity="medium",
                description="Technology choice affects development workflows and dependencies",
                estimated_effort="40-80 hours",
                risk_level="medium",
                timeline="short-term"
            ))
        
        # Check for database-related decisions
        if any(keyword in adr.decision.lower() for keyword in ['database', 'persistence', 'storage']):
            impacts.append(DecisionImpact(
                decision_id=adr.adr_id,
                impact_type=ImpactType.TECHNICAL,
                affected_components=['data-layer', 'persistence', 'backup-systems'],
                severity="high",
                description="Database changes affect data integrity, migration, and backup strategies",
                estimated_effort="80-160 hours",
                risk_level="high",
                timeline="long-term"
            ))
        
        return impacts
    
    def _analyze_business_impact(self, adr: ArchitectureDecisionRecord) -> List[DecisionImpact]:
        """Analyze business impacts of a decision"""
        impacts = []
        
        # Look for cost implications
        cost_keywords = ['cost', 'budget', 'license', 'subscription', 'pricing']
        if any(keyword in adr.decision.lower() for keyword in cost_keywords):
            impacts.append(DecisionImpact(
                decision_id=adr.adr_id,
                impact_type=ImpactType.COST,
                affected_components=['budget', 'operations'],
                severity="medium",
                description="Decision has financial implications for operations and licensing",
                estimated_effort="N/A",
                risk_level="low",
                timeline="immediate"
            ))
        
        return impacts
    
    def _analyze_security_impact(self, adr: ArchitectureDecisionRecord) -> List[DecisionImpact]:
        """Analyze security impacts of a decision"""
        impacts = []
        
        # Check for security-related decisions
        security_keywords = ['security', 'authentication', 'authorization', 'encryption', 'privacy']
        if any(keyword in adr.decision.lower() for keyword in security_keywords):
            impacts.append(DecisionImpact(
                decision_id=adr.adr_id,
                impact_type=ImpactType.SECURITY,
                affected_components=['auth-system', 'data-protection', 'access-control'],
                severity="high",
                description="Security decision affects system vulnerability and compliance",
                estimated_effort="60-120 hours",
                risk_level="high",
                timeline="immediate"
            ))
        
        return impacts
    
    def _extract_affected_components(self, adr: ArchitectureDecisionRecord) -> List[str]:
        """Extract affected components from ADR content"""
        # This would typically analyze the ADR content to identify affected components
        # For now, return a simplified list based on category
        component_mapping = {
            ADRCategory.TECHNOLOGY: ['development-tools', 'dependencies'],
            ADRCategory.ARCHITECTURE: ['system-design', 'interfaces'],
            ADRCategory.SECURITY: ['auth-system', 'data-protection'],
            ADRCategory.PERFORMANCE: ['caching', 'database', 'network'],
            ADRCategory.INTEGRATION: ['api-gateway', 'message-queue'],
            ADRCategory.PROCESS: ['development-workflow', 'deployment']
        }
        
        return component_mapping.get(adr.category, ['unknown'])
    
    def _calculate_risk_score(self, impacts: List[DecisionImpact]) -> float:
        """Calculate overall risk score for a decision"""
        if not impacts:
            return 0.0
        
        severity_weights = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
        risk_weights = {'low': 1, 'medium': 2, 'high': 3}
        
        total_score = 0
        max_possible_score = 0
        
        for impact in impacts:
            severity_score = severity_weights.get(impact.severity, 2)
            risk_score = risk_weights.get(impact.risk_level, 2)
            impact_score = severity_score * risk_score
            
            total_score += impact_score
            max_possible_score += 12  # max severity (4) * max risk (3)
        
        return (total_score / max_possible_score) * 10  # Scale to 0-10
```

### Technology Selection

**Definition:** Structured approach to evaluating and selecting technologies based on defined criteria and organizational needs.

#### Technology Evaluation Framework
```python
from typing import Dict, List, Tuple
from dataclasses import dataclass
import pandas as pd

@dataclass
class EvaluationCriterion:
    """Criterion for technology evaluation"""
    name: str
    description: str
    weight: float  # 0.0 to 1.0
    measurement_type: str  # quantitative, qualitative, binary
    scoring_guide: Dict[str, float]  # score mapping

@dataclass
class TechnologyOption:
    """Technology option being evaluated"""
    name: str
    version: str
    description: str
    vendor: str
    license_type: str
    cost_model: str
    scores: Dict[str, float]  # criterion_name -> score
    notes: str = ""

class TechnologyEvaluator:
    """Framework for systematic technology evaluation"""
    
    def __init__(self):
        self.criteria = {}
        self.options = {}
        self.evaluation_results = {}
    
    def add_criterion(self, criterion: EvaluationCriterion):
        """Add evaluation criterion"""
        self.criteria[criterion.name] = criterion
    
    def add_technology_option(self, option: TechnologyOption):
        """Add technology option for evaluation"""
        self.options[option.name] = option
    
    def setup_standard_criteria(self):
        """Setup standard technology evaluation criteria"""
        standard_criteria = [
            EvaluationCriterion(
                name="Technical Fit",
                description="How well the technology fits technical requirements",
                weight=0.25,
                measurement_type="qualitative",
                scoring_guide={
                    "excellent": 5.0,
                    "good": 4.0,
                    "adequate": 3.0,
                    "poor": 2.0,
                    "unacceptable": 1.0
                }
            ),
            EvaluationCriterion(
                name="Performance",
                description="Performance characteristics and benchmarks",
                weight=0.20,
                measurement_type="quantitative",
                scoring_guide={
                    "excellent": 5.0,
                    "good": 4.0,
                    "adequate": 3.0,
                    "poor": 2.0,
                    "unacceptable": 1.0
                }
            ),
            EvaluationCriterion(
                name="Scalability",
                description="Ability to scale with growing demands",
                weight=0.15,
                measurement_type="qualitative",
                scoring_guide={
                    "excellent": 5.0,
                    "good": 4.0,
                    "adequate": 3.0,
                    "poor": 2.0,
                    "unacceptable": 1.0
                }
            ),
            EvaluationCriterion(
                name="Community Support",
                description="Size and activity of community support",
                weight=0.10,
                measurement_type="quantitative",
                scoring_guide={
                    "very_active": 5.0,
                    "active": 4.0,
                    "moderate": 3.0,
                    "limited": 2.0,
                    "none": 1.0
                }
            ),
            EvaluationCriterion(
                name="Learning Curve",
                description="Ease of adoption for development team",
                weight=0.10,
                measurement_type="qualitative",
                scoring_guide={
                    "very_easy": 5.0,
                    "easy": 4.0,
                    "moderate": 3.0,
                    "difficult": 2.0,
                    "very_difficult": 1.0
                }
            ),
            EvaluationCriterion(
                name="Total Cost of Ownership",
                description="Complete cost including licensing, training, maintenance",
                weight=0.15,
                measurement_type="quantitative",
                scoring_guide={
                    "very_low": 5.0,
                    "low": 4.0,
                    "moderate": 3.0,
                    "high": 2.0,
                    "very_high": 1.0
                }
            ),
            EvaluationCriterion(
                name="Vendor Stability",
                description="Long-term viability of technology vendor",
                weight=0.05,
                measurement_type="qualitative",
                scoring_guide={
                    "excellent": 5.0,
                    "good": 4.0,
                    "adequate": 3.0,
                    "concerning": 2.0,
                    "poor": 1.0
                }
            )
        ]
        
        for criterion in standard_criteria:
            self.add_criterion(criterion)
    
    def evaluate_options(self) -> Dict[str, Dict]:
        """Evaluate all technology options against criteria"""
        results = {}
        
        for option_name, option in self.options.items():
            weighted_score = 0.0
            criterion_scores = {}
            
            for criterion_name, criterion in self.criteria.items():
                if criterion_name in option.scores:
                    score = option.scores[criterion_name]
                    weighted_score += score * criterion.weight
                    criterion_scores[criterion_name] = {
                        'raw_score': score,
                        'weighted_score': score * criterion.weight,
                        'weight': criterion.weight
                    }
            
            results[option_name] = {
                'total_weighted_score': weighted_score,
                'criterion_scores': criterion_scores,
                'option_details': option
            }
        
        self.evaluation_results = results
        return results
    
    def generate_evaluation_report(self) -> str:
        """Generate comprehensive evaluation report"""
        if not self.evaluation_results:
            self.evaluate_options()
        
        # Sort options by total score
        sorted_options = sorted(
            self.evaluation_results.items(),
            key=lambda x: x[1]['total_weighted_score'],
            reverse=True
        )
        
        report = "# Technology Evaluation Report\n\n"
        report += f"**Evaluation Date:** {datetime.utcnow().strftime('%Y-%m-%d')}\n"
        report += f"**Options Evaluated:** {len(self.options)}\n"
        report += f"**Evaluation Criteria:** {len(self.criteria)}\n\n"
        
        # Executive Summary
        report += "## Executive Summary\n\n"
        if sorted_options:
            winner = sorted_options[0]
            report += f"**Recommended Option:** {winner[0]}\n"
            report += f"**Total Score:** {winner[1]['total_weighted_score']:.2f}/5.00\n\n"
        
        # Detailed Results
        report += "## Detailed Evaluation Results\n\n"
        
        for rank, (option_name, results) in enumerate(sorted_options, 1):
            option = results['option_details']
            report += f"### {rank}. {option_name}\n"
            report += f"**Total Score:** {results['total_weighted_score']:.2f}/5.00\n"
            report += f"**Version:** {option.version}\n"
            report += f"**Vendor:** {option.vendor}\n"
            report += f"**License:** {option.license_type}\n"
            report += f"**Description:** {option.description}\n\n"
            
            # Criterion breakdown
            report += "**Criterion Scores:**\n"
            for criterion_name, scores in results['criterion_scores'].items():
                report += f"- {criterion_name}: {scores['raw_score']:.1f}/5.0 "
                report += f"(weighted: {scores['weighted_score']:.2f})\n"
            
            if option.notes:
                report += f"\n**Notes:** {option.notes}\n"
            
            report += "\n"
        
        # Criteria Details
        report += "## Evaluation Criteria\n\n"
        for criterion_name, criterion in self.criteria.items():
            report += f"### {criterion_name}\n"
            report += f"**Description:** {criterion.description}\n"
            report += f"**Weight:** {criterion.weight:.1%}\n"
            report += f"**Measurement Type:** {criterion.measurement_type}\n\n"
        
        return report
    
    def create_comparison_matrix(self) -> pd.DataFrame:
        """Create comparison matrix as DataFrame"""
        if not self.evaluation_results:
            self.evaluate_options()
        
        # Prepare data for DataFrame
        data = []
        for option_name, results in self.evaluation_results.items():
            row = {'Technology': option_name}
            
            for criterion_name, scores in results['criterion_scores'].items():
                row[criterion_name] = scores['raw_score']
            
            row['Total Score'] = results['total_weighted_score']
            data.append(row)
        
        df = pd.DataFrame(data)
        df = df.sort_values('Total Score', ascending=False)
        
        return df

# Example usage for database selection
def example_database_evaluation():
    """Example: Evaluating database technologies"""
    evaluator = TechnologyEvaluator()
    evaluator.setup_standard_criteria()
    
    # Add database options
    postgres_option = TechnologyOption(
        name="PostgreSQL",
        version="15.0",
        description="Open-source relational database with strong ACID compliance",
        vendor="PostgreSQL Global Development Group",
        license_type="PostgreSQL License (Open Source)",
        cost_model="Free (operational costs only)",
        scores={
            "Technical Fit": 4.5,
            "Performance": 4.0,
            "Scalability": 3.5,
            "Community Support": 4.5,
            "Learning Curve": 3.5,
            "Total Cost of Ownership": 4.5,
            "Vendor Stability": 4.0
        },
        notes="Excellent for complex queries, ACID compliance, extensive extensions"
    )
    
    mongodb_option = TechnologyOption(
        name="MongoDB",
        version="6.0",
        description="Document-oriented NoSQL database",
        vendor="MongoDB Inc.",
        license_type="Server Side Public License (SSPL)",
        cost_model="Free community edition, paid enterprise features",
        scores={
            "Technical Fit": 3.5,
            "Performance": 4.5,
            "Scalability": 4.5,
            "Community Support": 4.0,
            "Learning Curve": 4.0,
            "Total Cost of Ownership": 3.5,
            "Vendor Stability": 4.0
        },
        notes="Good for flexible schemas, horizontal scaling, rapid development"
    )
    
    mysql_option = TechnologyOption(
        name="MySQL",
        version="8.0",
        description="Popular open-source relational database",
        vendor="Oracle Corporation",
        license_type="GPL v2 (with commercial licenses available)",
        cost_model="Free open source, paid commercial licenses",
        scores={
            "Technical Fit": 4.0,
            "Performance": 4.0,
            "Scalability": 3.0,
            "Community Support": 4.5,
            "Learning Curve": 4.5,
            "Total Cost of Ownership": 4.0,
            "Vendor Stability": 4.5
        },
        notes="Mature, widely adopted, good performance for read-heavy workloads"
    )
    
    evaluator.add_technology_option(postgres_option)
    evaluator.add_technology_option(mongodb_option)
    evaluator.add_technology_option(mysql_option)
    
    # Generate evaluation
    results = evaluator.evaluate_options()
    report = evaluator.generate_evaluation_report()
    
    return evaluator, results, report
```

### Architectural Debt Management

**Definition:** Systematic identification, tracking, and remediation of architectural decisions that may have introduced technical debt or suboptimal outcomes.

#### Architectural Debt Tracker
```python
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

class DebtType(Enum):
    TECHNOLOGY = "technology"
    DESIGN = "design"
    PROCESS = "process"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    PERFORMANCE = "performance"

class DebtSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ArchitecturalDebt:
    """Represents architectural debt item"""
    debt_id: str
    title: str
    description: str
    debt_type: DebtType
    severity: DebtSeverity
    related_adr: Optional[str]
    introduced_date: datetime
    estimated_effort: str  # e.g., "2-3 sprints", "40-60 hours"
    business_impact: str
    technical_impact: str
    remediation_plan: str
    owner: str
    status: str = "identified"  # identified, planned, in_progress, resolved
    due_date: Optional[datetime] = None

class ArchitecturalDebtManager:
    """Manages architectural debt lifecycle"""
    
    def __init__(self, adr_manager: ADRManager):
        self.adr_manager = adr_manager
        self.debt_items = {}
        self.debt_metrics = {}
    
    def identify_debt_from_adr(self, adr_id: str, debt_description: str, 
                             debt_type: DebtType, severity: DebtSeverity) -> str:
        """Identify architectural debt related to an ADR"""
        debt_id = f"DEBT-{len(self.debt_items) + 1:03d}"
        
        if adr_id in self.adr_manager.adrs:
            adr = self.adr_manager.adrs[adr_id]
            title = f"Debt from {adr.title}"
        else:
            title = "Architectural Debt"
        
        debt = ArchitecturalDebt(
            debt_id=debt_id,
            title=title,
            description=debt_description,
            debt_type=debt_type,
            severity=severity,
            related_adr=adr_id,
            introduced_date=datetime.utcnow(),
            estimated_effort="TBD",
            business_impact="TBD",
            technical_impact="TBD",
            remediation_plan="TBD",
            owner="TBD"
        )
        
        self.debt_items[debt_id] = debt
        return debt_id
    
    def update_debt_details(self, debt_id: str, **updates):
        """Update debt item details"""
        if debt_id not in self.debt_items:
            raise ValueError(f"Debt item {debt_id} not found")
        
        debt = self.debt_items[debt_id]
        
        for field, value in updates.items():
            if hasattr(debt, field):
                setattr(debt, field, value)
    
    def prioritize_debt(self) -> List[ArchitecturalDebt]:
        """Prioritize debt items based on severity and business impact"""
        debt_list = list(self.debt_items.values())
        
        # Priority scoring
        severity_scores = {
            DebtSeverity.CRITICAL: 4,
            DebtSeverity.HIGH: 3,
            DebtSeverity.MEDIUM: 2,
            DebtSeverity.LOW: 1
        }
        
        def priority_score(debt: ArchitecturalDebt) -> float:
            base_score = severity_scores[debt.severity]
            
            # Adjust based on age
            age_days = (datetime.utcnow() - debt.introduced_date).days
            age_factor = min(age_days / 365, 1.0)  # Max 1 year factor
            
            # Adjust based on due date proximity
            due_date_factor = 1.0
            if debt.due_date:
                days_until_due = (debt.due_date - datetime.utcnow()).days
                if days_until_due <= 0:
                    due_date_factor = 2.0  # Overdue
                elif days_until_due <= 30:
                    due_date_factor = 1.5  # Due soon
            
            return base_score * (1 + age_factor) * due_date_factor
        
        return sorted(debt_list, key=priority_score, reverse=True)
    
    def generate_debt_report(self) -> Dict:
        """Generate comprehensive debt report"""
        total_debt = len(self.debt_items)
        
        # Count by severity
        severity_counts = {severity: 0 for severity in DebtSeverity}
        for debt in self.debt_items.values():
            severity_counts[debt.severity] += 1
        
        # Count by type
        type_counts = {debt_type: 0 for debt_type in DebtType}
        for debt in self.debt_items.values():
            type_counts[debt.debt_type] += 1
        
        # Count by status
        status_counts = {}
        for debt in self.debt_items.values():
            status = debt.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Overdue items
        overdue_items = [
            debt for debt in self.debt_items.values()
            if debt.due_date and debt.due_date < datetime.utcnow() and debt.status != "resolved"
        ]
        
        # High priority items
        prioritized_debt = self.prioritize_debt()
        high_priority = prioritized_debt[:5]
        
        return {
            'summary': {
                'total_debt_items': total_debt,
                'severity_distribution': {sev.value: count for sev, count in severity_counts.items()},
                'type_distribution': {dtype.value: count for dtype, count in type_counts.items()},
                'status_distribution': status_counts,
                'overdue_items': len(overdue_items)
            },
            'high_priority_items': [
                {
                    'debt_id': debt.debt_id,
                    'title': debt.title,
                    'severity': debt.severity.value,
                    'type': debt.debt_type.value,
                    'age_days': (datetime.utcnow() - debt.introduced_date).days,
                    'owner': debt.owner
                }
                for debt in high_priority
            ],
            'overdue_items': [
                {
                    'debt_id': debt.debt_id,
                    'title': debt.title,
                    'due_date': debt.due_date.isoformat(),
                    'days_overdue': (datetime.utcnow() - debt.due_date).days
                }
                for debt in overdue_items
            ],
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def create_remediation_roadmap(self, quarters: int = 4) -> Dict:
        """Create quarterly roadmap for debt remediation"""
        prioritized_debt = self.prioritize_debt()
        unresolved_debt = [d for d in prioritized_debt if d.status != "resolved"]
        
        # Divide debt into quarters based on priority and estimated effort
        quarters_plan = {}
        current_quarter_capacity = 100  # Assuming 100 story points per quarter
        
        for quarter in range(1, quarters + 1):
            quarter_key = f"Q{quarter}"
            quarters_plan[quarter_key] = {
                'debt_items': [],
                'total_effort': 0,
                'capacity_used': 0
            }
        
        current_quarter = 1
        current_capacity = current_quarter_capacity
        
        for debt in unresolved_debt:
            if current_quarter > quarters:
                break
            
            # Estimate effort in story points (simplified)
            effort_estimate = self._estimate_effort_points(debt.estimated_effort)
            
            if effort_estimate <= current_capacity:
                quarter_key = f"Q{current_quarter}"
                quarters_plan[quarter_key]['debt_items'].append({
                    'debt_id': debt.debt_id,
                    'title': debt.title,
                    'severity': debt.severity.value,
                    'estimated_effort': debt.estimated_effort,
                    'owner': debt.owner
                })
                quarters_plan[quarter_key]['total_effort'] += effort_estimate
                quarters_plan[quarter_key]['capacity_used'] = (
                    quarters_plan[quarter_key]['total_effort'] / current_quarter_capacity
                ) * 100
                
                current_capacity -= effort_estimate
            else:
                # Move to next quarter
                current_quarter += 1
                current_capacity = current_quarter_capacity
                
                if current_quarter <= quarters:
                    quarter_key = f"Q{current_quarter}"
                    quarters_plan[quarter_key]['debt_items'].append({
                        'debt_id': debt.debt_id,
                        'title': debt.title,
                        'severity': debt.severity.value,
                        'estimated_effort': debt.estimated_effort,
                        'owner': debt.owner
                    })
                    quarters_plan[quarter_key]['total_effort'] += effort_estimate
                    quarters_plan[quarter_key]['capacity_used'] = (
                        quarters_plan[quarter_key]['total_effort'] / current_quarter_capacity
                    ) * 100
                    
                    current_capacity -= effort_estimate
        
        return {
            'roadmap': quarters_plan,
            'total_debt_items': len(unresolved_debt),
            'planned_items': sum(len(q['debt_items']) for q in quarters_plan.values()),
            'backlog_items': len(unresolved_debt) - sum(len(q['debt_items']) for q in quarters_plan.values())
        }
    
    def _estimate_effort_points(self, effort_description: str) -> int:
        """Convert effort description to story points"""
        effort_lower = effort_description.lower()
        
        if "sprint" in effort_lower:
            # Extract number of sprints
            import re
            sprint_match = re.search(r'(\d+)', effort_lower)
            if sprint_match:
                sprints = int(sprint_match.group(1))
                return sprints * 20  # Assume 20 points per sprint
        
        if "hour" in effort_lower:
            # Extract hours and convert
            import re
            hour_match = re.search(r'(\d+)', effort_lower)
            if hour_match:
                hours = int(hour_match.group(1))
                return max(hours // 8, 1)  # 8 hours = 1 story point
        
        # Default estimate
        return 8

# Example usage
def setup_debt_management_example():
    """Example setup for debt management"""
    adr_manager = ADRManager()
    debt_manager = ArchitecturalDebtManager(adr_manager)
    
    # Create example ADR
    adr_id = adr_manager.create_adr(
        title="Use MongoDB for User Data Storage",
        context="Need flexible schema for user profiles with varying attributes",
        decision="Implement MongoDB as primary user data store",
        author="tech-lead@company.com",
        category=ADRCategory.TECHNOLOGY
    )
    
    # Identify debt from the decision
    debt_id = debt_manager.identify_debt_from_adr(
        adr_id=adr_id,
        debt_description="MongoDB choice creates data consistency challenges and lacks ACID guarantees needed for financial transactions",
        debt_type=DebtType.TECHNOLOGY,
        severity=DebtSeverity.HIGH
    )
    
    # Update debt details
    debt_manager.update_debt_details(
        debt_id=debt_id,
        estimated_effort="2-3 sprints",
        business_impact="Risk of data inconsistency in financial operations",
        technical_impact="Complex transaction management, eventual consistency issues",
        remediation_plan="Migrate financial data to PostgreSQL, keep user profiles in MongoDB",
        owner="backend-team@company.com",
        due_date=datetime.utcnow() + timedelta(days=90)
    )
    
    # Generate reports
    debt_report = debt_manager.generate_debt_report()
    roadmap = debt_manager.create_remediation_roadmap()
    
    return debt_manager, debt_report, roadmap
```

This comprehensive Architecture Decision Records (ADR) implementation provides production-ready solutions for documenting, tracking, and managing architectural decisions throughout their lifecycle, including decision impact analysis, technology evaluation frameworks, and architectural debt management.