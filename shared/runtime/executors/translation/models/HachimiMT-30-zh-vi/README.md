---
language:
- zh
- vi
pipeline_tag: translation
tags:
- translation
- zh-vi
- chinese-vietnamese
- marianmt
- machine-translation
library_name: transformers
base_model: none
datasets:
- chi-vi/hirashiba-mt-zh2vi-b-filtered
---

# Hachimi MT 30 zh-vi

Fast Chinese to Vietnamese Marian-style machine translation model.

## Intended Use

- Chinese -> Vietnamese web novel / fiction translation.
- Fast local or server inference where a small model is preferred.
- This is an experimental release; output should still be reviewed for high-stakes or publication use.

## Model Details

- Architecture: Marian seq2seq
- Parameters: ~32M
- Tokenizer: SentencePiece source/target tokenizer
- Suggested decoding: `num_beams=1`, `max_length=512`

## Benchmark Snapshot

FLORES-200 `zho_Hans -> vie_Latn` devtest, decoded with `num_beams=1`,
`max_length=512`.

| Evaluation set | Rows | BLEU | chrF | Chinese-character leak rows |
|---|---:|---:|---:|---:|
| FLORES-200 devtest | 1,012 | 14.29 | 37.30 | 0 |

This is a general-domain benchmark; it is useful for public comparability but
does not fully reflect web-novel style or domain terminology.

Metric notes:

- BLEU and chrF are automatic reference-based metrics. Higher is generally
  better, but human quality may differ, especially for fiction/web-novel style.
- Chinese-character leak rows counts outputs that still contain Chinese
  characters after translation. Lower is better.

## Quick Start

```python
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

model_id = "ngocdang83/HachimiMT-30-zh-vi"
tok = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForSeq2SeqLM.from_pretrained(model_id)

text = "他抬头看向远处的山门。"
inputs = tok(text, return_tensors="pt", truncation=True, max_length=512)
out = model.generate(**inputs, max_length=512, num_beams=1)
print(tok.decode(out[0], skip_special_tokens=True))
```

## Notes

- This model prioritizes speed and small footprint.
- A CTranslate2 INT8 runtime is available in `ct2-int8_float32/` for faster CPU inference.
- Known hard cases include rare proper nouns, idioms, and highly domain-specific OOD terminology.
- For production-style usage, pair with reviewed glossary/guard layers where appropriate.