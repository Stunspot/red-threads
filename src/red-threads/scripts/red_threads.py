#!/usr/bin/env python3
"""RED THREADS case toolkit. Python 3.10+, standard library only."""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile
import uuid
from urllib.parse import urlsplit
import investigation_ops as ops

COLLECTIONS = ("nodes", "edges", "sources", "hypotheses", "leads", "games")
EDGE_STATUSES = {"documented", "reported", "inferred", "hypothesis", "disputed", "retracted"}
HYPOTHESIS_STATUSES = {"open", "supported", "weakened", "rejected", "parked"}
LEAD_STATUSES = {"open", "pursuing", "answered", "parked"}
GAME_KINDS = {"bargaining", "signaling", "coordination", "principal-agent", "coalition", "commitment"}
SKILL_ROOT = Path(__file__).resolve().parent.parent
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATETIME_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}[Tt ]\d{2}:\d{2}")


class CaseError(Exception):
    """A user-actionable error safe to return without a traceback."""

    def __init__(self, message, details=None):
        super().__init__(message)
        self.details = details


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise CaseError(message)


def _date(value, allow_datetime=False):
    if not isinstance(value, str):
        raise ValueError("must be an ISO date string")
    if DATE_PATTERN.fullmatch(value):
        return dt.date.fromisoformat(value)
    if allow_datetime and DATETIME_PATTERN.match(value):
        return dt.datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    raise ValueError("must be YYYY-MM-DD" + (" or an ISO datetime" if allow_datetime else ""))


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise CaseError("JSON contains a duplicate object key: " + repr(key))
        result[key] = value
    return result


def _reject_constant(value):
    raise CaseError("JSON contains a non-finite number: " + value)


def read_case(path):
    """Read strict UTF-8 JSON, also accepting a UTF-8 BOM."""
    try:
        with Path(path).open("r", encoding="utf-8-sig") as stream:
            return json.load(stream, object_pairs_hook=_unique_object, parse_constant=_reject_constant)
    except json.JSONDecodeError as exc:
        raise CaseError(f"Invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}") from None
    except UnicodeError:
        raise CaseError("Case file must contain valid UTF-8 text.") from None
    except RecursionError:
        raise CaseError("Case JSON is nested too deeply to process safely.") from None
    except OSError as exc:
        raise CaseError(f"Cannot read case file: {exc.strerror or type(exc).__name__}.") from None


