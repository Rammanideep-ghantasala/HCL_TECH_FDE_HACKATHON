# Dataset validation: `starter_kit/data/tickets_1000.json`

Validated on 2026-11-17 with `tools/validate_dataset.py` (Python standard library only). The machine-readable result is in [validation_results.json](validation_results.json).

```powershell
backend\.venv\Scripts\python.exe -I -B tools\validate_dataset.py
```

## Result

**PASS. All 16 structural checks pass. No content flags were raised.** The run was repeated after the content-review corrections below, with the same result.

| Item | Value |
|---|---|
| Total tickets | 1,000 |
| Original tickets (T-1001 to T-1705), first and unchanged | 40 |
| Generated tickets (T-2001 to T-2960) | 960 |
| Categories | 12 |

## Source verification (before generation)

| Check | Finding |
|---|---|
| Dataset the application loads | `starter_kit/data/tickets.json`, from `Settings.tickets_path` in `backend/app/config.py` (`TICKETS_PATH` in the container) |
| Structure | An object with one `tickets` array |
| Count | 40 tickets, 8 categories × 5 (auth, sync, render, billing, export, perm, perf, api) |
| Fields | ticket_id, category, subject, description, resolution_notes, tags, created_at, status |
| IDs | 40 unique |
| Status | All "resolved" |
| Prior expansion | None. The file was the original 40-ticket set, so 960 tickets were added |

The source files were hashed (SHA-256) before generation and checked after the final assembly. `tickets.json` and `new_tickets_example.json` are byte-for-byte unchanged.

## Checks executed (automated)

| # | Check | Result |
|---|---|---|
| 1 | Valid UTF-8 JSON | Pass |
| 2 | Root object holds only a `tickets` array | Pass |
| 3 | Exactly 1,000 records | Pass |
| 4 | Every record has exactly the eight application fields with the right types | Pass |
| 5 | Ticket IDs unique | Pass |
| 6 | T-2001 to T-2960 each present exactly once; no other new IDs; no collision with original IDs | Pass |
| 7 | Only the 12 permitted categories | Pass |
| 8 | Category counts: 8 × 83 and 4 × 84 | Pass |
| 9 | The 40 original records are first, in order, and equal to the source as JSON values | Pass |
| 10 | Required strings not blank | Pass |
| 11 | Tags: non-empty arrays of strings, no duplicates; generated tickets have 2–5 lowercase-hyphenated tags, not only the category name | Pass |
| 12 | Dates valid; generated dates between 2025-01-01 and 2026-11-17 | Pass |
| 13 | Every status is "resolved" | Pass |
| 14 | No exact duplicate subject–description pairs (lowercased, whitespace collapsed) | Pass |
| 15 | No incoming example copied by subject or description | Pass |
| 16 | No generated Snowflake incident | Pass |

Final category counts: auth 83, sync 83, render 83, billing 83, export 83, perm 83, perf 83, api 83, alerts 84, data_quality 84, connectivity 84, workspace_admin 84.

### Flags for review (automated; flags never fail the run)

| Flag | Rule | Found |
|---|---|---|
| Near-duplicate descriptions | Word-set Jaccard ≥ 0.6 between generated descriptions | 0 |
| Resembles an incoming example | Jaccard ≥ 0.5 with an incoming ticket | 0 |
| Data-warehouse terms | bigquery, redshift, databricks, synapse, warehouse | 0 |
| References to other tickets | `T-dddd` in generated text | 0 |
| Non-reserved domains or e-mail domains | Anything other than example.com/.org/.net | 0 |
| Non-documentation IP addresses | Outside 192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24 | 0 |

## Duplicate findings and disposition

- **Exact duplicates:** none.
- **Near duplicates (separate measurement, lower threshold):** among all 460,320 pairs of generated descriptions, one pair reaches Jaccard 0.40 (T-2378 and T-2438, workspace_admin) and none reaches 0.50. That pair was reviewed as part of the content review below. Both reviewers judged them genuinely related incidents, not a template copy, so they were kept unchanged.
- **Related groups:** the low overlap is deliberate. 112 related groups covering 294 tickets share a root cause but are described in different words (listed in the manifest).

## Content-quality review

Content quality was reviewed by sampling, not exhaustively.

| Item | Detail |
|---|---|
| Records reviewed | 116 generated tickets: 8–13 per category plus the closest near-duplicate pair |
| Sample | Reproducible (seed 4242), recorded in `tools/dataset_generation/review_sample.json` |
| Sample composition per category | 2 challenge-marked tickets, 2 boundary cases, one complete related group, 2 random tickets, and every ticket a generator flagged as borderline |
| First review | One reviewer per category checked category boundaries, subject–description consistency, whether the resolution addresses the cause, plausible verification, honest workarounds, safe fixes (no disabled security controls, no needlessly broad access), no vendor claims, fictional identifiers only, and repeated templates |
| Second opinion | An independent reviewer judged every reported problem and every proposed correction |

