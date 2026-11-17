# Support Ticket Similarity Assistant

For a new support ticket, this application retrieves similar past resolved tickets, shows their original resolutions word for word, and gives the support agent the evidence to judge whether a past resolution applies. The agent investigates and resolves the ticket. The application never performs a refund, reset, account change or ticket closure, and never writes a resolution of its own.

Built for the Solari Analytics case study in [case-study-brief.md](case-study-brief.md), on the 40 synthetic tickets in [starter_kit/data/](starter_kit/data/), which are used unmodified.

| Document | Contents |
|---|---|
| [SOLUTION_DESIGN.md](SOLUTION_DESIGN.md) | Problem, assumptions, approach, trade-offs, results |
| [TECHNICAL_APPENDIX.md](TECHNICAL_APPENDIX.md) | Architecture, algorithms, API, failure handling, evaluation in detail |
| [DEPLOY_AWS.md](DEPLOY_AWS.md) | AWS deployment (Amazon ECR and ECS Express Mode). Prepared, not performed |
| [POSTGRES.md](POSTGRES.md) | PostgreSQL storage: setup, migrations, import, refresh, limitations |
| [DEMO_GUIDE.md](DEMO_GUIDE.md) | Three-minute walkthrough and likely questions |

## Run it

### Option 1: Docker (one command, closest to production)

Needs Docker and an internet connection for the build (it downloads dependencies and the embedding model).

```powershell
docker build -t ticket-similarity-assistant .
docker run --rm -p 8080:8080 ticket-similarity-assistant
```

Open <http://localhost:8080>. Retrieval needs no credentials and downloads nothing when it starts. Optional summaries require server-side configuration and outbound HTTPS access (below).

Resolutions saved through the form are written to `/app/state` in JSON mode. To keep them across container restarts, mount a volume: `docker run --rm -p 8080:8080 -v tsa-state:/app/state ticket-similarity-assistant`. For durable shared storage use PostgreSQL ([POSTGRES.md](POSTGRES.md)).

### Option 2: Local development

