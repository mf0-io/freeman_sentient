"""
Temporal People Graph — cross-platform relationship tracking over time.

Tracks every person Freeman interacts with across Telegram, Twitter/X,
Kickstarter, and YouTube. Builds a temporal graph where:
- Nodes = people (with cross-platform identity resolution)
- Edges = interactions (with timestamps, types, and platform source)
- Snapshots = graph state at any point in time

Enables: influence analysis, community evolution tracking,
cross-platform identity resolution, and relationship trajectory queries.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class PersonNode:
    """A person in the temporal graph."""
    person_id: str
    name: str
    platform_ids: Dict[str, str] = field(default_factory=dict)
    first_seen: datetime = field(default_factory=datetime.utcnow)
    last_seen: datetime = field(default_factory=datetime.utcnow)
    platforms: List[str] = field(default_factory=list)
    role: str = "community"  # team, community, influencer, backer, viewer, bot
    tags: List[str] = field(default_factory=list)
    influence_score: float = 0.0
    interaction_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["first_seen"] = self.first_seen.isoformat()
        d["last_seen"] = self.last_seen.isoformat()
        return d


@dataclass
class InteractionEdge:
    """A directed interaction between two people."""
    edge_id: str
    source_id: str
    target_id: str
    interaction_type: str  # mention, reply, comment, back, subscribe, react, collaborate
    platform: str  # telegram, twitter, kickstarter, youtube
    timestamp: datetime = field(default_factory=datetime.utcnow)
    weight: float = 1.0
    context: str = ""
    sentiment: Optional[float] = None  # -1.0 to 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        return d


@dataclass
class GraphSnapshot:
    """Graph state at a specific point in time."""
    timestamp: datetime
    node_count: int
    edge_count: int
    active_platforms: List[str]
    top_connectors: List[Dict[str, Any]]
    community_clusters: List[Dict[str, Any]]
    metrics: Dict[str, Any]


class TemporalPeopleGraph:
    """
    Temporal graph of all people Freeman interacts with.

    Stores nodes (people) and edges (interactions) with full temporal
    history. Supports time-sliced queries, influence analysis,
    cross-platform identity resolution, and community detection.

    Backed by Graphiti (Neo4j) for persistent storage and graph traversal.
    """

    def __init__(self, adapter=None):
        """
        Initialize the temporal people graph.

        Args:
            adapter: GraphitiAdapter instance for persistent storage.
                     If None, operates in memory-only mode.
        """
        self.adapter = adapter
        self._nodes: Dict[str, PersonNode] = {}
        self._edges: List[InteractionEdge] = []
        self._platform_index: Dict[str, Dict[str, str]] = defaultdict(dict)
        self._edge_counter = 0

    async def initialize(self) -> None:
        """Load existing graph from persistent storage."""
        if self.adapter:
            try:
                results = await self.adapter.search_memory(
                    "person node temporal graph",
                    limit=1000
                )
                for r in results:
                    if r.get("entity_type") == "person_node":
                        attrs = r.get("attributes", {})
                        node = PersonNode(
                            person_id=attrs.get("person_id", r.get("entity_id", "")),
                            name=attrs.get("name", ""),
                            platform_ids=attrs.get("platform_ids", {}),
                            first_seen=datetime.fromisoformat(attrs["first_seen"]) if "first_seen" in attrs else datetime.utcnow(),
                            last_seen=datetime.fromisoformat(attrs["last_seen"]) if "last_seen" in attrs else datetime.utcnow(),
                            platforms=attrs.get("platforms", []),
                            role=attrs.get("role", "community"),
                            tags=attrs.get("tags", []),
                            influence_score=attrs.get("influence_score", 0.0),
                            interaction_count=attrs.get("interaction_count", 0),
                            metadata=attrs.get("metadata", {})
                        )
                        self._nodes[node.person_id] = node
                        for platform, pid in node.platform_ids.items():
                            self._platform_index[platform][pid] = node.person_id
                logger.info(f"Loaded {len(self._nodes)} person nodes from storage")
            except Exception as e:
                logger.warning(f"Failed to load graph from storage: {e}")

    # --- Node Operations ---

    async def add_person(
        self,
        name: str,
        platform: str,
        platform_user_id: str,
        role: str = "community",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PersonNode:
        """
        Add or update a person in the graph.

        Cross-platform identity resolution: if a person with the same
        platform_user_id already exists, updates the existing node.
        """
        existing_id = self._platform_index.get(platform, {}).get(platform_user_id)

        if existing_id and existing_id in self._nodes:
            node = self._nodes[existing_id]
            node.last_seen = datetime.utcnow()
            node.interaction_count += 1
            if platform not in node.platforms:
                node.platforms.append(platform)
            node.platform_ids[platform] = platform_user_id
            if tags:
                node.tags = list(set(node.tags + tags))
            if metadata:
                node.metadata.update(metadata)
        else:
            person_id = f"person:{platform}:{platform_user_id}"
            node = PersonNode(
                person_id=person_id,
                name=name,
                platform_ids={platform: platform_user_id},
                platforms=[platform],
                role=role,
                tags=tags or [],
                metadata=metadata or {},
            )
            self._nodes[person_id] = node
            self._platform_index[platform][platform_user_id] = person_id

        if self.adapter:
            try:
                await self.adapter.add_entity(
                    name=f"person_{node.person_id}",
                    entity_type="person_node",
                    attributes=node.to_dict(),
                )
            except Exception as e:
                logger.error(f"Failed to persist person node: {e}")

        return node

    async def merge_identities(
        self, person_id_a: str, person_id_b: str
    ) -> Optional[PersonNode]:
        """
        Merge two person nodes when they're the same person on different platforms.

        Keeps person_id_a as the primary, absorbs person_id_b.
        """
        node_a = self._nodes.get(person_id_a)
        node_b = self._nodes.get(person_id_b)
        if not node_a or not node_b:
            return None

        node_a.platform_ids.update(node_b.platform_ids)
        node_a.platforms = list(set(node_a.platforms + node_b.platforms))
        node_a.tags = list(set(node_a.tags + node_b.tags))
        node_a.first_seen = min(node_a.first_seen, node_b.first_seen)
        node_a.last_seen = max(node_a.last_seen, node_b.last_seen)
        node_a.interaction_count += node_b.interaction_count
        node_a.influence_score = max(node_a.influence_score, node_b.influence_score)
        node_a.metadata.update(node_b.metadata)

        for platform, pid in node_b.platform_ids.items():
            self._platform_index[platform][pid] = person_id_a

        for edge in self._edges:
            if edge.source_id == person_id_b:
                edge.source_id = person_id_a
            if edge.target_id == person_id_b:
                edge.target_id = person_id_a

        del self._nodes[person_id_b]
        logger.info(f"Merged {person_id_b} into {person_id_a}")
        return node_a

    async def get_person(self, person_id: str) -> Optional[PersonNode]:
        """Get a person node by ID."""
        return self._nodes.get(person_id)

    async def find_person_by_platform(
        self, platform: str, platform_user_id: str
    ) -> Optional[PersonNode]:
        """Find a person by their platform-specific ID."""
        person_id = self._platform_index.get(platform, {}).get(platform_user_id)
        if person_id:
            return self._nodes.get(person_id)
        return None

    async def list_people(
        self,
        platform: Optional[str] = None,
        role: Optional[str] = None,
        min_interactions: int = 0,
        limit: int = 100,
    ) -> List[PersonNode]:
        """List people with optional filters."""
        nodes = list(self._nodes.values())

        if platform:
            nodes = [n for n in nodes if platform in n.platforms]
        if role:
            nodes = [n for n in nodes if n.role == role]
        if min_interactions > 0:
            nodes = [n for n in nodes if n.interaction_count >= min_interactions]

        nodes.sort(key=lambda n: n.last_seen, reverse=True)
        return nodes[:limit]

    # --- Edge Operations ---

    async def add_interaction(
        self,
        source_id: str,
        target_id: str,
        interaction_type: str,
        platform: str,
        context: str = "",
        weight: float = 1.0,
        sentiment: Optional[float] = None,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> InteractionEdge:
        """
        Record an interaction between two people.

        Types: mention, reply, comment, back, subscribe, react, collaborate, quote
        """
        self._edge_counter += 1
        ts = timestamp or datetime.utcnow()

        edge = InteractionEdge(
            edge_id=f"edge:{self._edge_counter}:{ts.timestamp():.0f}",
            source_id=source_id,
            target_id=target_id,
            interaction_type=interaction_type,
            platform=platform,
            timestamp=ts,
            weight=weight,
            context=context,
            sentiment=sentiment,
            metadata=metadata or {},
        )
        self._edges.append(edge)

        for pid in [source_id, target_id]:
            if pid in self._nodes:
                self._nodes[pid].last_seen = max(self._nodes[pid].last_seen, ts)

        if self.adapter:
            try:
                await self.adapter.add_episode(
                    content=f"{interaction_type}: {source_id} -> {target_id} on {platform}. {context}",
                    reference_time=ts,
                    source_description=f"temporal_graph:{platform}",
                    entity_references=[source_id, target_id],
                )
            except Exception as e:
                logger.error(f"Failed to persist interaction edge: {e}")

        return edge

    async def get_interactions(
        self,
        person_id: str,
        direction: str = "both",
        interaction_type: Optional[str] = None,
        platform: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[InteractionEdge]:
        """Get interactions for a person with temporal and type filters."""
        edges = []
        for e in self._edges:
            if direction == "outgoing" and e.source_id != person_id:
                continue
            if direction == "incoming" and e.target_id != person_id:
                continue
            if direction == "both" and person_id not in (e.source_id, e.target_id):
                continue
            if interaction_type and e.interaction_type != interaction_type:
                continue
            if platform and e.platform != platform:
                continue
            if since and e.timestamp < since:
                continue
            if until and e.timestamp > until:
                continue
            edges.append(e)

        edges.sort(key=lambda e: e.timestamp, reverse=True)
        return edges[:limit]

    # --- Temporal Queries ---

    async def get_snapshot(self, at_time: datetime) -> GraphSnapshot:
        """Get the graph state at a specific point in time."""
        active_nodes = {
            pid: n for pid, n in self._nodes.items()
            if n.first_seen <= at_time
        }
        active_edges = [e for e in self._edges if e.timestamp <= at_time]

        platforms = set()
        for e in active_edges:
            platforms.add(e.platform)

        connection_counts = defaultdict(int)
        for e in active_edges:
            connection_counts[e.source_id] += 1
            connection_counts[e.target_id] += 1

        top_connectors = sorted(
            connection_counts.items(), key=lambda x: x[1], reverse=True
        )[:10]

        return GraphSnapshot(
            timestamp=at_time,
            node_count=len(active_nodes),
            edge_count=len(active_edges),
            active_platforms=list(platforms),
            top_connectors=[
                {"person_id": pid, "connections": cnt,
                 "name": self._nodes[pid].name if pid in self._nodes else "unknown"}
                for pid, cnt in top_connectors
            ],
            community_clusters=await self._detect_clusters(active_nodes, active_edges),
            metrics=self._compute_metrics(active_nodes, active_edges),
        )

    async def get_trajectory(
        self,
        person_id: str,
        start_time: datetime,
        end_time: datetime,
        granularity: str = "week",
    ) -> List[Dict[str, Any]]:
        """
        Get the interaction trajectory for a person over time.

        Returns time-bucketed interaction stats showing how the person's
        engagement evolved.
        """
        if granularity == "day":
            delta = timedelta(days=1)
        elif granularity == "week":
            delta = timedelta(weeks=1)
        elif granularity == "month":
            delta = timedelta(days=30)
        else:
            delta = timedelta(weeks=1)

        trajectory = []
        current = start_time

        while current < end_time:
            bucket_end = min(current + delta, end_time)
            edges = [
                e for e in self._edges
                if (e.source_id == person_id or e.target_id == person_id)
                and current <= e.timestamp < bucket_end
            ]

            platforms = set(e.platform for e in edges)
            types = defaultdict(int)
            for e in edges:
                types[e.interaction_type] += 1

            unique_contacts = set()
            for e in edges:
                if e.source_id == person_id:
                    unique_contacts.add(e.target_id)
                else:
                    unique_contacts.add(e.source_id)

            trajectory.append({
                "period_start": current.isoformat(),
                "period_end": bucket_end.isoformat(),
                "interaction_count": len(edges),
                "unique_contacts": len(unique_contacts),
                "platforms": list(platforms),
                "interaction_types": dict(types),
                "avg_sentiment": (
                    sum(e.sentiment for e in edges if e.sentiment is not None) /
                    max(1, sum(1 for e in edges if e.sentiment is not None))
                ) if any(e.sentiment is not None for e in edges) else None,
            })
            current = bucket_end

        return trajectory

    async def get_cross_platform_presence(
        self, person_id: str
    ) -> Dict[str, Dict[str, Any]]:
        """Get a person's activity breakdown per platform."""
        node = self._nodes.get(person_id)
        if not node:
            return {}

        result = {}
        for platform in node.platforms:
            edges = [
                e for e in self._edges
                if (e.source_id == person_id or e.target_id == person_id)
                and e.platform == platform
            ]
            if edges:
                result[platform] = {
                    "platform_id": node.platform_ids.get(platform, ""),
                    "interaction_count": len(edges),
                    "first_interaction": min(e.timestamp for e in edges).isoformat(),
                    "last_interaction": max(e.timestamp for e in edges).isoformat(),
                    "types": dict(defaultdict(int, {
                        e.interaction_type: sum(1 for x in edges if x.interaction_type == e.interaction_type)
                        for e in edges
                    })),
                }
        return result

    # --- Influence Analysis ---

    async def compute_influence_scores(self) -> Dict[str, float]:
        """
        Compute influence scores for all people using interaction-weighted PageRank.

        Higher score = more central/influential in the graph.
        """
        if not self._edges:
            return {}

        scores = {pid: 1.0 for pid in self._nodes}
        damping = 0.85
        iterations = 20

        for _ in range(iterations):
            new_scores = {pid: (1 - damping) for pid in self._nodes}

            outgoing_counts = defaultdict(float)
            for e in self._edges:
                outgoing_counts[e.source_id] += e.weight

            for e in self._edges:
                if outgoing_counts[e.source_id] > 0:
                    contribution = (
                        damping * scores.get(e.source_id, 0) *
                        e.weight / outgoing_counts[e.source_id]
                    )
                    new_scores[e.target_id] = new_scores.get(e.target_id, 0) + contribution

            scores = new_scores

        max_score = max(scores.values()) if scores else 1
        normalized = {pid: s / max_score for pid, s in scores.items()}

        for pid, score in normalized.items():
            if pid in self._nodes:
                self._nodes[pid].influence_score = round(score, 4)

        return normalized

    async def get_influence_path(
        self, source_id: str, target_id: str, max_depth: int = 4
    ) -> Optional[List[str]]:
        """Find the shortest interaction path between two people."""
        if source_id == target_id:
            return [source_id]

        adjacency = defaultdict(set)
        for e in self._edges:
            adjacency[e.source_id].add(e.target_id)
            adjacency[e.target_id].add(e.source_id)

        visited = {source_id}
        queue = [(source_id, [source_id])]

        while queue:
            current, path = queue.pop(0)
            if len(path) > max_depth:
                break

            for neighbor in adjacency[current]:
                if neighbor == target_id:
                    return path + [target_id]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return None

    # --- Graph Analytics ---

    async def get_stats(self) -> Dict[str, Any]:
        """Get overall graph statistics."""
        platform_counts = defaultdict(int)
        for n in self._nodes.values():
            for p in n.platforms:
                platform_counts[p] += 1

        role_counts = defaultdict(int)
        for n in self._nodes.values():
            role_counts[n.role] += 1

        interaction_type_counts = defaultdict(int)
        for e in self._edges:
            interaction_type_counts[e.interaction_type] += 1

        return {
            "total_people": len(self._nodes),
            "total_interactions": len(self._edges),
            "platforms": dict(platform_counts),
            "roles": dict(role_counts),
            "interaction_types": dict(interaction_type_counts),
            "multi_platform_people": sum(
                1 for n in self._nodes.values() if len(n.platforms) > 1
            ),
            "avg_interactions_per_person": (
                len(self._edges) / max(1, len(self._nodes))
            ),
        }

    # --- Internal Methods ---

    async def _detect_clusters(
        self, nodes: Dict, edges: List
    ) -> List[Dict[str, Any]]:
        """Simple community detection via connected components."""
        adjacency = defaultdict(set)
        for e in edges:
            if e.source_id in nodes and e.target_id in nodes:
                adjacency[e.source_id].add(e.target_id)
                adjacency[e.target_id].add(e.source_id)

        visited = set()
        clusters = []

        for node_id in nodes:
            if node_id in visited:
                continue
            cluster = set()
            stack = [node_id]
            while stack:
                current = stack.pop()
                if current in visited:
                    continue
                visited.add(current)
                cluster.add(current)
                for neighbor in adjacency.get(current, set()):
                    if neighbor not in visited:
                        stack.append(neighbor)

            if len(cluster) > 1:
                clusters.append({
                    "size": len(cluster),
                    "members": [
                        {"id": pid, "name": nodes[pid].name}
                        for pid in list(cluster)[:10]
                    ],
                })

        clusters.sort(key=lambda c: c["size"], reverse=True)
        return clusters[:10]

    def _compute_metrics(
        self, nodes: Dict, edges: List
    ) -> Dict[str, Any]:
        """Compute graph-level metrics."""
        if not nodes:
            return {"density": 0, "avg_degree": 0}

        degree = defaultdict(int)
        for e in edges:
            degree[e.source_id] += 1
            degree[e.target_id] += 1

        n = len(nodes)
        max_edges = n * (n - 1)
        density = len(edges) / max_edges if max_edges > 0 else 0

        return {
            "density": round(density, 6),
            "avg_degree": round(sum(degree.values()) / max(1, n), 2),
            "max_degree": max(degree.values()) if degree else 0,
            "isolated_nodes": sum(1 for pid in nodes if pid not in degree),
        }
