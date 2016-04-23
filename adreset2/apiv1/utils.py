"""
Author: StackFocus
File: utils.py
Purpose: General helper utils
"""

import os
from re import match
from mmap import mmap
from json import loads
from ..errors import ValidationError
from adreset2 import db
from adreset2.models import Configs


def is_file_writeable(file_path):
    """ Returns a bool based on if a file is writable or not
    """
    if os.path.isfile(file_path):
        return os.access(file_path, os.W_OK)
    else:
        absolute_path = os.path.abspath(file_path)
        dir_of_file = os.path.dirname(absolute_path)
        return os.access(dir_of_file, os.W_OK)


def is_config_update_valid(setting, value, valid_value_regex):
    """ A helper function for the update_config function on the /configs/<int:config_id> PUT route.
    A bool is returned based on if the users input is valid.
    """
    if match(valid_value_regex, value):

        if setting == 'Log File':
            if not is_file_writeable(value):
                raise ValidationError('The specified log path is not writable')
            else:
                # Enables Change Auditing when the log file is set
                change_auditing = Configs.query.filter_by(setting='Change Auditing').first()
                change_auditing.value = 'True'
                db.session.add(change_auditing)

        elif setting == 'Login Auditing' or setting == 'Change Auditing':
            log_file = Configs.query.filter_by(setting='Log File').first().value

            if not log_file:
                raise ValidationError('The log file must be set before auditing can be enabled')

        return True
    else:
        if setting == 'Local Account Minimum Password Length':
            raise ValidationError('An invalid minimum password length was supplied. The value must be between 1-25.')

        raise ValidationError('An invalid setting value was supplied')


def get_logs_dict(num_lines=50, reverse_order=False):
    """
    Returns the JSON formatted log file as a dict
    """
    log_path = Configs.query.filter_by(setting='Log File').first().value
    if log_path and os.path.exists(log_path):
        log_file = open(log_path, mode='r+')

        try:
            mmap_handler = mmap(log_file.fileno(), 0)
        except ValueError as e:
            if str(e) == 'cannot mmap an empty file':
                # If the file is empty, return empty JSON
                return {'items': [], }
            else:
                raise ValidationError(
                    'There was an error opening "{0}"'.format(
                        os.getcwd().replace('\\', '/') + '/' + log_path))

        new_line_count = 0
        # Assigns current_char to the last character of the file
        current_char = mmap_handler.size() - 1

        # If the file ends in a new line, add 1 more line to process
        # for mmap_handler[current_char:].splitlines() later on
        if mmap_handler[current_char] == '\n':
            num_lines += 1

        # While the number of lines iterated is less than numLines
        # and the beginning of the file hasn't been reached
        while new_line_count < num_lines and current_char > 0:
            # If a new line character is found, this means
            # the current line has ended
            if mmap_handler[current_char] == '\n':
                new_line_count += 1
            # Subtract from the character count to read the previous character
            current_char -= 1

        # If the beginning of the file hasn't been reached,
        # strip the preceding new line character
        if current_char > 0:
            current_char += 2

        # Create the list
        logs = mmap_handler[current_char:].splitlines()

        # Close the log file
        mmap_handler.close()
        log_file.close()

        if reverse_order:
            logs = list(reversed(logs))

        return {'items': [loads(log) for log in logs], }
    else:
        raise ValidationError('The log file could not be found')
