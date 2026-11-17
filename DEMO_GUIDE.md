# Demo Guide

A three-minute walkthrough and the questions an evaluator is likely to ask. Every result quoted here was observed on the local container on 2026-11-17; if you change thresholds or data, re-check before presenting.

## Before the demo

- Start the application (`docker run --rm -p 8080:8080 ticket-similarity-assistant`) at least a minute beforehand and run one search to warm it up.
- Open <http://localhost:8080> in a fresh tab so the "Recent in this tab" list is empty.
- Have [SOLUTION_DESIGN.md](SOLUTION_DESIGN.md) open in a second tab.

## Three minutes

**0:00 — The problem (20 seconds).**
"Solari's agents handle about 150 tickets a day and often re-solve something a colleague already solved, or give a different answer. This tool shows the agent similar past tickets and their original resolutions. The agent still does the investigating."

**0:20 — A clear match (50 seconds).** Click **Example 3** ("Getting charged twice this month"), then **Search**.
- One close match: T-1303, with its resolution shown verbatim.
- Point at the highlighted words side by side: "These are the exact words both tickets use."
- Point at "Check before reusing this resolution": "It quotes the past cause and asks whether there is any sign of it here. It does not claim the retry caused this customer's problem."
- Open "Technical details": "Raw scores are there for evaluation. The agent sees labels, never a percentage, because a similarity score is not the chance that a fix works."

**1:10 — An unfamiliar problem, and closing the loop (50 seconds).** Click **Example 4** (Snowflake), then **Search**.
- "No relevant historical match found. No previous matching tickets are available for this search. Human investigation is required." No past-ticket cards are shown, not even weak ones.
- Point at the escalation link and say it only opens the agent's mail client; nothing is sent automatically.
- "The starter scorer returns three tickets for this. Mine says there is no good match."
- Click **Record resolution**. The form is prefilled from the ticket that was searched. Fill in the category, investigation, resolution steps and verification, tick the confirmation, then press **Save resolved ticket**.
- "Ticket saved and available for future searches" appears only once the new ticket is in the search index. Search Example 4 again: it now returns the ticket you just recorded as an exact text match. (Only do this on a local demo. On a public URL saving is normally switched off.)

**2:00 — A misleading look-alike (20 seconds).** Click **Example 1** (reset email never arrives), then **Search**.
- No relevant historical match. T-1001, about a rejected password after the email arrived, scored below the line by a small margin, so it is not shown.
- "Same topic, different problem. Hiding below-threshold tickets keeps wrong fixes off the screen, but it also hides reworded true matches. That is a measured trade-off I can show you."

**2:20 — Refinement and honesty about input (20 seconds).** Type `not working please help` as the subject, **Search**.
- "More detail is needed before searching." Nothing was searched; the suggestions say what to add.

**2:40 — How I know (20 seconds).** Switch to the design document's results table.
- "52 labelled queries in two sets that share no source ticket. Thresholds tuned on one, checked once on the other. Near-verbatim tickets are found; reworded ones are ranked but not labelled close matches; zero false matches on the final set. Small samples, synthetic data."

## If there is time

- **Category filter:** search Example 3 with the category set to `export`. The result disappears and the page says how many close matches the filter hides.
- **Different product:** subject `SSO login redirects to a blank page`, description `Customer using Auth0 SSO is redirected back to the app after authenticating, but the page is completely blank.`, Product `Auth0`. T-1002 comes back as a close match because the wording is nearly identical, and the card states "The tickets give different names. New ticket: Auth0. Past ticket: SSO, Okta" and asks whether the resolution was specific to Okta. This is the card doing its job where the score cannot.
- **Feedback:** click Useful on a card, then "Export feedback (JSON)". Say that it stays in the browser tab and trains nothing.
- **Degraded mode:** restart the container with `-e SEMANTIC_ENABLED=false`. The banner says results are keyword-only.

## Likely questions

**What does "similar" mean in your system?**
The same symptom in the same product area, so the past resolution is a sensible first thing to check. I measure it two ways, shared wording and similar meaning, and I state plainly that neither can tell "same topic" from "same problem".

