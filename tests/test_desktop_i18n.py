import pytest

pytest.importorskip("PySide6")

from datetime import datetime

from desktop import i18n


def test_arabic_translation_and_switch_label(tmp_path, monkeypatch):
    monkeypatch.setattr(i18n, "LANG_FILE", tmp_path / "settings.json")
    previous = i18n.language()
    try:
        i18n.set_language("ar")
        assert i18n.tr("Log in.") == "تسجيل الدخول."
        assert i18n.switch_label() == "English"
        assert "٢٠٢٦" in i18n.format_date(datetime(2026, 11, 1))
    finally:
        i18n.set_language(previous)


def test_english_is_the_default_fallback(tmp_path, monkeypatch):
    monkeypatch.setattr(i18n, "LANG_FILE", tmp_path / "settings.json")
    previous = i18n.language()
    try:
        i18n.set_language("en")
        assert i18n.tr("Log in.") == "Log in."
        assert i18n.switch_label() == "العربية"
    finally:
        i18n.set_language(previous)
