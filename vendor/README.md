# vendor/

Third-party code shipped inside MART, because nothing can be installed on
the work laptop. Rule: **pure Python only** (no compiled extensions), so the
folder works on any machine with Python 3.12.

| Package | Version | Licence | Source |
|---|---|---|---|
| Jinja2 | 3.1.6 | BSD-3-Clause (`LICENSES/jinja2-LICENSE.txt`) | sdist from PyPI, `src/jinja2` copied unchanged |
| flag-icons | 7.6.0 | MIT (`LICENSES/flag-icons-LICENSE.txt`) | npm package, `flags/4x3/<iso>.svg` copied unchanged to `mart/web/static/flags/` (country codes only; not code, just images) |
| MarkupSafe | 3.0.2 | BSD-3-Clause (`LICENSES/markupsafe-LICENSE.txt`) | sdist from PyPI, `src/markupsafe` copied; the optional C speed-up (`_speedups.c`) removed, so the pure-Python `_native` path is used |

`mart/__init__.py` puts this folder first on `sys.path`. To update a
package: replace its folder with the new release's source, update this
table, and run the tests.
