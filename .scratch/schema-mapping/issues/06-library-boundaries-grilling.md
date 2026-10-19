Type: grilling
Status: resolved

## Question

What is in v1 vs later? Options for v1 scope: mapping scores only, bundled type coercion, Pydantic integration, saved mapping YAML, optional embedding dependency as extra `[semantic]`.

Blocked by: none

## Answer

v1 ships: mapping engine, coercion helpers, Pydantic adapter, optional `[semantic]` FastEmbed header scorer. No LLM scorer. YAML persistence via optional extra.
