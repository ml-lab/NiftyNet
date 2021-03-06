# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import re

from six import string_types

from niftynet.utilities.user_parameters_regex import match_array

TRUE_VALUE = {'yes', 'true', 't', 'y', '1'}
FALSE_VALUE = {'no', 'false', 'f', 'n', '0'}


def str2boolean(string_input):
    """
    convert user input config string to boolean
    :param string_input: any string in TRUE_VALUE or FALSE_VALUE
    :return: True or False
    """
    if string_input.lower() in TRUE_VALUE:
        return True
    elif string_input.lower() in FALSE_VALUE:
        return False
    else:
        raise argparse.ArgumentTypeError(
            'Boolean value expected, received {}'.format(string_input))


def int_array(string_input):
    try:
        output_tuple = match_array(string_input, 'int')
    except ValueError:
        raise argparse.ArgumentTypeError(
            'array of int expected, received {}'.format(string_input))
    return output_tuple


def float_array(string_input):
    try:
        output_tuple = match_array(string_input, 'float')
    except ValueError:
        raise argparse.ArgumentTypeError(
            'array of float expected, received {}'.format(string_input))
    return output_tuple


def str_array(string_input):
    try:
        output_tuple = match_array(string_input, 'str')
    except ValueError:
        raise argparse.ArgumentTypeError(
            "list of strings expected, for each list element the allowed"
            "characters: [ a-zA-Z0-9], but received {}".format(string_input))
    return output_tuple


def make_input_tuple(input_str, element_type=string_types):
    assert input_str, \
        "invalid input {} for type {}".format(input_str, element_type)
    if isinstance(input_str, element_type):
        new_tuple = (input_str,)
    else:
        try:
            new_tuple = tuple(input_str)
        except TypeError:
            raise ValueError("can't cast to tuple of {}".format(element_type))
    assert all([isinstance(item, element_type) for item in new_tuple]), \
        "the input should be a tuple of {}".format(element_type)
    return new_tuple


def standardise_section_name(configparser, old_name):
    """
    rename configparser section
    This helper is useful when user specifies complex section names
    """
    new_name = standardise_string(old_name)
    if old_name == new_name:
        return old_name
    items = configparser.items(old_name)
    configparser.add_section(new_name)
    for (name, value) in items:
        configparser.set(new_name, name, value)
    configparser.remove_section(old_name)
    return new_name


def standardise_string(input_string):
    """
    to make the user's input consistent
    replace any characters not in set [0-9a-zA-Z] with underscrore _

    :param input_string: to be standardised
    :return: capitalised string
    """
    if not isinstance(input_string, string_types):
        return input_string
    new_name = re.sub('[^0-9a-zA-Z ]+', '', input_string.strip())
    return new_name


def has_section_in_config(config, required_custom_section):
    required_custom_section = standardise_string(required_custom_section)
    if required_custom_section is not None:
        user_sections = [standardise_string(section_name)
                         for section_name in config.sections()]
        if not required_custom_section in user_sections:
            raise ValueError
        else:
            return True


def add_input_name_args(parser, supported_input):
    for input_name in supported_input:
        parser.add_argument(
            "--{}".format(input_name),
            metavar='',
            help="names of grouping the input sections".format(input_name),
            type=str_array,
            default=())
    return parser


def spatialnumarray(string_input):
    """
    This function parses a 3-element tuple from a string input
    """
    int_tuple = int_array(string_input)
    while len(int_tuple) < 3:
        int_tuple = int_tuple + (int_tuple[-1],)
    int_tuple = int_tuple[:3]
    return int_tuple
