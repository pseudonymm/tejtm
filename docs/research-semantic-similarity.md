# Research: CPU-light semantic similarity for column names and table semantics

**Scope:** Matching and ranking **short text** (column headers, glossary terms, schema labels) across languages on CPU, and how that relates to **value-based** column semantic typing (Sherlock, Sato, Doduo).

**Primary sources:** [`primary-sources.md`](./primary-sources.md) (URLs and paper IDs).

---

## 1. Problem framing

Two related tasks are often conflated:

| Task | Input | Output | Typical method |
|------|--------|--------|----------------|
| **Header / metadata similarity** | Column name (+ optional table name, neighbors) | Similarity score or nearest neighbors in a target schema | Dense embeddings + cosine similarity |
| **Semantic column typing** | Cell **values** (± table context) | One of ~78 DBpedia-style types (e.g. `city`, `birth_date`) | Feature-based NN (Sherlock), hybrid + CRF (Sato), fine-tuned Transformer (Doduo) |

Header-only matching is cheap and privacy-friendly but ambiguous (`id`, `date`, `name`). Value-based typing disambiguates using distributions in the column ([SHERLOCK], [SATO], [DODUO]). A practical pipeline often uses **embeddings for candidate generation** and **value features or a small classifier** when sample values exist.

---

## 2. CPU-light multilingual dense embeddings

### 2.1 `paraphrase-multilingual-MiniLM-L12-v2`

The default workhorse for **multilingual paraphrase-style similarity** in the Sentence Transformers ecosystem ([SBERT-MULTI], [ST-PMM]):

- **Architecture:** 12-layer multilingual BERT (MiniLM footprint), mean pooling → **384-dimensional** vectors.
- **Context:** **128 tokens** max sequence length ([ST-PMM]) — ample for column headers.
- **Languages:** 50+ languages via multilingual knowledge distillation from a monolingual teacher ([REIMERS-KD], [SBERT-MULTI]).
- **Size:** ~118M parameters; ~471 MB in PyTorch/safetensors form on the Hub ([ST-PMM]); FastEmbed lists **~0.22 GB** ONNX package ([FASTEMBED-MODELS]).

**Why it fits column names:** Headers are short phrases; mean-pooled sentence embeddings handle multi-token names (`customer_id`, `fecha_nacimiento`) better than per-word averaging. Cross-lingual alignment lets `postal_code`, `PLZ`, and `codigo_postal` land nearby without language tags ([REIMERS-KD]).

**Inference:** PyTorch + `sentence-transformers` is simplest for prototyping; for production CPU paths, prefer ONNX (below).

### 2.2 FastEmbed (ONNX Runtime, no PyTorch)

FastEmbed ([FASTEMBED-README]) is a **Python embedding library** built on **ONNX Runtime** ([ONNXRUNTIME]): few dependencies, no GPU requirement, aimed at serverless and batch indexing ([FASTEMBED-DOCS]).

Relevant properties for this project:

- Ships pre-exported ONNX for **`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`** (384-dim; [FASTEMBED-MODELS]).
- Also lists **`ParaphraseMLMiniLML12V2Q`** — quantized variant in the Rust/API catalog (smaller/faster; same semantic family).
- Supports **custom ONNX** registration (pooling, normalization, `model_file` for `model_O4.onnx` / qint8 variants) ([FASTEMBED-README]).

**Typical usage pattern:** `TextEmbedding(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")` → `list(model.embed(texts))` → cosine similarity on **L2-normalized** vectors (FastEmbed normalizes by default for many models; verify per model card).

**When to choose FastEmbed over raw `sentence-transformers`:** Deployments that must avoid PyTorch/CUDA, cold-start latency, or bundle size; batch encoding with ONNX threading.

### 2.3 Other CPU-friendly multilingual options (same stack)

From the supported-models table ([FASTEMBED-MODELS]) — trade accuracy for size/speed:

| Model | Dim | Approx. size (GB) | Notes |
|-------|-----|-------------------|--------|
| `BAAI/bge-small-en-v1.5` | 384 | 0.067 | English-only; very small |
| `sentence-transformers/all-MiniLM-L6-v2` | 384 | 0.09 | English; 256 tokens |
| **`paraphrase-multilingual-MiniLM-L12-v2`** | **384** | **0.22** | **Balanced multilingual default** |
| `paraphrase-multilingual-mpnet-base-v2` | 768 | 1.0 | Heavier multilingual |
| `intfloat/multilingual-e5-small` | 384 | (see Hub) | Strong MTEB family; **instruction prefixes** |

### 2.4 `intfloat/multilingual-e5-small` (ONNX + prefixes)

