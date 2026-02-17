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
        return {
            '{{PROJECT_NAME}}': full_name,
            '{{NAMESPACE}}': self.config['namespace'],
            '{{GTEST_URL}}': self.config['gtest_url'],
            '{{AUTHOR}}': self.config.get('author', 'Artisan'),
            '{{DESCRIPTION}}': self.config.get('description', 'A module of great potential'),
            '{{PREFIX}}': self.config['prefix'],
            '{{SUFFIX}}': self.config['suffix']
        }

    @property
    def folder_name(self):
        return f"{self.config['prefix']}{self.config['project_name']}{self.config['suffix']}"
