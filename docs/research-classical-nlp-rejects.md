# Classical NLP families that fail the column-mapping bar

Research note for **import column mapping** only. It lists named classical NLP families that fail the locked bar for tejtm, and the primary source that defines each family. It does not add scorers, and it does not time anything.

The locked bar for this note:

- The product job is column-to-field mapping. Joins, identity match, and named entity recognition are out of scope as product features.
- The core install is the Python standard library plus RapidFuzz. A network fetch at map time is a reject.
- FastEmbed is an existing optional extra. This note does not propose embedding changes.
- The yardstick is 17 fixture pairs at `min_confidence` 0.55. That set is not a customer corpus.

This note records **no** latency measurement of these families against RapidFuzz, on those 17 pairs or on about 50 column names. Where a family fails, the reason is a documented install or download, or a task that is not column-to-field mapping.

The string matcher already in the core is RapidFuzz. Its home page describes fuzzy string matching between two or more sequences, with a pure Python fallback when a C extension cannot be compiled ([RapidFuzz documentation](https://rapidfuzz.github.io/RapidFuzz/)). Installation is `pip install rapidfuzz`, with wheels for common platforms and no separate model download on that page ([Installation](https://rapidfuzz.github.io/RapidFuzz/Installation.html)).

---

## Rejected families

| Family | Defining source | Reject reason |
|--------|-----------------|---------------|
| Part-of-speech tagging | [NLTK book, ch. 5](https://www.nltk.org/book/ch05.html); [spaCy linguistic features](https://spacy.io/usage/linguistic-features#pos-tagging) | Network or model download. The usual taggers ship as separate data. A tagger that needs no download still emits part-of-speech tags, not field ids. |
| WordNet-style lexical database | [WordNet 1.6 README](https://wordnetcode.princeton.edu/README); [NLTK data index, package `wordnet`](https://www.nltk.org/nltk_data/) | Network or model download. The database is a corpus package, not part of the NLTK wheel. |
| HMM sequence labeling | [NLTK `nltk.tag.hmm`](https://www.nltk.org/api/nltk.tag.hmm.html) | Network or model download. Training takes labeled sequences, which in the NLTK path are downloaded corpora. |
| CRF sequence labeling | [Stanford CoreNLP NER, statistical models](https://stanfordnlp.github.io/CoreNLP/ner.html) | Network or model download. The published English models are trained CRF files inside the CoreNLP distribution. |
| Named entity recognition | [Stanford CoreNLP NER](https://stanfordnlp.github.io/CoreNLP/ner.html); [spaCy named entities](https://spacy.io/usage/linguistic-features#named-entities); [NLTK data, `maxent_ne_chunker`](https://www.nltk.org/nltk_data/) | Not column-to-field. The output is entity classes on text spans. The same pages also require a model download. |
| Record linkage toolkits | [Fellegi and Sunter, 1969](https://www.cs.cornell.edu/~shmat/courses/cs6434/fellegi-sunter.pdf); [dedupe documentation](https://docs.dedupe.io/en/latest/) | Not column-to-field. Both sources define identity match of records. |

---

## 1. Part-of-speech tagging

The NLTK book defines the task as labeling words with parts of speech, also called POS tagging or tagging. It treats tagging as sequence classification, where the tag at one point uses nearby words and tags ([Categorizing and Tagging Words](https://www.nltk.org/book/ch05.html)).

spaCy states the same job after tokenization. The part-of-speech section is marked as needing a model. A trained component holds binary data from examples, and the pipeline predicts which tag applies in context ([Part-of-speech tagging](https://spacy.io/usage/linguistic-features#pos-tagging)).

**Reject reason: network or model download.** Installing the NLTK package is not enough. The install page says to download the datasets and models a function needs, for example `python -m nltk.downloader popular` ([Installing NLTK](https://www.nltk.org/install.html)). The data index lists `averaged_perceptron_tagger` as its own zip under `taggers`, with a published compressed size of 2526731 bytes ([NLTK data](https://www.nltk.org/nltk_data/)). spaCy's model guide says the easiest download path is `python -m spacy download`, and that command selects a pipeline package compatible with the installed spaCy ([Models and languages](https://spacy.io/usage/models)). The English overview describes `en_core_web_sm` as a small pipeline that includes vocabulary, syntax, and entities ([English pipelines](https://spacy.io/models/en)).

The NLTK book also shows a regular-expression tagger built from patterns, without a downloaded model. That tagger still assigns part-of-speech tags. It does not map a column name to a canonical field id ([ch. 5](https://www.nltk.org/book/ch05.html)).

This note does not claim the tagger is slower than RapidFuzz. No timing was run.

## 2. WordNet-style lexical databases

The WordNet 1.6 README, served from Princeton's `wordnetcode.princeton.edu`, calls WordNet an online lexical reference system. Word forms use ordinary spelling. Meanings are synonym sets, lists of word forms that can replace each other in some context. Lexical relations hold between forms, and semantic relations hold between meanings ([README](https://wordnetcode.princeton.edu/README)). The same host lists version directories from 1.2 through 3.0 as downloadable trees ([index](https://wordnetcode.princeton.edu/)).

The HTML home page `https://wordnet.princeton.edu/` returned HTTP 403 during this research. The NLTK data index still points package `wordnet` version 3.0 at `http://wordnet.princeton.edu/`, with copyright "WordNet 3.0 Copyright 2006 by Princeton University", and package `wordnet31` version 3.1 with the 2011 Princeton copyright ([NLTK data](https://www.nltk.org/nltk_data/)). NLTK's own book describes the included English WordNet as a semantically oriented dictionary, with 155,287 words and 117,659 synonym sets, and points the original description to Fellbaum, 1998 ([Accessing Text Corpora](https://www.nltk.org/book/ch02.html)). The NLTK how-to loads it as `nltk.corpus.wordnet`, which is a corpus reader ([Sample usage for wordnet](https://www.nltk.org/howto/wordnet.html)).

**Reject reason: network or model download.** The data page says NLTK ships corpora and models separately from the library install. Manual install means downloading a zip from the data index and unpacking it under `nltk_data` ([Installing NLTK Data](https://www.nltk.org/data.html)). `wordnet` is one of those corpus zips ([NLTK data](https://www.nltk.org/nltk_data/)). A fetch of that database at map time fails the core-install bar.

Synonym lookup is also not a column-to-field decision procedure in these sources. They define a lexical database. They do not define a header-to-field assigner.

## 3. HMM sequence labeling

NLTK documents `nltk.tag.hmm.HiddenMarkovModelTagger` as a hidden Markov model used to assign a label sequence to sequential data, or to score a label sequence and an observation sequence. States emit observations, and the state sequence is hidden ([nltk.tag.hmm](https://www.nltk.org/api/nltk.tag.hmm.html)). `HiddenMarkovModelTagger.train` takes `labeled_sequence`, described as a list of sentences represented as tuples, plus optional unlabeled sentences ([same page](https://www.nltk.org/api/nltk.tag.hmm.html)).

**Reject reason: network or model download.** The documented training input is labeled sequences. In the NLTK distribution those sequences live in corpora that the data downloader fetches, not in the library wheel ([Installing NLTK Data](https://www.nltk.org/data.html)). The tagger's return value is a tagger over tokens. It is not a map from column names to field ids.

No measurement in this note compares HMM training or Viterbi tagging with RapidFuzz on about 50 names.

## 4. CRF sequence labeling

Stanford CoreNLP's named entity annotator says it recognizes named entities in text, principally with one or more machine learning sequence models ([Named Entity Recognition](https://stanfordnlp.github.io/CoreNLP/ner.html)). The statistical-model section says a series of trained CRFs runs on each sentence. Those CRFs are trained on large tagged data sets, score the whole sequence, and pick a tag sequence. The default English model paths on that page include:

- `edu/stanford/nlp/models/ner/english.all.3class.distsim.crf.ser.gz`
- `edu/stanford/nlp/models/ner/english.muc.7class.distsim.crf.ser.gz`
- `edu/stanford/nlp/models/ner/english.conll.4class.distsim.crf.ser.gz`

**Reject reason: network or model download.** Using the CRF path means shipping those serialized model files with CoreNLP. That is a model distribution, not stdlib plus RapidFuzz. The labels are entity classes such as `PERSON`, `LOCATION`, and `ORGANIZATION`, not canonical import fields ([same page](https://stanfordnlp.github.io/CoreNLP/ner.html)).

The older Stanford CRF-NER software page, `https://nlp.stanford.edu/software/CRF-NER.html`, did not return a readable document in this session. The CoreNLP NER page is the first-party description used here.

This note does not report a CRF runtime against RapidFuzz.

## 5. Named entity recognition

CoreNLP defines NER as recognition of named entities such as person and company names, plus numerical and temporal classes for English, using the sequence models above ([CoreNLP NER](https://stanfordnlp.github.io/CoreNLP/ner.html)).

spaCy defines a named entity as a real-world object with a name, such as a person, country, product, or book title. The library asks a model for a prediction, and the spans are `Doc.ents` ([Named Entity Recognition](https://spacy.io/usage/linguistic-features#named-entities)). Package names on the model overview use `core` for a pipeline that includes tagging, parsing, lemmatization, and named entity recognition ([Models](https://spacy.io/models)).

NLTK publishes `maxent_ne_chunker` as "ACE Named Entity Chunker (Maximum entropy)", a separate zip, with a published compressed size of 13404747 bytes ([NLTK data](https://www.nltk.org/nltk_data/)).

**Reject reason: not column-to-field.** The locked product bar excludes NER as a feature. These sources label spans in running text with entity types. They do not assign spreadsheet headers to schema fields. Each implementation above also fails the dependency bar, because the recognizer is a downloaded model.

## 6. Record linkage

Fellegi and Sunter, *A Theory for Record Linkage*, Journal of the American Statistical Association, vol. 64, no. 328, December 1969, pp. 1183-1210, develop a model for recognizing records in two files that represent identical persons, objects, or events. A comparison of recorded characteristics yields one of three decisions. Those decisions are link, non-link, or possible link. The introduction frames the work as comparing file A with file B to find pairs that refer to the same population unit, including master-file maintenance and merging files ([Cornell reprint PDF](https://www.cs.cornell.edu/~shmat/courses/cs6434/fellegi-sunter.pdf)).

dedupe's documentation describes the library as machine learning for de-duplication and entity resolution on structured data. The stated jobs are removing duplicate rows from a spreadsheet of names and addresses, linking a customer list to an order history without a shared id, and grouping campaign contributions that come from the same person ([dedupe 3.0.2](https://docs.dedupe.io/en/latest/)). A variable definition "describes the records that you want to match" and is a collection of field comparators such as `String` on a record key ([Variable Definitions](https://docs.dedupe.io/en/latest/Variable-definition.html)). PyPI describes the same package as data deduplication and entity resolution ([dedupe on PyPI](https://pypi.org/project/dedupe/)).

**Reject reason: not column-to-field.** Both sources define identity match between records. The tejtm map assigns a source column name to a canonical field. It does not decide whether two rows are the same person or object. dedupe also trains on human labels to set weights and blocking rules ([dedupe home](https://docs.dedupe.io/en/latest/)). That training loop is a different product from an unattended header score.

---

## What stays in scope

RapidFuzz remains the documented string scorer for header text. Families in the table above stay out of the core map. Nothing in this note is a timing result, and nothing here is a reason to change the FastEmbed extra.
