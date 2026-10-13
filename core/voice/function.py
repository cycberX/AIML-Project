import subprocess
import sys
import threading
import queue
import re

# Thread-safe speech queue
_speech_queue = queue.Queue()
_worker_started = False
_worker_lock = threading.Lock()


def _sanitize_for_powershell(text: str) -> str:
    """Clean text so PowerShell SAPI pronounces it cleanly without escaping errors."""
    text = text.replace("`", " ").replace('"', ' ').replace("$", " ")
    # Replace common underscores in function names with spaces (e.g. 'take_screenshot' -> 'take screenshot')
    text = text.replace("_", " ")
    # Collapse excess whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _speak_sync(message: str):
    """Executes Windows SAPI female voice synchronously."""
    clean_msg = _sanitize_for_powershell(message)
    if not clean_msg:
        return

    ps_script = f"""
    Add-Type -AssemblyName System.Speech;
    $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer;
    try {{
        $synth.SelectVoiceByHints([System.Speech.Synthesis.VoiceGender]::Female);
    }} catch {{
        try {{
            $synth.SelectVoice("Microsoft Zira Desktop");
        }} catch {{}}
    }}
    $synth.Rate = 0;
    $synth.Volume = 100;
    $synth.Speak("{clean_msg}");
    """

    try:
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=flags
        )
    except Exception:
        pass


def _speech_worker():
    """Background worker that guarantees only ONE voice speaks at any time in FIFO order."""
    while True:
        message = _speech_queue.get()
        if message is None:
            break
        try:
            _speak_sync(message)
        finally:
            _speech_queue.task_done()


def _ensure_worker():
    global _worker_started
    with _worker_lock:
        if not _worker_started:
            worker_thread = threading.Thread(target=_speech_worker, daemon=True)
            worker_thread.start()
            _worker_started = True


def speak(message: str, clear_previous: bool = False, wait: bool = False):
    """
    Queue a message to be spoken.
    If wait=True, blocks the current thread until the message finishes speaking.
    """
    if not message or not str(message).strip():
        return

    _ensure_worker()

    if clear_previous:
        while not _speech_queue.empty():
            try:
                _speech_queue.get_nowait()
                _speech_queue.task_done()
            except queue.Empty:
                break

    # If wait is requested, run directly on this thread so execution pauses until speech ends
    if wait:
        _speak_sync(str(message).strip())
    else:
        _speech_queue.put(str(message).strip())

def stop_speaking():
    """Flush pending speech items."""
    while not _speech_queue.empty():
        try:
            _speech_queue.get_nowait()
            _speech_queue.task_done()
        except queue.Empty:
            break