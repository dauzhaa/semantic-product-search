from statistics import mean, median
from time import perf_counter

import filter_product
import keyword_search
import semantic_search


RUNS = 5
METHODS = ("keyword", "semantic")

cases = filter_product.parse_products("evaluation/test_queries.json")

start = perf_counter()
resources = semantic_search.load_search_resources("products.json")
resource_loading_ms = (perf_counter() - start) * 1000

prepared = []
for case in cases:
    filters = case["filters"]
    eligible = filter_product.matching_prod(
        resources["products"],
        filters["category"],
        filters["max_price"],
        filters["in_stock"],
    )
    prepared.append((case, eligible))


def run_search(method, query, eligible):
    if method == "keyword":
        return keyword_search.key_search(query, eligible)

    return semantic_search.semantic_search(
        query,
        eligible=eligible,
        model=resources["model"],
        embeddings=resources["embeddings"],
        index_id=resources["index_by_id"],
    )


def violating_ids(products, filters):
    violations = []

    for product in products:
        wrong_category = (
            filters["category"] is not None
            and product["category"] != filters["category"]
        )
        over_budget = (
            filters["max_price"] is not None
            and product["price"] > filters["max_price"]
        )
        wrong_stock = (
            filters["in_stock"] is not None
            and product["in_stock"] != filters["in_stock"]
        )

        if wrong_category or over_budget or wrong_stock:
            violations.append(product["id"])

    return violations


# Warm-up: no timings or quality calculations.
for case, eligible in prepared:
    for method in METHODS:
        run_search(method, case["query"], eligible)


# Five timed passes. Save quality-evaluation results only on pass 0.
timings = []
first_pass_results = {}

for pass_num in range(RUNS):
    for case, eligible in prepared:
        for method in METHODS:
            start = perf_counter()
            results = run_search(method, case["query"], eligible)
            end = perf_counter()

            timings.append({
                "case_id": case["id"],
                "method": method,
                "pass": pass_num + 1,
                "eligible_empty": len(eligible) == 0,
                "ms": (end - start) * 1000,
            })

            if pass_num == 0:
                first_pass_results.setdefault(case["id"], {})
                first_pass_results[case["id"]][method] = results


# Calculate quality metrics once per case and method.
quality = {method: [] for method in METHODS}

for case, eligible in prepared:
    expected_ids = set(case["relevant_ids"])

    for method in METHODS:
        results = first_pass_results[case["id"]][method]
        returned_ids = [product["id"] for product in results]
        top_five_ids = set(returned_ids[:5])

        relevant_found = expected_ids & top_five_ids
        unwanted_ids = sorted(top_five_ids - expected_ids)
        violations = violating_ids(results, case["filters"])

        recall = (
            len(relevant_found) / len(expected_ids)
            if expected_ids
            else None
        )
        no_result_pass = (
            len(results) == 0
            if not expected_ids
            else None
        )

        quality[method].append({
            "case_id": case["id"],
            "returned_ids": returned_ids,
            "recall": recall,
            "no_result_pass": no_result_pass,
            "eligible_empty": len(eligible) == 0,
            "unwanted_ids": unwanted_ids,
            "violating_ids": violations,
        })

        print(f"\n{case['id']} | {method}")
        print("Returned:", returned_ids)

        if recall is not None:
            print(f"Recall@5: {recall:.3f}")
        else:
            print("No-result check:", no_result_pass)

        print("Unwanted:", unwanted_ids, "Count:", len(unwanted_ids))
        print(
            "Filter violations:",
            sorted(violations),
            "Count:",
            len(violations),
        )


def print_no_result_summary(label, rows):
    passed = sum(row["no_result_pass"] for row in rows)
    print(f"{label}: {passed}/{len(rows)}")


# Final summary.
print("\nFINAL SUMMARY")
print(f"Resource-loading time: {resource_loading_ms:.1f} ms")
print(f"Timing records: {len(timings)}")
print(f"Saved cases: {len(first_pass_results)}")

for method in METHODS:
    rows = quality[method]
    recalls = [
        row["recall"]
        for row in rows
        if row["recall"] is not None
    ]
    no_result_rows = [
        row for row in rows
        if row["no_result_pass"] is not None
    ]

    print(f"\n{method.upper()}")
    print("Cases:", len(rows))

    if recalls:
        print(
            f"Mean recall@5: {mean(recalls):.4f} "
            f"({len(recalls)} cases)"
        )
    else:
        print("Mean recall@5: N/A (0 cases)")

    print_no_result_summary("No-result passes", no_result_rows)
    print_no_result_summary(
        "  Empty eligible lists",
        [row for row in no_result_rows if row["eligible_empty"]],
    )
    print_no_result_summary(
        "  Nonempty eligible lists",
        [row for row in no_result_rows if not row["eligible_empty"]],
    )

    print(
        "Total unwanted results:",
        sum(len(row["unwanted_ids"]) for row in rows),
    )
    print(
        "Total violating products:",
        sum(len(row["violating_ids"]) for row in rows),
    )
    print(
        "Cases with violations:",
        sum(bool(row["violating_ids"]) for row in rows),
    )

    for empty, label in (
        (False, "Nonempty eligible lists"),
        (True, "Empty eligible lists"),
    ):
        durations = [
            timing["ms"]
            for timing in timings
            if timing["method"] == method
            and timing["eligible_empty"] == empty
        ]

        if durations:
            print(
                f"{label}: median {median(durations):.3f} ms "
                f"({len(durations)} samples)"
            )
        else:
            print(f"{label}: N/A (0 samples)")