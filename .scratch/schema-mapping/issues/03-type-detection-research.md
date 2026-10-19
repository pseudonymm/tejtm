Type: research
Status: resolved

## Question

How should the library heuristically detect semantic column types from sample values?

## Answer

See [research-type-detection.md](../../../writeups/research-type-detection.md). Use layered detectors (boolean, integer, float, email, url, phone, uuid, date, datetime, time, currency, freetext) with per-type confidence from match rate on samples.
