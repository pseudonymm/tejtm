from tejtm.typing.detectors import detect_semantic_type, type_compatibility


def test_detects_email_majority():
    guess = detect_semantic_type(["a@x.com", "b@y.org", "not"])
    assert guess.label == "email"
    assert guess.confidence >= 0.66


def test_type_compatibility_exact():
    from tejtm.models import TypeGuess

    g = TypeGuess("email", 0.9)
    assert type_compatibility(g, "email") > 0.8