[E5-SMALL] is a **12-layer, 384-dim** multilingual embedder (100 XLM-R–family languages; low-resource may degrade ([E5-SMALL])). Official **ONNX** artifacts include full, `O4`, and **qint8** checkpoints ([E5-SMALL-ONNX]) — attractive for CPU.

**Important for similarity:** E5 models are trained with **asymmetric** `query:` / `passage:` prefixes ([E5-REPORT], [E5-SMALL]). For **symmetric** header↔header matching, use the **same prefix** for both sides (commonly `passage: ` for both, or `query: ` for both) so vectors are comparable. For header→glossary retrieval (query = unknown column, passage = glossary entry), use `query:` on the column and `passage:` on glossary text.

FastEmbed can load `multilingual-e5-small` via `add_custom_model` ([FASTEMBED-README]).

### 2.5 ONNX models (general)

Pattern used across [ST-PMM-ONNX], [E5-SMALL-ONNX], and FastEmbed:

1. Export or download ONNX + tokenizer assets.
2. Run via ONNX Runtime (optionally **quantized** graphs for AVX512 VNNI).
3. Apply the same pooling + normalization as the PyTorch SentenceTransformer.

**paraphrase-multilingual-MiniLM ONNX** reports 384-dim, 128 max length, ~0.44 GB on disk ([ST-PMM-ONNX]).

---

## 3. GloVe for column **headers** (and how Sherlock used GloVe differently)

### 3.1 GloVe basics

GloVe learns **word** vectors from global word–word co-occurrence statistics ([GLOVE]). Vectors are **static** (one vector per word type), typically 50–300 dimensions ([GLOVE-VECTORS]).

### 3.2 Header matching with GloVe

**Procedure (classic):** Tokenize header → lookup vectors → **average** (or weighted average) → cosine similarity. Works for single-token, dictionary-covered words; weak on:

- **OOV** (`cust_id`, SKU codes, non-Latin scripts not in a 6B/42B English-centric table).
- **Multi-word semantics** where composition is not additive (`birth_date` vs `date_of_birth`).
- **Cross-lingual** alignment unless you use multilingual GloVe or separate monolingual tables per language.

Short-text similarity with word embeddings is a known setting ([SHORT-TEXT-KENTER]); modern **sentence** embedders generally dominate on phrase-level schema matching ([ST-PMM], [REIMERS-KD]).

**CPU profile:** GloVe inference is a hash lookup + small vector ops — **extremely cheap** per header, but you pay **memory** for the lexicon (e.g. 400K×300 floats) and **engineering** for tokenization/normalization.

### 3.3 Sherlock’s GloVe use (values, not headers)

Sherlock does **not** embed column **names** for its main classifier. It labels columns using **header–ontology string matching** for training data construction, then predicts type from **value-derived features** ([SHERLOCK]):

| Feature block | Count | Role |
|---------------|-------|------|
| Global statistics | 27 | Cardinality, entropy, numeric character ratios, etc. |
| Character distributions | 960 | ASCII char counts aggregated with moments |
| **Pretrained word embeddings** | **200** | **50-dim GloVe (6B token, 400K vocab)** per value, aggregated mean/mode/median/variance across column |
| Paragraph vectors (PV-DBOW) | 400 | Column-as-document over cell values |

So GloVe in Sherlock is a **value-content** signal for English-like tokens in cells, not a header-similarity model. Headers are weak supervision only ([SHERLOCK]).

---

## 4. Value-based column semantics: Sherlock → Sato → Doduo

### 4.1 Shared setup

- **Type system:** ~**78** semantic types from DBpedia / T2Dv2 gold standard ([T2D-GOLD], [SHERLOCK], [SATO]).
- **Training corpus:** Large web/open tables via **VizNet** ([VIZNET]) and WebTables-derived columns ([SHERLOCK], [SATO]).

### 4.2 Sherlock ([SHERLOCK])

- **Model:** Multi-input **deep neural network** over hand-crafted features (1,588 dims); not an end-to-end Transformer on raw text.
- **Supervision:** ~686K columns where semantic type matched column header string.
- **Reported result:** Support-weighted **F1 ≈ 0.89** on the filtered 78-type task ([SHERLOCK]).
- **Takeaway for tejtm:** Reusing Sherlock features requires **sample values** and English-centric GloVe coverage; heavy feature pipeline vs. a single embedding call.

### 4.3 Sato ([SATO])

- **Extension:** Same Sherlock-style column encoder + **topic model** on table-wide tokens + **structured prediction** (CRF) over columns using **neighboring column types** and global table context ([SATO]).
- **Reported result:** Support-weighted **F1 0.925**, macro **F1 0.735** ([SATO], VLDB PDF).
- **Open source:** [SATO-CODE].
- **Takeaway:** If you have **whole tables**, context fixes many ambiguous types; overhead is higher than pairwise header similarity.

