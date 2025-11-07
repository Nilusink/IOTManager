"""
_utility_functions.py
19. March 2024

a few useful functions

Author:
Nilusink
"""


def classname(c: object) -> str:
    """
    get the name of an obect class
    """
    return c.__class__.__name__