def validate_case(data):
    """Validate structure and dependencies; never decide whether a claim is true."""
    errors, warnings = [], []

    def issue(path, message, warning=False):
        (warnings if warning else errors).append({"path": path, "message": message})

    def string(obj, key, path, required=False):
        if key not in obj:
            if required:
                issue(path + "." + key, "Required field is missing.")
            return None
        value = obj[key]
        if not isinstance(value, str) or (required and not value.strip()):
            issue(path + "." + key, "Expected " + ("a nonempty" if required else "a") + " string.")
            return None
        return value

    def strings(obj, key, path, required=False):
        if key not in obj:
            if required:
                issue(path + "." + key, "Required array is missing.")
            return []
        value = obj[key]
        if not isinstance(value, list):
            issue(path + "." + key, "Expected an array of strings.")
            return []
        for index, item in enumerate(value):
            if not isinstance(item, str) or not item.strip():
                issue(f"{path}.{key}[{index}]", "Expected a nonempty string.")
        return [item for item in value if isinstance(item, str) and item.strip()]

    def datefield(obj, key, path, required=False, timestamp=False, nullable=False):
        if key not in obj:
            if required:
                issue(path + "." + key, "Required date is missing.")
            return None
        if obj[key] is None and nullable:
            return None
        try:
            return _date(obj[key], allow_datetime=timestamp)
        except (ValueError, TypeError) as exc:
            issue(path + "." + key, str(exc))
            return None

    def status(obj, key, path, choices, required=True):
        value = string(obj, key, path, required)
        if value is not None and value not in choices:
            issue(path + "." + key, "Expected one of: " + ", ".join(sorted(choices)) + ".")
        return value

    def json_values(value, path):
        if isinstance(value, str):
            try:
                value.encode("utf-8")
            except UnicodeEncodeError:
                issue(path, "String contains an unpaired Unicode surrogate.")
        elif isinstance(value, float) and not math.isfinite(value):
            issue(path, "JSON numbers must be finite.")
        elif isinstance(value, dict):
            for key, item in value.items():
                if not isinstance(key, str):
                    issue(path, "JSON object keys must be strings.")
                else:
                    json_values(key, path)
                json_values(item, path + "." + str(key))
        elif isinstance(value, list):
            for index, item in enumerate(value):
                json_values(item, f"{path}[{index}]")
        elif value is not None and not isinstance(value, (bool, int, float)):
            issue(path, "Value is not a JSON data type.")

    if not isinstance(data, dict):
        return {"valid": False, "errors": [{"path": "$", "message": "Case must be a JSON object."}],
                "warnings": [], "counts": {}}
    try:
        json_values(data, "$")
    except RecursionError:
        issue("$", "Case is nested too deeply to validate safely.")
    if type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        issue("$.schema_version", "Expected integer schema version 1; migration must be explicit.")

    case = data.get("case")
    if not isinstance(case, dict):
        issue("$.case", "Expected a case object.")
    else:
        for key in ("id", "title", "question"):
            string(case, key, "$.case", True)
        datefield(case, "updated_at", "$.case", True, timestamp=True)
        for key in ("notes", "scope"):
            string(case, key, "$.case")
        for key in ("priors", "journal"):
            if key in case and not isinstance(case[key], list):
                issue("$.case." + key, "Expected an array.")

    records, indices = {}, {}
    for collection in COLLECTIONS:
        values = data.get(collection)
        records[collection], indices[collection] = [], {}
        if not isinstance(values, list):
            issue("$." + collection, "Expected a required array (empty is allowed).")
            continue
        for index, item in enumerate(values):
            path = f"$.{collection}[{index}]"
            if not isinstance(item, dict):
                issue(path, "Expected an object.")
                continue
            records[collection].append((item, path))
            identifier = string(item, "id", path, True)
            if identifier is not None:
                if identifier in indices[collection]:
                    issue(path + ".id", "Duplicate ID within " + collection + ": " + identifier)
                else:
                    indices[collection][identifier] = item

    def reference(obj, key, path, collection, required=False):
        value = string(obj, key, path, required)
        if value is not None and value not in indices[collection]:
            issue(path + "." + key, "Unknown " + collection + " ID: " + value)
        return value

    def references(obj, key, path, collection, required=False):
        values = strings(obj, key, path, required)
        for index, value in enumerate(values):
            if value not in indices[collection]:
                issue(f"{path}.{key}[{index}]", "Unknown " + collection + " ID: " + value)
        if len(values) != len(set(values)):
            issue(path + "." + key, "Repeated IDs do not create additional evidence.", True)
        return values

    for node, path in records["nodes"]:
        for key in ("label", "type"):
            string(node, key, path, True)
        for key in ("group", "summary"):
            string(node, key, path)
        strings(node, "aliases", path)
        if "identifiers" in node and not isinstance(node["identifiers"], dict):
            issue(path + ".identifiers", "Expected an object.")
        if "core" in node and type(node["core"]) is not bool:
            issue(path + ".core", "Expected a boolean.")

    for source, path in records["sources"]:
        string(source, "title", path, True)
        for key in ("locator", "publisher", "note"):
            string(source, key, path)
        for key in ("published_at", "retrieved_at"):
            datefield(source, key, path, timestamp=True)
        if "url" in source:
            url = string(source, "url", path)
            if url is not None:
                try:
                    parsed = urlsplit(url)
                    valid = (parsed.scheme.lower() in {"http", "https"} and bool(parsed.hostname)
                             and parsed.username is None and parsed.password is None
                             and not any(character.isspace() or ord(character) < 32 for character in url))
                    parsed.port
                except ValueError:
                    valid = False
                if not valid:
                    issue(path + ".url", "Use an absolute http/https URL without credentials or whitespace; use locator for local records.")
        reference(source, "origin_id", path, "sources")
        if not source.get("url") and not source.get("locator"):
            issue(path, "Source has no URL or locator; add a way to inspect the underlying record.", True)

    # Iterative ancestry walks handle disconnected graphs without recursion.
    done = set()
    for source_id in indices["sources"]:
        chain, positions = [], {}
        current = source_id
        while current in indices["sources"] and current not in done:
            if current in positions:
                cycle = chain[positions[current]:] + [current]
                issue("$.sources", "Source ancestry cycle: " + " -> ".join(cycle))
                break
            positions[current] = len(chain)
            chain.append(current)
            parent = indices["sources"][current].get("origin_id")
            current = parent if isinstance(parent, str) else None
        done.update(chain)

    unknown_intervals = 0
    for edge, path in records["edges"]:
        reference(edge, "source", path, "nodes", True)
        reference(edge, "target", path, "nodes", True)
        for key in ("relation", "layer", "summary"):
            string(edge, key, path, True)
        edge_status = status(edge, "status", path, EDGE_STATUSES)
        source_ids = references(edge, "source_ids", path, "sources", True)
        if edge_status in {"documented", "reported"} and not source_ids:
            issue(path + ".source_ids", "Documented/reported relationships require at least one source.")
        for key in ("evidence", "mechanism", "date_note"):
            string(edge, key, path)
        basis = edge.get("summary") or edge.get("evidence") or source_ids
        if edge_status == "inferred" and not basis:
            issue(path, "An inference requires an explicit basis in summary, evidence, or source_ids.")
        elif edge_status == "inferred" and not source_ids and not edge.get("evidence"):
            issue(path, "Inference rests on its summary; inspect whether that text states an actual basis.", True)
        if edge_status in {"disputed", "retracted"} and not source_ids:
            issue(path, "Preserve the disputed or retracted assertion's source when available.", True)
        references(edge, "hypothesis_ids", path, "hypotheses")
        start = datefield(edge, "start", path, nullable=True)
        end = datefield(edge, "end", path, nullable=True)
        datefield(edge, "observed_at", path)
        if start and end and start > end:
            issue(path, "Effective start date must not be after end date.")
        if not edge.get("start") and not edge.get("end"):
            unknown_intervals += 1
        if "amount" in edge:
            amount = edge["amount"]
            if not isinstance(amount, dict):
                issue(path + ".amount", "Expected an object with value, currency, kind, and period.")
            else:
                value = amount.get("value")
                if type(value) not in (int, float) or (type(value) is float and not math.isfinite(value)):
                    issue(path + ".amount.value", "Expected a finite numeric amount; booleans are not numbers.")
                for key in ("currency", "kind", "period"):
                    string(amount, key, path + ".amount", True)
    if unknown_intervals:
        issue("$.edges", f"{unknown_intervals} relationship(s) have unknown effective intervals; keep them visibly unknown in date slices.", True)

    for hypothesis, path in records["hypotheses"]:
        for key in ("title", "statement"):
            string(hypothesis, key, path, True)
        hypothesis_status = status(hypothesis, "status", path, HYPOTHESIS_STATUSES)
        for key in ("assumptions", "predictions"):
            strings(hypothesis, key, path)
        supports = references(hypothesis, "supports", path, "edges")
        challenges = references(hypothesis, "challenges", path, "edges")
        if set(supports) & set(challenges):
            issue(path, "Some edges appear as both support and challenge; preserve the reasoning for this assignment.", True)
        if hypothesis_status == "supported" and not supports:
            issue(path, "Supported hypothesis has no supporting edge references.", True)
        for key in ("next_test", "alternative", "prior"):
            string(hypothesis, key, path)
        if "probability" in hypothesis:
            probability = hypothesis["probability"]
            if not isinstance(probability, dict):
                issue(path + ".probability", "Expected an object with value or range, basis, and assessed_at.")
            else:
                ppath = path + ".probability"
                string(probability, "basis", ppath, True)
                datefield(probability, "assessed_at", ppath, True, timestamp=True)
                if "value" not in probability and "range" not in probability:
                    issue(ppath, "An explicit estimate requires value or range.")
                value = probability.get("value")
                if "value" in probability and (type(value) not in (int, float) or not 0 <= value <= 1):
                    issue(ppath + ".value", "Expected a probability between 0 and 1.")
                bounds = probability.get("range")
                if "range" in probability:
                    valid_range = (isinstance(bounds, list) and len(bounds) == 2
                                   and all(type(item) in (int, float) and 0 <= item <= 1 for item in bounds)
                                   and bounds[0] <= bounds[1])
                    if not valid_range:
                        issue(ppath + ".range", "Expected [low, high] with 0 <= low <= high <= 1.")
                    elif type(value) in (int, float) and not bounds[0] <= value <= bounds[1]:
                        issue(ppath, "Probability value must lie within its supplied range.")
                issue(ppath, "Numeric estimate is supplied by the case author; the validator does not calibrate or infer it.", True)

    for lead, path in records["leads"]:
        for key in ("question", "rationale"):
            string(lead, key, path, True)
        status(lead, "status", path, LEAD_STATUSES)
        if "priority" in lead:
            status(lead, "priority", path, {"high", "medium", "low"})
        for key, collection in (("edge_ids", "edges"), ("node_ids", "nodes"), ("source_ids", "sources")):
            references(lead, key, path, collection)
        for key in ("expected_observation", "alternative_result", "answer"):
            string(lead, key, path)
        if lead.get("status") == "answered" and not lead.get("answer"):
            issue(path, "Answered lead has no recorded answer.", True)

    for game, path in records["games"]:
        for key in ("title", "summary"):
            string(game, key, path, True)
        if "kind" in game:
            status(game, "kind", path, GAME_KINDS)
        strings(game, "sequence", path)
        players = game.get("players")
        if not isinstance(players, list):
            issue(path + ".players", "Expected a required array of player objects.")
        else:
            for index, player in enumerate(players):
                ppath = f"{path}.players[{index}]"
                if not isinstance(player, dict):
                    issue(ppath, "Expected a player object.")
                    continue
                reference(player, "node_id", ppath, "nodes", True)
                string(player, "objective", ppath, True)
                string(player, "basis", ppath)
                for key in ("constraints", "outside_options", "moves"):
                    strings(player, key, ppath)
        if "scenarios" in game:
            scenarios = game["scenarios"]
            if not isinstance(scenarios, list):
                issue(path + ".scenarios", "Expected an array of scenario objects.")
            else:
                for index, scenario in enumerate(scenarios):
                    spath = f"{path}.scenarios[{index}]"
                    if not isinstance(scenario, dict):
                        issue(spath, "Expected a scenario object.")
                        continue
                    string(scenario, "label", spath, True)
                    for key in ("assumptions", "implications", "signals"):
                        strings(scenario, key, spath, True)

    extra_errors, extra_warnings = ops.validate_additions(data)
    errors.extend(extra_errors)
    warnings.extend(extra_warnings)
    return {"valid": not errors, "errors": errors, "warnings": warnings,
            "counts": {name: len(records[name]) for name in COLLECTIONS}}


