"""Exact investigation operations over the portable case; no network or truth scoring."""
from __future__ import annotations

from collections import deque
import copy
import datetime as dt
from pathlib import PurePosixPath
import re

COLLECTIONS = ("nodes", "edges", "sources", "hypotheses", "leads", "games")
ACCESS_STATES = {"discovered", "inspected", "read", "inaccessible", "excluded"}
LEVELS = {"high", "medium", "low"}


def record_index(data):
    return {name + ":" + row["id"]: row
            for name in COLLECTIONS for row in (data.get(name, []) if isinstance(data.get(name, []), list) else [])
            if isinstance(row, dict) and isinstance(row.get("id"), str)}


def source_parents(source):
    parents = [source["origin_id"]] if isinstance(source.get("origin_id"), str) else []
    parents += source.get("origin_ids", []) if isinstance(source.get("origin_ids"), list) else []
    return list(dict.fromkeys(p for p in parents if isinstance(p, str)))


def dependency_graph(data):
    """Map each record token to its declared prerequisites, excluding contextual links."""
    index = record_index(data)
    graph = {token: set() for token in index}

    def add(dependent, prerequisite):
        if dependent in graph and prerequisite in graph:
            graph[dependent].add(prerequisite)

    def refs(row, field):
        value = row.get(field, [])
        return [v for v in value if isinstance(v, str)] if isinstance(value, list) else []

    for token, row in index.items():
        collection, _ = token.split(":", 1)
        for prerequisite in refs(row, "depends_on"):
            add(token, prerequisite)
        if collection == "sources":
            for parent in source_parents(row):
                add(token, "sources:" + parent)
        elif collection == "edges":
            for source in refs(row, "source_ids"):
                add(token, "sources:" + source)
            for hypothesis in refs(row, "hypothesis_ids"):
                add("hypotheses:" + hypothesis, token)
        elif collection == "hypotheses":
            for edge in refs(row, "supports") + refs(row, "challenges"):
                add(token, "edges:" + edge)
        elif collection == "leads":
            for field, kind in (("source_ids", "sources"), ("edge_ids", "edges")):
                for identifier in refs(row, field):
                    add(token, kind + ":" + identifier)
    return graph


def dependency_cycle(graph):
    """Return one concrete cycle without recursion, including deep source chains."""
    done = set()
    for root in sorted(graph):
        if root in done:
            continue
        path, positions = [root], {root: 0}
        stack = [(root, iter(sorted(graph[root])))]
        while stack:
            token, children = stack[-1]
            child = next(children, None)
            if child is None:
                done.add(token)
                stack.pop()
                positions.pop(token)
                path.pop()
            elif child in positions:
                return path[positions[child]:] + [child]
            elif child not in done:
                positions[child] = len(path)
                path.append(child)
                stack.append((child, iter(sorted(graph[child]))))
    return []


def dependency_coverage(data, graph=None):
    graph = dependency_graph(data) if graph is None else graph
    untracked = []
    for token, row in record_index(data).items():
        collection, identifier = token.split(":", 1)
        analytical = (collection in {"hypotheses", "games"}
                      or collection == "edges" and row.get("status") == "inferred"
                      or collection == "leads" and row.get("status") == "answered")
        if analytical and not graph[token]:
            untracked.append({"collection": collection, "id": identifier, "token": token,
                              "reason": "Analytical record has no declared evidentiary prerequisite; prose is not traced."})
    return {
        "scope": "Declared dependencies only; all substantive premises still require human/model review.",
        "untracked_analytical_records": untracked,
        "warnings": (["Untracked analytical records require a manual dependency sweep before claiming complete review coverage."]
                     if untracked else [])
                    + ["Missing ancestry does not establish source independence.",
                       "Contextual node links, prose citations and unknown extension fields are not automatically evidence dependencies."],
    }


