# Python Coding Standards

## File Structure
Each Python file should follow this order:
1. All imports at the top of the file
   - Standard library imports first
   - Third-party imports second
   - Local/application imports third
   - Imports should be sorted alphabetically within each group
   - Leave one blank line between import groups

2. Module-level constants and configuration variables
   - All uppercase with underscores
   - Leave two blank lines after imports before constants

3. Function definitions
   - Leave two blank lines between the last constant and first function
   - Leave two blank lines between function definitions
   - Include docstrings for all functions

4. Main execution block (if applicable)
   - Put any `if __name__ == "__main__":` code at the bottom of the file

## Example:
```python
# Standard library imports
import json
import os

# Third-party imports
import requests
from dotenv import load_dotenv

# Constants
CONFIG_FILE = "config.json"
MAX_RETRIES = 3

# Functions
def function_one():
    """Docstring for function one."""
    pass


def function_two():
    """Docstring for function two."""
    pass


if __name__ == "__main__":
    # Main execution code here
    pass
```
