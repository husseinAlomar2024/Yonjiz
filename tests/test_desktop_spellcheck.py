import pytest

pytest.importorskip("spellchecker")

from desktop.spellcheck import correct_text


def test_common_task_typos_are_corrected():
    fixed, changes = correct_text("Finish teh breif and recieve it tommorow")
    assert fixed == "Finish the brief and receive it tomorrow"
    assert ("teh", "the") in changes


def test_names_and_brand_are_not_mangled():
    fixed, changes = correct_text("Hussein and YONJIZ use the app")
    assert fixed == "Hussein and YONJIZ use the app"
    assert changes == []


def test_notes_can_be_corrected_without_touching_clean_text():
    fixed, changes = correct_text("The studio is quiet today.")
    assert fixed == "The studio is quiet today."
    assert changes == []
