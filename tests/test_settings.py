from pathlib import Path

from mart import settings as s


def test_no_settings_means_not_set_up():
    assert s.load() is None


def test_save_and_load_round_trip(tmp_path):
    saved = s.Settings(data_dir=str(tmp_path / "d"), backup_dir=str(tmp_path / "b"),
                       backups_keep=7, port=8099)
    s.save(saved)
    assert s.load() == saved


def test_damaged_settings_file_counts_as_not_set_up():
    s.settings_file().parent.mkdir(parents=True, exist_ok=True)
    s.settings_file().write_text("{ not json", encoding="utf-8")
    assert s.load() is None


def _validate(tmp_path, data="d", backup="b", keep="20", port="8070"):
    return s.validate(str(tmp_path / data) if data else "",
                      str(tmp_path / backup) if backup else "", keep, port)


def test_valid_folders_are_accepted(tmp_path):
    settings, errors = _validate(tmp_path)
    assert errors == []
    assert settings.db_path == tmp_path / "d" / "mart.db"


def test_relative_paths_are_rejected():
    _, errors = s.validate("MART-data", "backups", "20", "8070")
    assert any("full path" in e for e in errors)


def test_backup_folder_must_differ_from_and_not_sit_inside_data(tmp_path):
    _, errors = _validate(tmp_path, data="d", backup="d")
    assert any("different" in e for e in errors)
    _, errors = _validate(tmp_path, data="d", backup="d/backups")
    assert any("inside the data folder" in e for e in errors)


def test_data_folder_in_onedrive_is_refused_but_backups_there_are_fine(tmp_path, monkeypatch):
    od = tmp_path / "OD-Company"
    od.mkdir()
    monkeypatch.setenv("OneDriveCommercial", str(od))
    _, errors = s.validate(str(od / "MART-data"), str(tmp_path / "b"), "20", "8070")
    assert any("synced folder" in e for e in errors)
    settings, errors = s.validate(str(tmp_path / "d"), str(od / "MART-backups"), "20", "8070")
    assert errors == []


def test_onedrive_is_recognised_by_folder_name_too(tmp_path):
    for name in ("OneDrive - Contoso", "OneDrive", "Dropbox"):
        _, errors = s.validate(str(tmp_path / name / "MART"), str(tmp_path / "b"), "20", "8070")
        assert any("synced folder" in e for e in errors), name


def test_folders_that_merely_mention_onedrive_are_fine(tmp_path):
    for name in ("my-onedrive-notes", "Boxes", "dropboxer"):
        _, errors = s.validate(str(tmp_path / name / "MART"), str(tmp_path / "b"), "20", "8070")
        assert errors == [], name


def test_numbers_are_checked(tmp_path):
    _, errors = _validate(tmp_path, keep="0", port="80")
    assert any("Backups to keep" in e for e in errors)
    assert any("port" in e for e in errors)


def test_defaults_put_backups_in_onedrive_when_there_is_one(tmp_path, monkeypatch):
    assert Path(s.defaults().backup_dir).name == "MART-backups"
    monkeypatch.setenv("OneDrive", str(tmp_path / "OD"))
    d = s.defaults()
    assert Path(d.backup_dir) == tmp_path / "OD" / "MART-backups"
    assert s.synced_folder(d.data_dir) is None
