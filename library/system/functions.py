"""Windows PC controls for the AIML project.

Uses Python's standard library only. Some controls depend on Windows hardware/drivers.
This module deliberately does not auto-elevate or run arbitrary shell commands.
"""

import ctypes
import json
import os
import platform
import subprocess
import sys
import time
import winreg
from datetime import datetime
from pathlib import Path


# ----------------------------- helpers --------------------------------------
def _require_windows():
    if sys.platform != "win32":
        raise OSError("This function is supported on Windows only.")


def _run(command, timeout=15):
    """Run a fixed argument-list command, never through a shell."""
    _require_windows()
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=timeout,
            shell=False, check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except PermissionError as exc:
        raise PermissionError(
            "Windows denied permission. Try the related Windows Settings page; "
            "only run as administrator if you trust and specifically need this operation."
        ) from exc
    if result.returncode != 0:
        message = (result.stderr or result.stdout).strip()
        if "740" in message or "elevation" in message.lower() or "administrator" in message.lower():
            raise PermissionError(
                "Windows requires administrator privileges for this operation. "
                "This library will not elevate itself automatically."
            )
        raise RuntimeError(message or f"Command failed with exit code {result.returncode}.")
    return result.stdout.strip()


def _powershell(script, timeout=20):
    """Run an internally-authored PowerShell script (not user-provided code)."""
    return _run([
        "powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script
    ], timeout=timeout)


def _open_uri(uri):
    _require_windows()
    # URI values passed by this module are fixed constants.
    os.startfile(uri)
    return f"Opened {uri}."


def _open_settings_page(page):
    pages = {
        "sound": "ms-settings:sound",
        "display": "ms-settings:display",
        "brightness": "ms-settings:display",
        "bluetooth": "ms-settings:bluetooth",
        "network": "ms-settings:network",
        "wifi": "ms-settings:network-wifi",
        "airplane": "ms-settings:network-airplanemode",
        "hotspot": "ms-settings:network-mobilehotspot",
        "battery": "ms-settings:powersleep",
        "power": "ms-settings:powersleep",
        "night_light": "ms-settings:nightlight",
        "personalization": "ms-settings:personalization",
        "notifications": "ms-settings:notifications",
        "apps": "ms-settings:appsfeatures",
        "storage": "ms-settings:storagesense",
        "updates": "ms-settings:windowsupdate",
        "privacy": "ms-settings:privacy",
        "accessibility": "ms-settings:easeofaccess",
    }
    try:
        uri = pages[page]
    except KeyError as exc:
        raise ValueError("Unsupported Settings page.") from exc
    return _open_uri(uri)


def _media_key(vk):
    """Send one standard Windows multimedia key press."""
    _require_windows()
    user32 = ctypes.windll.user32
    KEYEVENTF_KEYUP = 0x0002
    user32.keybd_event(vk, 0, 0, 0)
    user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)


def _get_brightness_values():
    script = (
        "$b = @(Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightness "
        "-ErrorAction SilentlyContinue); "
        "if (!$b -or $null -eq $b[0].CurrentBrightness) { '{\"available\":false}' } "
        "else { $b | Select-Object InstanceName,CurrentBrightness | ConvertTo-Json -Compress }"
    )
    output = _powershell(script)
    if not output:
        return []
    data = json.loads(output)
    if isinstance(data, dict):
        if data.get("available") is False:
            return []
        data = [data]
    return data


