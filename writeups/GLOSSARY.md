# Glossary

Terms for the schema-mapping library. No implementation detail.

## Source schema

The column names and optional sample values from an incoming file or table. The user does not need to declare a rigid schema before import.

## Target schema

The canonical fields the application expects. Each field has an identifier, optional human labels, optional aliases, and optional expected semantic type.

## Field

One slot in the target schema. It is the unit of mapping.

## Column

One labeled series in the source data. It is the unit on the source side.

## Mapping

A proposed link from one source column to one target field, with a confidence score and an explanation of score factors.

## Semantic type

A coarse label for what values in a column mean. Examples: email, phone, date, freetext. Detection uses heuristics on sampled cell values.

## Header similarity

Similarity between source column name text and target field name or alias text. It uses string metrics and optional embedding cosine similarity.

## Value intent

Inference of field meaning from value patterns when headers are ambiguous. Example: two columns named `name` where one holds product SKUs and one holds person names.

## Scorer

A pluggable component that returns a partial score in `[0, 1]` or abstains. The engine combines scorer outputs.

## Score breakdown

A structured record of each scorer name, weight, raw score, and short reason. The host app can show this in a review UI.

## Assignment

The step that picks a global set of mappings when many column–field pairs have scores. It enforces business rules such as one-to-one links.

## Unmapped column

A source column with no accepted mapping above the threshold.

## Unmatched field

A target field with no source column assigned.

## Transform

A separate step that merges or splits columns. It is not the same as a one-to-one mapping.