Results:

| Outcome | Count |
|---|---|
| OK | 103 |
| Minor optional tweaks (left unchanged; none broke a rule) | 12 |
| Problems confirmed by both reviewers, corrected | 5 |
| Problems reported but rejected by the second reviewer (wording preference) | 2 |
| Wrong category | 0 of 116 |

Corrections applied (the before and after text of each is recorded in `tools/dataset_generation/content_fixes_applied.json`):

| Ticket | Problem | Field changed |
|---|---|---|
| T-2129 | The stated cause (a cache ignoring the week-start preference) produces identical totals, but the text said "different totals" | subject, description |
| T-2833 | An "ASCII-safe" cause cannot produce the non-ASCII U+FFFD character the description reported | description, resolution_notes |
| T-2086 | The description said alert emails were quarantined; the resolution said rejected | resolution_notes |
| T-2663 | The resolution had no verification outcome | resolution_notes |
| T-2960 | Trading name versus registered name mismatch | description |

Corrections were made in the generation batches, then the dataset was reassembled and re-validated. IDs did not change, because the seeded shuffle depends only on the order of records, not their content.

## Original records

Check 9 confirms the 40 original records are the first 40 entries, in their original order, and equal to the source. The source files' SHA-256 hashes match before and after generation. No original record caused any validation issue.

## Unresolved concerns

1. **Recurring phrasing.**
   - Reviewers noticed that verification sentences often start with "Confirmed …", in all 9 sampled export tickets and all 8 sampled perm tickets.
   - "As a workaround …; the permanent fix …" recurs across categories.
   - These are stylistic patterns, not copies. They were not rewritten, because rewriting only to defeat similarity measures was out of scope. They may give lexical shortcuts to keyword search.
2. **Uneven challenge types.** Of 329 challenge-marked tickets, same symptom with different cause accounts for 107. Related symptom with a different product accounts for only 33.
3. **Boundary calls are judgements.** 194 generated tickets carry a classification rationale (late reports from a busy queue filed as perf; integration keys revoked at offboarding filed as api; decimal-comma parsing filed as sync). The rationales are in the manifest. Reasonable reviewers could file some of them differently.
4. **Sampled review only.** Correct resolutions are not established for every ticket. 844 generated tickets were checked only automatically.
5. **Dates.** Generated dates span all months from 2025-01 to 2026-11, but 2026-Q4 is thinner because the range ends on 17 November.
6. **Effect on the incoming examples.** Measured with the application's current retrieval and thresholds against the 1,000-ticket set, without changing the application:
   - **NT-4 (Snowflake):** still no strong match. Its nearest tickets are the original HubSpot and sync-job tickets plus one generated connector ticket, all below the threshold.
   - **NT-1 (reset email never arrives):** still no strong match, but new related auth tickets now rank nearby, one of them about reset emails that never arrive.
   - **NT-2:** unchanged; T-1201 is still the only close match.
   - **NT-3 (charged twice):** now gets a second "close match", T-2577, a duplicate-looking charge with a different cause (two subscriptions). The thresholds were tuned on 40 tickets and now label a same-symptom, different-cause ticket as close. They must be re-evaluated before this dataset is used.

## Not done (next integration steps)

The application's active dataset path was not changed and no index was rebuilt. To use this dataset:

1. **Point the application at it.**
   - JSON mode: set `TICKETS_PATH` to `starter_kit/data/tickets_1000.json`. The Dockerfile copies only `tickets.json`, so add the new file to the image.
   - PostgreSQL mode: `python -m app.manage import-json ../starter_kit/data/tickets_1000.json --dry-run`, then the same command without `--dry-run`.
2. **Rebuild indexes.**
   - TF-IDF refits automatically at start-up.
   - Embeddings: `python -m app.prepare build-index` after changing `TICKETS_PATH`. The 40 existing vectors are reused and 960 are new.
3. **New categories.** Categories come from the data: `GET /api/meta` lists them and the filter shows them. The underscore names (`data_quality`, `workspace_admin`) are shown as raw values; add display labels if wanted.
4. **Re-evaluate retrieval.** Re-run the evaluation and re-tune the thresholds and match labels on the larger corpus. The existing evaluation labels were assigned against 40 tickets and some queries may now have additional useful matches, so the labels need re-review first. The NT-3 result above shows the current thresholds are not reliable at this size.
