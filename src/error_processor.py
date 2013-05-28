#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Oleg Beloglazov'


# Error types
LEXICAL = 'lexical'
SYNTAX = 'syntax'
SEMANTIC = 'semantic'

lexical_errors = []
syntax_errors = []
semantic_errors = []


def add_error(error_type, line, pos_in_line, message):
    complete_message = '%i:%i %s error: %s' % (line, pos_in_line, error_type, message)
    if error_type == LEXICAL:
        lexical_errors.append(complete_message)
    elif error_type == SYNTAX:
        syntax_errors.append(complete_message)
    elif error_type == SEMANTIC:
        semantic_errors.append(complete_message)


def get_all_errors():
    return lexical_errors + syntax_errors + semantic_errors


class SemanticException(Exception):
    def __init__(self, line, pos_in_line, message):
        self.line = line
        self.pos_in_line = pos_in_line
        self.message = message


class UndefinedIDException(SemanticException): pass
class UnsupportedOperation(SemanticException): pass
class FunctionUnfoundException(SemanticException): pass