def validate_additions(data):
    errors, warnings = [], []
    if not isinstance(data, dict):
        return errors, warnings
    index = record_index(data)

    def issue(path, message, warning=False):
        (warnings if warning else errors).append({"path": path, "message": message})

    def text(obj, key, path):
        if key in obj and (not isinstance(obj[key], str) or not obj[key].strip()):
            issue(path + "." + key, "Expected a nonempty string.")

    def strings(obj, key, path):
        if key not in obj:
            return []
        value = obj[key]
        if not isinstance(value, list):
            issue(path + "." + key, "Expected an array of strings.")
            return []
        valid = []
        for i, item in enumerate(value):
            if not isinstance(item, str) or not item.strip():
                issue(f"{path}.{key}[{i}]", "Expected a nonempty string.")
            else:
                valid.append(item)
        if len(valid) != len(set(valid)):
            issue(path + "." + key, "Repeated references do not create additional evidence or placement.", True)
        return valid

    def references(obj, key, path, collection):
        values = strings(obj, key, path)
        for i, identifier in enumerate(values):
            if collection + ":" + identifier not in index:
                issue(f"{path}.{key}[{i}]", "Unknown " + collection + " ID: " + identifier)
        return values

    for collection in COLLECTIONS:
        rows = data.get(collection, [])
        if not isinstance(rows, list):
            continue
        for i, row in enumerate(rows):
            if not isinstance(row, dict):
                continue
            path = f"$.{collection}[{i}]"
            for j, reference in enumerate(strings(row, "depends_on", path)):
                if reference not in index:
                    issue(f"{path}.depends_on[{j}]", "Unresolved dependency; use exact plural COLLECTION:ID: " + reference)
            if collection == "sources":
                references(row, "origin_ids", path, "sources")
                if "access_state" in row and (not isinstance(row["access_state"], str) or row["access_state"] not in ACCESS_STATES):
                    issue(path + ".access_state", "Expected discovered, inspected, read, inaccessible or excluded.")
                if "note_path" in row:
                    text(row, "note_path", path)
                    value = row["note_path"]
                    if isinstance(value, str):
                        normalized = value.replace("\\", "/")
                        note = PurePosixPath(normalized)
                        if (note.is_absolute() or ".." in note.parts or ":" in normalized
                                or not note.parts or any(ord(c) < 32 for c in normalized)):
                            issue(path + ".note_path", "Use a relative path inside the case directory without parent traversal or a URL.")
            elif collection == "leads":
                for key in ("custodian", "record_type", "query"):
                    text(row, key, path)
                for key in ("decision_value", "effort"):
                    if key in row and (not isinstance(row[key], str) or row[key] not in LEVELS):
                        issue(path + "." + key, "Expected high, medium or low.")
    graph = dependency_graph(data)
    cycle = dependency_cycle(graph)
    if cycle:
        label = "Source ancestry cycle" if all(t.startswith("sources:") for t in cycle) else "Dependency cycle"
        issue("$", label + ": " + " -> ".join(cycle))

    case = data.get("case")
    if not isinstance(case, dict):
        return errors, warnings
    if "campaign" in case:
        campaign = case["campaign"]
        if not isinstance(campaign, dict):
            issue("$.case.campaign", "Expected an object.")
        else:
            for key in ("phase", "resume"):
                text(campaign, key, "$.case.campaign")
            for key, statuses in (("coverage", {"open", "partial", "covered", "parked"}),
                                  ("tasks", {"open", "active", "done", "parked"})):
                if key not in campaign:
                    continue
                rows = campaign[key]
                if not isinstance(rows, list):
                    issue("$.case.campaign." + key, "Expected an array.")
                    continue
                seen = set()
                for i, row in enumerate(rows):
                    path = f"$.case.campaign.{key}[{i}]"
                    if not isinstance(row, dict):
                        issue(path, "Expected an object.")
                        continue
                    for field in ("id", "question", "status"):
                        if field not in row:
                            issue(path + "." + field, "Required field is missing.")
                        else:
                            text(row, field, path)
                    identifier = row.get("id")
                    if isinstance(identifier, str):
                        if identifier in seen:
                            issue(path + ".id", "Duplicate campaign " + key + " ID: " + identifier)
                        seen.add(identifier)
                    if not isinstance(row.get("status"), str) or row["status"] not in statuses:
                        issue(path + ".status", "Expected one of: " + ", ".join(sorted(statuses)) + ".")
                    for field, kind in (("source_ids", "sources"), ("lead_ids", "leads")):
                        references(row, field, path, kind)
                    if key == "coverage":
                        strings(row, "searches", path)
                        text(row, "remaining_gap", path)
                    else:
                        text(row, "owner", path)
                        text(row, "return_condition", path)
    if "views" in case:
        views = case["views"]
        if not isinstance(views, dict):
            issue("$.case.views", "Expected an object.")
        else:
            nodes = {t.split(":", 1)[1]: row for t, row in index.items() if t.startswith("nodes:")}
            groups = {n.get("group") or "Ungrouped" for n in nodes.values() if isinstance(n.get("group", ""), str)}
            for group in strings(views, "group_order", "$.case.views"):
                if group not in groups:
                    issue("$.case.views.group_order", "Unknown group: " + group)
            references(views, "pinned_nodes", "$.case.views", "nodes")
            limit = views.get("overview_limit", 9)
            if type(limit) is not int or not 1 <= limit <= 50:
                issue("$.case.views.overview_limit", "Expected integer 1 through 50.")
            for key in ("group_hubs", "overview"):
                if key not in views:
                    continue
                mapping = views[key]
                if not isinstance(mapping, dict):
                    issue("$.case.views." + key, "Expected an object mapping group names.")
                    continue
                for group, value in mapping.items():
                    path = "$.case.views." + key + "." + str(group)
                    if group not in groups:
                        issue(path, "Unknown group.")
                    identifiers = strings({"nodes": value}, "nodes", path) if key == "overview" else [value]
                    for identifier in identifiers:
                        if not isinstance(identifier, str) or identifier not in nodes:
                            issue(path, "Unknown node ID.")
                        elif (nodes[identifier].get("group") or "Ungrouped") != group:
                            issue(path, "Curated node must belong to the mapped group.")
    warnings += [{"path": item["token"], "message": item["reason"]}
                 for item in dependency_coverage(data, graph)["untracked_analytical_records"]]
    return errors, warnings


