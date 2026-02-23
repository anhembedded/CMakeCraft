import os
import json
from .exceptions import ConfigError

class Storyteller:
    """The Storyteller interprets your requirements and prepares the 'chapters' of the module's creation."""
    
    def __init__(self, raw_config):
        self.config = raw_config
        self.chapters = []

    def weave_the_story(self):
        """Prepares the sequence of generation phases."""
        try:
            # Phase 1: Validation
            self._validate_config()
            self.chapters.append(("Configuration Validation", "Validating module parameters and requirements."))
            
            # Phase 2: Infrastructure
            self.chapters.append(("Infrastructure Setup", f"Initializing project structure for '{self.config['project_name']}'."))
            
            # Phase 3: Template Processing
            self.chapters.append(("Source Generation", "Processing templates and generating source files."))
            
            # Phase 4: Finalization
            self.chapters.append(("Finalization", "Configuring automation scripts and build hooks."))
            
            return self.chapters
        except Exception as e:
            raise ConfigError(f"Configuration failure: {str(e)}")

    def _validate_config(self):
        """Internal validation logic."""
        if 'project_name' not in self.config:
            raise ConfigError("Missing required requirement: 'project_name'")
        
        # Defaults
        self.config.setdefault('prefix', '')
        self.config.setdefault('suffix', '')
        self.config.setdefault('namespace', self.folder_name + "Space")
        self.config.setdefault('output_dir', os.getcwd())
        self.config['output_dir'] = os.path.abspath(os.path.normpath(self.config['output_dir']))

    def get_replacements(self):
        """Returns the dictionary of strings to be replaced in templates."""
        full_name = self.folder_name
        
        # Build hardcoded GTest declaration
        if self.config.get('gtest_is_local'):
            gtest_decl = (
                "FetchContent_Declare(\n"
                "    googletest\n"
                "    SOURCE_DIR ${CMAKE_CURRENT_SOURCE_DIR}/third_party/googletest\n"
                ")"
            )
        else:
            gtest_url = self.config.get('gtest_url', 'https://github.com/google/googletest/archive/refs/tags/v1.14.0.zip')
            gtest_decl = (
                "FetchContent_Declare(\n"
                "    googletest\n"
                f"    URL {gtest_url}\n"
                "    DOWNLOAD_EXTRACT_TIMESTAMP TRUE\n"
                ")"
            )

        return {
            '{{PROJECT_NAME}}': full_name,
            '{{NAMESPACE}}': self.config['namespace'],
            '{{GTEST_DECLARATION}}': gtest_decl,
            '{{AUTHOR}}': self.config.get('author', 'Artisan'),
            '{{DESCRIPTION}}': self.config.get('description', 'A module of great potential'),
            '{{PREFIX}}': self.config.get('prefix', ''),
            '{{SUFFIX}}': self.config.get('suffix', '')
        }

    @property
    def folder_name(self):
        return f"{self.config['prefix']}{self.config['project_name']}{self.config['suffix']}"
