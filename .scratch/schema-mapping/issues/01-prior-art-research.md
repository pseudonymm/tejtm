Type: research
Status: resolved

## Question

What prior art, academic matchers, and Python libraries define the state of the art for automatic column/schema mapping?

## Answer

See [research-prior-art.md](../../../writeups/research-prior-art.md). Key pattern: composite scorers plus global assignment; validation libraries (Pandera, Frictionless) sit after mapping. Close competitors: Valentine (research matchers), infermap (multi-scorer + Hungarian), tabmodel (import-focused fuzzy headers).
