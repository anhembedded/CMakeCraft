import argparse
import json
import os
import sys
from core.app import ModuleGeneratorApp
from core.exceptions import ConfigError

def main():
    parser = argparse.ArgumentParser(description="C++ Module Artisan - TUI Template Generator")
    parser.add_argument("-c", "--config", help="Path to JSON configuration file")
    parser.add_argument("-n", "--name", help="Project name")
    parser.add_argument("-ns", "--namespace", help="C++ namespace")
    parser.add_argument("-p", "--prefix", help="Folder/File prefix", default="")
    parser.add_argument("-s", "--suffix", help="Folder/File suffix", default="")
    parser.add_argument("-g", "--gtest", help="GTest URL")
    parser.add_argument("-o", "--output", help="Output directory")
    parser.add_argument("--silent", action="store_true", help="Run without TUI (console output only)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing module directory")

    args = parser.parse_args()

    config = {}
    session_file = 'last_session.json'
    
    # Load persistence
    if os.path.exists(session_file):
        try:
            with open(session_file, 'r') as f:
                config = json.load(f)
        except Exception:
            pass # Ignore corrupt session files

    try:
        cli_run = False
        if args.config:
            cli_run = True
            if os.path.exists(args.config):
                with open(args.config, 'r') as f:
                    config.update(json.load(f))
            else:
                print(f"Error: Config file '{args.config}' not found.")
                sys.exit(1)

        # Merge CLI args
        if args.name: 
            config['project_name'] = args.name
            cli_run = True
        if args.namespace: config['namespace'] = args.namespace
        if args.prefix: config['prefix'] = args.prefix
        if args.suffix: config['suffix'] = args.suffix
        if args.gtest: config['gtest_url'] = args.gtest
        if args.output: config['output_dir'] = args.output
        if args.overwrite: config['overwrite'] = True

        if cli_run:
            config['_cli_run'] = True

        if args.silent:
            # Silent CLI Mode
            from core.config import Storyteller
            from core.engine import Builder
            from rich import print as rprint

            # In silent mode, name is mandatory if not in config
            if 'project_name' not in config:
                rprint("[bold red]ERROR:[/] project_name is required for silent execution.")
                sys.exit(1)
            
            storyteller = Storyteller(config)
            phases = storyteller.weave_the_story()
            builder = Builder(storyteller)

            rprint(f"[bold blue]>>>[/] [bold]C++ Module Artisan:[/] Initializing [cyan]{config['project_name']}[/]")
            for title, desc in phases:
                rprint(f"\n[bold blue]PHASE:[/] {title}")
                rprint(f"  [dim]{desc}[/]")
                if title == "Infrastructure Setup":
                    builder.prepare_ground(callback=lambda m: rprint(f"  [green]✓[/] {m}"))
                elif title == "Source Generation":
                    builder.breathe_life(callback=lambda m: rprint(f"  [green]✓[/] {m}"))
            
            # Save session for CLI/Silent mode (filter out internal flags)
            try:
                save_data = {k: v for k, v in config.items() if not k.startswith('_')}
                with open(session_file, 'w') as f:
                    json.dump(save_data, f, indent=4)
            except Exception:
                pass

            rprint("\n[bold green]SUCCESS:[/] Generation sequence complete.")
            rprint(f"[bold blue]>>>[/] Location: [cyan]{builder.output_path}[/]")
        else:
            # Launch the TUI App (Default)
            # If no args were passed at all (and no config), config will be empty
            # The App will handle showing the Wizard if project_name is missing.
            app = ModuleGeneratorApp(config)
            app.run()

    except Exception as e:
        print(f"Failed to start the generator: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