def checked_case(path):
    data = read_case(path)
    validation = validate_case(data)
    if not validation["valid"]:
        raise CaseError("Case validation failed.", validation)
    return data, validation


def source_impact(data, source_id):
    """Follow complete declared dependencies while retaining the schema-1 result keys."""
    if source_id not in {source["id"] for source in data["sources"]}:
        raise CaseError("Unknown source ID: " + source_id)
    result = ops.impact_records(data, ["sources:" + source_id])
    return {"source_id": source_id,
            "descendant_source_ids": [identifier for identifier in result["affected_source_ids"] if identifier != source_id],
            **result}


def _new_destination(path):
    path = Path(path).expanduser().absolute()
    resolved = path.resolve()
    if resolved == SKILL_ROOT or SKILL_ROOT in resolved.parents:
        raise CaseError("Write case artifacts to a user-owned case directory outside the installed skill.")
    # Resolve ancestors while retaining the final name so dangling symlinks
    # still count as existing destinations and cannot be silently followed.
    return path.parent.resolve() / path.name


def _exists(path):
    return os.path.lexists(path)


def _json_text(data):
    return json.dumps(data, ensure_ascii=False, allow_nan=False, indent=2) + "\n"


def _publish_new(staged, target):
    """Atomic publication with no replacement of an existing destination."""
    if os.name == "nt":
        # Windows rename fails if target exists, including on removable media.
        os.rename(staged, target)
    else:
        # POSIX rename can overwrite; atomic link creation cannot.
        os.link(staged, target)


