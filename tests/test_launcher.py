from pathlib import Path

import launcher


def make_paths(tmp_path: Path) -> launcher.LauncherPaths:
    local_root = tmp_path / "local"
    nas_root = tmp_path / "nas"
    return launcher.LauncherPaths(
        local_root=local_root,
        nas_root=nas_root,
        local_version_file=local_root / "version.json",
        nas_version_file=nas_root / "version.json",
        local_log_file=local_root / "launcher_debug.log",
        local_crash_file=local_root / "crash_launcher.txt",
        source_entrypoint=tmp_path / "launcher.py",
    )


def write_version(path: Path, version: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f'{{"version": "{version}"}}', encoding="utf-8")


def test_version_info_compares_semantic_parts() -> None:
    assert launcher.VersionInfo("2.0.10").is_newer_than(launcher.VersionInfo("2.0.9"))
    assert not launcher.VersionInfo("2.0.9").is_newer_than(launcher.VersionInfo("2.0.10"))
    assert launcher.VersionInfo("v2.1").is_newer_than(launcher.VersionInfo("2.0.99"))


def test_decide_update_requires_sync_when_nas_is_newer(tmp_path: Path) -> None:
    paths = make_paths(tmp_path)
    write_version(paths.local_version_file, "2.0.17")
    write_version(paths.nas_version_file, "2.0.18")

    decision = launcher.decide_update(paths)

    assert decision.online is True
    assert decision.update_required is True
    assert decision.first_install is False
    assert decision.remote_version is not None
    assert decision.remote_version.raw == "2.0.18"


def test_decide_update_falls_back_to_local_when_nas_missing(tmp_path: Path) -> None:
    paths = make_paths(tmp_path)
    write_version(paths.local_version_file, "2.0.17")

    decision = launcher.decide_update(paths)

    assert decision.online is False
    assert decision.update_required is False
    assert "copia local" in decision.message


def test_build_child_command_in_source_mode(tmp_path: Path, monkeypatch) -> None:
    paths = make_paths(tmp_path)
    monkeypatch.setattr(launcher.sys, "frozen", False, raising=False)
    monkeypatch.setattr(launcher.sys, "executable", "C:/Python/python.exe")

    command = launcher.build_child_command(paths)

    assert command == [
        "C:/Python/python.exe",
        str(paths.source_entrypoint),
        "--run-app",
    ]


def test_local_app_ready_requires_core_files(tmp_path: Path) -> None:
    paths = make_paths(tmp_path)
    assert launcher.local_app_ready(paths) is False

    write_version(paths.local_version_file, "2.0.18")
    (paths.local_root / "pyside_ui" / "assets").mkdir(parents=True, exist_ok=True)
    (paths.local_root / "pyside_ui" / "app.py").write_text("def main():\n    return 0\n", encoding="utf-8")
    (paths.local_root / "pyside_ui" / "main_window.py").write_text("class MainWindow:\n    pass\n", encoding="utf-8")
    (paths.local_root / "pyside_ui" / "assets" / "ico.png").write_bytes(b"png")

    assert launcher.local_app_ready(paths) is True


def test_parse_robocopy_line_counts_actions() -> None:
    stats = launcher.SyncStats()

    event, payload, percent = launcher.parse_robocopy_line(stats, "New File                1234  file.txt", list_only=True)
    assert event == "file"
    assert "file.txt" in (payload or "")
    assert percent is None
    assert stats.files_total == 1

    event, payload, percent = launcher.parse_robocopy_line(stats, " 45.0% ", list_only=False)
    assert event == "progress"
    assert percent == 45
