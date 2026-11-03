import zipfile

from mart import __version__
from tools.build_zip import build


def test_zip_holds_exactly_what_runs(tmp_path):
    path = build(tmp_path)
    assert path.name == f"MART-{__version__}.zip"
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        assert all(n.startswith("MART/") for n in names)
        assert "MART/MART.bat" in names and "MART/START-HERE.txt" in names
        assert "MART/mart/__main__.py" in names
        assert "MART/vendor/jinja2/__init__.py" in names
        assert "MART/vendor/LICENSES/jinja2-LICENSE.txt" in names
        assert not any("/tests/" in n or "__pycache__" in n or n.endswith(".pyc") for n in names)
        assert not any(n.endswith((".xlsx", ".xls", ".csv", ".db")) for n in names)
        bat = zf.read("MART/MART.bat")
        assert b"\r\n" in bat and b"\n" not in bat.replace(b"\r\n", b"")
