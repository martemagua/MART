"""Country flags: BM+ country name -> the flag shipped in static/flags/.

The flags are the flag-icons set (MIT, vendor/LICENSES/flag-icons-LICENSE.txt),
one 4:3 SVG per ISO 3166 code. Images, not emoji: Windows draws flag emoji
as two letters. A name MART doesn't know simply shows without a flag.
"""

from __future__ import annotations

import re
import unicodedata

from markupsafe import Markup, escape

# the flag set's own names
NAMES = {
    "Afghanistan": "af", "Aland Islands": "ax", "Albania": "al", "Algeria": "dz",
    "American Samoa": "as", "Andorra": "ad", "Angola": "ao", "Anguilla": "ai", "Antarctica": "aq",
    "Antigua and Barbuda": "ag", "Argentina": "ar", "Armenia": "am", "Aruba": "aw",
    "Australia": "au", "Austria": "at", "Azerbaijan": "az", "Bahamas": "bs", "Bahrain": "bh",
    "Bangladesh": "bd", "Barbados": "bb", "Belarus": "by", "Belgium": "be", "Belize": "bz",
    "Benin": "bj", "Bermuda": "bm", "Bhutan": "bt", "Bolivia": "bo",
    "Bonaire, Sint Eustatius and Saba": "bq", "Bosnia and Herzegovina": "ba", "Botswana": "bw",
    "Bouvet Island": "bv", "Brazil": "br", "British Indian Ocean Territory": "io",
    "Brunei Darussalam": "bn", "Bulgaria": "bg", "Burkina Faso": "bf", "Burundi": "bi",
    "Cabo Verde": "cv", "Cambodia": "kh", "Cameroon": "cm", "Canada": "ca", "Canary Islands": "ic",
    "Cayman Islands": "ky", "Central African Republic": "cf", "Chad": "td", "Chile": "cl",
    "China": "cn", "Christmas Island": "cx", "Clipperton Island": "cp",
    "Cocos (Keeling) Islands": "cc", "Colombia": "co", "Comoros": "km", "Cook Islands": "ck",
    "Costa Rica": "cr", "Croatia": "hr", "Cuba": "cu", "Curaçao": "cw", "Cyprus": "cy",
    "Czech Republic": "cz", "Côte d'Ivoire": "ci", "Democratic Republic of the Congo": "cd",
    "Denmark": "dk", "Diego Garcia": "dg", "Djibouti": "dj", "Dominica": "dm",
    "Dominican Republic": "do", "Ecuador": "ec", "Egypt": "eg", "El Salvador": "sv",
    "Equatorial Guinea": "gq", "Eritrea": "er", "Estonia": "ee", "Eswatini": "sz", "Ethiopia": "et",
    "Europe": "eu", "Falkland Islands": "fk", "Faroe Islands": "fo",
    "Federated States of Micronesia": "fm", "Fiji": "fj", "Finland": "fi", "France": "fr",
    "French Guiana": "gf", "French Polynesia": "pf", "French Southern Territories": "tf",
    "Gabon": "ga", "Gambia": "gm", "Georgia": "ge", "Germany": "de", "Ghana": "gh",
    "Gibraltar": "gi", "Greece": "gr", "Greenland": "gl", "Grenada": "gd", "Guadeloupe": "gp",
    "Guam": "gu", "Guatemala": "gt", "Guernsey": "gg", "Guinea": "gn", "Guinea-Bissau": "gw",
    "Guyana": "gy", "Haiti": "ht", "Heard Island and McDonald Islands": "hm", "Holy See": "va",
    "Honduras": "hn", "Hong Kong": "hk", "Hungary": "hu", "Iceland": "is", "India": "in",
    "Indonesia": "id", "Iran": "ir", "Iraq": "iq", "Ireland": "ie", "Isle of Man": "im",
    "Israel": "il", "Italy": "it", "Jamaica": "jm", "Japan": "jp", "Jersey": "je", "Jordan": "jo",
    "Kazakhstan": "kz", "Kenya": "ke", "Kiribati": "ki", "Kosovo": "xk", "Kuwait": "kw",
    "Kyrgyzstan": "kg", "Laos": "la", "Latvia": "lv", "Lebanon": "lb", "Lesotho": "ls",
    "Liberia": "lr", "Libya": "ly", "Liechtenstein": "li", "Lithuania": "lt", "Luxembourg": "lu",
    "Macau": "mo", "Madagascar": "mg", "Malawi": "mw", "Malaysia": "my", "Maldives": "mv",
    "Mali": "ml", "Malta": "mt", "Marshall Islands": "mh", "Martinique": "mq", "Mauritania": "mr",
    "Mauritius": "mu", "Mayotte": "yt", "Mexico": "mx", "Moldova": "md", "Monaco": "mc",
    "Mongolia": "mn", "Montenegro": "me", "Montserrat": "ms", "Morocco": "ma", "Mozambique": "mz",
    "Myanmar": "mm", "Namibia": "na", "Nauru": "nr", "Nepal": "np", "Netherlands": "nl",
    "New Caledonia": "nc", "New Zealand": "nz", "Nicaragua": "ni", "Niger": "ne", "Nigeria": "ng",
    "Niue": "nu", "Norfolk Island": "nf", "North Korea": "kp", "North Macedonia": "mk",
    "Northern Mariana Islands": "mp", "Norway": "no", "Oman": "om", "Pacific Community": "pc",
    "Pakistan": "pk", "Palau": "pw", "Panama": "pa", "Papua New Guinea": "pg", "Paraguay": "py",
    "Peru": "pe", "Philippines": "ph", "Pitcairn": "pn", "Poland": "pl", "Portugal": "pt",
    "Puerto Rico": "pr", "Qatar": "qa", "Republic of the Congo": "cg", "Romania": "ro",
    "Russia": "ru", "Rwanda": "rw", "Réunion": "re", "Saint Barthélemy": "bl",
    "Saint Helena, Ascension and Tristan da Cunha": "sh", "Saint Kitts and Nevis": "kn",
    "Saint Lucia": "lc", "Saint Martin": "mf", "Saint Pierre and Miquelon": "pm",
    "Saint Vincent and the Grenadines": "vc", "Samoa": "ws", "San Marino": "sm",
    "Sao Tome and Principe": "st", "Saudi Arabia": "sa", "Senegal": "sn", "Serbia": "rs",
    "Seychelles": "sc", "Sierra Leone": "sl", "Singapore": "sg", "Sint Maarten": "sx",
    "Slovakia": "sk", "Slovenia": "si", "Solomon Islands": "sb", "Somalia": "so",
    "South Africa": "za", "South Georgia and the South Sandwich Islands": "gs", "South Korea": "kr",
    "South Sudan": "ss", "Spain": "es", "Sri Lanka": "lk", "State of Palestine": "ps",
    "Sudan": "sd", "Suriname": "sr", "Svalbard and Jan Mayen": "sj", "Sweden": "se",
    "Switzerland": "ch", "Syria": "sy", "Taiwan": "tw", "Tajikistan": "tj", "Tanzania": "tz",
    "Thailand": "th", "Timor-Leste": "tl", "Togo": "tg", "Tokelau": "tk", "Tonga": "to",
    "Trinidad and Tobago": "tt", "Tunisia": "tn", "Turkmenistan": "tm",
    "Turks and Caicos Islands": "tc", "Tuvalu": "tv", "Türkiye": "tr", "Uganda": "ug",
    "Ukraine": "ua", "United Arab Emirates": "ae", "United Kingdom": "gb", "United Nations": "un",
    "United States Minor Outlying Islands": "um", "United States of America": "us", "Uruguay": "uy",
    "Uzbekistan": "uz", "Vanuatu": "vu", "Venezuela": "ve", "Vietnam": "vn",
    "Virgin Islands (British)": "vg", "Virgin Islands (U.S.)": "vi", "Wallis and Futuna": "wf",
    "Western Sahara": "eh", "Yemen": "ye", "Zambia": "zm", "Zimbabwe": "zw",
}

