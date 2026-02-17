class ModuleGenError(Exception):
    """Base category for all module generation errors."""
    pass

class ConfigError(ModuleGenError):
    """Raised when there is an issue with the configuration (JSON or CLI)."""
    pass

class TemplateError(ModuleGenError):
    """Raised when a required template file is missing or broken."""
    pass

class FileSystemError(ModuleGenError):
    """Raised when there are issues creating directories or writing files."""
    pass
