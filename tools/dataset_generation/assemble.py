"""Assemble the 1,000-ticket dataset from the per-category generation batches.

    python tools/dataset_generation/assemble.py

Reads tools/dataset_generation/batches/<category>.json, keeps the 40 original
records first and byte-for-byte equal as JSON values, interleaves the 960
generated records with a seeded shuffle, assigns T-2001..T-2960 in that
order, and writes:

    starter_kit/data/tickets_1000.json        tickets only (the eight application fields)
    starter_kit/data/generation_manifest.json  everything else (families, groups, rationale)

The shuffle is reproducible from the seed. The ticket text itself was written
by language-model agents and is not reproducible.
"""

from __future__ import annotations

import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA = ROOT / "starter_kit" / "data"
BATCHES = Path(__file__).resolve().parent / "batches"
SEED = 20261117
FIELDS = ["ticket_id", "category", "subject", "description", "resolution_notes", "tags", "created_at", "status"]
PLAN = {
    "auth": 78, "sync": 78, "render": 78, "billing": 78, "export": 78, "perm": 78, "perf": 78, "api": 78,
    "alerts": 84, "data_quality": 84, "connectivity": 84, "workspace_admin": 84,
}
BOUNDARIES = {
    "alerts": "Metric threshold rules, alert triggering, suppression, missed and duplicate alerts. Password-reset emails stay auth; scheduled report delivery stays export.",
    "data_quality": "Incorrect values, calculations, units, mappings or aggregations after successful ingestion. Failed or missing ingestion stays sync.",
    "connectivity": "DNS, proxies, firewalls, TLS configuration and network reachability. Credential problems stay auth or the relevant integration category.",
    "workspace_admin": "Workspace identity, branding, locale, preferences and organizational settings. Access permissions stay perm; charges and subscriptions stay billing.",
}


def main() -> None:
    original = json.loads((DATA / "tickets.json").read_text(encoding="utf-8"))["tickets"]
    batches = {}
    for category, expected in PLAN.items():
        path = BATCHES / f"{category}.json"
        batch = json.loads(path.read_text(encoding="utf-8"))
        if batch.get("category") != category or len(batch["tickets"]) != expected:
            sys.exit(f"{path.name}: expected {expected} {category} tickets, found {len(batch.get('tickets', []))}")
        batches[category] = batch

    generated = [ticket for category in PLAN for ticket in batches[category]["tickets"]]
    random.Random(SEED).shuffle(generated)

    records, provenance = [], {}
    for number, ticket in enumerate(generated, start=2001):
        ticket_id = f"T-{number}"
        records.append({
            "ticket_id": ticket_id,
            "category": ticket["category"],
            "subject": ticket["subject"],
            "description": ticket["description"],
            "resolution_notes": ticket["resolution_notes"],
            "tags": ticket["tags"],
            "created_at": ticket["created_at"],
            "status": "resolved",
        })
        provenance[ticket_id] = {
            "batch_key": ticket["key"],
            "family_id": ticket["family_id"],
            "related_group": ticket.get("related_group"),
            "challenge": ticket.get("challenge"),
            "classification_rationale": ticket.get("classification_rationale"),
        }

    lines = [json.dumps(ticket, ensure_ascii=False) for ticket in original + records]
    (DATA / "tickets_1000.json").write_text(
        '{\n  "tickets": [\n    ' + ",\n    ".join(lines) + "\n  ]\n}\n", encoding="utf-8"
    )

    groups: dict[str, list[str]] = {}
    for ticket_id, info in provenance.items():
        if info["related_group"]:
            groups.setdefault(info["related_group"], []).append(ticket_id)
    final_counts = Counter(t["category"] for t in original + records)
    manifest = {
        "dataset": "starter_kit/data/tickets_1000.json",
        "synthetic": True,
        "description": "Fictional support tickets for a fictional B2B analytics SaaS product, for prototype development and evaluation only.",
        "counts": {
            "total": len(original) + len(records),
            "original": len(original),
            "generated": len(records),
            "by_category": dict(sorted(final_counts.items())),
            "generated_by_category": dict(Counter(t["category"] for t in records)),
        },
        "id_ranges": {"original": [t["ticket_id"] for t in original], "generated": "T-2001..T-2960"},
        "generation_method": {
            "text": "Written by four parallel language-model agents (Claude), three categories each, from one shared specification "
                    "(category boundaries, content rules, diversity and relationship targets, exclusions), in batches with "
                    "self-checks. The text is not reproducible.",
            "ordering": f"Python random.Random({SEED}).shuffle over the 960 generated records in category order "
                        "(auth, sync, render, billing, export, perm, perf, api, alerts, data_quality, connectivity, workspace_admin), "
                        "then ids assigned sequentially from T-2001. Reproducible given the same batch files.",
            "originals": "The 40 records of starter_kit/data/tickets.json are first, unchanged and in their original order.",
            "exclusions": "No Snowflake or data-warehouse destination incidents, so the incoming Snowflake example keeps no historical answer.",
        },
        "category_boundaries": BOUNDARIES,
        "issue_families": {category: batches[category]["issue_families"] for category in PLAN},
        "related_groups": {
            group["group_id"]: {**group, "ticket_ids": sorted(groups.get(group["group_id"], []))}
            for category in PLAN for group in batches[category]["related_groups"]
        },
        "challenge_counts": dict(Counter(info["challenge"] for info in provenance.values() if info["challenge"])),
        "tickets": provenance,
    }
    (DATA / "generation_manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(manifest["counts"], indent=1))


if __name__ == "__main__":
    main()
