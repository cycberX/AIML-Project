import sys
import threading
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.ui.input_widget import FloatingInputWidget
from core.ui.confirm_dialog import ask_confirmation  # Import modal dialog
from core.intent_predictor import predict_intent
from core.executor import execute_all
from core.voice import speak
from core.spell_checker import check_spelling


def main():
    print("Starting Assistant...")
    speak("Assistant is ready.")

    input_widget = FloatingInputWidget()

    def gui_confirm(prompt: str, expected_response: str) -> bool:
        """Runs the confirmation modal on the UI thread."""
        is_ok = [False]
        event = threading.Event()

        def _open_dialog():
            is_ok[0] = ask_confirmation(prompt, expected_response, parent=input_widget.root)
            event.set()

        input_widget.root.after(0, _open_dialog)
        event.wait()
        return is_ok[0]

    def handle_user_command(raw_query: str):
        def _worker():
            print(f"\n[Raw Query]: {raw_query}")

            try:
                query = check_spelling(raw_query)
            except Exception:
                query = raw_query

            try:
                parsed = predict_intent(query)
                intents = parsed.get("intents", [])

                if not intents:
                    speak("No matching action recognized.")
                    return

                # Pass gui_confirm into execute_all
                summary = execute_all(
                    intents_payload=parsed,
                    confirm=gui_confirm,
                    stop_on_error=True
                )
                print("[Execution Result]:", summary)

            except Exception as e:
                print(f"[Error]: {e}")
                speak("An error occurred during execution.")

        threading.Thread(target=_worker, daemon=True).start()

    input_widget.on_submit = handle_user_command
    input_widget.run()


if __name__ == "__main__":
    main()