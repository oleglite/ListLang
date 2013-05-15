#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Oleg Beloglazov'

import sys
import os
import argparse

import antlr3
import antlr3.tree
from antlr3.dottreegen import DOTTreeGenerator

import jtrans

from ListLangLexer import ListLangLexer
from ListLangParser import ListLangParser
from ListLangWalker import ListLangWalker




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


def getChildren(tree):
    return [tree.getChild(i) for i in xrange(tree.getChildCount())]


def test_examples(examples_dir):
    # FIXME: реализовать функцию
    pass


def main():
    # Parse command line arguments
    args_parser = argparse.ArgumentParser(description='Compile listlang source files.')
    args_parser.add_argument('src_filename', type=str, help='path to source file')
    args_parser.add_argument('dest_filename', type=str, help='path to output compiled file')
    args_parser.add_argument('--tokens', '-t', dest='tokens_filename', help='write token stream to file')
    args_parser.add_argument('--expamles', '-e', dest='examples_dir', help='try to parse examples, print errors if exists')
    args = args_parser.parse_args()

    if args.examples_dir:
        test_examples(args.examples_dir)

    # Run lexer
    char_stream = antlr3.ANTLRFileStream(args.src_filename, encoding='utf8')
    lexer = ListLangLexer(char_stream)
    tokens = antlr3.CommonTokenStream(lexer)

    if args.tokens_filename:
        tokens_out(tokens.getTokens(), args.tokens_filename)

    # Get AST tree
    parser = ListLangParser(tokens)
    ast = parser.program().tree

    nodes = antlr3.tree.CommonTreeNodeStream(ast)
    nodes.setTokenStream(tokens)
    
    walker = ListLangWalker(nodes)
    '''
    if parser.errors > 0:
        print 'Total: %d errors' % parser.errors
        sys.exit(1)
    '''
    try:
        target_file = open(args.dest_filename, 'w')
        target_code = walker.program()
        if target_code:
            target_file.write(target_code)
    except jtrans.SemanticException as e:
            print 'Exception', str(e)
            sys.exit(1)




if __name__ == "__main__":
    main()