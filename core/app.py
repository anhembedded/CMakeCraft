import asyncio
import os
import re
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, RichLog, Label, Input, Button, Static, Switch, RadioSet, RadioButton, Select, Collapsible
from textual.screen import Screen
from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from textual.message import Message
import json

from .config import Storyteller
from .engine import Builder
from .exceptions import ModuleGenError

class WizardScreen(Screen):
    """The configuration wizard for module generation."""
    
    BINDINGS = [
        ("escape", "app.quit", "Quit"),
        ("ctrl+r", "reset_fields", "Reset Fields")
    ]

    class Generated(Message):
        """Message sent when the configuration is confirmed."""
        def __init__(self, config_data):
            self.config_data = config_data
            super().__init__()

    def __init__(self, initial_data=None):
        super().__init__()
        self.initial_data = initial_data or {}
        self.is_valid = True

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id="wizard-container"):
            yield Label("💎 C++ MODULE ARTISAN", id="wizard-title")
            
            with Vertical(classes="section"):
                yield Label("📦 MODULE IDENTITY", classes="section-title")
                with Horizontal(classes="col-container"):
                    with Vertical(classes="col"):
                        yield Label("Module Name:")
                        yield Input(
                            value=self.initial_data.get("module_name", ""),
                            placeholder="e.g. MyModule", 
                            id="module_name",
                            tooltip="The base name of your module. Used for generating file names and CMake targets."
                        )
                    with Vertical(classes="col"):
                        yield Label("C++ Namespace:")
                        yield Input(
                            value=self.initial_data.get("namespace", ""),
                            placeholder="e.g. my_namespace", 
                            id="namespace",
                            tooltip="The C++ namespace for your code. Use lower_case_with_underscores."
                        )
                
                yield Static("", id="validation-msg")

                with Horizontal(classes="col-container"):
                    with Vertical(classes="col"):
                        yield Label("Prefix:")
                        yield Input(
                            value=self.initial_data.get("prefix", ""),
                            placeholder="(Optional)", 
                            id="prefix",
                            tooltip="Text prepended to the module name (e.g., 'Lib_')."
                        )
                    with Vertical(classes="col"):
                        yield Label("Suffix:")
                        yield Input(
                            value=self.initial_data.get("suffix", ""),
                            placeholder="(Optional)", 
                            id="suffix",
                            tooltip="Text appended to the module name (e.g., '_Internal')."
                        )
            
            with Vertical(classes="section"):
                yield Label("📂 OUTPUT & OVERWRITE", classes="section-title")
                yield Label("Target Output Directory:")
                yield Input(
                    value=self.initial_data.get("output_dir", "./"),
                    placeholder="./", 
                    id="output_dir",
                    tooltip="Where the magic happens. The module's root folder will be created here."
                )
                with Horizontal(id="switch-container"):
                    yield Switch(value=self.initial_data.get("overwrite", False), id="overwrite")
                    yield Label("Overwrite existing directory", id="switch-label")

            with Collapsible(title="🧪 GOOGLE TEST SETUP", id="gtest-config"):
                with Horizontal(classes="col-container"):
                    with Vertical(classes="col", id="gtest-mode-col"):
                        yield Label("Source Mode:")
                        with RadioSet(id="gtest_mode"):
                            yield RadioButton("Fetch URL", id="mode-url", value=not self.initial_data.get("gtest_is_local", False))
                            yield RadioButton("Local Scr", id="mode-local", value=self.initial_data.get("gtest_is_local", False))

                    with Vertical(classes="col"):
                        with Vertical(id="gtest-url-container", classes="" if not self.initial_data.get("gtest_is_local", False) else "hidden"):
                            yield Label("Repository URL:")
                            yield Input(
                                value=self.initial_data.get("gtest_url", "https://github.com/google/googletest/archive/refs/tags/v1.14.0.zip"), 
                                id="gtest_url",
                                tooltip="URL to download GoogleTest archive."
                            )
                        
                        with Vertical(id="gtest-local-container", classes="" if self.initial_data.get("gtest_is_local", False) else "hidden"):
                            yield Label("Select Local Version:")
                            versions = self.scan_gtest_versions()
                            yield Select(
                                [(v, v) for v in versions],
                                value=self.initial_data.get("gtest_local_version") if self.initial_data.get("gtest_local_version") in versions else (versions[0] if versions else None),
                                id="gtest_local_version",
                                tooltip="Physical copy from your GoogleTestScr directory."
                            )

            with Collapsible(title="⚙️ ADVANCED CONFIGURATION (C++, LINT, DOCS)", id="advanced-config"):
                with Horizontal(classes="col-container"):
                    with Vertical(classes="col"):
                        yield Label("C++ Standard")
                        yield Select(
                            [("11", "11"), ("14", "14"), ("17", "17"), ("20", "20"), ("23", "23")],
                            value=self.initial_data.get("cpp_std", "17"),
                            id="cpp_std",
                            tooltip="Specifies the C++ language level."
                        )
                    with Vertical(classes="col"):
                        yield Label("Library Type")
                        with RadioSet(id="lib_type", tooltip="STATIC or SHARED (.dll/.so)."):
                            yield RadioButton("STATIC", id="lib-static", value=self.initial_data.get("lib_type", "STATIC") == "STATIC")
                            yield RadioButton("SHARED", id="lib-shared", value=self.initial_data.get("lib_type", "STATIC") == "SHARED")
                
                with Horizontal(classes="switch-grid"):
                    with Vertical(classes="switch-col"):
                        yield Label("CMake Settings", classes="sub-title")
                        yield Label("C++ Compiler Path (Optional):")
                        yield Input(
                            value=self.initial_data.get("cpp_compiler", ""),
                            placeholder="e.g. g++", 
                            id="cpp_compiler",
                            tooltip="Optional path to a specific C++ compiler (sets CMAKE_CXX_COMPILER)."
                        )
                        yield Label("CMake Generator (Optional):")
                        yield Select(
                            [
                                ("Default", ""),
                                ("Ninja", "Ninja"),
                                ("Unix Makefiles", "Unix Makefiles"),
                                ("MinGW Makefiles", "MinGW Makefiles"),
                                ("NMake Makefiles", "NMake Makefiles"),
                            ],
                            value=self.initial_data.get("cmake_generator", ""),
                            id="cmake_generator",
                            tooltip="Optional: Override the default CMake generator (sets -G)."
                        )
                        with Horizontal(classes="switch-item"):
                            yield Switch(value=self.initial_data.get("cpp_std_req", True), id="cpp_std_req")
                            yield Label("Std Required")
                        with Horizontal(classes="switch-item"):
                            yield Switch(value=self.initial_data.get("export_cmds", True), id="export_cmds")
                            yield Label("Export Cmds")
                    
                    with Vertical(classes="switch-col"):
                        yield Label("Build Quality", classes="sub-title")
                        with Horizontal(classes="switch-item"):
                            yield Switch(value=self.initial_data.get("werror", False), id="werror")
                            yield Label("Werror")
                        with Horizontal(classes="switch-item"):
                            yield Switch(value=self.initial_data.get("lto", False), id="lto")
                            yield Label("LTO")
                        with Horizontal(classes="switch-item"):
                            yield Switch(value=self.initial_data.get("tidy_in_build", False), id="tidy_in_build")
                            yield Label("Lint on Build")

                    with Vertical(classes="switch-col"):
                        yield Label("Templates", classes="sub-title")
                        with Horizontal(classes="switch-item"):
                            yield Switch(value=self.initial_data.get("gen_format", True), id="gen_format")
                            yield Label(".format")
                        with Horizontal(classes="switch-item"):
                            yield Switch(value=self.initial_data.get("gen_tidy", True), id="gen_tidy")
                            yield Label(".tidy")
                        with Horizontal(classes="switch-item"):
                            yield Switch(value=self.initial_data.get("gen_readme", True), id="gen_readme")
                            yield Label("README")

            with Horizontal(id="button-container"):
                yield Button("FACTORY RESET", variant="error", id="reset")
                yield Button("CREATE MODULE", variant="primary", id="submit")
        yield Footer()

    def scan_gtest_versions(self):
        base_dir = "GoogleTestScr"
        if os.path.exists(base_dir) and os.path.isdir(base_dir):
            try:
                return [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
            except Exception:
                return []
        return []

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        if event.radio_set.id == "gtest_mode":
            is_local = event.pressed.id == "mode-local"
            self.query_one("#gtest-url-container").set_class(is_local, "hidden")
            self.query_one("#gtest-local-container").set_class(not is_local, "hidden")

    def on_input_changed(self, event: Input.Changed) -> None:
        """Real-time validation of identifier-naming."""
        if event.input.id in ("module_name", "namespace", "prefix", "suffix"):
            self.validate_form()

    def validate_form(self) -> None:
        module_name = self.query_one("#module_name", Input).value
        namespace = self.query_one("#namespace", Input).value
        prefix = self.query_one("#prefix", Input).value
        suffix = self.query_one("#suffix", Input).value
        
        valid_regex = r"^[a-zA-Z_][a-zA-Z0-9_]*$"
        
        errors = []
        if module_name and not re.match(valid_regex, module_name):
            errors.append("Invalid Module Name (must follow C++ identifier rules)")
        if namespace and not re.match(valid_regex, namespace):
            errors.append("Invalid Namespace")
        if prefix and not re.match(valid_regex, prefix):
            errors.append("Invalid Prefix")
        if suffix and not re.match(valid_regex, suffix):
            errors.append("Invalid Suffix")
        
        msg_widget = self.query_one("#validation-msg", Static)
        submit_btn = self.query_one("#submit", Button)
        
        if errors:
            msg_widget.update(f"[bold red]⚠ {errors[0]}[/]")
            submit_btn.disabled = True
            self.is_valid = False
        else:
            msg_widget.update("")
            submit_btn.disabled = False
            self.is_valid = True

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "submit" and self.is_valid:
            self.submit_form()
        elif event.button.id == "reset":
            self.action_reset_fields()

    def action_reset_fields(self) -> None:
        """Clears all input fields."""
        for input_widget in self.query(Input):
            input_widget.value = ""
        self.query_one("#overwrite", Switch).value = False
        self.query_one("#output_dir", Input).value = "./"
        self.query_one("#mode-url", RadioButton).value = True
        self.query_one("#gtest_url", Input).value = "https://github.com/google/googletest/archive/refs/tags/v1.14.0.zip"
        
        # Reset Advanced
        self.query_one("#cpp_std", Select).value = "17"
        self.query_one("#lib-static", RadioButton).value = True
        self.query_one("#cpp_compiler", Input).value = ""
        self.query_one("#cmake_generator", Select).value = ""
        self.query_one("#cpp_std_req", Switch).value = True
        self.query_one("#export_cmds", Switch).value = True
        self.query_one("#werror", Switch).value = False
        self.query_one("#lto", Switch).value = False
        self.query_one("#tidy_in_build", Switch).value = False
        self.query_one("#gen_format", Switch).value = True
        self.query_one("#gen_tidy", Switch).value = True
        self.query_one("#gen_readme", Switch).value = True
        
        self.validate_form()

    def submit_form(self) -> None:
        config_data = {
            "module_name": self.query_one("#module_name", Input).value,
            "namespace": self.query_one("#namespace", Input).value,
            "prefix": self.query_one("#prefix", Input).value,
            "suffix": self.query_one("#suffix", Input).value,
            "output_dir": self.query_one("#output_dir", Input).value,
            "gtest_is_local": self.query_one("#mode-local", RadioButton).value,
            "gtest_url": self.query_one("#gtest_url", Input).value,
            "gtest_local_version": self.query_one("#gtest_local_version", Select).value,
            "overwrite": self.query_one("#overwrite", Switch).value,
            
            # Advanced
            "cpp_compiler": self.query_one("#cpp_compiler", Input).value,
            "cmake_generator": self.query_one("#cmake_generator", Select).value,
            "cpp_std": self.query_one("#cpp_std", Select).value,
            "cpp_std_req": self.query_one("#cpp_std_req", Switch).value,
            "export_cmds": self.query_one("#export_cmds", Switch).value,
            "lib_type": "STATIC" if self.query_one("#lib-static", RadioButton).value else "SHARED",
            "werror": self.query_one("#werror", Switch).value,
            "lto": self.query_one("#lto", Switch).value,
            "tidy_in_build": self.query_one("#tidy_in_build", Switch).value,
            "gen_format": self.query_one("#gen_format", Switch).value,
            "gen_tidy": self.query_one("#gen_tidy", Switch).value,
            "gen_readme": self.query_one("#gen_readme", Switch).value,
        }
        # Clean empty values but keep boolean
        config_data = {k: v for k, v in config_data.items() if v is not None and v != ""}
        self.post_message(self.Generated(config_data))

class GenerationScreen(Screen):
    """The generation progress monitoring screen."""
    
    BINDINGS = [
        ("escape", "app.quit", "Quit"),
        ("b", "back", "Back to Wizard")
    ]

    class Back(Message):
        """Request to go back to the wizard."""
        pass

    def __init__(self, config_data):
        super().__init__()
        self.config_data = config_data

    def compose(self) -> ComposeResult:
        yield Header()
        yield Label("System Status: Initializing Module Generation...", id="status-label")
        yield RichLog(id="log", markup=True)
        with Horizontal(id="gen-footer"):
            yield Button("BACK TO WIZARD", variant="default", id="back-btn", classes="hidden")
            yield Static("", id="spacer")
            yield Button("EXIT", variant="error", id="exit-btn", classes="hidden")
        yield Footer()

    async def on_mount(self) -> None:
        self.log_widget = self.query_one("#log", RichLog)
        asyncio.create_task(self.run_generation())

    async def run_generation(self):
        try:
            storyteller = Storyteller(self.config_data)
            chapters = storyteller.weave_the_story()
            builder = Builder(storyteller)
            
            self.log_widget.write("[bold blue]INFO:[/] Starting generation sequence...")
            
            self.log_widget.write(f"\n[bold blue]PHASE 1:[/] {chapters[0][0]}")
            self.log_widget.write(f"  [dim]{chapters[0][1]}[/]")
            
            self.log_widget.write(f"\n[bold blue]PHASE 2:[/] {chapters[1][0]}")
            builder.prepare_ground(callback=self.log_message)
            
            self.log_widget.write(f"\n[bold blue]PHASE 3:[/] {chapters[2][0]}")
            builder.breathe_life(callback=self.log_message)
            
            self.log_widget.write(f"\n[bold blue]PHASE 4:[/] {chapters[3][0]}")
            self.log_widget.write("  [dim]Finalizing build environment and scripts.[/]")
            
            self.log_widget.write("\n[bold green]COMPLETED:[/] Module generation successful.")
            self.log_widget.write(f"Target: [cyan]{os.path.abspath(builder.output_path)}[/]")
            self.log_widget.write("\n[dim]Press [bold]ESC[/] to exit or [bold]B[/] to return to Wizard.[/]")
            self.show_completion_buttons()
            
        except ModuleGenError as e:
            self.log_widget.write(f"\n[bold red]ERROR:[/] {str(e)}")
            self.log_widget.write("\n[dim]Press [bold]ESC[/] to exit or [bold]B[/] to return to Wizard.[/]")
            self.show_completion_buttons()
        except Exception as e:
            self.log_widget.write(f"\n[bold red]CRITICAL:[/] {str(e)}")
            self.log_widget.write("\n[dim]Press [bold]ESC[/] to exit or [bold]B[/] to return to Wizard.[/]")
            self.show_completion_buttons()

    def show_completion_buttons(self):
        self.query_one("#back-btn", Button).remove_class("hidden")
        self.query_one("#exit-btn", Button).remove_class("hidden")

    def log_message(self, msg: str):
        if "Manifested" in msg:
            file_path = msg.split(": ")[-1]
            self.log_widget.write(f"  [green]✓[/] Created: [dim]{file_path}[/]")
        else:
            self.log_widget.write(f"  [blue]i[/] {msg}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back-btn":
            self.post_message(self.Back())
        elif event.button.id == "exit-btn":
            self.app.quit()

    def action_back(self) -> None:
        self.post_message(self.Back())

class ModuleGeneratorApp(App):
    """C++ Module Artisan - Professional Edition."""
    
    TITLE = "C++ Module Artisan"
    SUB_TITLE = "Professional Generation Suite"
    
    CSS = """
    Screen {
        background: #0f111a;
        align: center middle;
    }
    #wizard-container {
        padding: 0 4 1 4;
        background: #1a1e2a;
        border: solid #3b4261;
        margin: 1 1;
        height: auto;
        max-height: 98vh;
        min-width: 80;
        max-width: 100;
        align-horizontal: center;
        overflow-y: auto;
    }
    #wizard-title {
        width: 100%;
        content-align: center middle;
        text-style: bold;
        color: #7aa2f7;
        margin-bottom: 0;
        background: #24283b;
        padding: 0 1;
        border-bottom: double #7aa2f7;
    }
    .section {
        border: solid #3b4261;
        padding: 1;
        margin-bottom: 1;
        height: auto;
    }
    .section-title {
        color: #bb9af7;
        text-style: bold;
        margin-bottom: 1;
    }
    .col-container {
        height: auto;
        margin-bottom: 0;
    }
    .col {
        width: 1fr;
        padding-right: 1;
        height: auto;
    }
    Label {
        color: #a9b1d6;
        margin-top: 0;
    }
    #gtest-mode-col {
        max-width: 30;
    }
    RadioSet {
        background: transparent;
        border: none;
        padding: 0;
        margin: 0;
    }
    RadioButton {
        padding: 0 1;
    }
    .sub-title {
        color: #9ece6a;
        text-style: italic;
    }
    Input {
        margin-bottom: 0;
        border: solid #414868;
        background: #16161e;
        color: #c0caf5;
    }
    Input:focus {
        border: double #7aa2f7;
    }
    #validation-msg {
        height: 1;
        margin-top: 0;
        margin-bottom: 1;
        color: #f7768e;
    }
    #switch-container {
        height: auto;
        margin-top: 1;
        align: left middle;
    }
    #switch-label {
        margin: 0 0 0 1;
    }
    .switch-grid {
        height: auto;
        margin-top: 1;
    }
    .switch-col {
        width: 1fr;
        height: auto;
    }
    .switch-item {
        height: auto;
        align: left middle;
    }
    #button-container {
        height: auto;
        margin-top: 1;
        align: center middle;
        background: #24283b;
        padding: 1;
        border-top: solid #3b4261;
    }
    Collapsible {
        border: solid #3b4261;
        margin-bottom: 1;
        background: #1e2233;
    }
    CollapsibleTitle {
        color: #bb9af7;
        text-style: bold;
    }
    #gen-footer {
        height: auto;
        margin: 0 2 1 2;
        padding: 0 2;
    }
    #spacer {
        width: 1fr;
    }
    .hidden {
        display: none;
    }
    Button {
        width: 1fr;
        text-style: bold;
    }
    #submit {
        margin-left: 1;
        background: #7aa2f7;
        color: #1a1b26;
    }
    #submit:hover {
        background: #bb9af7;
    }
    #log {
        height: 1fr;
        border: solid #3b4261;
        background: #16161e;
        color: #c0caf5;
        margin: 1 2;
        padding: 1 2;
    }
    """

    def __init__(self, config_data=None):
        super().__init__()
        self.config_data = config_data or {}

    async def on_mount(self) -> None:
        # Check if we should skip the wizard (only if CLI args or config file were provided)
        cli_run = self.config_data.pop("_cli_run", False)
        
        if not cli_run:
            # Open Wizard by default, pre-filled with persistent session data
            await self.push_screen(WizardScreen(self.config_data))
        else:
            # Run generation directly if CLI args were provided
            await self.push_screen(GenerationScreen(self.config_data))

    def save_session(self) -> None:
        """Persists the current configuration to a file."""
        try:
            # We want to capture the current screen's state if it's the Wizard
            if isinstance(self.screen, WizardScreen):
                # Manual extraction from widgets
                wizard = self.screen
                config_to_save = {
                    "module_name": wizard.query_one("#module_name", Input).value,
                    "namespace": wizard.query_one("#namespace", Input).value,
                    "prefix": wizard.query_one("#prefix", Input).value,
                    "suffix": wizard.query_one("#suffix", Input).value,
                    "output_dir": wizard.query_one("#output_dir", Input).value,
                    "gtest_is_local": wizard.query_one("#mode-local", RadioButton).value,
                    "gtest_url": wizard.query_one("#gtest_url", Input).value,
                    "gtest_local_version": wizard.query_one("#gtest_local_version", Select).value,
                    "overwrite": wizard.query_one("#overwrite", Switch).value,
                    # Advanced
                    "cpp_compiler": wizard.query_one("#cpp_compiler", Input).value,
                    "cmake_generator": wizard.query_one("#cmake_generator", Select).value,
                    "cpp_std": wizard.query_one("#cpp_std", Select).value,
                    "cpp_std_req": wizard.query_one("#cpp_std_req", Switch).value,
                    "export_cmds": wizard.query_one("#export_cmds", Switch).value,
                    "lib_type": "STATIC" if wizard.query_one("#lib-static", RadioButton).value else "SHARED",
                    "werror": wizard.query_one("#werror", Switch).value,
                    "lto": wizard.query_one("#lto", Switch).value,
                    "tidy_in_build": wizard.query_one("#tidy_in_build", Switch).value,
                    "gen_format": wizard.query_one("#gen_format", Switch).value,
                    "gen_tidy": wizard.query_one("#gen_tidy", Switch).value,
                    "gen_readme": wizard.query_one("#gen_readme", Switch).value,
                }
                # Clean empty values
                config_to_save = {k: v for k, v in config_to_save.items() if v is not None and v != ""}
                
                with open('last_session.json', 'w') as f:
                    json.dump(config_to_save, f, indent=4)
        except Exception:
            pass

    async def on_wizard_screen_generated(self, message: WizardScreen.Generated) -> None:
        """Handle form submission from the Wizard."""
        self.config_data = message.config_data
        self.save_session()
        await self.push_screen(GenerationScreen(self.config_data))

    def on_generation_screen_back(self) -> None:
        """Return to the wizard screen."""
        self.pop_screen()

    def on_unmount(self) -> None:
        """Save session on application exit."""
        self.save_session()
