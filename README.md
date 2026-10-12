# Search evaluation

## MVP search behavior

The MVP uses `sentence-transformers/all-MiniLM-L6-v2` for local semantic search. Keyword search remains the evaluation baseline.

The application applies explicit category, maximum-price, and stock filters before ranking. Maximum price is inclusive. Stock `true` means in-stock only, `false` means out-of-stock only, and `null` means no stock restriction.

For a nonblank query, semantic search returns up to five eligible products ranked by similarity. No similarity cutoff is applied. If no products pass the explicit filters, the search returns an empty list.

Missing, empty, or whitespace-only queries currently return all eligible products without ranking. The final blank-query limit will be settled and tested during correctness review.

## Evaluation method

### Case files

- `dev_queries.json`: 20 development cases (`dev01`–`dev20`). Used to compare methods and choose the MVP behavior.
- `test_queries.json`: 20 held-out cases (`test01`–`test20`). Labeled before either search method was run on them, and evaluated only after the model, catalog, ranking, and cutoff behavior were fixed.

Each case has a query, explicit filters, the IDs of all relevant products, and a reason for those labels. Labels come from documented catalog evidence (name and description). A product is not labeled relevant when suitability depends on a feature its description does not mention.

### Metrics

All quality metrics use the first five results returned for each case.

- **Recall@5**: for a case with at least one relevant product, the number of relevant products in the first five results divided by the total number of relevant products. The table reports the mean across those cases. A case with more than five relevant products cannot reach 1.0 (dev01 has six, so its maximum is 5/6).
- **Unwanted products**: returned products in the first five that are not labeled relevant, summed across all cases.
- **Correct empty results**: for cases with no relevant products, whether the method returned an empty list. Reported for all no-result cases and separately for those where eligible candidates still existed after filtering.
- **Filter-violating products**: returned products that fail any explicit filter (category, maximum price, or stock). Checked across all returned results.
- **Median search time**: median elapsed milliseconds per search call, using only samples where the eligible list was nonempty.

### Timing procedure

1. Load search resources (model, product embeddings, ID index) once. This is timed separately as resource-loading time.
2. Apply each case's explicit filters once and store its eligible products. Filtering is not part of any search timing.
3. Warm-up: run every case once through keyword search and once through semantic search. These runs are not timed, printed, or scored.
4. Measured runs: five passes over all cases. In each pass, for each case, keyword search and semantic search are timed separately with `time.perf_counter()` recorded immediately before and after the search call. Each sample stores the case ID, method, pass number, whether the eligible list was empty, and elapsed milliseconds.
5. Quality metrics are computed in a separate, untimed loop.

Each method gets 100 timing samples per case file (20 cases × 5 passes). Timings exclude filtering, HTTP handling, and browser rendering. They are local measurements, not deployed-service latency.

### Environment

| Item | Value |
|---|---|
| Hardware | TODO: e.g. MacBook Air, chip, RAM |
| Operating system | TODO |
| Python version | TODO |
| Model device | TODO: actual device reported by the loaded model |
| Model weights | TODO: already downloaded / downloaded during this run |

## Development results

On 20 development cases, semantic search achieved higher mean recall@5 than the keyword baseline, particularly on everyday-language paraphrases. It also returned more unwanted products.

| Metric | Keyword | Semantic |
|---|---:|---:|
| Mean recall@5 across 14 cases with relevant products | 0.7381 | 0.9762 |
| Unwanted products across the first five results per case | 43 | 55 |
| Correct empty results across 6 no-result cases | 2/6 | 2/6 |
| Correct empty results when eligible candidates existed | 0/4 | 0/4 |
| Observed filter-violating products | 0 | 0 |
| Median search time with nonempty eligible lists | 0.031 ms | 2.571 ms |

Timing produced 90 nonempty-eligible samples per method. Resource loading took approximately 4.81 seconds in this run.

### Why this approach was selected

We retained semantic ranking without a cutoff because the inspected similarity scores did not reliably separate relevant from irrelevant products across queries. For example, an unsupported phone-charging speaker request produced an irrelevant match scoring 0.622, while a relevant noisy-commute match scored 0.340. A cutoff high enough to reject the former would also reject the latter.

This does not rule out all benefits from a cutoff, but a cutoff alone cannot resolve these examples.

These results support the MVP decision but are not held-out evidence.

## Held-out results

TODO: paste the held-out results table here.

| Metric | Keyword | Semantic |
|---|---:|---:|
| Mean recall@5 across 14 cases with relevant products | TODO | TODO |
| Unwanted products across the first five results per case | TODO | TODO |
| Correct empty results across 6 no-result cases | TODO | TODO |
| Correct empty results when eligible candidates existed | TODO | TODO |
| Observed filter-violating products | TODO | TODO |
| Median search time with nonempty eligible lists | TODO | TODO |

Timing produced 90 nonempty-eligible samples per method (18 of 20 cases have eligible products; test19 and test20 have none). Resource loading took 4.99 seconds in this run.

### Interpretation

TODO: paste the interpretation of the held-out results here.

### test07 ranking failure

TODO: describe what semantic search ranked for test07 and where p025 appeared.

test07 asks for "recording interviews with two guests on my phone, with mics attached to their shirts". The only relevant product is p025, which has two clip-on wireless microphones with a phone receiver.

### Test file version

- File: `evaluation/test_queries.json`
- SHA-256: `0be9b3c6b15956690328f734d670810702765fa4a5078669f4be71e437475806`

Verify with `shasum -a 256 evaluation/test_queries.json`. If the hash differs, the file was edited after this version was recorded.

### Labeling corrections

- **test17, before any search was run:** the draft query "wireless earbuds" duplicated dev01's query text. It was reworded to "earbuds that pair over bluetooth". Its filters (earbuds, maximum 5,000 KZT) and label (`[]`) did not change.
- **After running:** none. No held-out label or query was changed after results were seen.

## Known limitations

Similarity measures closeness of meaning; it is not a probability of suitability and does not verify every requested feature.

The application does not extract or enforce category, price, or stock constraints from query text. Users must specify these through the explicit controls. Other natural-language requirements, such as waterproofing or phone charging, are not strictly enforced.

When eligible candidates exist, unsupported requests may return related products. Reliable rejection of unsupported requests remains unfinished. Successful no-result cases so far were caused by filters excluding all products.

The catalog is synthetic. Evaluation uses small, manually labeled English case sets. Labels reflect documented catalog evidence; a missing feature description does not prove the feature is absent.

The dev18 query was narrowed during development to reduce labeling ambiguity. This was an evaluation-case revision, not a search improvement.