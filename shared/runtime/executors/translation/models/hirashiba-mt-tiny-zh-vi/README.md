---
library_name: transformers
license: gpl-3.0
datasets:
- Moleys/mtl-zh2vi
- Moleys/mtl-zh2vi-b
language:
- zh
- vi
metrics:
- bleu
pipeline_tag: translation
---

# Hirashiba ^^

![Hirashiba](https://wsrv.nl/?url=https://img.hagihagi.ru/file/c6f95084f23f9e80&w=225)

Hira's intelligence, Shiba's speed

Hirashiba-MT-zh-vi is a model used for gatekeeping and refilling water.

## Usage

```python
                                                              
from transformers import MarianMTModel, MarianTokenizer

model_name = "chi-vi/hirashiba-mt-tiny-zh-vi"
tokenizer = MarianTokenizer.from_pretrained(model_name)
model = MarianMTModel.from_pretrained(model_name)

def translate(lines):
    inputs = tokenizer(lines, return_tensors="pt", padding=True)
    translated = model.generate(**inputs)
    return [tokenizer.decode(t, skip_special_tokens=True) for t in translated]

with open('sample.txt') as f:
    src_text = f.readlines()

import time

start = time.time()
translated = translate(src_text)
end = time.time()

print(translated)
print(end - start)
```