def impact_records(data, changed_tokens, previous=None):
    """Follow all declared evidence paths; previous state keeps removed/replaced dependencies visible."""
    graph = dependency_graph(data)
    if previous is not None:
        for token, dependencies in dependency_graph(previous).items():
            graph.setdefault(token, set()).update(dependencies)
    index = record_index(previous) if previous is not None else {}
    index.update(record_index(data))
    seeds = list(dict.fromkeys(changed_tokens))
    missing = [token for token in seeds if token not in graph]
    if missing:
        raise ValueError("Unknown record token: " + ", ".join(missing))
    dependents = {token: set() for token in graph}
    for token, prerequisites in graph.items():
        for prerequisite in prerequisites:
            dependents[prerequisite].add(token)
    affected = set(seeds)
    queue = deque(seeds)
    while queue:
        for dependent in sorted(dependents[queue.popleft()]):
            if dependent not in affected:
                affected.add(dependent)
                queue.append(dependent)
    affected_ids = {collection: sorted(token.split(":", 1)[1] for token in affected
                                       if token.startswith(collection + ":")) for collection in COLLECTIONS}
    affected_edges = []
    for identifier in affected_ids["edges"]:
        row = index["edges:" + identifier]
        source_ids = row.get("source_ids", [])
        affected_edges.append({
            "id": identifier, "status": row.get("status"),
            "affected_source_ids": [sid for sid in source_ids if "sources:" + sid in affected],
            "remaining_source_ids": [sid for sid in source_ids if "sources:" + sid not in affected],
            "affected_dependencies": sorted(graph["edges:" + identifier] & affected),
        })
    affected_hypotheses = []
    for identifier in affected_ids["hypotheses"]:
        row = index["hypotheses:" + identifier]
        affected_hypotheses.append({
            "id": identifier, "status": row.get("status"),
            "edge_ids": sorted(t.split(":", 1)[1] for t in graph["hypotheses:" + identifier] & affected
                               if t.startswith("edges:")),
            "edge_tagged": any(identifier in edge.get("hypothesis_ids", [])
                               for token, edge in index.items()
                               if token.startswith("edges:") and token in affected),
        })
    coverage = dependency_coverage(data)
    return {
        "changed_tokens": seeds, "affected_ids": affected_ids,
        "affected_node_ids": affected_ids["nodes"], "affected_source_ids": affected_ids["sources"],
        "affected_edge_ids": affected_ids["edges"], "affected_hypothesis_ids": affected_ids["hypotheses"],
        "affected_lead_ids": affected_ids["leads"], "affected_game_ids": affected_ids["games"],
        "affected_edges": affected_edges, "affected_hypotheses": affected_hypotheses,
        "untracked_analytical_records": coverage["untracked_analytical_records"],
        "coverage": coverage,
        "note": "Dependency impact only. Review all affected records and untracked analytical premises; no truth judgment or status change was made.",
    }