def _file_identity(path):
    info = Path(path).stat(follow_symlinks=False)
    return info.st_dev, info.st_ino


def atomic_write_text(path, content):
    """Flush a temporary sibling, then publish without replacing any name."""
    path = Path(path)
    if _exists(path):
        raise CaseError("Refusing to overwrite existing destination: " + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="",
                                         prefix="." + path.name + ".", suffix=".tmp",
                                         dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        _publish_new(temporary, path)
    except FileExistsError:
        raise CaseError("Refusing to overwrite existing destination: " + str(path)) from None
    except OSError as exc:
        raise CaseError("Cannot atomically create destination: " + (exc.strerror or type(exc).__name__)
                        + ". Choose a writable destination supporting atomic no-replace publication.") from None
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


CSV_FIELDS = {
    "nodes": ["id", "label", "type", "group", "summary", "aliases", "identifiers", "core"],
    "edges": ["id", "source", "target", "relation", "layer", "status", "source_ids", "summary", "evidence",
              "mechanism", "start", "end", "date_note", "observed_at", "hypothesis_ids", "amount"],
    "sources": ["id", "title", "url", "locator", "publisher", "published_at", "retrieved_at", "origin_id", "note"],
}


def _csv_cell(value):
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        stripped = value.lstrip()
        if value.startswith(("\t", "\r", "\n")) or (stripped and stripped[0] in "=+-@"):
            return "'" + value
    return value


def _csv_text(collection, rows):
    extra = sorted({key for row in rows for key in row} - set(CSV_FIELDS[collection]))
    columns = CSV_FIELDS[collection] + extra
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow([_csv_cell(column) for column in columns])
    for row in rows:
        writer.writerow([_csv_cell(row.get(column)) for column in columns])
    return output.getvalue()


def export_case(data, output):
    """Export a staged set, rolling back only files linked by this operation."""
    output = _new_destination(output)
    names = ("nodes.csv", "edges.csv", "sources.csv", "case.json")
    if output.exists() and not output.is_dir():
        raise CaseError("Export destination is not a directory.")
    for name in names:
        if _exists(output / name):
            raise CaseError("Refusing to overwrite existing export: " + str(output / name))
    content = {name + ".csv": _csv_text(name, data[name]) for name in ("nodes", "edges", "sources")}
    content["case.json"] = _json_text(data)
    created_directory = not output.exists()
    output.mkdir(parents=True, exist_ok=True)
    staged, published = [], []
    try:
        for name in names:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="",
                                             prefix="." + name + ".", suffix=".tmp", dir=output, delete=False) as stream:
                staged_path = Path(stream.name)
                staged.append((staged_path, output / name))
                stream.write(content[name])
                stream.flush()
                os.fsync(stream.fileno())
        for staged_path, target in staged:
            identity = _file_identity(staged_path)
            _publish_new(staged_path, target)
            published.append((target, identity))
    except OSError as exc:
        for target, identity in published:
            if target.exists() and _file_identity(target) == identity:
                target.unlink()
        raise CaseError("Export was not completed: " + (exc.strerror or type(exc).__name__)
                        + ". No preexisting export was overwritten.") from None
    finally:
        for staged_path, _ in staged:
            if staged_path.exists():
                staged_path.unlink()
        if created_directory and output.exists() and not any(output.iterdir()):
            output.rmdir()
    return [str(output / name) for name in names]


