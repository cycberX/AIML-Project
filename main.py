import sys
import threading
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.ui.input_widget import FloatingInputWidget
from core.ui.output_widget import FloatingOutputWidget
from core.intent_predictor import predict_intent
from core.executor import execute_all
from core.voice import speak
from core.spell_checker import check_spelling  # Spell checker integration


# Whitelist of intents that genuinely require a visual popup
VISUAL_OUTPUT_INTENTS = {
    "take_screenshot",
    "screenshot",
    "list_directory",
    "list_files",
    "list_folders",
    "find_file",
    "get_datetime",
    "get_time",
    "get_date",
}


def display_result_if_needed(action_name: str, result_data, output_widget: FloatingOutputWidget):
    """
    Renders the output widget ONLY when visual feedback is necessary.
    Keeps the widget hidden for standard background executions.
    """
    if result_data is None:
        return

    # 1. Date & Time
    if any(k in action_name for k in ["time", "date", "datetime"]):
        output_widget.render_datetime(result_data)

    # 2. Screenshots / Images
    elif "screenshot" in action_name or (
        isinstance(result_data, str) and result_data.lower().endswith((".png", ".jpg", ".bmp", ".gif"))
    ):
        output_widget.render_image(str(result_data), caption="Screenshot Result")

    # 3. File or Directory listings
    elif any(k in action_name for k in ["list", "find_file"]) or (isinstance(result_data, list) and len(result_data) > 0):
        items = result_data if isinstance(result_data, list) else [result_data]
        output_widget.render_file_list(title=action_name.replace("_", " ").title(), items=items)

    # All other actions (e.g. open_settings, volume, delete_file) do NOT open the popup


def main():
    print("Starting Assistant...")
    speak("Assistant is ready.")

    # Main input bar
    input_widget = FloatingInputWidget()

    # Output widget (hidden by default)
    output_widget = FloatingOutputWidget(parent=input_widget.root)
    output_widget.hide()

    def handle_user_command(raw_query: str):
        def _worker():
            print(f"\n[Raw Query]: {raw_query}")

            # 1. Correct spelling before prediction
            try:
                corrected_query = check_spelling(raw_query)
                if corrected_query != raw_query:
                    print(f"[Spell-Corrected]: {corrected_query}")
                query = corrected_query
            except Exception:
                query = raw_query

            # 2. Predict intent
            try:
                parsed = predict_intent(query)
                intents = parsed.get("intents", [])

                if not intents:
                    speak("No matching action recognized.")
                    return

                # 3. Execute actions
                summary = execute_all(intents_payload=parsed, stop_on_error=True)
                results = summary.get("results", [])

                # 4. Show output window ONLY for visual results
                for res in results:
                    if res.get("status") == "success":
                        action_name = res.get("function", "")
                        data = res.get("result")

                        # If intent is in visual list, pop up the output widget
                        if action_name in VISUAL_OUTPUT_INTENTS or isinstance(data, list):
                            input_widget.root.after(
                                0,
                                lambda a=action_name, d=data: display_result_if_needed(a, d, output_widget)
                            )

            except Exception as e:
                print(f"[Error]: {e}")
                speak("An error occurred during execution.")

        threading.Thread(target=_worker, daemon=True).start()

    input_widget.on_submit = handle_user_command
    input_widget.run()


if __name__ == "__main__":
    main()