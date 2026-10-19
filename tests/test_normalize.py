from tejtm.normalize import normalize_identifier, tokenize_identifier


def test_normalize_collapses_punctuation_and_case():
    assert normalize_identifier("Customer.Name") == "customer name"


def test_tokenize_splits_camel_and_snake():
    assert "customer" in tokenize_identifier("customerName")
    assert "name" in tokenize_identifier("customer_name")