def _set_brightness_wmi(value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("Brightness must be an integer from 0 to 100.")
    if not 0 <= value <= 100:
        raise ValueError("Brightness must be between 0 and 100.")
    script = (
        "$m = @(Get-CimInstance -Namespace root/WMI -ClassName WmiMonitorBrightnessMethods "
        "-ErrorAction SilentlyContinue); "
        "if (!$m) { throw 'Brightness control is not supported by this display/driver.' }; "
        f"$m | ForEach-Object {{ Invoke-CimMethod -InputObject $_ -MethodName WmiSetBrightness "
        f"-Arguments @{{Timeout=1; Brightness={value}}} | Out-Null }}; 'OK'"
    )
    _powershell(script)
    return f"Brightness set to {value}%."


# ----------------------------- volume ---------------------------------------
def mute_volume() -> str:
    """Toggle the Windows master mute state using the multimedia keyboard key."""
    _media_key(0xAD)  # VK_VOLUME_MUTE
    return "Mute/unmute toggle sent to Windows."


def volume_up(steps: int = 2) -> str:
    """Raise volume by sending standard media-key presses; each step is approximate."""
    if isinstance(steps, bool) or not isinstance(steps, int) or not 1 <= steps <= 25:
        raise ValueError("steps must be an integer between 1 and 25.")
    for _ in range(steps):
        _media_key(0xAF)  # VK_VOLUME_UP
    return f"Sent {steps} volume-up step(s)."


def volume_down(steps: int = 2) -> str:
    """Lower volume by sending standard media-key presses; each step is approximate."""
    if isinstance(steps, bool) or not isinstance(steps, int) or not 1 <= steps <= 25:
        raise ValueError("steps must be an integer between 1 and 25.")
    for _ in range(steps):
        _media_key(0xAE)  # VK_VOLUME_DOWN
    return f"Sent {steps} volume-down step(s)."


def set_volume(level: int) -> str:
    """Approximate a target volume using media keys (Windows exposes no simple stdlib setter)."""
    if isinstance(level, bool) or not isinstance(level, int) or not 0 <= level <= 100:
        raise ValueError("Volume level must be an integer between 0 and 100.")
    # Reset to minimum, then send approximately one step per 2 percentage points.
    for _ in range(50):
        _media_key(0xAE)
    for _ in range(round(level / 2)):
        _media_key(0xAF)
    if level == 0:
        return "Volume lowered to the minimum using media keys."
    return f"Sent volume adjustment for approximately {level}%. Check the Windows volume indicator."


def open_volume_settings() -> str:
    return _open_settings_page("sound")


def open_sound_settings() -> str:
    return _open_settings_page("sound")


# ----------------------------- brightness -----------------------------------
def get_brightness() -> dict:
    displays = _get_brightness_values()
    if not displays:
        return {"available": False, "message": "Brightness reading is unsupported on this display/driver."}
    return {"available": True, "displays": displays}


def set_brightness(value: int) -> str:
    return _set_brightness_wmi(value)


def increase_brightness(step: int = 10) -> str:
    if isinstance(step, bool) or not isinstance(step, int) or not 1 <= step <= 100:
        raise ValueError("step must be an integer between 1 and 100.")
    displays = _get_brightness_values()
    if not displays:
        raise RuntimeError("Brightness control is not available. Open Display Settings and check your display driver.")
    current = int(displays[0]["CurrentBrightness"])
    return _set_brightness_wmi(min(100, current + step))


def decrease_brightness(step: int = 10) -> str:
    if isinstance(step, bool) or not isinstance(step, int) or not 1 <= step <= 100:
        raise ValueError("step must be an integer between 1 and 100.")
    displays = _get_brightness_values()
    if not displays:
        raise RuntimeError("Brightness control is not available. Open Display Settings and check your display driver.")
    current = int(displays[0]["CurrentBrightness"])
    return _set_brightness_wmi(max(0, current - step))


def open_brightness_settings() -> str:
    return _open_settings_page("brightness")


def open_display_settings() -> str:
    return _open_settings_page("display")


# ----------------------------- dark/light theme -----------------------------
def _set_theme_value(name: str, value: int):
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
        winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, value)


def _broadcast_theme_change():
    # Tell Windows apps the current-user theme preference changed.
    HWND_BROADCAST = 0xFFFF
    WM_SETTINGCHANGE = 0x001A
    SMTO_ABORTIFHUNG = 0x0002
    result = ctypes.c_size_t()
    ctypes.windll.user32.SendMessageTimeoutW(
        HWND_BROADCAST, WM_SETTINGCHANGE, 0, "ImmersiveColorSet",
        SMTO_ABORTIFHUNG, 1000, ctypes.byref(result)
    )


