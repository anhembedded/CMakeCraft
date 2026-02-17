# C++ Module Artisan 🎨

A professional tool to automate the creation of C++ module templates following a production-ready pattern.

## 🌟 Features

- **Modern TUI**: Interactive Terminal UI powered by [Textual](https://textual.textualize.io/).
- **Storytelling Logic**: Descriptive generation process that explains each step.
- **Full Boilerplate**: Generates Public Interface, Private Implementation, Unit Tests (GTest), and Examples.
- **Configurable**: Support for JSON configuration files and CLI overrides.
- **Custom Output**: Generate modules anywhere on your system.
- **Automation Ready**: Includes `auto_run.ps1` in every generated module for one-click build/test.

## 🚀 Getting Started

### Prerequisites

- Python 3.7+
- `textual` package: `pip install textual`

### Installation

No installation required! Just clone the tool and run it.

### Usage

#### 🎨 Interactive Mode (TUI)
Just run the tool without any parameters to open the **Wizard**:
```powershell
python generator.py
```

#### ⚡ Quick TUI Mode
Pass arguments to skip the Wizard and go straight to generation:
```powershell
python generator.py -n MyModule -ns MyNamespace
```

#### 🤖 Silent/CLI Mode
Run without UI (standard console output):
```powershell
python generator.py -n SilentModule --silent
```

### CLI Arguments

| Argument | Description |
|---|---|
| `-c`, `--config` | Path to JSON configuration file |
| `-n`, `--name` | Project/Module name |
| `-ns`, `--namespace` | C++ Namespace |
| `-p`, `--prefix` | Folder/File prefix (e.g., `lib_`) |
| `-s`, `--suffix` | Folder/File suffix (e.g., `_impl`) |
| `-o`, `--output` | Root directory for the generated module |
| `-g`, `--gtest` | Custom GoogleTest download URL |
| `--silent` | Run without TUI (standard console output) |

## 🏗 Architecture

The tool is split into a modular structure for maintainability:
- `generator.py`: CLI entry point.
- `core/app.py`: Textual TUI Application logic.
- `core/config.py`: Business logic ("The Storyteller").
- `core/engine.py`: Processing and file system logic ("The Builder").
- `templates/`: Folder containing the C++/CMake templates.

## 📄 License
MIT
