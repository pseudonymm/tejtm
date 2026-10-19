Type: research
Status: resolved

## Question

Which string similarity metrics and normalization steps should the library combine for column-name matching?

## Answer

See [research-string-heuristics.md](../../../writeups/research-string-heuristics.md). Recommended stack: Unicode normalize, split camel/snake, tokenize, then max or weighted blend of Jaro-Winkler, Levenshtein ratio, token_sort_ratio, token_set_ratio; optional Jaccard on token sets.
