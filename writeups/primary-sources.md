# Primary sources (bibliography)

Canonical URLs and identifiers for claims in `research-semantic-similarity.md`. Prefer these over secondary summaries.

## Sentence embeddings (multilingual, CPU)

| ID | Resource | URL |
|----|----------|-----|
| [ST-PMM] | Model card: `paraphrase-multilingual-MiniLM-L12-v2` | https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 |
| [ST-PMM-ONNX] | ONNX port (384-dim, 128 tokens) | https://huggingface.co/onnx-models/paraphrase-multilingual-MiniLM-L12-v2-onnx |
| [SBERT-MULTI] | SBERT docs: multilingual pretrained models | https://www.sbert.net/docs/sentence_transformer/pretrained_models.html |
| [REIMERS-KD] | Reimers & Gurevych, multilingual knowledge distillation (arXiv:2004.09813) | https://arxiv.org/abs/2004.09813 |
| [E5-SMALL] | Model card: `intfloat/multilingual-e5-small` | https://huggingface.co/intfloat/multilingual-e5-small |
| [E5-SMALL-ONNX] | Official ONNX weights (incl. quantized) | https://huggingface.co/intfloat/multilingual-e5-small/tree/main/onnx |
| [E5-REPORT] | Wang et al., Multilingual E5 technical report (arXiv:2402.05672) | https://arxiv.org/abs/2402.05672 |

## FastEmbed / ONNX Runtime inference

| ID | Resource | URL |
|----|----------|-----|
| [FASTEMBED-README] | Qdrant FastEmbed README | https://github.com/qdrant/fastembed/blob/main/README.md |
| [FASTEMBED-DOCS] | Qdrant FastEmbed documentation | https://qdrant.tech/documentation/fastembed/ |
| [FASTEMBED-MODELS] | Supported models table (size, dim, license) | https://qdrant.github.io/fastembed/examples/Supported_Models/ |
| [ONNXRUNTIME] | ONNX Runtime (inference engine used by FastEmbed) | https://onnxruntime.ai/ |

## GloVe and short-text similarity

| ID | Resource | URL |
|----|----------|-----|
| [GLOVE] | Pennington, Socher, Manning — GloVe (EMNLP 2014) | https://nlp.stanford.edu/pubs/glove.pdf |
| [GLOVE-VECTORS] | Stanford GloVe download / format | https://nlp.stanford.edu/projects/glove/ |
| [SHORT-TEXT-KENTER] | Kenter & De Rijke, short text similarity with word embeddings (CIKM 2015) | https://doi.org/10.1145/2806416.2806475 |

## Column semantic typing (value-based)

| ID | Resource | URL |
|----|----------|-----|
| [SHERLOCK] | Hulsebos et al., Sherlock (KDD 2019; arXiv:1905.10688) | https://doi.org/10.1145/3292500.3330993 · https://arxiv.org/abs/1905.10688 |
| [SATO] | Zhang et al., Sato (PVLDB 13(11), 2020; arXiv:1911.06311) | https://doi.org/10.14778/3407790.3407793 · https://arxiv.org/abs/1911.06311 · https://www.vldb.org/pvldb/vol13/p1835-zhang.pdf |
| [DODUO] | Suhara et al., Doduo (SIGMOD 2022; arXiv:2104.01785) | https://doi.org/10.1145/3514221.3517906 · https://arxiv.org/abs/2104.01785 |
| [DODUO-CODE] | Doduo toolbox (Megagon Labs) | https://github.com/megagonlabs/doduo |
| [SATO-CODE] | Sato (Megagon Labs) | https://github.com/megagonlabs/sato |

## Header-only / metadata matching (related)

| ID | Resource | URL |
|----|----------|-----|
| [CVA] | Column Vocabulary Association — dataless tables (arXiv:2409.13709) | https://arxiv.org/abs/2409.13709 |
| [GLOSSARY-LLM] | Matching table metadata to business glossaries (OM 2023) | https://arxiv.org/abs/2309.11506 |

## Corpora and type systems referenced by Sherlock/Sato/Doduo

| ID | Resource | URL |
|----|----------|-----|
| [T2D-GOLD] | T2Dv2 gold standard (DBpedia ↔ WebTables headers) | http://webdatacommons.org/webtables/goldstandardV2.html |
| [VIZNET] | VizNet table corpus (Hu et al., 2019) | https://arxiv.org/abs/1907.03629 |
