"""Country flags: BM+ country name -> the flag shipped in static/flags/.

The flags are the flag-icons set (MIT, vendor/LICENSES/flag-icons-LICENSE.txt),
one 4:3 SVG per ISO 3166 code. Images, not emoji: Windows draws flag emoji
as two letters. A name MART doesn't know simply shows without a flag.
"""

from __future__ import annotations

from markupsafe import Markup, escape

from mart.ingestion.countries import ALIASES, NAMES, code  # noqa: F401  (re-exported)


def flag(country: str | None) -> Markup:
    """An <img> of the country's flag (a Jinja filter); empty when unknown.
    alt is empty: the country's name is always written beside it."""
    c = code(country)
    if not c:
        return Markup("")
    return Markup('<img class="flag" src="/static/flags/{}.svg" alt="" width="16" height="12" '
                  'title="{}">').format(c, escape(country))
