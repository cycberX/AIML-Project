import json
import math
import re
from collections import Counter
from pathlib import Path

try:
    from config import MODEL_PATH, INTENTS_PATH
except ImportError:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    MODEL_PATH = PROJECT_ROOT / "modal" / "model.json"
    INTENTS_PATH = PROJECT_ROOT / "modal" / "intents.json"


def tokenize(text):
    return re.findall(r"[a-z0-9]+(?:'[a-z0-9]+)?", text.lower())


def softmax(values):
    maximum = max(values)
    exps = [math.exp(v - maximum) for v in values]
    total = sum(exps)
    if total == 0:
        raise ValueError("Cannot calculate softmax probabilities.")
    return [v / total for v in exps]


class IntentPredictor:
    def __init__(self, model_path=MODEL_PATH, intents_path=INTENTS_PATH):
        self.model_path = Path(model_path)
        self.intents_path = Path(intents_path)
        self._load_model()

    def _load_model(self):
        if not self.model_path.is_file():
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
        if not self.intents_path.is_file():
            raise FileNotFoundError(f"Intent names file not found: {self.intents_path}")

        with self.model_path.open("r", encoding="utf-8") as f:
            self.model = json.load(f)
        with self.intents_path.open("r", encoding="utf-8") as f:
            self.intents = json.load(f)

        vectorizer = self.model.get("vectorizer", {})
        self.vocabulary = vectorizer.get("vocabulary", [])
        self.idf_weights = vectorizer.get("idf_weights", [])
        self.dense_layers = self.model.get("dense_layers", [])
        self.word_to_id = {word: idx for idx, word in enumerate(self.vocabulary)}

    def _vectorize(self, text):
        features = [0.0] * len(self.vocabulary)
        counts = Counter(tokenize(text))
        for word, count in counts.items():
            idx = self.word_to_id.get(word)
            if idx is not None:
                features[idx] = count * self.idf_weights[idx]
        return features

    @staticmethod
    def _dense_forward(inputs, layer):
        kernel = layer["kernel"]
        bias = layer["bias"]
        activation = layer["activation"]
        outputs = []

        for col, offset in enumerate(bias):
            val = offset
            for row, in_val in enumerate(inputs):
                if in_val != 0.0:
                    val += in_val * kernel[row][col]

            if activation == "relu":
                val = max(0.0, val)
            elif activation == "sigmoid":
                if val >= 0:
                    val = 1.0 / (1.0 + math.exp(-min(val, 709.0)))
                else:
                    exp_val = math.exp(max(val, -709.0))
                    val = exp_val / (1.0 + exp_val)
            outputs.append(val)

        if activation == "softmax":
            outputs = softmax(outputs)
        return outputs

    def _predict_single(self, text):
        """Internal helper to classify a single action phrase."""
        features = self._vectorize(text)
        if not any(features):
            return None, 0.0

        values = features
        for layer in self.dense_layers:
            values = self._dense_forward(values, layer)

        if self.dense_layers[-1].get("activation") != "softmax":
            values = softmax(values)

        best_idx = max(range(len(values)), key=lambda i: values[i])
        return self.intents[best_idx], round(float(values[best_idx]), 4)

    @staticmethod
    def _extract_parameters(intent, clause):
        """Extracts numerical arguments, paths, or names from the clause."""
        params = {}
        numbers = [
            int(n) if n.lstrip('-').isdigit() else float(n)
            for n in re.findall(r'-?\d+(?:\.\d+)?', clause)
        ]
        name_match = re.search(r'(?:name|called|named|file|folder)\s+([a-zA-Z0-9_\-\.]+)', clause, re.IGNORECASE)
        file_match = re.search(r'\b([a-zA-Z0-9_\-]+\.[a-zA-Z0-9]+)\b', clause)

        if intent in ["divide", "multiply", "add", "subtract"]:
            if len(numbers) >= 2:
                params["a"] = numbers[0]
                params["b"] = numbers[1]
            elif len(numbers) == 1:
                params["a"] = numbers[0]
        elif intent == "clamp":
            if len(numbers) >= 3:
                params["number"] = numbers[0]
                params["minimum_value"] = numbers[1]
                params["maximum_value"] = numbers[2]
        elif "file" in str(intent):
            if file_match:
                params["path"] = file_match.group(1)
            elif name_match:
                params["path"] = name_match.group(1)
        elif "folder" in str(intent):
            if name_match:
                params["folder_name"] = name_match.group(1)

        return params

    def predict(self, prompt: str):
        """
        Splits compound prompts (e.g., 'A and then B', 'A and B') into multiple
        intents and extracts parameters for each.
        """
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("Prompt must be a non-empty string.")

        # Split on coordinating sequence conjunctions
        clauses = re.split(r'\s+(?:and\s+then|and|then|\,)\s+', prompt, flags=re.IGNORECASE)

        intents_result = []
        exec_idx = 0

        for clause in clauses:
            clause = clause.strip()
            if not clause:
                continue

            intent, conf = self._predict_single(clause)
            if intent:
                params = self._extract_parameters(intent, clause)
                intents_result.append({
                    "index": exec_idx,
                    "intent": intent,
                    "parameters": params,
                    "execution_index": exec_idx,
                    "confidence": conf
                })
                exec_idx += 1

        # If splitting didn't yield anything (e.g. all out-of-vocab), try entire prompt
        if not intents_result:
            intent, conf = self._predict_single(prompt)
            if intent:
                intents_result.append({
                    "index": 0,
                    "intent": intent,
                    "parameters": self._extract_parameters(intent, prompt),
                    "execution_index": 0,
                    "confidence": conf
                })

        return {
            "prompt": prompt,
            "intents": intents_result
        }


_predictor = None

def get_predictor():
    global _predictor
    if _predictor is None:
        _predictor = IntentPredictor()
    return _predictor

def predict_intent(prompt: str):
    return get_predictor().predict(prompt)