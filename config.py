
# Application settings
from pathlib import Path


VOICE_ENABLED = True
SYSTEM_FUNCTIONS_ENABLED = True
FILE_SYSTEM_ROOT = r"D:\Projects\test"
# Keep risky-action confirmation mandatory in execution_env.py.
# Do not use a config flag to bypass it.
PROJECT_ROOT = Path(__file__).resolve().parent
MODEL_PATH = PROJECT_ROOT / "modal" / "model.json"
INTENTS_PATH = PROJECT_ROOT / "modal" / "intents.json"
VOCABULARY_PATH = PROJECT_ROOT / "modal" / "vocabulary.json"