**Why two retrievers?**
They fail differently. Keyword search misses rewording. Meaning-based search treats a Snowflake failure and a HubSpot failure as close. In my evaluation semantic search alone actually ranked best; I kept the hybrid because keyword search handles exact codes and names, and it is the tested fallback when the model is unavailable.

**What is Reciprocal Rank Fusion and why not use its score as confidence?**
Each ticket scores 1/(60 + rank) in each ranking, summed. It uses only ranks, so the top result of two bad lists scores exactly the same as the top result of two good ones. It orders candidates; a separate rule decides whether any is worth showing.

**How did you choose the thresholds?**
On a tuning set of 28 queries, by looking at the scores of the expected ticket and of the strongest other ticket. Then I froze them and ran a separate final set once. The values and the reasoning are in `backend/config/relevance.json`. They are provisional: margins are as small as 0.03.

**Your close-match rate on reworded tickets is zero. Is that acceptable?**
It is the honest result. Reworded matches score no higher than unrelated tickets, so labelling them "close" would also label unrelated tickets "close". I chose precision. On the no-match screen, below-threshold tickets are not shown at all, so on the final set 5 of the 6 reworded true matches are hidden from the agent even though the search ranked them. The API still returns them. With real data I would test a reranker, since the right ticket is already in the candidate list.

**What happens with a ticket about something you have never seen?**
"No relevant historical match found", "Human investigation is required", an escalation link, and a form to record the resolution once it is solved. That is a normal 200 response, distinct from a service error, which has its own screen and a Retry button.

**How does a recorded resolution become searchable?**
Saving is a separate, explicit request; searching never writes. The save is committed first (JSON file written atomically, or a PostgreSQL transaction). Then a complete new search index is built off to the side, embedding only new or changed text, and swapped in. If that fails, the ticket stays saved, marked "indexing failed", searches keep the previous index, and Retry or the next start-up indexes it.

**Why PostgreSQL, and what does it change?**
Only where tickets are stored. Retrieval is identical, and an integration test checks that both stores give the same results. PostgreSQL adds durable, transactional saves: insert once, idempotent repeats, row locks against stale updates, and a trigger that marks rows edited directly in SQL for re-indexing.

**How do you stop it inventing fixes?**
Original result cards fetch the resolution by ticket ID and show it unchanged. The optional summary is separately labelled AI-generated. It uses the exact displayed sources and their versions, cites source IDs and never writes a resolution. Coverage checks catch missing or substituted tickets, but they do not prove factual accuracy; the agent must verify the generated text against the originals.

**What if the model fails?**
Keyword-only results with a visible banner and separate thresholds. Readiness stays healthy while one search mode works and fails when none does. Both paths are tested.

**How does it scale to 55,000 tickets a year?**
Not as built. Brute-force comparison is fine for 40 tickets. I would precompute embeddings offline, use a nearest-neighbour index, and switch complete index snapshots in one step. Thresholds would need re-tuning.

**Is it secure? Could you load real tickets?**
No. There is no sign-in and the dataset has no ownership field, so I cannot demonstrate access isolation and do not claim it. What exists: input limits, safe rendering, a strict content security policy, logs without ticket text, a non-root read-only container. Sign-in, access filtering, redaction, retention and audit come first.

**When does the language model run?**
Only after the agent clicks Summarize. Choose Top 3 or Top 5, run a search, then summarize the actual main matches shown. If only two qualify, the button summarizes two. Changing the count clears the summary and reruns search; another click is needed to summarize again. Related context is excluded. A provider failure leaves the original results usable. An API key must be configured on the server, and the live provider has not yet been verified for this change.

**Did you deploy it?**
The container runs locally under production-like restrictions. The AWS scripts are written and checked against the documentation, but I have not run them against an account. *(Update this answer after you deploy.)*

**What did you cut?**
Persistence, import of new tickets, authentication, rate limiting per client, and detection of differences in meaning. Each is listed with its reason in the design document.

**What would you ask Jamie first?**
What agents count as "the same problem", whether resolutions may be shown across customers, and for a sample of real tickets to label.
