"""
Activity dependency management system for timeline generation.
Handles dependency graphs, critical path calculation, and buffer time allocation.
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict, deque
import heapq

from app.models.core import Activity, Dependency, TimedActivity, EventContext
from app.models.enums import Priority


@dataclass
class DependencyNode:
    """Node in the dependency graph representing an activity"""
    activity: Activity
    predecessors: Set[str] = field(default_factory=set)
    successors: Set[str] = field(default_factory=set)
    earliest_start: Optional[datetime] = None
    earliest_finish: Optional[datetime] = None
    latest_start: Optional[datetime] = None
    latest_finish: Optional[datetime] = None
    slack: timedelta = timedelta(0)
    is_critical: bool = False
    
    def total_duration(self) -> timedelta:
        """Get total duration including setup and cleanup"""
        return self.activity.setup_time + self.activity.duration + self.activity.cleanup_time


@dataclass
class DependencyGraph:
    """Dependency graph for timeline activities"""
    nodes: Dict[str, DependencyNode] = field(default_factory=dict)
    dependencies: List[Dependency] = field(default_factory=list)
    critical_path: List[str] = field(default_factory=list)
    total_duration: timedelta = timedelta(0)
    
    def add_activity(self, activity: Activity) -> None:
        """Add an activity to the dependency graph"""
        if activity.id not in self.nodes:
            self.nodes[activity.id] = DependencyNode(activity=activity)
    
    def add_dependency(self, dependency: Dependency) -> None:
        """Add a dependency between activities"""
        # Validate dependency
        errors = dependency.validate()
        if errors:
            raise ValueError(f"Invalid dependency: {', '.join(errors)}")
        
        # Ensure both activities exist
        if dependency.predecessor_id not in self.nodes:
            raise ValueError(f"Predecessor activity '{dependency.predecessor_id}' not found")
        if dependency.successor_id not in self.nodes:
            raise ValueError(f"Successor activity '{dependency.successor_id}' not found")
        
        # Add to graph
        self.dependencies.append(dependency)
        self.nodes[dependency.predecessor_id].successors.add(dependency.successor_id)
        self.nodes[dependency.successor_id].predecessors.add(dependency.predecessor_id)
    
    def has_cycle(self) -> bool:
        """Check if the dependency graph has cycles using DFS"""
        WHITE, GRAY, BLACK = 0, 1, 2
        colors = {node_id: WHITE for node_id in self.nodes}
        
        def dfs(node_id: str) -> bool:
            if colors[node_id] == GRAY:
                return True  # Back edge found, cycle detected
            if colors[node_id] == BLACK:
                return False  # Already processed
            
            colors[node_id] = GRAY
            for successor_id in self.nodes[node_id].successors:
                if dfs(successor_id):
                    return True
            colors[node_id] = BLACK
            return False
        
        for node_id in self.nodes:
            if colors[node_id] == WHITE:
                if dfs(node_id):
                    return True
        return False
    
    def topological_sort(self) -> List[str]:
        """Return activities in topological order"""
        if self.has_cycle():
            raise ValueError("Cannot perform topological sort: dependency graph has cycles")
        
        in_degree = {node_id: len(node.predecessors) for node_id, node in self.nodes.items()}
        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
        result = []
        
        while queue:
            node_id = queue.popleft()
            result.append(node_id)
            
            for successor_id in self.nodes[node_id].successors:
                in_degree[successor_id] -= 1
                if in_degree[successor_id] == 0:
                    queue.append(successor_id)
        
        if len(result) != len(self.nodes):
            raise ValueError("Topological sort failed: dependency graph has cycles")
        
        return result


class DependencyManager:
    """Manager for activity dependencies and critical path analysis"""
    
    def __init__(self):
        self.buffer_time_rules = self._initialize_buffer_rules()
    
    def _initialize_buffer_rules(self) -> Dict[str, Dict]:
        """Initialize buffer time calculation rules"""
        return {
            "priority_multipliers": {
                Priority.CRITICAL: 0.15,  # 15% buffer for critical activities
                Priority.HIGH: 0.20,      # 20% buffer for high priority
                Priority.MEDIUM: 0.25,    # 25% buffer for medium priority
                Priority.LOW: 0.30,       # 30% buffer for low priority
                Priority.OPTIONAL: 0.35   # 35% buffer for optional activities
            },
            "complexity_multipliers": {
                "low": 1.0,      # 0-3 complexity score
                "medium": 1.2,   # 3-6 complexity score
                "high": 1.5,     # 6-8 complexity score
                "very_high": 2.0 # 8-10 complexity score
            },
            "dependency_multipliers": {
                "no_dependencies": 1.0,
                "few_dependencies": 1.1,    # 1-2 dependencies
                "many_dependencies": 1.3,   # 3-5 dependencies
                "complex_dependencies": 1.5  # 5+ dependencies
            }
        }
    
    def create_dependency_graph(self, activities: List[Activity]) -> DependencyGraph:
        """Create a dependency graph from a list of activities"""
        graph = DependencyGraph()
        
        # Add all activities to the graph
        for activity in activities:
            graph.add_activity(activity)
        
        # Create automatic dependencies based on activity types and cultural sequences
        auto_dependencies = self._generate_automatic_dependencies(activities)
        for dependency in auto_dependencies:
            graph.add_dependency(dependency)
        
        return graph
    
    def _generate_automatic_dependencies(self, activities: List[Activity]) -> List[Dependency]:
        """Generate automatic dependencies based on activity types and logic"""
        dependencies = []
        activity_map = {activity.id: activity for activity in activities}
        
        # Group activities by type
        prep_activities = [a for a in activities if a.activity_type.value == "preparation"]
        ceremony_activities = [a for a in activities if a.activity_type.value == "ceremony"]
        cleanup_activities = [a for a in activities if a.activity_type.value == "cleanup"]
        
        # Rule 1: All preparation activities must finish before ceremonies start
        for prep in prep_activities:
            for ceremony in ceremony_activities:
                dependencies.append(Dependency(
                    predecessor_id=prep.id,
                    successor_id=ceremony.id,
                    dependency_type="finish_to_start",
                    lag_time=timedelta(minutes=15)  # 15-minute buffer
                ))
        
        # Rule 2: All ceremonies must finish before cleanup starts
        for ceremony in ceremony_activities:
            for cleanup in cleanup_activities:
                dependencies.append(Dependency(
                    predecessor_id=ceremony.id,
                    successor_id=cleanup.id,
                    dependency_type="finish_to_start",
                    lag_time=timedelta(minutes=30)  # 30-minute buffer
                ))
        
        # Rule 3: Photography activities should start with or after main ceremonies
        photo_activities = [a for a in activities if a.activity_type.value == "photography"]
        for photo in photo_activities:
            for ceremony in ceremony_activities:
                if ceremony.priority.value in ["critical", "high"]:
                    dependencies.append(Dependency(
                        predecessor_id=ceremony.id,
                        successor_id=photo.id,
                        dependency_type="start_to_start",
                        lag_time=timedelta(0)
                    ))
        
        # Rule 4: Catering setup before catering service
        catering_activities = [a for a in activities if a.activity_type.value == "catering"]
        for i, catering in enumerate(catering_activities):
            if i > 0:  # If there are multiple catering activities
                dependencies.append(Dependency(
                    predecessor_id=catering_activities[i-1].id,
                    successor_id=catering.id,
                    dependency_type="finish_to_start",
                    lag_time=timedelta(minutes=30)
                ))
        
        # Rule 5: Cultural sequence dependencies (e.g., Mehendi before Haldi before Wedding)
        cultural_sequences = self._get_cultural_sequence_dependencies(activities)
        dependencies.extend(cultural_sequences)
        
        return dependencies
    
    def _get_cultural_sequence_dependencies(self, activities: List[Activity]) -> List[Dependency]:
        """Generate dependencies based on cultural ceremony sequences"""
        dependencies = []
        
        # Hindu wedding sequence
        hindu_sequence = ["mehendi", "haldi", "sangeet", "wedding", "reception"]
        hindu_activities = {}
        
        for activity in activities:
            activity_name_lower = activity.name.lower()
            for ceremony in hindu_sequence:
                if ceremony in activity_name_lower:
                    hindu_activities[ceremony] = activity.id
                    break
        
        # Create sequential dependencies for Hindu ceremonies
        for i in range(len(hindu_sequence) - 1):
            current = hindu_sequence[i]
            next_ceremony = hindu_sequence[i + 1]
            
            if current in hindu_activities and next_ceremony in hindu_activities:
                dependencies.append(Dependency(
                    predecessor_id=hindu_activities[current],
                    successor_id=hindu_activities[next_ceremony],
                    dependency_type="finish_to_start",
                    lag_time=timedelta(hours=2)  # 2-hour gap between ceremonies
                ))
        
        # Muslim wedding sequence
        muslim_sequence = ["nikkah", "mehndi", "walima"]
        muslim_activities = {}
        
        for activity in activities:
            activity_name_lower = activity.name.lower()
            for ceremony in muslim_sequence:
                if ceremony in activity_name_lower:
                    muslim_activities[ceremony] = activity.id
                    break
        
        # Create sequential dependencies for Muslim ceremonies
        for i in range(len(muslim_sequence) - 1):
            current = muslim_sequence[i]
            next_ceremony = muslim_sequence[i + 1]
            
            if current in muslim_activities and next_ceremony in muslim_activities:
                dependencies.append(Dependency(
                    predecessor_id=muslim_activities[current],
                    successor_id=muslim_activities[next_ceremony],
                    dependency_type="finish_to_start",
                    lag_time=timedelta(hours=1)  # 1-hour gap between ceremonies
                ))
        
        return dependencies
    
    def calculate_critical_path(self, graph: DependencyGraph, start_time: datetime) -> None:
        """Calculate critical path using CPM (Critical Path Method)"""
        if graph.has_cycle():
            raise ValueError("Cannot calculate critical path: dependency graph has cycles")
        
        # Forward pass - calculate earliest start and finish times
        self._forward_pass(graph, start_time)
        
        # Backward pass - calculate latest start and finish times
        self._backward_pass(graph)
        
        # Calculate slack and identify critical activities
        self._calculate_slack(graph)
        
        # Find critical path
        graph.critical_path = self._find_critical_path(graph)
        
        # Calculate total project duration
        if graph.nodes:
            max_finish = max(node.earliest_finish for node in graph.nodes.values() if node.earliest_finish)
            graph.total_duration = max_finish - start_time
    
    def _forward_pass(self, graph: DependencyGraph, start_time: datetime) -> None:
        """Forward pass to calculate earliest start and finish times"""
        # Get activities in topological order
        topo_order = graph.topological_sort()
        
        for activity_id in topo_order:
            node = graph.nodes[activity_id]
            
            if not node.predecessors:
                # No predecessors, can start at project start time
                node.earliest_start = start_time
            else:
                # Calculate earliest start based on predecessors
                earliest_start = start_time
                
                for pred_id in node.predecessors:
                    pred_node = graph.nodes[pred_id]
                    
                    # Find the dependency to get lag time
                    dependency = next(
                        (d for d in graph.dependencies 
                         if d.predecessor_id == pred_id and d.successor_id == activity_id),
                        None
                    )
                    
                    if dependency:
                        if dependency.dependency_type == "finish_to_start":
                            candidate_start = pred_node.earliest_finish + dependency.lag_time
                        elif dependency.dependency_type == "start_to_start":
                            candidate_start = pred_node.earliest_start + dependency.lag_time
                        elif dependency.dependency_type == "finish_to_finish":
                            candidate_start = pred_node.earliest_finish + dependency.lag_time - node.total_duration()
                        else:  # start_to_finish
                            candidate_start = pred_node.earliest_start + dependency.lag_time - node.total_duration()
                        
                        earliest_start = max(earliest_start, candidate_start)
                
                node.earliest_start = earliest_start
            
            # Calculate earliest finish
            node.earliest_finish = node.earliest_start + node.total_duration()
    
    def _backward_pass(self, graph: DependencyGraph) -> None:
        """Backward pass to calculate latest start and finish times"""
        # Get activities in reverse topological order
        topo_order = list(reversed(graph.topological_sort()))
        
        # Find project end time
        project_end = max(node.earliest_finish for node in graph.nodes.values() if node.earliest_finish)
        
        for activity_id in topo_order:
            node = graph.nodes[activity_id]
            
            if not node.successors:
                # No successors, latest finish is project end
                node.latest_finish = project_end
            else:
                # Calculate latest finish based on successors
                latest_finish = project_end
                
                for succ_id in node.successors:
                    succ_node = graph.nodes[succ_id]
                    
                    # Find the dependency to get lag time
                    dependency = next(
                        (d for d in graph.dependencies 
                         if d.predecessor_id == activity_id and d.successor_id == succ_id),
                        None
                    )
                    
                    if dependency:
                        if dependency.dependency_type == "finish_to_start":
                            candidate_finish = succ_node.latest_start - dependency.lag_time
                        elif dependency.dependency_type == "start_to_start":
                            candidate_finish = succ_node.latest_start - dependency.lag_time + node.total_duration()
                        elif dependency.dependency_type == "finish_to_finish":
                            candidate_finish = succ_node.latest_finish - dependency.lag_time
                        else:  # start_to_finish
                            candidate_finish = succ_node.latest_finish - dependency.lag_time + node.total_duration()
                        
                        latest_finish = min(latest_finish, candidate_finish)
                
                node.latest_finish = latest_finish
            
            # Calculate latest start
            node.latest_start = node.latest_finish - node.total_duration()
    
    def _calculate_slack(self, graph: DependencyGraph) -> None:
        """Calculate slack time for each activity"""
        for node in graph.nodes.values():
            if node.latest_start and node.earliest_start:
                node.slack = node.latest_start - node.earliest_start
                node.is_critical = node.slack == timedelta(0)
    
    def _find_critical_path(self, graph: DependencyGraph) -> List[str]:
        """Find the critical path through the network"""
        critical_activities = [
            activity_id for activity_id, node in graph.nodes.items() 
            if node.is_critical
        ]
        
        # Sort critical activities by earliest start time
        critical_activities.sort(
            key=lambda aid: graph.nodes[aid].earliest_start or datetime.min
        )
        
        return critical_activities
    
    def calculate_buffer_time(self, 
                            activity: Activity, 
                            context: EventContext, 
                            dependency_count: int = 0) -> timedelta:
        """Calculate buffer time for an activity based on various factors"""
        base_buffer_percentage = self.buffer_time_rules["priority_multipliers"].get(
            activity.priority, 0.25
        )
        
        # Adjust for complexity
        complexity_level = self._get_complexity_level(context.complexity_score)
        complexity_multiplier = self.buffer_time_rules["complexity_multipliers"][complexity_level]
        
        # Adjust for dependencies
        dependency_level = self._get_dependency_level(dependency_count)
        dependency_multiplier = self.buffer_time_rules["dependency_multipliers"][dependency_level]
        
        # Calculate base buffer time
        base_buffer = timedelta(
            seconds=activity.duration.total_seconds() * base_buffer_percentage
        )
        
        # Apply multipliers
        total_multiplier = complexity_multiplier * dependency_multiplier
        buffer_time = timedelta(seconds=base_buffer.total_seconds() * total_multiplier)
        
        # Ensure minimum and maximum buffer times
        min_buffer = timedelta(minutes=15)
        max_buffer = timedelta(hours=2)
        
        return max(min_buffer, min(buffer_time, max_buffer))
    
    def _get_complexity_level(self, complexity_score: float) -> str:
        """Get complexity level from complexity score"""
        if complexity_score <= 3:
            return "low"
        elif complexity_score <= 6:
            return "medium"
        elif complexity_score <= 8:
            return "high"
        else:
            return "very_high"
    
    def _get_dependency_level(self, dependency_count: int) -> str:
        """Get dependency level from dependency count"""
        if dependency_count == 0:
            return "no_dependencies"
        elif dependency_count <= 2:
            return "few_dependencies"
        elif dependency_count <= 5:
            return "many_dependencies"
        else:
            return "complex_dependencies"
    
    def resolve_conflicts(self, graph: DependencyGraph) -> List[str]:
        """Identify and suggest resolutions for timeline conflicts"""
        conflicts = []
        
        # Check for impossible dependencies
        if graph.has_cycle():
            conflicts.append("Circular dependencies detected - some activities depend on each other")
        
        # Check for over-constrained activities
        for activity_id, node in graph.nodes.items():
            if node.slack and node.slack < timedelta(0):
                conflicts.append(f"Activity '{node.activity.name}' is over-constrained with negative slack")
        
        # Check for resource conflicts (activities requiring same vendors at same time)
        conflicts.extend(self._check_resource_conflicts(graph))
        
        return conflicts
    
    def _check_resource_conflicts(self, graph: DependencyGraph) -> List[str]:
        """Check for resource conflicts between activities"""
        conflicts = []
        
        # Group activities by required vendors
        vendor_activities = defaultdict(list)
        for activity_id, node in graph.nodes.items():
            for vendor in node.activity.required_vendors:
                vendor_activities[vendor].append((activity_id, node))
        
        # Check for time overlaps for same vendor
        for vendor, activities in vendor_activities.items():
            if len(activities) > 1:
                # Sort by earliest start time
                activities.sort(key=lambda x: x[1].earliest_start or datetime.min)
                
                for i in range(len(activities) - 1):
                    current_id, current_node = activities[i]
                    next_id, next_node = activities[i + 1]
                    
                    if (current_node.earliest_finish and next_node.earliest_start and
                        current_node.earliest_finish > next_node.earliest_start):
                        conflicts.append(
                            f"Vendor '{vendor}' conflict between activities "
                            f"'{current_node.activity.name}' and '{next_node.activity.name}'"
                        )
        
        return conflicts
    
    def optimize_timeline(self, graph: DependencyGraph) -> List[str]:
        """Suggest optimizations for the timeline"""
        suggestions = []
        
        # Suggest parallel execution opportunities
        parallel_opportunities = self._find_parallel_opportunities(graph)
        suggestions.extend(parallel_opportunities)
        
        # Suggest buffer time adjustments
        buffer_suggestions = self._suggest_buffer_adjustments(graph)
        suggestions.extend(buffer_suggestions)
        
        # Suggest critical path optimizations
        critical_suggestions = self._suggest_critical_path_optimizations(graph)
        suggestions.extend(critical_suggestions)
        
        return suggestions
    
    def _find_parallel_opportunities(self, graph: DependencyGraph) -> List[str]:
        """Find opportunities for parallel execution"""
        suggestions = []
        
        # Find activities that could run in parallel
        independent_activities = []
        for activity_id, node in graph.nodes.items():
            if not node.predecessors or len(node.predecessors) <= 1:
                independent_activities.append((activity_id, node))
        
        if len(independent_activities) > 1:
            suggestions.append(
                f"Consider running {len(independent_activities)} independent activities in parallel"
            )
        
        return suggestions
    
    def _suggest_buffer_adjustments(self, graph: DependencyGraph) -> List[str]:
        """Suggest buffer time adjustments"""
        suggestions = []
        
        # Find activities with excessive slack
        for activity_id, node in graph.nodes.items():
            if node.slack and node.slack > timedelta(hours=4):
                suggestions.append(
                    f"Activity '{node.activity.name}' has excessive slack ({node.slack}) - "
                    "consider reducing buffer time"
                )
        
        return suggestions
    
    def _suggest_critical_path_optimizations(self, graph: DependencyGraph) -> List[str]:
        """Suggest optimizations for critical path activities"""
        suggestions = []
        
        critical_activities = [
            node for node in graph.nodes.values() if node.is_critical
        ]
        
        if len(critical_activities) > len(graph.nodes) * 0.5:
            suggestions.append(
                "More than 50% of activities are on critical path - "
                "consider adding resources or reducing scope"
            )
        
        # Suggest duration reduction for critical activities
        for node in critical_activities:
            if node.activity.duration > timedelta(hours=4):
                suggestions.append(
                    f"Critical activity '{node.activity.name}' has long duration - "
                    "consider breaking into smaller tasks"
                )
        
        return suggestions
    
    def validate_timeline(self, graph: DependencyGraph) -> List[str]:
        """Validate the timeline and return any issues"""
        issues = []
        
        # Check for cycles
        if graph.has_cycle():
            issues.append("Timeline contains circular dependencies")
        
        # Check for conflicts
        conflicts = self.resolve_conflicts(graph)
        issues.extend(conflicts)
        
        # Validate individual activities
        for node in graph.nodes.values():
            activity_issues = node.activity.validate()
            issues.extend([f"Activity '{node.activity.name}': {issue}" for issue in activity_issues])
        
        # Validate dependencies
        for dependency in graph.dependencies:
            dependency_issues = dependency.validate()
            issues.extend([f"Dependency: {issue}" for issue in dependency_issues])
        
        return issues