from tejtm.engine import MappingEngine
from tejtm.models import MappingConfig, ScorerResult, SourceColumn, SourceProfile, TargetField, TargetSchema
from tejtm.scorers.base import ScoringContext


class AlwaysPhoneScorer:
    name = "always_phone"

    def score(self, column, field, context: ScoringContext) -> ScorerResult | None:
        if field.id == "phone_number":
            return ScorerResult(self.name, 0.99, 1.0, "test hook")
        return None


def test_custom_scorer_registered():
    source = SourceProfile(columns=[SourceColumn("x")])
    target = TargetSchema(fields=[TargetField("phone_number")])
    engine = MappingEngine(scorers=(AlwaysPhoneScorer(),))
    result = engine.propose_mappings(source, target, config=MappingConfig(min_confidence=0.5))
    assert result.mappings[0].target_field == "phone_number"
