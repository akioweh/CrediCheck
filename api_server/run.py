"""
Run the server.
Simply execute this file from anywhere.

To directly run uvicorn from the terminal, execute::

    uvicorn api_server:api

from the project root directory.
"""

from os.path import dirname, abspath

import uvicorn


def run(working_dir: str | None = None):
    """Runs the database server with its API served over HTTP."""
    uvicorn.run(
        'api_server:api',
        port=4269,
        reload=True,
        log_level='debug',
        app_dir=working_dir,
        reload_dirs=abspath(dirname(__file__)),
        reload_excludes=[
            'extension/**',
        ]  # exclude client package from reloading the SERVER
    )


if __name__ == '__main__':
    print('Direct execution of ``run.py`` in server package.')
    # in order for Python's relative imports to work, we need to set the working directory
    # to the project root directory (the directory containing the server package)
    target_cwd = abspath(dirname(dirname(__file__)))

    run(target_cwd)