def _structural_metrics(node_ids, edges):
    adjacency = {identifier: set() for identifier in node_ids}
    pair_edges = {}
    for edge in edges:
        a, b = edge["source"], edge["target"]
        if a == b:
            continue
        adjacency[a].add(b)
        adjacency[b].add(a)
        pair_edges.setdefault(tuple(sorted((a, b))), []).append(edge["id"])
    discovery, low, parent, child_count = {}, {}, {}, {}
    articulations, bridges = set(), []
    clock, components = 0, 0
    for root in sorted(adjacency):
        if root in discovery:
            continue
        components += 1
        clock += 1
        discovery[root] = low[root] = clock
        parent[root], child_count[root] = None, 0
        stack = [(root, iter(sorted(adjacency[root])))]
        while stack:
            node, neighbors = stack[-1]
            other = next(neighbors, None)
            if other is None:
                stack.pop()
                above = parent[node]
                if above is None:
                    if child_count[node] > 1:
                        articulations.add(node)
                else:
                    low[above] = min(low[above], low[node])
                    if parent[above] is not None and low[node] >= discovery[above]:
                        articulations.add(above)
                    if low[node] > discovery[above]:
                        bridges.append(tuple(sorted((above, node))))
            elif other not in discovery:
                parent[other] = node
                child_count[node] += 1
                child_count[other] = 0
                clock += 1
                discovery[other] = low[other] = clock
                stack.append((other, iter(sorted(adjacency[other]))))
            elif other != parent[node]:
                low[node] = min(low[node], discovery[other])
    return {
        "components": components,
        "articulation_node_ids": sorted(articulations),
        "bridge_pairs": [{"node_ids": list(pair), "edge_ids": sorted(pair_edges[pair])} for pair in sorted(bridges)],
        "isolated_node_ids": sorted(identifier for identifier, adjacent in adjacency.items() if not adjacent),
    }


def coverage_gaps(data):
    return copy.deepcopy([row for row in data.get("case", {}).get("campaign", {}).get("coverage", [])
                          if row.get("status") in {"open", "partial"}])


