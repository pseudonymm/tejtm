from tejtm.coercion import coerce_record, coerce_value


def test_coerce_integer_and_boolean():
    assert coerce_value("42", "integer") == 42
    assert coerce_value("yes", "boolean") is True


def test_coerce_record_skips_unknown_keys():
    out = coerce_record({"a": "1"}, {"a": "integer"})
    assert out["a"] == 1
