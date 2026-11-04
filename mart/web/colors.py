"""Colour coding (Martin, 04.11.2026: "so I can more easily identify the
different types of renewals"). One mapping per kind of value, used by every
template through the `strategy_class` filter; the colours themselves are CSS
tokens (`--st-*` in mart.css, light and dark).
"""

from __future__ import annotations

from typing import Any

from mart.ingestion.sheet import norm

# BM+ "Upcoming Renewal Strategy" values seen in the exports -> CSS class
STRATEGY_CLASSES = {
    norm("Remarketing"): "st-remarket",
    norm("Incumbent without Rate Guarantee"): "st-incumbent",
    norm("Incumbent with Rate Guarantee"): "st-guarantee",
    norm("Non-expiring"): "st-nonexpiring",
    norm("Unknown / New Policy"): "st-new",
    norm("TBC"): "st-tbc",
}


def strategy_class(value: Any) -> str:
    """CSS class for a strategy; an unknown or empty one is neutral."""
    return STRATEGY_CLASSES.get(norm(value), "st-none")
