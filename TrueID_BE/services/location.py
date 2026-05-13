from collections import Counter

from TrueID_BE.schemas import ContactContributionRecord


def format_location(city: str | None, state: str | None, country: str = "Nigeria") -> str:
    city_value = _clean(city)
    state_value = _clean(state)
    country_value = _clean(country) or "Nigeria"

    if city_value and state_value:
        return f"{city_value}, {state_value}"
    if state_value:
        return state_value
    if city_value:
        return city_value
    return country_value


def infer_location_from_contributions(
    contributions: list[ContactContributionRecord],
    default_country: str,
) -> str:
    state_counts = Counter()
    city_state_counts = Counter()
    for contribution in contributions:
        state_value = _clean(contribution.source_state)
        city_value = _clean(contribution.source_city)
        if state_value:
            state_counts[state_value] += 1
        if city_value or state_value:
            city_state_counts[format_location(city_value, state_value, default_country)] += 1

    if not state_counts and not city_state_counts:
        return default_country
    if state_counts:
        top_state, _ = state_counts.most_common(1)[0]
        city_matches = [
            contribution
            for contribution in contributions
            if _clean(contribution.source_state) == top_state and _clean(contribution.source_city)
        ]
        unique_cities = {_clean(item.source_city) for item in city_matches}
        if len(unique_cities) == 1 and city_matches:
            return format_location(city_matches[0].source_city, top_state, default_country)
        return top_state
    return city_state_counts.most_common(1)[0][0]


def _clean(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = " ".join(value.split())
    return cleaned or None
