"""Dependency resolution — topological sort, conflict & circular-dependency detection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import AbstractSet, Mapping


@dataclass(frozen=True)
class ResolvedNode:
    """A single resolved dependency in topological order."""

    name: str
    version_range: str | None = None
    depth: int = 0  # depth in the dependency graph


@dataclass
class ResolutionResult:
    """Output of dependency resolution."""

    order: list[ResolvedNode] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    cycles: list[list[str]] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.conflicts and not self.cycles


class DependencyResolver:
    """Resolves agent dependency graphs with conflict detection and topological ordering.

    Supply a mapping of ``agent_name -> set_of_dependency_names`` and call
    :meth:`resolve`.  The resolver will detect cycles, identify conflicting
    version requirements (if you provide a ``version_map``), and return a
    topological ordering.
    """

    def __init__(
        self,
        graph: Mapping[str, AbstractSet[str] | tuple[str, ...]],
        version_map: Mapping[str, str | None] | None = None,
    ) -> None:
        self.graph = {k: set(v) for k, v in graph.items()}
        self.version_map: dict[str, str | None] = dict(version_map or {})

    def resolve(self) -> ResolutionResult:
        result = ResolutionResult()

        # -- detect cycles via DFS --
        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[str, int] = {node: WHITE for node in self.graph}
        path: list[str] = []

        def dfs(node: str) -> None:
            color[node] = GRAY
            path.append(node)
            for dep in sorted(self.graph.get(node, set())):
                if dep not in color:
                    # External dep not in graph — add as leaf
                    color[dep] = WHITE
                    self.graph[dep] = set()
                if color[dep] == GRAY:
                    cycle_start = path.index(dep)
                    result.cycles.append(list(path[cycle_start:]) + [dep])
                elif color[dep] == WHITE:
                    dfs(dep)
            path.pop()
            color[node] = BLACK

        for node in sorted(self.graph):
            if color[node] == WHITE:
                dfs(node)

        # -- detect conflicts (same dep appears with different version ranges) --
        if self.version_map:
            ranges_by_dep: dict[str, list[str]] = {}
            for dep, vr in self.version_map.items():
                if vr is not None:
                    ranges_by_dep.setdefault(dep, []).append(vr)
            for dep, ranges in ranges_by_dep.items():
                unique = set(ranges)
                if len(unique) > 1:
                    result.conflicts.append(
                        f'{dep} has conflicting version requirements: {", ".join(sorted(unique))}'
                    )

        # -- topological sort (Kahn's algorithm) --
        # Graph: node -> set of dependencies it requires.
        # We want dependencies listed BEFORE their dependents.
        # Build reverse adjacency: for each dependency edge (node -> dep),
        # dep has an "incoming" edge from node. In-degree = number of dependents.
        # Kahn's starts with nodes that have no dependents (leaves) and works up.
        # But we want deps first, so we reverse: use forward in-degree (how many
        # of your deps are unresolved) and start with nodes whose deps are all
        # resolved (i.e., leaves with no deps = in-degree 0 in the "remaining deps" sense).
        if not result.cycles:
            all_nodes = set(self.graph)
            for deps in self.graph.values():
                all_nodes.update(deps)

            # out_degree: number of unresolved deps for each node
            remaining_deps: dict[str, set[str]] = {}
            for node in all_nodes:
                remaining_deps[node] = set(self.graph.get(node, set())) & all_nodes

            # in_degree: number of nodes that depend on this node
            reverse: dict[str, set[str]] = {n: set() for n in all_nodes}
            for node, deps in remaining_deps.items():
                for dep in deps:
                    reverse[dep].add(node)

            # Start with nodes that have no dependencies (leaves)
            queue = sorted([n for n in all_nodes if not remaining_deps[n]])
            order: list[str] = []

            while queue:
                node = queue.pop(0)
                order.append(node)
                # This node is resolved; update its dependents
                for dependent in sorted(reverse.get(node, set())):
                    remaining_deps[dependent].discard(node)
                    if not remaining_deps[dependent]:
                        queue.append(dependent)
                        queue.sort()

            if len(order) != len(all_nodes):
                result.cycles.append(["<unresolved>"])

            # Compute depths: leaf deps = depth 0, their dependents = depth 1, etc.
            depth_map: dict[str, int] = {}
            for node in order:
                max_dep_depth = -1
                for dep in self.graph.get(node, set()):
                    if dep in depth_map:
                        max_dep_depth = max(max_dep_depth, depth_map[dep])
                depth_map[node] = max_dep_depth + 1

            result.order = [
                ResolvedNode(
                    name=n,
                    version_range=self.version_map.get(n),
                    depth=depth_map.get(n, 0),
                )
                for n in order
            ]

        return result

    @staticmethod
    def detect_circular(
        graph: Mapping[str, AbstractSet[str] | tuple[str, ...]],
    ) -> list[list[str]]:
        """Quick check for circular dependencies. Returns list of cycles found."""
        resolver = DependencyResolver(graph)
        result = resolver.resolve()
        return result.cycles
