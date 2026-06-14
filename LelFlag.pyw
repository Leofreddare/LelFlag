import json
import os
import re
import subprocess
import sys
import tkinter as tk
from pathlib import Path
import customtkinter as ctk
from PIL import Image


# --- App Configuration ---
APP_NAME = "LelFlag"
APP_VERSION = "1.1"
AUTHOR = "Leofreddare"

# --- Paths ---
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "data"
ROBLOX_DATA_DIR = DATA_DIR / "roblox"
ROBLOX_STUDIO_DATA_DIR = DATA_DIR / "robloxstudio"
ASSETS_DIR = SCRIPT_DIR / "assets"
ICON_DIR = ASSETS_DIR / "icons"

CATEGORIES_FILE = ROBLOX_DATA_DIR / "categories.json"
MODULES_FILE = ROBLOX_DATA_DIR / "modules.json"
APP_ICON_PATH = SCRIPT_DIR / "icon.ico"


def prepare_dialog_window(window):
    """Prepare iconless popup windows.

    CTkToplevel sets its own title-bar icon shortly after creation on Windows.
    Making these dialogs borderless prevents both the default Tk icon flash and
    the later CustomTkinter icon swap, while keeping the main app icon unchanged.
    """
    try:
        window.withdraw()
    except Exception:
        pass

    try:
        window.overrideredirect(True)
    except Exception:
        pass

    # On Windows this also stops the dialog from appearing as a separate taskbar
    # item if the window manager briefly processes it before overrideredirect.
    try:
        if sys.platform.startswith("win"):
            window.attributes("-toolwindow", True)
    except Exception:
        pass


def make_window_draggable(window, *widgets):
    drag_data = {"x": 0, "y": 0}

    def start_move(event):
        drag_data["x"] = event.x
        drag_data["y"] = event.y

    def do_move(event):
        x = window.winfo_x() + event.x - drag_data["x"]
        y = window.winfo_y() + event.y - drag_data["y"]
        window.geometry(f"+{x}+{y}")

    for widget in widgets:
        try:
            widget.bind("<Button-1>", start_move)
            widget.bind("<B1-Motion>", do_move)
        except Exception:
            pass


def center_dialog_window(window, parent):
    try:
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        x = parent_x + (parent_w - width) // 2
        y = parent_y + (parent_h - height) // 2
        window.geometry(f"{width}x{height}+{max(x, 0)}+{max(y, 0)}")
    except Exception:
        pass


def show_dialog_window(window, parent):
    try:
        window.transient(parent)
    except Exception:
        pass
    try:
        window.update_idletasks()
        center_dialog_window(window, parent)
        window.deiconify()
        window.lift(parent)
        window.focus_force()
    except Exception:
        pass
    try:
        window.grab_set()
    except Exception:
        pass
    try:
        window.focus_force()
    except Exception:
        pass

# Dark UI colors
DARK_WINDOW = "#05070a"
DARK_PANEL = "#090d13"
DARK_PANEL_ALT = "#0d1118"
DARK_TOP_BAR = "#070a0f"
DARK_HOVER = "#171d29"
DARK_SELECTED = "#202838"
DARK_TEXT = "#f2f5f9"
DARK_MUTED_TEXT = "#aab4c2"
DARK_BORDER = "#273244"
DARK_ACCENT = "#3b82f6"

# Roblox shortcut path resolution
APPDATA = os.getenv("APPDATA")
LOCALAPPDATA = os.getenv("LOCALAPPDATA")
if not APPDATA:
    sys.exit(1)

START_MENU_ROBLOX_DIR = Path(APPDATA) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Roblox"
CLIENT_CONFIG = {
    "roblox": {
        "label": "Roblox",
        "data_dir": ROBLOX_DATA_DIR,
        "shortcut_name": "Roblox Player.lnk",
        "exe_name": "RobloxPlayerBeta.exe",
    },
    "robloxstudio": {
        "label": "Roblox Studio",
        "data_dir": ROBLOX_STUDIO_DATA_DIR,
        "shortcut_name": "Roblox Studio.lnk",
        "exe_name": "RobloxStudioBeta.exe",
    },
}


# --- JSON/Data Helpers ---
def load_json_file(path: Path, fallback):
    if not path.exists():
        return fallback

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def copy_json_if_missing(source: Path, destination: Path):
    if not source.exists() or destination.exists():
        return

    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    except Exception:
        pass


