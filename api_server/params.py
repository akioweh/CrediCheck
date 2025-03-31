"""
Runtime and configuration parameters for the API server.
"""

__all__ = ['DB_URI', 'DB_ARGS', 'DEMO_MODE']

from os import getenv
from typing import Final

USERNAME = getenv('USERNAME')
PASSWORD = getenv('PASSWORD')
SERVER = getenv('SERVER')
SCHEMA = getenv('SCHEMA')

DB_URI: Final[str] = f'mysql+asyncmy://{USERNAME}:{PASSWORD}@{SERVER}/{SCHEMA}'
DB_ARGS: Final[dict[str, str]] = {}

# enable demo mode to populate sites with random votes and credibility scores upon first vote cast
DEMO_MODE: Final[bool] = False
