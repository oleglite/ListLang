#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Oleg Beloglazov'

import sys
import os
import argparse
import antlr3
from generated.ListLangLexer import ListLangLexer
from generated.ListLangParser import ListLangParser


def tokens_out(tokens, tokens_filename):
    dir_name = os.path.dirname(tokens_filename)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    tokens_file = open(tokens_filename, 'w')

    for token in tokens:
        tokens_file.write('%3s |%3s: %s\n' %
                          (str(token.getTokenIndex()),
                           str(token.getType()),
                           repr(token.getText()))
        )


def main():
    # Parse command line arguments
    args_parser = argparse.ArgumentParser(description='Compile listlang source files.')
    args_parser.add_argument('src_filename', type=str, help='path to source file')
    args_parser.add_argument('--tokens', '-t', dest='tokens_filename', help='write token stream to file')
    args = args_parser.parse_args()

    # Run lexer
    char_stream = antlr3.ANTLRFileStream(args.src_filename, encoding='utf8')
    lexer = ListLangLexer(char_stream)
    tokens = antlr3.CommonTokenStream(lexer)
    #antlr3.CommonToken

    if args.tokens_filename:
        tokens_out(tokens.getTokens(), args.tokens_filename)

    parser = ListLangParser(tokens)
    ast = parser.program().tree


if __name__ == "__main__":
    main()