def ensure_client_data_files():
    ROBLOX_DATA_DIR.mkdir(parents=True, exist_ok=True)
    ROBLOX_STUDIO_DATA_DIR.mkdir(parents=True, exist_ok=True)

    legacy_categories = DATA_DIR / "categories.json"
    legacy_modules = DATA_DIR / "modules.json"

    copy_json_if_missing(legacy_categories, ROBLOX_DATA_DIR / "categories.json")
    copy_json_if_missing(legacy_modules, ROBLOX_DATA_DIR / "modules.json")

    copy_json_if_missing(ROBLOX_DATA_DIR / "categories.json", ROBLOX_STUDIO_DATA_DIR / "categories.json")
    copy_json_if_missing(ROBLOX_DATA_DIR / "modules.json", ROBLOX_STUDIO_DATA_DIR / "modules.json")


def sanitize_json_string(value: str) -> str:
    """Remove trailing commas before } or ] so json.loads() will not fail."""
    value = re.sub(r",\s*}", "}", value)
    value = re.sub(r",\s*]", "]", value)
    return value


def normalize_id(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value)
    return value.strip("_")


def load_categories() -> list[dict]:
    data = load_json_file(CATEGORIES_FILE, {"categories": []})
    categories = data.get("categories", [])

    if not isinstance(categories, list):
        raise ValueError("categories.json must contain a 'categories' list.")

    clean_categories = []

    for category in categories:
        if not isinstance(category, dict):
            continue

        category_id = category.get("id")
        name = category.get("name")
        icon = category.get("icon", "")

        if not category_id:
            raise ValueError("Every category in categories.json needs an 'id'.")

        if not name:
            raise ValueError(f"Category '{category_id}' needs a 'name'.")

        if icon and not str(icon).lower().endswith(".png"):
            raise ValueError(f"Icon for category '{category_id}' must be a .png file: {icon}")

        clean_categories.append(category)

    return clean_categories


def load_modules() -> list[dict]:
    data = load_json_file(MODULES_FILE, {"modules": []})
    modules = data.get("modules", [])

    if not isinstance(modules, list):
        raise ValueError("modules.json must contain a 'modules' list.")

    return modules


def load_ctk_image(path_text: str | None, size=(24, 24)):
    if not path_text:
        return None

    path = SCRIPT_DIR / path_text

    if not path.exists():
        return None

    try:
        image = Image.open(path)
        return ctk.CTkImage(light_image=image, dark_image=image, size=size)
    except Exception:
        return None


def parse_module_flags(module: dict) -> dict:
    flags = module.get("flags", {})

    if isinstance(flags, dict):
        return flags

    if isinstance(flags, str):
        return json.loads(sanitize_json_string(flags))

    raise ValueError(f"Module '{module.get('name', module.get('id'))}' has invalid flags data.")


# --- Roblox Helpers ---
def resolve_shortcut(path: Path) -> str | None:
    if not path.exists():
        return None

    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        f'$Shell = New-Object -COM WScript.Shell; $Shortcut = $Shell.CreateShortcut("{path}"); Write-Output $Shortcut.TargetPath'
    ]

    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            startupinfo=startupinfo
        )
        stdout, stderr = process.communicate(timeout=5)

        if process.returncode == 0 and stdout.strip():
            return stdout.strip()

        return None
    except subprocess.TimeoutExpired:
        process.kill()
        return None
    except Exception:
        return None


def find_roblox_executable(client_key: str = "roblox") -> str | None:
    config = CLIENT_CONFIG.get(client_key, CLIENT_CONFIG["roblox"])

    # Roblox Studio should use the same shortcut-based lookup as Roblox Player,
    # but with Roblox Studio.lnk:
    # %appdata%\Microsoft\Windows\Start Menu\Programs\Roblox\Roblox Studio.lnk
    if client_key == "robloxstudio":
        shortcut_path = START_MENU_ROBLOX_DIR / config["shortcut_name"]
        target_path = resolve_shortcut(shortcut_path)

        if target_path and os.path.exists(target_path):
            return str(Path(target_path))

        return None

    potential_paths = [
        Path(os.getenv("LOCALAPPDATA", "")) / "Roblox" / "Versions",
        Path(os.getenv("ProgramFiles(x86)", "")) / "Roblox" / "Versions",
        Path(os.getenv("ProgramFiles", "")) / "Roblox" / "Versions",
    ]

    latest_exe = None
    latest_time = 0

    for base_path in potential_paths:
        if not base_path.is_dir():
            continue

        try:
            for item in base_path.iterdir():
                potential_exe = item / config["exe_name"]

                if potential_exe.is_file():
                    modified_time = potential_exe.stat().st_mtime

                    if modified_time > latest_time:
                        latest_time = modified_time
                        latest_exe = potential_exe
        except OSError:
            pass

    if latest_exe:
        return str(latest_exe)

    shortcut_path = START_MENU_ROBLOX_DIR / config["shortcut_name"]
    target_path = resolve_shortcut(shortcut_path)

    if target_path and os.path.exists(target_path):
        target = Path(target_path)
        if target.name.lower() == config["exe_name"].lower():
            return str(target)

        sibling_exe = target.parent / config["exe_name"]
        if sibling_exe.is_file():
            return str(sibling_exe)

        return str(target)

    return None


