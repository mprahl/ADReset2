"""
Author: StackFocus
File: errors.py
Purpose: defines error handling functions
"""


class ValidationError(ValueError):
    """ A custom exception used for invalid input or values
    """
    pass


class ADException(Exception):
    """ A custom exception for the PostMasterLDAP class
    """
    pass
