from tejtm.value_profile import expectation_from_type, signature_similarity, value_signature


def test_exemplar_signature_beats_unrelated_shape():
    orders = value_signature(["ORD-1001", "ORD-1002"])
    shipments = value_signature(["SHP-9001", "SHP-9002"])
    order_expect = value_signature(["ORD-5000", "ORD-5001"])
    ship_expect = value_signature(["SHP-8000", "SHP-8001"])
    assert orders and shipments and order_expect and ship_expect
    assert signature_similarity(orders, order_expect) > signature_similarity(orders, ship_expect)


def test_type_profile_favors_email_over_phone():
    col = value_signature(["a@x.com", "b@y.org"])
    assert col is not None
    email = expectation_from_type("email")
    phone = expectation_from_type("phone")
    assert signature_similarity(col, email) > signature_similarity(col, phone)