def scan_case(data):
    nodes = {node["id"]: node for node in data["nodes"]}
    active = [edge for edge in data["edges"] if edge["status"] != "retracted"]
    documented = [edge for edge in active if edge["status"] == "documented"]
    baseline = _structural_metrics(nodes, active)
    strict = _structural_metrics(nodes, documented)
    cross = [edge for edge in active if (nodes[edge["source"]].get("group") or "Ungrouped")
             != (nodes[edge["target"]].get("group") or "Ungrouped")]
    crossing_by_node = {}
    for edge in cross:
        for identifier in (edge["source"], edge["target"]):
            crossing_by_node.setdefault(identifier, []).append(edge["id"])
    candidates = []
    for identifier in sorted(set(crossing_by_node) | set(baseline["articulation_node_ids"]) | set(strict["articulation_node_ids"])):
        reasons = []
        if identifier in crossing_by_node:
            reasons.append("Connects editorial workstreams; inspect what crosses these relationships.")
        if identifier in baseline["articulation_node_ids"]:
            reasons.append("Its removal splits the current undirected graph; test real substitutes and collection gaps.")
        if identifier in strict["articulation_node_ids"] and identifier not in baseline["articulation_node_ids"]:
            reasons.append("Becomes an articulation when only documented edges remain; inspect support for alternate routes.")
        candidates.append({"node_id": identifier, "label": nodes[identifier]["label"],
                           "cross_group_edge_ids": sorted(crossing_by_node.get(identifier, [])), "reasons": reasons,
                           "next_question": "Which record establishes the actual resource, access or decision right, and what would bypass it?"})
    return {
        "case_id": data["case"]["id"],
        "basis": "Undirected simple topology of active relations; parallel assertions form one pair. Direction and exact verbs remain in edge records.",
        "counts": {"nodes": len(nodes), "active_edges": len(active), "documented_edges": len(documented)},
        "active": baseline, "documented_only": strict,
        "sensitivity": {
            "excluded_edge_ids": sorted(edge["id"] for edge in active if edge["status"] != "documented"),
            "new_articulation_node_ids": sorted(set(strict["articulation_node_ids"]) - set(baseline["articulation_node_ids"])),
            "lost_articulation_node_ids": sorted(set(baseline["articulation_node_ids"]) - set(strict["articulation_node_ids"])),
            "component_change": strict["components"] - baseline["components"],
        },
        "cross_group_edge_ids": sorted(edge["id"] for edge in cross),
        "structural_candidates": candidates,
        "date_gaps": [{"edge_id": edge["id"], "start": edge.get("start"), "end": edge.get("end"),
                       "date_note": edge.get("date_note"), "question": "Which dated record bounds this relationship?"}
                      for edge in active if not edge.get("start") or not edge.get("end")],
        "source_access_gaps": [{"source_id": source["id"], "access_state": source.get("access_state", "unrecorded"),
                                "locator": source.get("locator"), "url": source.get("url")}
                               for source in data["sources"] if source.get("access_state") not in {"inspected", "read"}],
        "coverage_gaps": coverage_gaps(data),
        "dependency_coverage": dependency_coverage(data),
        "note": "Structural candidates are collection prompts, never influence, guilt, causal force or truth scores. A bridge pair disconnects only when every parallel edge on that pair is removed.",
    }


def frontier_case(data):
    value_order = {"high": 0, "medium": 1, "low": 2}
    effort_order = {"low": 0, "medium": 1, "high": 2}
    candidates = [lead for lead in data["leads"] if lead["status"] in {"open", "pursuing"}]

    def rank(lead):
        return (value_order.get(lead.get("decision_value"), 3),
                value_order.get(lead.get("priority"), 3),
                effort_order.get(lead.get("effort"), 3), lead["id"])

    results = []
    for lead in sorted(candidates, key=rank):
        item = copy.deepcopy(lead)
        item["ranking_reasons"] = [
            ("Supplied " + field + ": " + lead[field]) if field in lead else ("No " + field + " assessment supplied")
            for field in ("decision_value", "priority", "effort")]
        item["acquisition_gaps"] = [field for field in ("custodian", "record_type", "query") if not lead.get(field)]
        results.append(item)
    return {
        "case_id": data["case"]["id"], "leads": results, "coverage_gaps": coverage_gaps(data),
        "ranking_rule": "Supplied decision value (high first), then priority (high first), then effort (low first), then stable ID. Missing assessments sort after supplied values at each tier.",
        "note": "Ordinal editorial ordering, not computed expected information or confidence. Fill acquisition gaps to turn a question into an obtainable record.",
    }


def resume_case(data):
    campaign = data["case"].get("campaign", {})
    frontier = frontier_case(data)
    return {
        "case_id": data["case"]["id"], "title": data["case"]["title"], "question": data["case"]["question"],
        "updated_at": data["case"]["updated_at"], "phase": campaign.get("phase"),
        "checkpoint": campaign.get("resume"),
        "unresolved_tasks": copy.deepcopy([task for task in campaign.get("tasks", []) if task["status"] in {"open", "active"}]),
        "parked_tasks": copy.deepcopy([task for task in campaign.get("tasks", []) if task["status"] == "parked"]),
        "next_leads": frontier["leads"][:10], "remaining_actionable_leads": max(0, len(frontier["leads"]) - 10),
        "parked_lead_ids": [lead["id"] for lead in data["leads"] if lead["status"] == "parked"],
        "coverage_gaps": frontier["coverage_gaps"], "dependency_coverage": dependency_coverage(data),
        "available_views": copy.deepcopy(data["case"].get("views", {})),
        "latest_revision": copy.deepcopy(data["case"].get("journal", [])[-1:]),
        "note": "Resume from the recorded checkpoint and next obtainable record. Missing campaign state remains explicit; no completed work or source access is inferred.",
    }