def set_dark_mode() -> str:
    """Set current user's Windows app and system theme to dark; no admin needed."""
    _require_windows()
    _set_theme_value("AppsUseLightTheme", 0)
    _set_theme_value("SystemUsesLightTheme", 0)
    _broadcast_theme_change()
    return "Dark mode enabled for the current Windows user. Some apps may need reopening."


def set_light_mode() -> str:
    """Set current user's Windows app and system theme to light; no admin needed."""
    _require_windows()
    _set_theme_value("AppsUseLightTheme", 1)
    _set_theme_value("SystemUsesLightTheme", 1)
    _broadcast_theme_change()
    return "Light mode enabled for the current Windows user. Some apps may need reopening."


def toggle_dark_mode() -> str:
    _require_windows()
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            current, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
    except OSError:
        current = 1
    return set_dark_mode() if int(current) else set_light_mode()


def open_personalization_settings() -> str:
    return _open_settings_page("personalization")


def open_night_light_settings() -> str:
    return _open_settings_page("night_light")


# ----------------------------- screenshots / recording ----------------------
def take_screenshot() -> str:
    """Capture the primary display to the user's Pictures folder using .NET."""
    _require_windows()
    folder = Path.home() / "Pictures"
    if not folder.is_dir():
        folder = Path.home()
    target = folder / ("screenshot_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".png")
    safe_target = str(target).replace("'", "''")
    script = (
        "Add-Type -AssemblyName System.Windows.Forms; Add-Type -AssemblyName System.Drawing; "
        "$b=[System.Windows.Forms.Screen]::PrimaryScreen.Bounds; "
        "$bmp=New-Object System.Drawing.Bitmap($b.Width,$b.Height); "
        "$g=[System.Drawing.Graphics]::FromImage($bmp); "
        "$g.CopyFromScreen($b.X,$b.Y,0,0,$bmp.Size); "
        f"$bmp.Save('{safe_target}',[System.Drawing.Imaging.ImageFormat]::Png); "
        "$g.Dispose(); $bmp.Dispose(); 'OK'"
    )
    _powershell(script)
    return f"{target}"


def open_screen_recording() -> str:
    _require_windows()
    return _open_uri("ms-gamebar:")


def open_snipping_tool() -> str:
    _require_windows()
    subprocess.Popen(["explorer.exe", "ms-screenclip:"], shell=False)
    return "Opened the Windows screen capture interface."


# ----------------------------- Wi-Fi / connectivity -------------------------
def get_wifi_status() -> str:
    return _run(["netsh", "wlan", "show", "interfaces"])


def disconnect_wifi(interface: str = "Wi-Fi") -> str:
    if not isinstance(interface, str) or not interface.strip():
        raise ValueError("interface cannot be empty.")
    return _run(["netsh", "wlan", "disconnect", f"interface={interface}"]) or "Wi-Fi disconnect request completed."


def connect_wifi(profile: str, interface: str = "Wi-Fi") -> str:
    if not isinstance(profile, str) or not profile.strip():
        raise ValueError("profile cannot be empty.")
    if not isinstance(interface, str) or not interface.strip():
        raise ValueError("interface cannot be empty.")
    return _run(["netsh", "wlan", "connect", f"name={profile}", f"interface={interface}"]) or f"Connection requested for saved profile: {profile}"


def open_wifi_settings() -> str:
    return _open_settings_page("wifi")


def open_network_settings() -> str:
    return _open_settings_page("network")


def open_bluetooth_settings() -> str:
    return _open_settings_page("bluetooth")


def open_airplane_mode_settings() -> str:
    return _open_settings_page("airplane")


def open_hotspot_settings() -> str:
    return _open_settings_page("hotspot")


# ----------------------------- system information ---------------------------
def sleep(seconds: float) -> str:
    if isinstance(seconds, bool) or not isinstance(seconds, (int, float)):
        raise TypeError("seconds must be a number.")
    if not 0 <= seconds <= 3600:
        raise ValueError("seconds must be between 0 and 3600.")
    time.sleep(seconds)
    return f"Waited for {seconds} seconds."


def get_time() -> str:
    return datetime.now().strftime("%H:%M:%S")


def get_date() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def get_datetime() -> str:
    return datetime.now().isoformat(timespec="seconds")


def get_timestamp() -> float:
    return time.time()


def get_os_name() -> str:
    return platform.system()


def get_os_version() -> str:
    return platform.version()


def get_machine_type() -> str:
    return platform.machine()


def get_processor_name() -> str:
    return platform.processor() or "Unknown"


def get_python_version() -> str:
    return platform.python_version()


def get_username() -> str:
    return os.environ.get("USERNAME") or os.environ.get("USER") or "Unknown"


def get_cpu_count() -> int:
    return os.cpu_count() or 1


def get_process_id() -> int:
    return os.getpid()


def get_parent_process_id() -> int:
    return os.getppid()


def get_power_plan() -> str:
    return _run(["powercfg", "/getactivescheme"])


def get_battery_status() -> dict:
    output = _powershell(
        "$b=Get-CimInstance Win32_Battery -ErrorAction SilentlyContinue; "
        "if (!$b) { '{\"available\":false,\"message\":\"No battery reported\"}' } "
        "else { $b | Select-Object Name,EstimatedChargeRemaining,BatteryStatus,EstimatedRunTime | ConvertTo-Json -Compress }"
    )
    data = json.loads(output)
    return data


def open_battery_settings() -> str:
    return _open_settings_page("battery")


def open_power_settings() -> str:
    return _open_settings_page("power")


def lock_workstation() -> str:
    _require_windows()
    if not ctypes.windll.user32.LockWorkStation():
        raise OSError("Windows could not lock the workstation.")
    return "Workstation locked."


def open_task_manager() -> str:
    _require_windows()
    subprocess.Popen(["taskmgr.exe"], shell=False)
    return "Opened Task Manager."


def open_device_manager() -> str:
    _require_windows()
    # Device Manager commonly triggers WinError 740 on managed PCs. Do not force elevation.
    try:
        subprocess.Popen(["mmc.exe", "devmgmt.msc"], shell=False)
    except OSError as exc:
        if getattr(exc, "winerror", None) == 740:
            raise PermissionError("Device Manager requires elevation on this PC. Open it manually from Start and approve the Windows prompt if you have permission.") from exc
        raise
    return "Requested opening Device Manager. Windows may ask for administrator approval."


def open_settings() -> str:
    return _open_uri("ms-settings:")


def open_date_time_settings() -> str:
    return _open_uri("ms-settings:dateandtime")


def open_storage_settings() -> str:
    return _open_settings_page("storage")


def open_windows_update_settings() -> str:
    return _open_settings_page("updates")


def open_notifications_settings() -> str:
    return _open_settings_page("notifications")


def open_privacy_settings() -> str:
    return _open_settings_page("privacy")


def open_accessibility_settings() -> str:
    return _open_settings_page("accessibility")


def open_apps_settings() -> str:
    return _open_settings_page("apps")


# ----------------------------- registry metadata ----------------------------
def _entry(name, function, parameters=(), required=(), defaults=None,
           processing="Processing request...",
           speak_text="Working on request.", response="{result}",
           risk_level="low", confirmation_required=False):
    return {
        "name": name,
        "function": function,
        "parameters": list(parameters),
        "required": list(required),
        "defaults": dict(defaults or {}),
        "category": "system",
        "risk_level": risk_level,
        "confirmation_required": confirmation_required,
        "processing_command": processing,
        "speak": speak_text,
        "response": response,
    }


FUNCTIONS = [
    _entry("mute_volume", mute_volume, processing="Toggling mute...", speak_text="Changing mute state."),
    _entry("volume_up", volume_up, ["steps"], defaults={"steps": 2}, processing="Increasing volume..."),
    _entry("volume_down", volume_down, ["steps"], defaults={"steps": 2}, processing="Decreasing volume..."),
    _entry("set_volume", set_volume, ["level"], ["level"], processing="Adjusting volume..."),
    _entry("open_volume_settings", open_volume_settings),
    _entry("open_sound_settings", open_sound_settings),
    _entry("get_brightness", get_brightness),
    _entry("set_brightness", set_brightness, ["value"], ["value"], processing="Setting brightness..."),
    _entry("increase_brightness", increase_brightness, ["step"], defaults={"step": 10}, processing="Increasing brightness..."),
    _entry("decrease_brightness", decrease_brightness, ["step"], defaults={"step": 10}, processing="Decreasing brightness..."),
    _entry("open_brightness_settings", open_brightness_settings),
    _entry("open_display_settings", open_display_settings),
    _entry("set_dark_mode", set_dark_mode, processing="Enabling dark mode..."),
    _entry("set_light_mode", set_light_mode, processing="Enabling light mode..."),
    _entry("toggle_dark_mode", toggle_dark_mode, processing="Toggling theme..."),
    _entry("open_personalization_settings", open_personalization_settings),
    _entry("open_night_light_settings", open_night_light_settings),
    _entry("take_screenshot", take_screenshot, processing="Taking screenshot..."),
    _entry("open_screen_recording", open_screen_recording),
    _entry("open_snipping_tool", open_snipping_tool),
    _entry("get_wifi_status", get_wifi_status),
    _entry("disconnect_wifi", disconnect_wifi, ["interface"], defaults={"interface": "Wi-Fi"}, processing="Disconnecting Wi-Fi..."),
    _entry("connect_wifi", connect_wifi, ["profile", "interface"], ["profile"], defaults={"interface": "Wi-Fi"}, processing="Connecting to saved Wi-Fi profile..."),
    _entry("open_wifi_settings", open_wifi_settings),
    _entry("open_network_settings", open_network_settings),
    _entry("open_bluetooth_settings", open_bluetooth_settings),
    _entry("open_airplane_mode_settings", open_airplane_mode_settings),
    _entry("open_hotspot_settings", open_hotspot_settings),
    _entry("sleep", sleep, ["seconds"], ["seconds"], processing="Waiting..."),
    _entry("get_time", get_time),
    _entry("get_date", get_date),
    _entry("get_datetime", get_datetime),
    _entry("get_timestamp", get_timestamp),
    _entry("get_os_name", get_os_name),
    _entry("get_os_version", get_os_version),
    _entry("get_machine_type", get_machine_type),
    _entry("get_processor_name", get_processor_name),
    _entry("get_python_version", get_python_version),
    _entry("get_username", get_username),
    _entry("get_cpu_count", get_cpu_count),
    _entry("get_process_id", get_process_id),
    _entry("get_parent_process_id", get_parent_process_id),
    _entry("get_power_plan", get_power_plan),
    _entry("get_battery_status", get_battery_status),
    _entry("open_battery_settings", open_battery_settings),
    _entry("open_power_settings", open_power_settings),
    _entry("lock_workstation", lock_workstation, processing="Locking workstation...", speak_text="Locking the workstation."),
    _entry("open_task_manager", open_task_manager),
    _entry("open_device_manager", open_device_manager),
    _entry("open_settings", open_settings),
    _entry("open_date_time_settings", open_date_time_settings),
    _entry("open_storage_settings", open_storage_settings),
    _entry("open_windows_update_settings", open_windows_update_settings),
    _entry("open_notifications_settings", open_notifications_settings),
    _entry("open_privacy_settings", open_privacy_settings),
    _entry("open_accessibility_settings", open_accessibility_settings),
    _entry("open_apps_settings", open_apps_settings),
]

__all__ = ["FUNCTIONS"]
