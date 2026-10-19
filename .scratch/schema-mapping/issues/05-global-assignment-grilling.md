Type: grilling
Status: resolved

## Question

How should the engine assign source columns to target fields when scores compete? Options: (A) one-to-one Hungarian on a cost matrix, (B) greedy best-first with locks, (C) allow many-to-one and one-to-many with explicit transform hooks, (D) leave unmapped below threshold.

Blocked by: none

## Answer

Hungarian one-to-one assignment on the score matrix. Pairs below `min_confidence` stay unmapped.
