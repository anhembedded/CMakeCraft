import asyncio
import os
import re
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, RichLog, Label, Input, Button, Static, Switch, RadioSet, RadioButton, Select
from textual.screen import Screen
from textual.containers import Container, Vertical, Horizontal
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
        with Vertical(id="wizard-container"):
            yield Label("MODULE GENERATION WIZARD", id="wizard-title")
            
            yield Label("Project Name:")
            yield Input(
                value=self.initial_data.get("project_name", ""),
                placeholder="e.g. MyModule", 
                id="project_name"
            )
            
            yield Label("C++ Namespace:")
            yield Input(
                value=self.initial_data.get("namespace", ""),
                placeholder="e.g. my_namespace", 
                id="namespace"
            )
            
            yield Static("", id="validation-msg")

            with Horizontal():
                with Vertical():
                    yield Label("Prefix:")
                    yield Input(
                        value=self.initial_data.get("prefix", ""),
                        placeholder="(Optional)", 
                        id="prefix"
                    )
                with Vertical():
                    yield Label("Suffix:")
                    yield Input(
                        value=self.initial_data.get("suffix", ""),
                        placeholder="(Optional)", 
                        id="suffix"
                    )
            
            yield Label("Target Output Directory:")
            yield Input(
                value=self.initial_data.get("output_dir", "./"),
                placeholder="./", 
                id="output_dir"
            )
            
            yield Label("GoogleTest Source:")
            with RadioSet(id="gtest_mode"):
                yield RadioButton("Fetch from URL", id="mode-url", value=not self.initial_data.get("gtest_is_local", False))
                yield RadioButton("Copy from Local (GoogleTestScr)", id="mode-local", value=self.initial_data.get("gtest_is_local", False))

            with Vertical(id="gtest-url-container", classes="" if not self.initial_data.get("gtest_is_local", False) else "hidden"):
                yield Label("GoogleTest Repository URL:")
                yield Input(
                    value=self.initial_data.get("gtest_url", "https://github.com/google/googletest/archive/refs/tags/v1.14.0.zip"), 
                    id="gtest_url"
                )
            
            with Vertical(id="gtest-local-container", classes="" if self.initial_data.get("gtest_is_local", False) else "hidden"):
                yield Label("Select Local Version:")
                versions = self.scan_gtest_versions()
                yield Select(
                    [(v, v) for v in versions],
                    value=self.initial_data.get("gtest_local_version") if self.initial_data.get("gtest_local_version") in versions else (versions[0] if versions else None),
                    id="gtest_local_version"
                )

            with Horizontal(id="switch-container"):
                yield Switch(value=self.initial_data.get("overwrite", False), id="overwrite")
                yield Label("Overwrite existing directory", id="switch-label")
            
            with Horizontal(id="button-container"):
                yield Button("RESET", variant="error", id="reset")
                yield Button("GENERATE MODULE", variant="primary", id="submit")
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
        if event.input.id in ("project_name", "namespace", "prefix", "suffix"):
            self.validate_form()

    def validate_form(self) -> None:
        project_name = self.query_one("#project_name", Input).value
        namespace = self.query_one("#namespace", Input).value
        prefix = self.query_one("#prefix", Input).value
        suffix = self.query_one("#suffix", Input).value
        
        valid_regex = r"^[a-zA-Z_][a-zA-Z0-9_]*$"
        
        errors = []
        if project_name and not re.match(valid_regex, project_name):
            errors.append("Invalid Project Name (use only letters, numbers, and underscores, cannot start with number)")
        if namespace and not re.match(valid_regex, namespace):
            errors.append("Invalid Namespace (use only letters, numbers, and underscores, cannot start with number)")
        if prefix and not re.match(valid_regex, prefix):
            errors.append("Invalid Prefix (use only letters, numbers, and underscores, cannot start with number)")
        if suffix and not re.match(valid_regex, suffix):
            errors.append("Invalid Suffix (use only letters, numbers, and underscores, cannot start with number)")
        
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
        self.validate_form()
 
    def submit_form(self) -> None:
        config_data = {
            "project_name": self.query_one("#project_name", Input).value,
            "namespace": self.query_one("#namespace", Input).value,
            "prefix": self.query_one("#prefix", Input).value,
            "suffix": self.query_one("#suffix", Input).value,
            "output_dir": self.query_one("#output_dir", Input).value,
            "gtest_is_local": self.query_one("#mode-local", RadioButton).value,
            "gtest_url": self.query_one("#gtest_url", Input).value,
            "gtest_local_version": self.query_one("#gtest_local_version", Select).value,
            "overwrite": self.query_one("#overwrite", Switch).value,
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
    }
    #wizard-container {
        padding: 1 4;
        background: #1a1e2a;
        border: solid #3b4261;
        margin: 2 6;
        height: auto;
    }
    #wizard-title {
        width: 100%;
        content-align: center middle;
        text-style: bold;
        color: #89b4fa;
        margin-bottom: 1;
        background: #24283b;
        padding: 1;
    }
    Label {
        color: #a9b1d6;
        margin-top: 1;
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
        margin-top: 1;
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
    #button-container {
        height: auto;
        margin-top: 2;
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
    }
    #log {
        height: 1fr;
        border: solid #3b4261;
        background: #16161e;
        color: #c0caf5;
        margin: 1 2;
        padding: 1 2;
    }
    #status-label {
        padding: 1 4;
        color: #7aa2f7;
        text-style: bold;
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
                    "project_name": wizard.query_one("#project_name", Input).value,
                    "namespace": wizard.query_one("#namespace", Input).value,
                    "prefix": wizard.query_one("#prefix", Input).value,
                    "suffix": wizard.query_one("#suffix", Input).value,
                    "output_dir": wizard.query_one("#output_dir", Input).value,
                    "gtest_is_local": wizard.query_one("#mode-local", RadioButton).value,
                    "gtest_url": wizard.query_one("#gtest_url", Input).value,
                    "gtest_local_version": wizard.query_one("#gtest_local_version", Select).value,
                    "overwrite": wizard.query_one("#overwrite", Switch).value,
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
