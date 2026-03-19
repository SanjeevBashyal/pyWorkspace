import os

class Workspace:
    """
    Workspace represents a collection of programs and files that belong together.
    It stores their paths and arguments so they can be launched as a group.
    """
    def __init__(self, name: str):
        self.name = name
        self.programs = []
        self.files = []

    def add_program(self, path: str, args: str = "", cwd: str = None):
        """
        Add a program (executable) to the workspace.
        
        Args:
            path: Absolute path to the executable.
            args: Command line arguments for the program.
            cwd: Working directory from which to launch the program.
        """
        self.programs.append({'path': path, 'args': args, 'cwd': cwd})

    def add_file(self, file_path: str):
        """
        Add a specific file to be opened in the workspace.
        It will be opened with its default associated application in Windows.
        
        Args:
            file_path: Absolute path to the file.
        """
        self.files.append({'path': file_path})

    def to_dict(self) -> dict:
        """Convert workspace to dictionary for serialization."""
        return {
            'name': self.name,
            'programs': self.programs,
            'files': self.files
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Workspace':
        """Create a workspace instance from a dictionary."""
        ws = cls(data['name'])
        ws.programs = data.get('programs', [])
        ws.files = data.get('files', [])
        return ws