### 4.4 Doduo ([DODUO])

- **Paradigm shift:** Fine-tuned **BERT-base** (12-layer) over **serialized tables**; column representations from token-level Transformer states; **multi-task** heads for column type and column relation ([DODUO]).
- **Input:** Primarily **cell values** in context (headers may be missing in the motivating setting); as few as **8 tokens per column** still competitive ([DODUO]).
- **Reported result:** New SOTA on WikiTable and VizNet benchmarks at time of publication (e.g. up to **+4.0%** column-type and **+11.9%** relation micro-F1 over prior SOTA on WikiTable — [DODUO]).
- **Toolbox:** [DODUO-CODE].
- **Takeaway:** Best when you can run a **Transformer forward pass per table** and need relations (`birthplace_of`, etc.), not just similarity scores. **Not CPU-light** relative to MiniLM-on-headers.

### 4.5 Header-only annotation (no cell access)

When only metadata is available, literature moves toward **Column Vocabulary Association (CVA)** and glossary matching ([CVA], [GLOSSARY-LLM]) — embedding or LLM-based matching of headers to ontology terms **without** reading rows. That aligns with the **embedding track** in §2, not with Sherlock/Sato/Doduo value encoders.

---

## 5. Recommendations for short column-name similarity (CPU)

### 5.1 Default stack

1. **Model:** `paraphrase-multilingual-MiniLM-L12-v2` via **FastEmbed** ([FASTEMBED-MODELS], [ST-PMM]).
2. **Similarity:** Cosine on normalized embeddings; optional score threshold + top-k.
3. **Preprocessing (cheap disambiguation):**
   - Normalize: lowercase, strip, split `snake_case` / `camelCase` → tokens.
   - Optionally prepend table name: `"{table_name} | {column_name}"` (mirrors glossary work that uses surrounding metadata — [GLOSSARY-LLM]).
4. **Quantization:** If latency dominates, try FastEmbed’s **Q** variant or E5 **qint8** ONNX ([E5-SMALL-ONNX]).

### 5.2 When to upgrade models

| Signal | Action |
|--------|--------|
| English-only, extreme size budget | `bge-small-en-v1.5` ([FASTEMBED-MODELS]) |
| Need best multilingual retrieval quality at 384-d | `multilingual-e5-small` with correct **prefixes** ([E5-SMALL]) |
| Have labeled header pairs | Fine-tune MiniLM with contrastive loss (same family as [REIMERS-KD]) |

### 5.3 When to add value-based typing

| Signal | Action |
|--------|--------|
| Ambiguous headers, values available | Sample N cell values → run **Sherlock-style features** or a small classifier; or table-level **Doduo** if GPU/batch acceptable ([SHERLOCK], [DODUO]) |
| Full tables, need SOTA semantic types | **Sato** or **Doduo** ([SATO], [DODUO]) |
| Only headers + ontology | Embeddings + CVA-style glossary ranking ([CVA]) |

### 5.4 GloVe niche

Use GloVe ([GLOVE]) when you need **minimal dependencies**, **English** headers with good dictionary coverage, and **microsecond** lookups — e.g. a baseline or ensemble feature (Sherlock used this pattern on **values**, not names). For multilingual header matching, prefer [ST-PMM] or [E5-SMALL].

---

## 6. Implementation sketch (header similarity)

```python
from fastembed import TextEmbedding

model = TextEmbedding(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

def embed_header(name: str, table: str | None = None) -> list[float]:
    text = f"{table} | {name}" if table else name
    return list(model.embed([text]))[0]

# cosine_similarity(embed_header("cust_id"), embed_header("customer_identifier"))
```

For E5, prefix both strings consistently, e.g. `f"passage: {text}"` ([E5-SMALL]).

---

## 7. Open questions / validation

- **Benchmark on your schema:** Measure precision@k on real column→glossary pairs; MTEB scores do not target 1–3 token headers.
- **OOV / codes:** Embedding models handle subword tokenization better than GloVe; still test internal codes (`sku_`, `flg_`).
- **Hybrid:** Embed headers for recall, re-rank with regex/dtype/value sketches when a data sample exists (Sherlock character features are strong on numeric types — [SHERLOCK]).

---

## References (short form)

See [`primary-sources.md`](./primary-sources.md) for full links. Key citations: [ST-PMM], [FASTEMBED-MODELS], [REIMERS-KD], [E5-SMALL], [GLOVE], [SHERLOCK], [SATO], [DODUO], [CVA].
