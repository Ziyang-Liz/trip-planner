def estimate_cost(origin, destination, days):
    return {
        "transport": 120,
        "accommodation": 80 * days,
        "meals": 50 * days,
        "total": 120 + (80 + 50) * days
    }
