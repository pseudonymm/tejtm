from tejtm.assignment import assign_one_to_one


def test_assignment_respects_min_confidence():
    scores = [[0.9, 0.1], [0.1, 0.85]]
    assigned = assign_one_to_one(scores, min_confidence=0.5)
    assert assigned[0] == (0, 0)
    assert assigned[1] == (1, 1)


def test_assignment_leaves_weak_pairs_unmapped():
    scores = [[0.2, 0.1]]
    assigned = assign_one_to_one(scores, min_confidence=0.55)
    assert assigned[0] is None