def build_client_paths(client_key: str, target_path: str) -> dict[str, str | None]:
    exe_dir = Path(target_path).parent
    settings_dir = exe_dir / "ClientSettings"
    settings_json = settings_dir / "ClientAppSettings.json"

    return {
        "exe_path": target_path,
        "settings_dir": str(settings_dir),
        "settings_json": str(settings_json),
    }


# --- Main App ---
class LelFlagApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(APP_NAME)
        self.geometry("900x680")
        self.minsize(760, 520)
        self.configure(fg_color=DARK_WINDOW)

        if APP_ICON_PATH.exists():
            try:
                self.iconbitmap(APP_ICON_PATH)
            except Exception:
                pass

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.selected_client: str = "roblox"
        self.client_paths: dict[str, dict[str, str | None]] = {
            key: {"exe_path": None, "settings_dir": None, "settings_json": None}
            for key in CLIENT_CONFIG
        }
        self.roblox_path: str | None = None
        self.client_settings_dir: str | None = None
        self.client_settings_json_path: str | None = None

        self.current_flags: dict = {}
        self.categories: list[dict] = []
        self.modules: list[dict] = []
        self.category_modules: dict[str, list[dict]] = {}

        self.icons: dict[str, object] = {}
        self.sidebar_buttons: dict[str, ctk.CTkButton] = {}
        self.category_frames: dict[str, ctk.CTkFrame] = {}
        self.var_map: dict[str, tuple[ctk.BooleanVar, dict]] = {}

        ensure_client_data_files()
        self._set_data_paths(self.selected_client)
        self._load_plugin_data()
        self._detect_installation(self.selected_client)

    def _set_data_paths(self, client_key: str):
        global CATEGORIES_FILE, MODULES_FILE

        config = CLIENT_CONFIG.get(client_key, CLIENT_CONFIG["roblox"])
        CATEGORIES_FILE = config["data_dir"] / "categories.json"
        MODULES_FILE = config["data_dir"] / "modules.json"

    def _load_plugin_data(self):
        try:
            self.categories = load_categories()
            self.modules = load_modules()
        except Exception:
            self.destroy()
            return

        valid_category_ids = {category["id"] for category in self.categories}

        self.category_modules = {category_id: [] for category_id in valid_category_ids}

        for module in self.modules:
            category_id = module.get("categoryId")

            if category_id not in valid_category_ids:
                continue

            if module.get("disabled", False):
                continue

            self.category_modules[category_id].append(module)

        self.icons = {}
        for category in self.categories:
            icon_size = tuple(category.get("iconSize", [24, 24]))
            self.icons[category["id"]] = load_ctk_image(category.get("icon"), icon_size)


    def _detect_installation(self, client_key: str = "roblox"):
        target_path = find_roblox_executable(client_key)

        if not target_path or not os.path.exists(target_path):
            self.destroy()
            return

        self.client_paths[client_key] = build_client_paths(client_key, target_path)
        self._activate_client_paths(client_key)

        if not os.path.exists(self.client_settings_json_path):
            self._force_create_json()

        if self._load_json_data():
            self._create_main_ui()
        else:
            self._force_create_json()
            self._load_json_data()
            self._create_main_ui()

    def _activate_client_paths(self, client_key: str):
        paths = self.client_paths.get(client_key, {})
        self.roblox_path = paths.get("exe_path")
        self.client_settings_dir = paths.get("settings_dir")
        self.client_settings_json_path = paths.get("settings_json")

    def _force_create_json(self):
        if not self.client_settings_json_path:
            return

        os.makedirs(os.path.dirname(self.client_settings_json_path), exist_ok=True)

        with open(self.client_settings_json_path, "w", encoding="utf-8") as file:
            json.dump({}, file, indent=4)

    def _create_main_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar_frame = ctk.CTkFrame(self, width=215, corner_radius=0, fg_color=DARK_PANEL)
        self.sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsw")
        self.sidebar_frame.grid_rowconfigure(100, weight=1)

        self.sidebar_buttons = {}
        row_index = 0

        for category in self.categories:
            category_id = category["id"]
            button = ctk.CTkButton(
                self.sidebar_frame,
                text=category.get("name", category_id),
                image=self.icons.get(category_id),
                compound="left",
                command=lambda cid=category_id: self._switch_category(cid),
                anchor="w",
                font=ctk.CTkFont(size=13),
                fg_color="transparent",
                hover_color=DARK_HOVER,
                text_color=DARK_TEXT
            )
            button.grid(row=row_index, column=0, padx=10, pady=5, sticky="ew")
            self.sidebar_buttons[category_id] = button
            row_index += 1


        self.reset_modules_button = ctk.CTkButton(
            self.sidebar_frame,
            text="Reset Modules",
            command=self._open_reset_modules_popup,
            anchor="w",
            fg_color=DARK_PANEL_ALT,
            hover_color=DARK_HOVER,
            text_color=DARK_TEXT
        )
        self.reset_modules_button.grid(row=100, column=0, padx=20, pady=(20, 8), sticky="sew")

        self.custom_fflag_button = ctk.CTkButton(
            self.sidebar_frame,
            text="Custom FFlags",
            command=self._open_editor,
            anchor="w",
            fg_color=DARK_PANEL_ALT,
            hover_color=DARK_HOVER,
            text_color=DARK_TEXT
        )
        self.custom_fflag_button.grid(row=101, column=0, padx=20, pady=(0, 8), sticky="sew")

        self.open_client_settings_button = ctk.CTkButton(
            self.sidebar_frame,
            text="Open JSON Path",
            command=self._open_client_settings_json_location,
            anchor="w",
            fg_color=DARK_PANEL_ALT,
            hover_color=DARK_HOVER,
            text_color=DARK_TEXT
        )
        self.open_client_settings_button.grid(row=102, column=0, padx=20, pady=(0, 18), sticky="sew")

        self.content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=DARK_WINDOW)
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        self.content_frame.grid_rowconfigure(1, weight=1)
        self.content_frame.grid_rowconfigure(2, weight=0)
        self.content_frame.grid_columnconfigure(0, weight=1)

        self.top_bar_frame = ctk.CTkFrame(
            self.content_frame,
            height=52,
            corner_radius=0,
            fg_color=DARK_TOP_BAR
        )
        self.top_bar_frame.grid(row=0, column=0, sticky="new")
        self.top_bar_frame.grid_columnconfigure(1, weight=1)

        self.category_title_label = ctk.CTkLabel(
            self.top_bar_frame,
            text="",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=DARK_TEXT
        )
        self.category_title_label.grid(row=0, column=0, padx=15, pady=10, sticky="w")

        self.launch_button = ctk.CTkButton(
            self.top_bar_frame,
            text="Launch",
            command=self._launch_roblox,
            width=100,
            fg_color=DARK_PANEL_ALT,
            hover_color=DARK_HOVER,
            text_color=DARK_TEXT
        )
        self.launch_button.grid(row=0, column=2, padx=15, pady=10, sticky="e")

        self.bottom_bar_frame = ctk.CTkFrame(
            self.content_frame,
            height=46,
            corner_radius=0,
            fg_color=DARK_WINDOW
        )
        self.bottom_bar_frame.grid(row=2, column=0, sticky="sew")
        self.bottom_bar_frame.grid_columnconfigure(0, weight=1)

        self.roblox_client_button = ctk.CTkButton(
            self.bottom_bar_frame,
            text="Roblox",
            command=lambda: self._switch_client("roblox"),
            width=95,
            fg_color=DARK_PANEL_ALT,
            hover_color=DARK_HOVER,
            text_color=DARK_TEXT
        )
        self.roblox_client_button.grid(row=0, column=1, padx=(10, 5), pady=(5, 10), sticky="e")

        self.roblox_studio_client_button = ctk.CTkButton(
            self.bottom_bar_frame,
            text="Roblox Studio",
            command=lambda: self._switch_client("robloxstudio"),
            width=125,
            fg_color=DARK_PANEL_ALT,
            hover_color=DARK_HOVER,
            text_color=DARK_TEXT
        )
        self.roblox_studio_client_button.grid(row=0, column=2, padx=(5, 15), pady=(5, 10), sticky="e")

        self._update_client_buttons()

        if self.categories:
            self._switch_category(self.categories[0]["id"])

    def _update_client_buttons(self):
        if hasattr(self, "roblox_client_button"):
            self.roblox_client_button.configure(
                fg_color=DARK_SELECTED if self.selected_client == "roblox" else DARK_PANEL_ALT
            )

        if hasattr(self, "roblox_studio_client_button"):
            self.roblox_studio_client_button.configure(
                fg_color=DARK_SELECTED if self.selected_client == "robloxstudio" else DARK_PANEL_ALT
            )

        if hasattr(self, "launch_button"):
            label = CLIENT_CONFIG.get(self.selected_client, CLIENT_CONFIG["roblox"])["label"]
            self.launch_button.configure(text=f"Launch {label}")

    def _switch_client(self, client_key: str):
        if client_key == self.selected_client:
            return

        if client_key not in CLIENT_CONFIG:
            return

        target_path = find_roblox_executable(client_key)
        if not target_path or not os.path.exists(target_path):
            return

        self.selected_client = client_key
        self._set_data_paths(client_key)

        self.client_paths[client_key] = build_client_paths(client_key, target_path)
        self._activate_client_paths(client_key)

        if not os.path.exists(self.client_settings_json_path):
            self._force_create_json()

        if not self._load_json_data():
            self._force_create_json()
            self._load_json_data()

        self._reload_plugin_json_and_ui()

    def _create_or_get_category_frame(self, category_id: str):
        if category_id in self.category_frames:
            return self.category_frames[category_id]

        frame = ctk.CTkScrollableFrame(self.content_frame, fg_color=DARK_WINDOW)
        frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.category_frames[category_id] = frame

        self._populate_fflag_frame(frame, category_id)

        return frame

    def _populate_fflag_frame(self, frame, category_id: str):
        modules = self.category_modules.get(category_id, [])

        if not modules:
            label = ctk.CTkLabel(
                frame,
                text="No modules are defined for this category.",
                text_color=DARK_MUTED_TEXT
            )
            label.grid(row=0, column=0, sticky="w", padx=10, pady=10)
            return

        for row_index, module in enumerate(modules):
            self._add_module_switch(frame, module, row_index)

    def _module_is_active(self, snippet: dict) -> bool:
        return all(
            key in self.current_flags and str(self.current_flags[key]) == str(value)
            for key, value in snippet.items()
        )

    def _add_module_switch(self, frame, module: dict, row_index: int):
        module_id = module.get("id", normalize_id(module.get("name", "module")))
        title = module.get("name", module_id)
        description = module.get("description", "")

        try:
            snippet = parse_module_flags(module)
        except Exception as error:
            error_label = ctk.CTkLabel(
                frame,
                text=f"Error loading {title}: {error}",
                text_color="red"
            )
            error_label.grid(row=row_index, column=0, sticky="w", padx=10, pady=6)
            return

        card = ctk.CTkFrame(
            frame,
            corner_radius=12,
            border_width=1,
            border_color=DARK_BORDER,
            fg_color=DARK_PANEL
        )
        card.grid(row=row_index, column=0, sticky="ew", padx=10, pady=6)
        card.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)

        var = ctk.BooleanVar(value=self._module_is_active(snippet))
        self.var_map[module_id] = (var, snippet)

        switch_text = title
        if description:
            switch_text = f"{title}\n{description}"

        switch = ctk.CTkSwitch(
            card,
            text=switch_text,
            variable=var,
            command=lambda mid=module_id: self._toggle_flag(mid),
            font=ctk.CTkFont(size=12),
            progress_color=DARK_ACCENT,
            text_color=DARK_TEXT
        )
        switch.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 8))

    def _switch_category(self, category_id: str):
        category_name = ""

        for category in self.categories:
            if category["id"] == category_id:
                category_name = category.get("name", category_id)
                break

        self.category_title_label.configure(text=category_name)

        for button_id, button in self.sidebar_buttons.items():
            if button_id == category_id:
                button.configure(fg_color=DARK_SELECTED)
            else:
                button.configure(fg_color="transparent")

        target_frame = self._create_or_get_category_frame(category_id)

        for frame in self.category_frames.values():
            if frame != target_frame:
                frame.grid_remove()

        target_frame.grid()
        target_frame.tkraise()

    def _open_client_settings_json_location(self):
        if not self.client_settings_dir:
            return

        try:
            if os.path.isdir(self.client_settings_dir):
                os.startfile(self.client_settings_dir)
            else:
                return
        except Exception:
            return

    def _launch_roblox(self):
        if not self.roblox_path:
            return

        try:
            subprocess.Popen([self.roblox_path])
        except FileNotFoundError:
            return
        except Exception:
            return

    def _load_json_data(self) -> bool:
        if not self.client_settings_json_path or not os.path.exists(self.client_settings_json_path):
            self.current_flags = {}
            return True

        try:
            with open(self.client_settings_json_path, "r", encoding="utf-8") as file:
                content = file.read()

            if not content.strip():
                self.current_flags = {}
                return True

            data = json.loads(content)

            if not isinstance(data, dict):
                return False

            self.current_flags = data
            return True
        except json.JSONDecodeError as error:
            return False
        except Exception:
            return False

    def _save_json_data(self) -> bool:
        if not self.client_settings_json_path:
            return False

        try:
            os.makedirs(os.path.dirname(self.client_settings_json_path), exist_ok=True)

            with open(self.client_settings_json_path, "w", encoding="utf-8") as file:
                json.dump(self.current_flags, file, indent=4)

            return True
        except Exception:
            return False

    def _toggle_flag(self, module_id: str):
        if module_id not in self.var_map:
            return

        var, snippet = self.var_map[module_id]

        if var.get():
            for key, value in snippet.items():
                self.current_flags[key] = value
        else:
            for key in snippet.keys():
                self.current_flags.pop(key, None)

        self._save_json_data()

    def _reload_flags_and_ui(self):
        if not self._load_json_data():
            return

        for module_id, (var, snippet) in self.var_map.items():
            is_active = all(
                key in self.current_flags and str(self.current_flags[key]) == str(value)
                for key, value in snippet.items()
            )
            var.set(is_active)


    def _reload_plugin_json_and_ui(self):
        try:
            self._load_plugin_data()
        except Exception:
            return

        for frame in self.category_frames.values():
            frame.destroy()

        self.category_frames.clear()
        self.var_map.clear()

        for button in self.sidebar_buttons.values():
            button.destroy()

        self.sidebar_buttons.clear()
        self.sidebar_frame.destroy()
        self.content_frame.destroy()

        self._create_main_ui()


    def _open_reset_modules_popup(self):
        selected_label = CLIENT_CONFIG.get(self.selected_client, CLIENT_CONFIG["roblox"])["label"]

        popup = ctk.CTkToplevel(self)
        prepare_dialog_window(popup)
        popup.title("Reset Modules")
        popup.geometry("420x250")
        popup.resizable(False, False)
        popup.configure(fg_color=DARK_WINDOW)

        popup.attributes("-topmost", True)
        popup.grid_columnconfigure(0, weight=1)

        container = ctk.CTkFrame(
            popup,
            corner_radius=16,
            border_width=1,
            border_color=DARK_BORDER,
            fg_color=DARK_PANEL
        )
        container.grid(row=0, column=0, sticky="nsew", padx=18, pady=18)
        container.grid_columnconfigure(0, weight=1)

        title_bar = ctk.CTkFrame(container, fg_color="transparent")
        title_bar.grid(row=0, column=0, padx=18, pady=(18, 8), sticky="ew")
        title_bar.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            title_bar,
            text="Reset Modules?",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=DARK_TEXT
        )
        title_label.grid(row=0, column=0, sticky="w")

        close_button = ctk.CTkButton(
            title_bar,
            text="×",
            width=32,
            height=28,
            command=popup.destroy,
            fg_color="transparent",
            hover_color=DARK_HOVER,
            text_color=DARK_MUTED_TEXT
        )
        close_button.grid(row=0, column=1, sticky="e")
        make_window_draggable(popup, title_bar, title_label)

        message_label = ctk.CTkLabel(
            container,
            text=(
                f"This will reset modules for {selected_label} only.\n\n"
                "ClientAppSettings.json will be replaced with an empty JSON object: {}\n"
                "This turns off all module flags and removes any custom FFlags for the selected client."
            ),
            justify="left",
            wraplength=350,
            text_color=DARK_MUTED_TEXT
        )
        message_label.grid(row=1, column=0, padx=18, pady=(0, 18), sticky="ew")

        button_frame = ctk.CTkFrame(container, fg_color="transparent")
        button_frame.grid(row=2, column=0, padx=18, pady=(0, 18), sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=popup.destroy,
            fg_color=DARK_PANEL_ALT,
            hover_color=DARK_HOVER,
            text_color=DARK_TEXT
        )
        cancel_button.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        reset_button = ctk.CTkButton(
            button_frame,
            text="Yes, Reset",
            command=lambda: self._reset_modules_for_selected_client(popup),
            fg_color="#b91c1c",
            hover_color="#991b1b",
            text_color=DARK_TEXT
        )
        reset_button.grid(row=0, column=1, padx=(6, 0), sticky="ew")

        popup.bind("<Escape>", lambda _event: popup.destroy())
        show_dialog_window(popup, self)

    def _reset_modules_for_selected_client(self, popup):
        self.current_flags = {}

        if self._save_json_data():
            popup.destroy()
            self._reload_flags_and_ui()

    def _open_editor(self):
        editor_win = ctk.CTkToplevel(self)
        prepare_dialog_window(editor_win)
        editor_win.title("Custom FFlags Editor - ClientAppSettings.json")
        editor_win.geometry("680x560")
        editor_win.configure(fg_color=DARK_WINDOW)

        editor_win.attributes("-topmost", True)
        editor_win.grid_rowconfigure(2, weight=1)
        editor_win.grid_columnconfigure(0, weight=1)

        title_bar = ctk.CTkFrame(editor_win, fg_color=DARK_PANEL, corner_radius=0, height=42)
        title_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        title_bar.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            title_bar,
            text="Custom FFlags Editor - ClientAppSettings.json",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=DARK_TEXT
        )
        title_label.grid(row=0, column=0, padx=12, pady=8, sticky="w")

        close_button = ctk.CTkButton(
            title_bar,
            text="×",
            width=36,
            height=28,
            command=editor_win.destroy,
            fg_color="transparent",
            hover_color=DARK_HOVER,
            text_color=DARK_MUTED_TEXT
        )
        close_button.grid(row=0, column=1, padx=(0, 8), pady=7, sticky="e")
        make_window_draggable(editor_win, title_bar, title_label)

        warning_label = ctk.CTkLabel(
            editor_win,
            text="Warning: manual editing requires valid JSON format.",
            text_color="orange",
            font=ctk.CTkFont(weight="bold")
        )
        warning_label.grid(row=1, column=0, columnspan=2, padx=10, pady=(10, 0), sticky="ew")

        textbox = ctk.CTkTextbox(editor_win, wrap="none", font=("Consolas", 11))
        textbox.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=10, pady=5)
        textbox.insert("0.0", json.dumps(self.current_flags, indent=4))

        button_frame = ctk.CTkFrame(editor_win, fg_color="transparent")
        button_frame.grid(row=3, column=0, columnspan=2, pady=(5, 10), sticky="ew")
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        save_btn = ctk.CTkButton(
            button_frame,
            text="Save and Close",
            command=lambda: self._save_editor(textbox, editor_win)
        )
        save_btn.grid(row=0, column=0, padx=10, pady=5, sticky="e")

        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=editor_win.destroy,
            fg_color=DARK_PANEL_ALT,
            hover_color=DARK_HOVER
        )
        cancel_btn.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        editor_win.bind("<Escape>", lambda _event: editor_win.destroy())
        show_dialog_window(editor_win, self)

    def _save_editor(self, textbox, window):
        text_content = textbox.get("0.0", "end").strip()

        try:
            new_data = json.loads(text_content)

            if not isinstance(new_data, dict):
                raise ValueError("ClientAppSettings.json must contain a JSON object.")

            self.current_flags = new_data

            if self._save_json_data():
                window.destroy()
                self._reload_flags_and_ui()
        except json.JSONDecodeError:
            return
        except Exception:
            return


if __name__ == "__main__":
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    try:
        app = LelFlagApp()
        app.mainloop()
    except KeyboardInterrupt:
        pass
