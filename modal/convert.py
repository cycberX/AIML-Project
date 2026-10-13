import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
model_path = PROJECT_ROOT / "modal" / "model.json"
intents_path = PROJECT_ROOT / "modal" / "intents.json"

print(f"Reading {model_path}...")
with open(model_path, "r", encoding="utf-8") as f:
    old = json.load(f)

# 1. Rebuild Vocabulary & IDF arrays
vocab_dict = old.get("vocab", {})
# Sort words in order of their integer token index
sorted_vocab = sorted(vocab_dict.keys(), key=lambda w: vocab_dict[w])

idf_dict = old.get("idf", {})
idf_weights = [
    float(idf_dict.get(str(i), idf_dict.get(i, 1.0)))
    for i in range(len(sorted_vocab))
]

# 2. Extract Intent Names list
id2intent = old.get("id2intent", {})
intents_list = [id2intent[str(i)] for i in range(len(id2intent))]

# 3. Transpose PyTorch [out_features, in_features] to [in_features, out_features]
weights = old.get("weights", {})

# Find fc1 weights
w1_key = next((k for k in weights if "fc1.weight" in k or "0.weight" in k), "fc1.weight")
b1_key = next((k for k in weights if "fc1.bias" in k or "0.bias" in k), "fc1.bias")

# Find output layer weights (fc2 or last layer)
w2_key = next((k for k in weights if "fc2.weight" in k or "4.weight" in k), "fc2.weight")
b2_key = next((k for k in weights if "fc2.bias" in k or "4.bias" in k), "fc2.bias")

w1 = weights[w1_key]
b1 = weights[b1_key]
w2 = weights[w2_key]
b2 = weights[b2_key]

# Transpose matrices: [rows][cols] -> [cols][rows]
kernel_1 = [[w1[row][col] for row in range(len(w1))] for col in range(len(w1[0]))]
kernel_2 = [[w2[row][col] for row in range(len(w2))] for col in range(len(w2[0]))]

# 4. Assemble the schema required by pure_python_tfidf_dense_v1
new_model = {
    "format": "pure_python_tfidf_dense_v1",
    "vectorizer": {
        "vocabulary": sorted_vocab,
        "idf_weights": idf_weights
    },
    "dense_layers": [
        {
            "activation": "relu",
            "kernel": kernel_1,
            "bias": b1
        },
        {
            "activation": "linear",
            "kernel": kernel_2,
            "bias": b2
        }
    ]
}

# 5. Overwrite model.json and write intents.json
with open(model_path, "w", encoding="utf-8") as f:
    json.dump(new_model, f)

with open(intents_path, "w", encoding="utf-8") as f:
    json.dump(intents_list, f)

print("Conversion complete!")
print(f"Updated: {model_path}")
print(f"Created: {intents_path}")