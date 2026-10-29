import pytest

from tejtm.models import TypeGuess
from tejtm.typing.detectors import detect_semantic_type, type_compatibility


def test_detects_email_majority():
    guess = detect_semantic_type(["a@x.com", "b@y.org", "not"])
    assert guess.label == "email"
    assert guess.confidence >= 0.66


@pytest.mark.parametrize(
    ("samples", "label"),
    [
        (("a@x.com", "b@y.org"), "email"),
        (("+1 555-0100", "555-0199"), "phone"),
        (("https://ex.com", "http://a.io/x"), "url"),
        (("550e8400-e29b-41d4-a716-446655440000", "6ba7b810-9dad-11d1-80b4-00c04fd430c8"), "uuid"),
        (("2020-01-01", "2021-12-31"), "date"),
        (("2020-01-01T10:00", "2021-12-31 12:30"), "datetime"),
        (("10:00", "23:15"), "time"),
        (("$12.00", "€9.50"), "currency"),
        (("yes", "true"), "boolean"),
        (("42", "100"), "integer"),
        (("hello world", "foo bar baz"), "freetext"),
    ],
)
def test_detects_catalog_majority(samples, label):
    guess = detect_semantic_type(samples)
    assert guess.label == label
    if label != "freetext":
        assert guess.confidence >= 0.5


def test_sparse_email_falls_back_to_freetext():
    guess = detect_semantic_type(["a@x.com", "nope", "also nope"])
    assert guess.label == "freetext"
    assert guess.confidence < 0.5


def test_type_compatibility_exact():
    g = TypeGuess("email", 0.9)
    assert type_compatibility(g, "email") > 0.8


def test_type_compatibility_number_agrees_with_currency():
    g = TypeGuess("number", 1.0)
    assert type_compatibility(g, "currency") > 0.5
    assert type_compatibility(g, "email") == 0.0
