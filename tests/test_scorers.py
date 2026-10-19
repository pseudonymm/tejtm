from tejtm.models import MappingConfig, SourceColumn, TargetField
from tejtm.scorers.base import ScoringContext
from tejtm.scorers.exact import ExactNameScorer
from tejtm.scorers.fuzzy import FuzzyNameScorer
from tejtm.scorers.semantic_type import SemanticTypeScorer
from tejtm.models import TypeGuess


def test_exact_name_scorer_matches_alias():
    scorer = ExactNameScorer()
    col = SourceColumn("phone")
    field = TargetField("phone_number", aliases=("phone",))
    ctx = ScoringContext(MappingConfig())
    result = scorer.score(col, field, ctx)
    assert result is not None
    assert result.score == 1.0


def test_fuzzy_name_phone_number():
    scorer = FuzzyNameScorer()
    col = SourceColumn("phone")
    field = TargetField("phone_number")
    ctx = ScoringContext(MappingConfig())
    result = scorer.score(col, field, ctx)
    assert result is not None
    assert result.score >= 0.7


def test_semantic_type_contact_to_email():
    scorer = SemanticTypeScorer()
    col = SourceColumn("contact", samples=("a@x.com", "b@y.com"))
    field = TargetField("email", expected_semantic_type="email")
    ctx = ScoringContext(
        MappingConfig(),
        column_types={"contact": TypeGuess("email", 1.0)},
    )
    result = scorer.score(col, field, ctx)
    assert result is not None
    assert result.score > 0.5