def make_parser():
    parser = Parser(description="RED THREADS: validate, explore, and export a portable investigative case.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    init = subparsers.add_parser("init", help="Create a minimal case in a new or empty case directory.")
    init.add_argument("case_dir", type=Path)
    init.add_argument("--title", required=True)
    init.add_argument("--question", required=True)
    validate = subparsers.add_parser("validate", help="Check structure, references, dates, and evidence boundaries.")
    validate.add_argument("case_json", type=Path)
    render = subparsers.add_parser("render", help="Create a new offline atlas; refuse an existing output file.")
    render.add_argument("case_json", type=Path)
    render.add_argument("--output", type=Path, required=True)
    export = subparsers.add_parser("export", help="Create CSV tables and a complete JSON copy without overwriting.")
    export.add_argument("case_json", type=Path)
    export.add_argument("--output", type=Path, required=True)
    impact = subparsers.add_parser("impact", help="Inspect a source's downstream dependencies without changing the case.")
    impact.add_argument("case_json", type=Path)
    impact.add_argument("--source", required=True)
    for command, help_text in (
        ("scan", "Find structural collection candidates, documented-only sensitivity and coverage gaps."),
        ("frontier", "Rank actionable leads by supplied decision value, priority and effort."),
        ("resume", "Read the campaign checkpoint, unresolved work and view definition."),
    ):
        operation = subparsers.add_parser(command, help=help_text)
        operation.add_argument("case_json", type=Path)
    apply = subparsers.add_parser("apply", help="Apply an optimistic patch into a new validated case file.")
    apply.add_argument("case_json", type=Path)
    apply.add_argument("--changes", type=Path, required=True)
    apply.add_argument("--output", type=Path, required=True)
    return parser


def apply_case(args):
    target = _new_destination(args.output)
    if _exists(target):
        raise CaseError("Refusing to overwrite existing destination: " + str(target))
    original_bytes = args.case_json.read_bytes()
    data = json.loads(original_bytes.decode("utf-8-sig"), object_pairs_hook=_unique_object,
                      parse_constant=_reject_constant)
    original_validation = validate_case(data)
    if not original_validation["valid"]:
        raise CaseError("Original case validation failed.", original_validation)
    digest = hashlib.sha256(original_bytes).hexdigest()
    patch = read_case(args.changes)
    try:
        updated, change = ops.apply_changes(data, patch, digest)
    except ValueError as exc:
        raise CaseError(str(exc)) from None
    validation = validate_case(updated)
    if not validation["valid"]:
        raise CaseError("Patched case validation failed; no output created.", validation)
    frontier = ops.impact_records(updated, change["changed_tokens"], previous=data)
    content = _json_text(updated)
    if args.case_json.read_bytes() != original_bytes:
        raise CaseError("Original case changed during patch preparation; reread and reconcile before retrying.")
    atomic_write_text(target, content)
    return {"ok": True, "command": "apply", "path": str(target), "base_sha256": digest,
            "result_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            **change, "review_frontier": frontier, "warnings": validation["warnings"]}, 0


def run(args):
    if args.command == "init":
        if not args.title.strip() or not args.question.strip():
            raise CaseError("Title and question must be nonempty.")
        target = _new_destination(args.case_dir / "case.json")
        data = {
            "schema_version": 1,
            "case": {"id": "case-" + uuid.uuid4().hex[:12], "title": args.title, "question": args.question,
                     "updated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")},
            **{name: [] for name in COLLECTIONS},
        }
        atomic_write_text(target, _json_text(data))
        return {"ok": True, "command": "init", "path": str(target)}, 0

    if args.command == "validate":
        result = validate_case(read_case(args.case_json))
        return {"command": "validate", "path": str(args.case_json.resolve()), **result}, 0 if result["valid"] else 1

    if args.command == "apply":
        return apply_case(args)
    data, validation = checked_case(args.case_json)
    if args.command in {"scan", "frontier", "resume"}:
        operation = {"scan": ops.scan_case, "frontier": ops.frontier_case, "resume": ops.resume_case}[args.command]
        return {"ok": True, "command": args.command, **operation(data), "warnings": validation["warnings"]}, 0
    if args.command == "impact":
        return {"ok": True, "command": "impact", **source_impact(data, args.source)}, 0
    if args.command == "export":
        files = export_case(data, args.output)
        return {"ok": True, "command": "export", "files": files, "warnings": validation["warnings"],
                "csv_text_protection": "Formula-leading text cells have an apostrophe prefix; case.json preserves the original values."}, 0
    if args.command == "render":
        target = _new_destination(args.output)
        if _exists(target):
            raise CaseError("Refusing to overwrite existing destination: " + str(target))
        try:
            from render_atlas import render
        except ImportError:
            raise CaseError("Atlas renderer is unavailable; use the complete installed skill package.") from None
        try:
            html = render(data)
        except Exception as exc:
            raise CaseError("Atlas rendering failed (" + type(exc).__name__ + "); the case was not changed.") from None
        if not isinstance(html, str):
            raise CaseError("Atlas renderer returned invalid output; expected HTML text.")
        atomic_write_text(target, html)
        return {"ok": True, "command": "render", "path": str(target), "warnings": validation["warnings"]}, 0
    raise CaseError("Unknown command.")


def main(argv=None):
    try:
        args = make_parser().parse_args(argv)
        result, exit_code = run(args)
    except CaseError as exc:
        result, exit_code = {"ok": False, "error": str(exc)}, 1
        if exc.details is not None:
            result["validation"] = exc.details
    except (OSError, ValueError, TypeError, OverflowError, RecursionError) as exc:
        result, exit_code = {"ok": False, "error": "Operation failed (" + type(exc).__name__
                             + "); check input structure and destination access. No automatic overwrite was requested."}, 1
    except KeyboardInterrupt:
        result, exit_code = {"ok": False, "error": "Interrupted."}, 130
    print(json.dumps(result, ensure_ascii=True, allow_nan=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
