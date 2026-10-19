from typing import Annotated

import pytest
from pydantic import BaseModel, EmailStr, Field

from tejtm.models import MappingConfig
from tejtm.pydantic_adapter import propose_and_apply, target_schema_from_model


class Customer(BaseModel):
    name: str = Field(title="Full Name")
    email: EmailStr = Field(json_schema_extra={"tejtm_aliases": ["Contact", "E-mail"], "semantic_type": "email"})


def test_target_schema_from_model():
    schema = target_schema_from_model(Customer)
    ids = {f.id for f in schema.fields}
    assert ids == {"name", "email"}


def test_propose_and_apply_maps_contact_to_email():
    rows = [
        {"Contact": "a@example.com", "Full Name": "Ada"},
        {"Contact": "b@example.com", "Full Name": "Bob"},
    ]
    result = propose_and_apply(Customer, rows, config=MappingConfig(min_confidence=0.4))
    assert result.column_rename.get("Contact") == "email"
    assert len(result.valid_rows) == 2
    assert result.valid_rows[0].email == "a@example.com"
