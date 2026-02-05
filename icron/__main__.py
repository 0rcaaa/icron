"""
Entry point for running icron as a module: python -m icron
"""

from icron.cli.commands import app

if __name__ == "__main__":
    app()
