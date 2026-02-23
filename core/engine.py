import os
import shutil
from .exceptions import FileSystemError, TemplateError

class Builder:
    """The Builder is responsible for the physical manifestation of the module."""
    
    def __init__(self, storyteller):
        self.storyteller = storyteller
        self.output_path = os.path.join(storyteller.config['output_dir'], storyteller.folder_name)
        self.template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')

    def prepare_ground(self, callback=None):
        """Creates the directory structure."""
        if os.path.exists(self.output_path) and not self.storyteller.config.get('overwrite', False):
            raise FileSystemError(f"The ground is already occupied: '{self.output_path}' exists. Enable 'Overwrite' to proceed.")
        
        try:
            if not os.path.exists(self.output_path):
                os.makedirs(self.output_path)
            if callback: callback(f"Founding the capital: {os.path.abspath(self.output_path)}")
        except Exception as e:
            raise FileSystemError(f"Could not claim the territory: {str(e)}")

    def breathe_life(self, callback=None):
        """Processes templates and writes files."""
        replacements = self.storyteller.get_replacements()
        project_name = replacements['{{PROJECT_NAME}}']

        for root, dirs, files in os.walk(self.template_dir):
            rel_path = os.path.relpath(root, self.template_dir)
            target_root = os.path.normpath(os.path.join(self.output_path, rel_path))
            
            if not os.path.exists(target_root):
                os.makedirs(target_root)

            for file_name in files:
                # Use decorated name (Prefix + Project + Suffix) for file names
                target_file_name = file_name.replace('PROJECT_NAME', self.storyteller.folder_name)
                template_file_path = os.path.join(root, file_name)
                target_file_path = os.path.join(target_root, target_file_name)

                try:
                    with open(template_file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Perform replacements
                    for key, value in replacements.items():
                        content = content.replace(key, value)

                    with open(target_file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                        callback(f"  - Manifested: {os.path.abspath(target_file_path)}")
                except Exception as e:
                    raise TemplateError(f"Failure in the forge during creation of {file_name}: {str(e)}")
        
        # Second, handle local GTest copy if requested
        if self.storyteller.config.get('gtest_is_local'):
            version = self.storyteller.config.get('gtest_local_version')
            if version:
                source_gtest = os.path.join("GoogleTestScr", version)
                target_gtest = os.path.join(self.output_path, "tests", "third_party", "googletest")
                
                if os.path.exists(source_gtest):
                    try:
                        if callback: callback(f"Importing ancient scrolls: Copying {version} to module...")
                        if os.path.exists(target_gtest):
                            shutil.rmtree(target_gtest)
                        shutil.copytree(source_gtest, target_gtest)
                        if callback: callback(f"  [green]✓[/] GTest imported to {os.path.abspath(target_gtest)}")
                    except Exception as e:
                        raise FileSystemError(f"Failed to copy local GTest: {str(e)}")
                else:
                    if callback: callback(f"  [red]⚠[/] Local GTest source not found at {source_gtest}")