Needs [uv](https://docs.astral.sh/uv/) (it installs Python 3.12 itself) and Node.js 24.

```powershell
# Backend, from the backend folder
cd backend
uv sync                                    # install locked dependencies
uv run python -m app.prepare fetch-model   # one-time download of the pinned model
uv run python -m app.prepare build-index   # precompute the ticket embeddings
$env:PORT = "8000"; uv run python -m app   # API on http://127.0.0.1:8000
```

```powershell
# Frontend, in a second terminal, from the frontend folder
cd frontend
npm ci
npm run dev                                # http://localhost:5173, proxies /api to port 8000
```

Without the model step the backend still starts, in keyword-only mode, and says so.

Configuration is by environment variable; every value has a default. See [.env.example](.env.example).

### Optional summaries of Top 3 / Top 5 results

Select **Top 3** (default) or **Top 5** beside the search controls. This is a maximum applied after relevance filtering; the app does not fill spare slots with weak matches. Changing the selection after a search reruns that search. Below-threshold related context remains a separate disclosure and is excluded from summaries.

Click **Summarize N tickets** to summarize exactly the N main matches displayed, in order. The summary shows an overview with source links, each reported issue and recorded resolution or workaround, and supported differences or missing information. It cannot establish the cause or fix for the current incident. Original records and match labels remain unchanged. Editing the query, filters or result count clears the summary; late responses are ignored.

Set `OPENAI_API_KEY` privately in the backend environment. `SUMMARY_MODEL` defaults to `gpt-4o-mini` and can be changed to a Responses API model supporting structured outputs. Do not put keys in React, `VITE_` variables, source files or Docker build arguments. To use a local untracked root `.env`, fill in the optional summary settings from `.env.example`, then run from `backend`:

```powershell
uv run --env-file ..\.env python -m app
```

For Docker, pass an untracked runtime env file: `docker run --rm -p 8080:8080 --env-file .env ticket-similarity-assistant`. Account access, quota and network connectivity must be configured by the operator. No credentials means a clear disabled-summary message; search stays usable. No provider call is made during search, page load or dropdown changes.

The summary sends the current query and canonical main-match records to OpenAI only on a click. The server checks a signed 15-minute result reference and the ordered IDs, reloads each source version, and checks for edits again before returning. Changed, deleted, expired or mismatched records require a new search. No database or summary cache is added. For multiple replicas, set the same random `SUMMARY_SIGNING_KEY` secret on every replica; otherwise result references work only on the process that issued them and expire on restart. Signed references contain readable query text and must not be logged or persisted.

Provider timeouts, refusals, incomplete output and invalid source coverage produce errors with retry guidance. The input budget is 30,000 characters; oversized requests fail without silently dropping or truncating a ticket. A summary failure does not affect search readiness. Structured-output validation checks shape, coverage, order and references, not factual truth: agents must compare the output with the originals. The integration follows the [OpenAI Responses structured-output documentation](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses).

## Check it

```powershell
# Backend tests (PostgreSQL integration tests run only when TEST_DATABASE_URL is set; see POSTGRES.md)
cd backend; uv run pytest

# Frontend: types, tests, lint, production build
cd frontend; npm run typecheck; npm test; npm run lint; npm run build

# Retrieval evaluation
cd backend
uv run python -m evaluation.run --set tuning
uv run python -m evaluation.run --set final
uv run python -m evaluation.run --set tuning --sweep   # compare threshold settings
```

Against a running instance:

```powershell
Invoke-RestMethod http://localhost:8080/health
Invoke-RestMethod http://localhost:8080/ready
$body = @{ subject = "Customer charged twice"; description = "Two deductions appear for one monthly subscription." } | ConvertTo-Json
Invoke-RestMethod http://localhost:8080/api/search -Method Post -ContentType "application/json" -Body $body
```

## What it does

- **Hybrid retrieval.** Keyword search (TF-IDF) and meaning-based search (sentence embeddings, `all-MiniLM-L6-v2`) each rank the past tickets; Reciprocal Rank Fusion merges the two rankings.
- **A separate relevance decision.** Each candidate is labelled *close match* or *related context*, or dropped, from the raw evidence. The user selects up to three or five main matches; the list is never padded.
- **On-demand summaries.** Summarize the displayed main matches together, with source links and preserved source versions. Requires an API key; does not generate a new resolution or change rankings.
- **Comparison cards.** The original resolution verbatim, the wording both tickets share highlighted side by side, differences in names and error codes, missing information shown as unknown, and questions to check before reusing the resolution. Every line comes from stored text or a fixed rule.
- **Honest outcomes.** "Not enough detail to search", "no strong match", "keyword-only results because the model is unavailable" and "service error" are four different states.
- **Supporting features.** Load a supplied example, optional product and error-detail fields, an optional category filter that reports what it hides, refinement suggestions, expandable full records, and recent searches and feedback kept in the browser tab only.

## API

| Endpoint | Purpose |
|---|---|
| `POST /api/search` | Search. Body: `subject`, `description`, optional `product`, `error_detail`, `category`, `top_k` (integer 3 or 5, default 3). Returns `top_k` and `summary_token` |
| `POST /api/summaries` | Explicit summary. Body: `summary_token` and ordered `ticket_ids` from the displayed main results. Returns overview, one summary per source, source revisions, model and disclaimer |
| `GET /api/tickets/{ticket_id}` | One stored ticket, with its revision and indexing status |
| `POST /api/tickets` | Explicitly save a resolved ticket (insert once, idempotent repeats, no silent overwrites). The only write path |
| `POST /api/index/refresh` | Retry indexing, or pick up external changes to the ticket store (`?full=true` forces a rebuild) |
| `GET /api/examples` | The supplied example tickets |
| `GET /api/meta` | Limits, categories, versions, save settings, unindexed tickets |
| `GET /health` | Liveness |
| `GET /ready` | Readiness: 503 when no search mode is usable or the ticket store cannot be read |

Search limits: subject 200 characters, description 4,000, product 80, error detail 300, request body 65,536 bytes, 4 concurrent searches. `POST /api/search` also accepts an optional `ticket_id`, used only to look up an existing record.

## Storage modes

| `TICKET_STORE` | Tickets come from | Saved resolutions go to |
|---|---|---|
| `json` (default) | `starter_kit/data/tickets.json`, never written, plus `DATA_DIR/saved_tickets.json` | `DATA_DIR/saved_tickets.json` (atomic writes) |
| `postgresql` | The `assistant_tickets` table only. No JSON fallback | The same table, in a transaction |

Searching never writes in either mode. Each saved ticket is tracked as indexing `pending`, `indexed` or `failed`. A failed indexing attempt keeps the ticket saved, leaves searches on the previous index and is retried with `POST /api/index/refresh` or at the next start-up. See [POSTGRES.md](POSTGRES.md).

## Results so far

Measured on 2026-11-17. Details and caveats are in [TECHNICAL_APPENDIX.md](TECHNICAL_APPENDIX.md), section 9.

| Final evaluation set (24 queries, run once) | Hybrid | Keyword only | Semantic only |
|---|---|---|---|
| Expected ticket shown as a close match (of 12) | 5 | 5 | 6 |
| Expected ticket ranked in the first three (of 12) | 10 | 7 | 12 |
| A ticket wrongly shown as a close match (of 11) | 0 | 3 | 1 |

Local container: ready about 10 seconds after start, about 370 MiB of memory, median 29 ms per search on one CPU. These are small samples on synthetic data, and the evaluation labels are AI-assisted judgements that a person should review.

## Known limitations

- **Reworded tickets are not labelled close matches.** In the evaluation none of the reworded queries reached the "close match" label, because their scores overlap those of unrelated tickets. They usually appear as related context.
- **Same topic is not the same problem.** A ticket that shares a topic with a past ticket can be retrieved although the past fix would not help. The card shows the texts side by side; the agent decides.
- **Negation is invisible to retrieval.** "The code arrives" and "the code never arrives" look alike to both retrievers.
- **Thresholds are provisional.** They were tuned on 28 queries against 40 tickets, with margins as small as 0.03, and must be re-tuned for other data.
- **Word comparisons are exact.** No synonyms, spelling variants or word forms. Product names are detected by capital letters, which also picks up words such as weekday names.
- **Past resolutions may be outdated or one-off product fixes.** The data records no review status and no resolution date.
- **No sign-in, no access control, no tenant isolation.** The dataset has no ownership field. The ticket-detail endpoint is as public as search. Do not load real customer data.
- **No rate limiting per client.** Load is bounded only by the request-size cap and the concurrent-search limit.
- **Feedback and recent searches stay in the browser tab.** Nothing is stored centrally and nothing learns from them.
- **Saving has no sign-in.** Anyone who can reach the server can save a resolved ticket. Use `SAVE_ENABLED=false` on a public demo, or put the service behind authentication.
- **Saved tickets need durable storage.** JSON mode writes to a local folder (lost on a container or Fargate task replacement unless a volume is mounted). PostgreSQL is durable, but with several instances each one sees the others' saves only after a refresh (`INDEX_REFRESH_INTERVAL_SECONDS`).
- **The escalation address `ticketexpert@solar.com` was supplied as given.** The customer is Solari Analytics; confirm the domain before a demo (`ESCALATION_EMAIL`).
- **English only.** The tokenizer handles plain Latin text.
- **AWS deployment is untested.** The scripts were checked against documentation and run in dry-run mode only.
- **The image is large (2.2 GB)** because of PyTorch, and base images are pinned by tag, not by digest.

## What I would do next

1. Have support staff review the evaluation labels and add real, reworded tickets.
2. Deploy to AWS, measure start-up and latency there, and confirm the task size.
3. Add sign-in and access filtering before any real ticket is loaded.
4. Record whether each resolution is an approved fix, a workaround or outdated.
5. Collect reviewed feedback centrally and use it to re-tune thresholds.

## Repository layout

```
backend/
  app/            API, search engine, tokenizer, retrieval, comparison cards
  config/         relevance thresholds and how they were chosen
  evaluation/     reviewed query sets, the evaluation command, saved results
  tests/          pytest suite
frontend/
  src/            React components, API client and types, tests
deploy/aws/       PowerShell scripts and JSON for Amazon ECR and ECS Express Mode
starter_kit/      original case-study materials, unmodified
Dockerfile        multi-stage build: frontend, backend, model, embeddings
```

About the starter utility: [starter_kit/ticket_utils.py](starter_kit/ticket_utils.py) is not used by the application. It always returns three tickets even when nothing is similar, ignores resolution notes, and counts common words as matches. The evaluation runs it unmodified as a baseline.
