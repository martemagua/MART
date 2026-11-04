import zipfile

from mart import __version__
from tools.build_zip import build, build_info, verify


def test_zip_holds_exactly_what_runs(tmp_path):
    path = build(tmp_path)
    assert path.name == f"MART-{__version__}.zip"
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        assert all(n.startswith("MART/") for n in names)
        for needed in ("MART/MART.bat", "MART/START-HERE.txt", "MART/BUILD-INFO.txt",
                       "MART/mart/__main__.py", "MART/mart/find-python.cmd",
                       "MART/vendor/jinja2/__init__.py", "MART/vendor/LICENSES/jinja2-LICENSE.txt"):
            assert needed in names, needed
        assert "MART/make-zip.bat" not in names  # the build tool stays on the PC
        assert not any("/tests/" in n or "/tools/" in n or "__pycache__" in n
                       or n.endswith(".pyc") for n in names)
        assert not any(n.endswith((".xlsx", ".xls", ".csv", ".db")) for n in names)
        for script in ("MART/MART.bat", "MART/mart/find-python.cmd"):
            data = zf.read(script)
            assert b"\r\n" in data and b"\n" not in data.replace(b"\r\n", b""), script
    assert not list(tmp_path.glob("*.part"))


def test_build_info_names_the_version_and_commit():
    info = build_info()
    assert info.startswith(f"MART {__version__}") and "Commit" in info


def test_the_built_zip_passes_its_own_start_up_check(tmp_path):
    ok, output = verify(build(tmp_path))
    assert ok, output
    assert "Python" in output and "Page templates (shipped)" in output
