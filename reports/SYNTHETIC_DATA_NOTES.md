# Synthetic data notes: the 1,000-ticket dataset

## What this is

`starter_kit/data/tickets_1000.json` contains the 40 original case-study tickets, unchanged, followed by 960 generated tickets. Every generated ticket is a **fictional** incident for a **fictional** B2B analytics SaaS product.

- Organisations, people, accounts and identifiers are invented.
- Domains are limited to example.com, example.org and example.net.
- IP addresses come only from the documentation ranges.
- Where a third-party product name appears, it is only the customer's own tool. No ticket claims a real vendor changed or broke anything.
- No ticket contains real personal information, credentials or production identifiers.

## Intended use

- **Prototype development:** a larger, more varied history to build and demonstrate the similarity assistant against.
- **Retrieval evaluation:** realistic related cases and hard distinctions to measure ranking and relevance decisions against.

## What it does not establish

- **Production retrieval accuracy.** Measurements on fictional tickets written by language models do not predict results on real customer tickets. Real tickets differ in length, language, noise, vocabulary and distribution.
- **That every resolution is correct.** Content quality was reviewed on a sample of 116 generated tickets (see [DATASET_VALIDATION.md](DATASET_VALIDATION.md)). The other tickets were checked automatically for structure, not for technical correctness.
- **That more data improves search.** Adding tickets changes TF-IDF weights, candidate sets and the scores the relevance thresholds were tuned on. With this dataset, one incoming example gains a "close match" with a different cause. Measure before and after; do not assume.

## Design choices

These are choices made for this prototype, not facts about any customer.

**Twelve categories.** The original eight are kept with their meaning. Four were added:

| Category | Covers | Stays elsewhere |
|---|---|---|
| alerts | Threshold rules, triggering, suppression, missed and duplicate alerts | Password-reset emails (auth); scheduled report delivery (export) |
| data_quality | Wrong values, units, mappings or aggregations after successful ingestion | Failed or missing ingestion (sync) |
| connectivity | DNS, proxies, firewalls, TLS and network reachability | Credential problems (auth or the integration category) |
| workspace_admin | Workspace identity, branding, locale and organisational settings | Access (perm); charges (billing) |

**Distribution.** 83 tickets for each original category (5 original + 78 new) and 84 for each new category, totalling 1,000. The near-even split is a choice for balanced evaluation. Real ticket volumes are not even.

**Structure for evaluation.**
- **Issue families:** 13–15 per category (165 in total), each a distinct root cause or feature area.
- **Related groups:** 112, covering 294 tickets that share a root cause but are worded differently.
- **Challenge-marked tickets:** 329, each tagged with one challenge type:

| Challenge type | Tickets |
|---|---|
| Same symptom, different cause | 107 |
| Similar wording, different problem | 79 |
| Negation or opposite behaviour | 58 |
| Workaround versus permanent fix | 52 |
| Related symptom in a different product | 33 |

**Evaluation integrity.**
- The incoming example tickets were not copied into the history.
- No resolved Snowflake or data-warehouse incident was generated, so the deliberately unfamiliar Snowflake example keeps no historical answer. Excluding the word alone does not guarantee that, so it was checked with the retrieval system itself.
- Other examples may now have more relevant history, as a real support desk would after a year. For example, NT-1 now has related password-reset tickets.

**Records.**
- Each ticket keeps exactly the eight original fields.
- Generation metadata (family, related group, challenge type, boundary rationale) is stored separately in [generation_manifest.json](../starter_kit/data/generation_manifest.json), keyed by ticket ID.

## How it was made

- **Text.** Written by four parallel language-model agents (Claude), three categories each, from one shared specification covering boundaries, content rules, diversity targets and exclusions. They worked in batches with self-checks. **The text is not reproducible.**
- **Ordering and IDs.** The 960 generated records were shuffled with Python `random.Random(20261117)` and given T-2001 to T-2960 in that order, after the 40 originals. This step is reproducible from the batch files in `tools/dataset_generation/batches/`, using `tools/dataset_generation/assemble.py`.
- **Checks.** Validation by `tools/validate_dataset.py`. A sampled content review was followed by an independent second opinion, and five confirmed corrections were applied.

## Files

| File | Purpose |
|---|---|
| `starter_kit/data/tickets_1000.json` | The dataset: 40 originals followed by 960 generated tickets |
| `starter_kit/data/generation_manifest.json` | Counts, generation method, seed, category boundaries, issue families, related groups and per-ticket provenance |
| `tools/validate_dataset.py` | Validator |
| `reports/validation_results.json` | Latest validator output |
| `reports/DATASET_VALIDATION.md` | Checks, results and review scope |
| `tools/dataset_generation/` | Batches, assembler, review sample and applied corrections |

The original `starter_kit/data/tickets.json` and `new_tickets_example.json` are unchanged. The application still loads the 40-ticket file until `TICKETS_PATH` is changed.
