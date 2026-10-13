
import json
import re
from pathlib import Path
from collections import defaultdict

from config import MODEL_PATH, VOCABULARY_PATH


SYSTEM_WORDS = {
    "increase", "increases", "increasing",
    "decrease", "decreases", "decreasing",
    "volume", "brightness", "brighten", "dim",
    "screen", "display", "sound", "mute", "unmute",
    "raise", "lower", "turn", "up", "down",
    "the", "and", "set", "maximum", "minimum",
    "higher", "open", "close", "start", "stop",
    "create", "delete", "remove", "rename", "find",
    "search", "file", "folder", "directory",
    "calculate", "add", "addition", "subtract",
    "multiply", "multiplication", "divide", "division",
    "power", "modulo", "remainder", "number",
    "numbers", "plus", "minus", "times", "equal",
    "equals", "settings", "brightness", "volume",
    "increase", "decrease", "please", "what", "is",
    "my", "computer", "system", "lock", "unlock",
    "restart", "shutdown", "sleep", "wake"
}


def edit_distance(a, b):
    """Calculate Levenshtein distance without external packages."""
    previous = list(range(len(b) + 1))

    for i, char_a in enumerate(a, start=1):
        current = [i]

        for j, char_b in enumerate(b, start=1):
            insert_cost = current[j - 1] + 1
            delete_cost = previous[j] + 1
            replace_cost = previous[j - 1] + (char_a != char_b)

            current.append(
                min(insert_cost, delete_cost, replace_cost)
            )

        previous = current

    return previous[-1]


class SpellChecker:
    def __init__(
        self,
        vocabulary_path=VOCABULARY_PATH,
        model_path=MODEL_PATH,
        extra_words=None
    ):
        self.words = set()

        # Load vocabulary.json.
        vocabulary_path = Path(vocabulary_path)

        if vocabulary_path.is_file():
            with vocabulary_path.open("r", encoding="utf-8") as file:
                vocabulary_data = json.load(file)

            if isinstance(vocabulary_data, list):
                vocabulary = vocabulary_data

            elif isinstance(vocabulary_data, dict):
                vocabulary = vocabulary_data.get(
                    "vocabulary",
                    vocabulary_data.get(
                        "words",
                        list(vocabulary_data.keys())
                    )
                )

            else:
                raise ValueError(
                    "Unsupported vocabulary.json format."
                )

            if isinstance(vocabulary, dict):
                vocabulary = list(vocabulary.keys())

            if isinstance(vocabulary, list):
                self._add_words(vocabulary)

        # Also load vocabulary embedded in the intent model.
        model_path = Path(model_path)

        if model_path.is_file():
            with model_path.open("r", encoding="utf-8") as file:
                model_data = json.load(file)

            model_vocabulary = (
                model_data.get("vectorizer", {}).get("vocabulary", [])
            )

            if isinstance(model_vocabulary, dict):
                model_vocabulary = list(model_vocabulary.keys())

            if isinstance(model_vocabulary, list):
                self._add_words(model_vocabulary)

        # Include common system-command words.
        self._add_words(SYSTEM_WORDS)

        # Include any caller-provided words.
        if extra_words:
            self._add_words(extra_words)

        if not self.words:
            raise ValueError(
                "No vocabulary words found. Check vocabulary.json "
                "and MODEL_PATH."
            )

        self.by_length = defaultdict(list)

        for word in self.words:
            self.by_length[len(word)].append(word)

    def _add_words(self, words):
        """Add valid alphabetic words to the dictionary."""
        for word in words:
            if not isinstance(word, str):
                continue

            word = word.lower().strip()

            if re.fullmatch(r"[a-z]+", word):
                self.words.add(word)

    def suggest(self, word, limit=5):
        """Return possible spelling corrections."""
        if not isinstance(word, str) or not word.isalpha():
            return []

        if limit <= 0:
            return []

        original = word.lower()

        if original in self.words:
            return []

        max_distance = 1 if len(original) <= 3 else 2
        candidates = []

        min_length = max(1, len(original) - max_distance)
        max_length = len(original) + max_distance

        for length in range(min_length, max_length + 1):
            for candidate in self.by_length.get(length, []):
                distance = edit_distance(original, candidate)

                if distance <= max_distance:
                    candidates.append((distance, candidate))

        candidates.sort(key=lambda item: (item[0], item[1]))

        return [
            candidate
            for _, candidate in candidates[:limit]
        ]

    def check(self, text):
        """
        Check spelling and propose corrections.
        Does not automatically apply corrections to the user's input.
        """
        if not isinstance(text, str):
            raise TypeError("Text must be a string.")

        corrections = []

        for match in re.finditer(r"[A-Za-z]+", text):
            original_word = match.group(0)
            suggestions = self.suggest(original_word)

            if not suggestions:
                continue

            best = suggestions[0]
            best_distance = edit_distance(
                original_word.lower(), best
            )

            # Do not suggest a correction when multiple candidates
            # have the same minimum edit distance.
            tied = (
                len(suggestions) > 1
                and edit_distance(
                    original_word.lower(), suggestions[1]
                ) == best_distance
            )

            if tied:
                continue

            corrections.append({
                "original": original_word,
                "suggestion": best,
                "start": match.start(),
                "end": match.end()
            })

        corrected = text

        # Apply replacements right to left to preserve offsets.
        for item in reversed(corrections):
            start = item["start"]
            end = item["end"]
            replacement = item["suggestion"]
            original_word = text[start:end]

            if original_word.isupper():
                replacement = replacement.upper()
            elif original_word[:1].isupper():
                replacement = replacement.capitalize()

            corrected = (
                corrected[:start]
                + replacement
                + corrected[end:]
            )

        return {
            "original": text,
            "corrected": corrected,
            "has_suggestions": bool(corrections),
            "corrections": corrections
        }


_checker = None


def get_spell_checker():
    global _checker

    if _checker is None:
        _checker = SpellChecker()

    return _checker


def check_spelling(text):
    return get_spell_checker().check(text)


def suggest_corrections(word, limit=5):
    return get_spell_checker().suggest(word, limit=limit)
