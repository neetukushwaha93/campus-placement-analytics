from typing import Any


def build_parameterized_filter(
    tiers: list[str],
    branches: list[str],
    cgpa_range: tuple[float, float],
    min_dsa: int,
    placed_only: bool = True
) -> tuple[str, dict[str, Any]]:

    """
    Constructs a sanitized SQL WHERE clause and
    corresponding named-parameter dictionary.
    """

    conditions = []
    params: dict[str, Any] = {}

    # College tier filter
    if tiers:
        tier_keys = [f"tier_{i}" for i in range(len(tiers))]
        placeholders = ",".join([f":{k}" for k in tier_keys])

        conditions.append(
            f"college_tier IN ({placeholders})"
        )

        for k, val in zip(tier_keys, tiers):
            params[k] = val

    # Branch filter
    if branches:
        branch_keys = [f"branch_{i}" for i in range(len(branches))]
        placeholders = ",".join([f":{k}" for k in branch_keys])

        conditions.append(
            f"Branch IN ({placeholders})"
        )

        for k, val in zip(branch_keys, branches):
            params[k] = val

    # CGPA filter
    conditions.append(
        "CGPA BETWEEN :cgpa_min AND :cgpa_max"
    )

    params["cgpa_min"] = float(cgpa_range[0])
    params["cgpa_max"] = float(cgpa_range[1])

    # DSA problems solved filter
    conditions.append(
        "DSA_problem_solved >= :min_dsa"
    )

    params["min_dsa"] = int(min_dsa)

    # Placement status filter
    if placed_only:
        conditions.append(
            "Placement_status = :status"
        )

        params["status"] = "placed"

    # Build WHERE clause
    where_clause = (
        f"WHERE {' AND '.join(conditions)}"
        if conditions
        else ""
    )

    return where_clause, params