def _merge_object(original, update):
    result = copy.deepcopy(original)
    for key, value in update.items():
        result[key] = (_merge_object(result[key], value) if isinstance(result.get(key), dict) and isinstance(value, dict)
                       else copy.deepcopy(value))
    return result


def apply_changes(data, patch, actual_hash, timestamp=None):
    """Pure optimistic merge. Caller validates the complete result before publishing a new file."""
    if not isinstance(patch, dict):
        raise ValueError("Patch must be an object.")
    unknown = set(patch) - {"base_sha256", "reason", "case", "upsert", "remove"}
    if unknown:
        raise ValueError("Unknown patch control fields: " + ", ".join(sorted(unknown)))
    if not isinstance(patch.get("base_sha256"), str) or not re.fullmatch(r"[0-9a-fA-F]{64}", patch["base_sha256"]):
        raise ValueError("Patch requires the SHA-256 of the original case bytes.")
    if patch["base_sha256"].lower() != actual_hash:
        raise ValueError("Patch base_sha256 does not match the current case bytes; reread and reconcile before retrying.")
    if not isinstance(patch.get("reason"), str) or not patch["reason"].strip():
        raise ValueError("Patch requires a nonempty reason.")
    operations = {}
    for name in ("upsert", "remove"):
        mapping = patch.get(name, {})
        if not isinstance(mapping, dict) or set(mapping) - set(COLLECTIONS):
            raise ValueError(name + " must map exact collection names to arrays.")
        operations[name] = {}
        for collection, rows in mapping.items():
            if not isinstance(rows, list):
                raise ValueError(name + "." + collection + " must be an array.")
            identifiers = []
            for row in rows:
                identifier = row.get("id") if name == "upsert" and isinstance(row, dict) else row if name == "remove" else None
                if not isinstance(identifier, str) or not identifier.strip():
                    raise ValueError(name + "." + collection + " requires records/IDs with nonempty IDs.")
                if identifier in identifiers:
                    raise ValueError("Conflicting duplicate " + name + " for " + collection + ":" + identifier)
                identifiers.append(identifier)
            operations[name][collection] = (rows, identifiers)
    result = copy.deepcopy(data)
    changed, removed = [], []
    for collection in COLLECTIONS:
        upserts, upsert_ids = operations["upsert"].get(collection, ([], []))
        _, remove_ids = operations["remove"].get(collection, ([], []))
        overlap = set(upsert_ids) & set(remove_ids)
        if overlap:
            raise ValueError("Cannot both upsert and remove " + collection + ": " + ", ".join(sorted(overlap)))
        existing = {row["id"]: row for row in result[collection]}
        for identifier in remove_ids:
            if identifier not in existing:
                raise ValueError("Cannot remove unknown " + collection + ":" + identifier)
            del existing[identifier]
            token = collection + ":" + identifier
            changed.append(token)
            removed.append(token)
        for row in upserts:
            old = existing.get(row["id"], {})
            merged = _merge_object(old, row)
            if merged != old:
                changed.append(collection + ":" + row["id"])
            existing[row["id"]] = merged
        result[collection] = list(existing.values())
    case_update = patch.get("case", {})
    if not isinstance(case_update, dict):
        raise ValueError("Patch case must be a partial object.")
    previous_case = copy.deepcopy(result["case"])
    result["case"] = _merge_object(result["case"], case_update)
    if not changed and result["case"] == previous_case:
        raise ValueError("Patch has no material change.")
    if not isinstance(result["case"].get("journal", []), list):
        raise ValueError("case.journal must be an array.")
    when = timestamp or dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    result["case"]["updated_at"] = when
    result["case"].setdefault("journal", []).append({
        "date": when, "change": patch["reason"], "changed_tokens": changed,
        "case_fields": sorted(case_update), "base_sha256": actual_hash,
    })
    return result, {"changed_tokens": changed, "removed_tokens": removed, "case_fields": sorted(case_update)}