# how BM+ (ISO 3166's long forms) and people also write them
ALIASES = {
    "Bolivia, Plurinational State Of": "bo", "Cape Verde": "cv", "Congo": "cg",
    "Congo, The Democratic Republic Of The": "cd", "Czechia": "cz", "Great Britain": "gb",
    "Hong Kong SAR": "hk", "Iran, Islamic Republic Of": "ir", "Korea": "kr",
    "Korea, Democratic People's Republic Of": "kp", "Korea, Republic Of": "kr",
    "Lao People's Democratic Republic": "la", "Macao": "mo",
    "Macedonia, The Former Yugoslav Republic Of": "mk", "Micronesia, Federated States Of": "fm",
    "Moldova, Republic Of": "md", "Palestine, State Of": "ps", "Russian Federation": "ru",
    "Swaziland": "sz", "Syrian Arab Republic": "sy", "Taiwan, Province Of China": "tw",
    "Tanzania, United Republic Of": "tz", "Turkey": "tr", "UAE": "ae", "UK": "gb",
    "United States": "us", "USA": "us", "Venezuela, Bolivarian Republic Of": "ve",
    "Viet Nam": "vn", "Burma": "mm", "Republic of Korea": "kr", "East Timor": "tl",
}


def _norm(name: str) -> str:
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", " ", text.casefold()).strip()


_CODES = {_norm(n): c for n, c in (NAMES | ALIASES).items()}


def code(country: str | None) -> str | None:
    """The ISO code of a country name, or None when MART doesn't know it."""
    return _CODES.get(_norm(country)) if country else None


def flag(country: str | None) -> Markup:
    """An <img> of the country's flag (a Jinja filter); empty when unknown.
    alt is empty: the country's name is always written beside it."""
    c = code(country)
    if not c:
        return Markup("")
    return Markup('<img class="flag" src="/static/flags/{}.svg" alt="" width="16" height="12" '
                  'title="{}">').format(c, escape(country))
