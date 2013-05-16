# -*- coding: utf-8 -*-
import os
import re
import unittest
import logging
from collections import defaultdict

logging.getLogger().setLevel(logging.NOTSET)


class CodeScanner(object):
    '''
    返回源码文件
    '''
    code_ext_names = ['.cs', '.java', '.js', '.py', '.h', '.c', '.cpp']

    def __init__(self, code_dir):
        self.code_dir = code_dir

    def get_sources(self):
        for root, dirs, files in os.walk(self.code_dir):
            for file in files:
                if os.path.splitext(file)[1] in self.code_ext_names:
                    logging.debug('CodeScanner:%s', os.path.join(root, file))
                    yield os.path.join(root, file)
         

class TokenScanner(object):
    '''
    返回某源码文件里的符号流
    '''

    patt_tokens = r"""
    (?P<comment1>(?:\/\/).*)                                # c的单行注释
    |(?P<regex>\/(?:\\\/)*.*?\/[a-zA-Z]?)                   # js的正则表达式字面量
    |(?P<comment2>\/\*[\s\S]*?\*\/)                         # c的多行注释
    |(?P<string1>:\'\'\'[\s\S]*?\'\'\')                     # python多行字符串
    |(?P<string2>\"\"\"[\s\S]*?\"\"\")                      # python多行字符串
    |(?P<comment3>\#.*)                                     # python shell的单行注释
    |(?P<operator1>(?:\+\+)                                 # 多字符运算符
        |(?:\-\-) |(?:\-\>) |(?:\>\>) |(?:\<\<) |(?:\>\=)
        |(?:\<\=) |(?:\!\=) |(?:\+\=) |(?:\-\=) |(?:\=\=)
        |(?:\*\=) |(?:\/\=) |(?:\%\=) |(?:\&\=) |(?:\<\<\=)
        |(?:\>\>\=) |(?:\?\?) |(?:\?\:)
     )
    |(?P<operator2>[\+\-!\.\(\)\[\]\{\}~&\/\*%\<\>\|\?=:])  # 单字符运算符
    |(?P<number>\d+(?:\.\d+)?(?:[Ee]+[\+\-]?\d+)?[a-zA-Z]?) # 数字类型
    |(?P<identity>[a-zA-Z_]+\w*)                            # 标识符
    |(?P<string3>\"(?:(?:\\\")*[^\"])*?\")                  # 字符串
    |(?P<string4>\'(?:(?:\\\')*[^\'])*?\')                  # 字符串
    """
    re_tokens = re.compile(patt_tokens, re.VERBOSE)

    def __init__(self, code):
        self.code = code

    def _get_token_type(self, result):
        groupdict = result.groupdict().items()
        token_type = filter(lambda d: d[1] is not None, groupdict)[0][0]
        return token_type.rstrip('123456789')

    def get_tokens(self):
        for result in self.re_tokens.finditer(self.code):
            token_type = self._get_token_type(result)
            token = result.group()
            if token_type == 'identity' and len(token) > 3:
                yield token


class KeywordFilter(object):
    '''
    过滤掉各语言的关键字
    '''
    python_keywords = '''
    and continue else for import not raise assert def except from in or return break
    del exec global is pass try class elif finally if lambda print while
    '''

    java_keywords = '''
    abstract assert boolean break byte case catch char class continue default do double
    else enum extends final finally float for if implements import instanceof int interface
    long native new package private protected public return strictfp short static super switch
    synchronized this throw throws transient try void volatile while
    '''

    c_keywords = '''
    asm do if return typedef auto double inline short typeid bool dynamic_cast int signed
    typename break else long sizeof union case enum mutable static unsigned catch explicit
    namespace static_cast using char export new struct virtual class extern operator switch
    void const false private template volatile const_cast float protected this wchar_t continue
    for public throw while default friend register true delete goto reinterpret_cast try
    '''

    javascript_keywords = '''
    break   case    catch   continue    default delete  do  else    finally for function
    if  in  instanceof  new return  switch  this    throw   try typeof  var void    while   with
    '''

    csharp_keywords = '''
    abstract event new struct as explicit null switch base extern object this bool false operator
    throw break finally out true byte fixed override try case float params typeof catch for private
    uint char foreach protected ulong checked goto public unchecked class if readonly unsafe const
    implicit ref ushort continue in return using decimal int sbyte virtual default interface sealed
    volatile delegate internal short void do is sizeof while double lock stackalloc else long static
    enum namespace string
    '''

    keywords = python_keywords + java_keywords + c_keywords + javascript_keywords + csharp_keywords
    keywords = set(keywords.split())

    def __init__(self, tokens):
        self.tokens = tokens

    def get_tokens(self):
        for token in self.tokens:
            if token not in self.keywords:
                yield token


class TokensHandler(object):
    '''
    对tokens进行计数，排序
    '''
    def __init__(self, tokens):
        self.token_counters = defaultdict(int)
        for token in tokens:
            self.token_counters[token] += 1

    def get_tokens(self):
        tokens = sorted(self.token_counters.items(), key=lambda d: d[1], reverse=True)
        return tokens
        

def get_tokens(project):
    print '*' * 20, project, '*' * 20
    scanner = CodeScanner(os.path.join('./codes', project))
    files = scanner.get_sources()

    all_tokens = []
    for file in files:
        code = open(file).read()
        scanner = TokenScanner(code)
        tokens = scanner.get_tokens()
        all_tokens.extend(tokens)

    keywordfilter = KeywordFilter(all_tokens)
    filter_tokens = keywordfilter.get_tokens()
    return filter_tokens


def handler_tokens(project, filter_tokens):
    handler = TokensHandler(filter_tokens)
    results = handler.get_tokens()

    result_file = open(os.path.join('./results', project), 'w')
    for token, count in results[:1000]:
        print '%s %s' % (token, count)
        result_file.write('%s %s\n' % (token, count))

    result_file.close()


class CodeScannerTestCase(unittest.TestCase):
    def test_get_sources(self):
        code_dir = './codes/fortest'

        scanner = CodeScanner(code_dir)
        results = set(scanner.get_sources())

        expect = ['a.c', 'a.cs', 'a.h', 'a.java']
        expect = set(map(lambda x: os.path.join(code_dir, x), expect))

        self.assertSetEqual(expect, results)


class TokenScannerTestCase(unittest.TestCase):
    def test_get_names(self):
        code = '''
            // comment
            aaaa bbb_ccc  DddEee + ==
            /*
            fff
            ggg
            */
            "hhh", 'iii'
            # jjj
        '''
        scanner = TokenScanner(code)
        results = list(scanner.get_tokens())
        expect = ['aaaa', 'bbb_ccc', 'DddEee']

        self.assertListEqual(results, expect)


class KeywordFilterTestCase(unittest.TestCase):
    def test_get_tokens(self):
        tokens = ['final', 'for', 'TokenScanner', 'is', 'unittest', 'while']
        keywordfilter = KeywordFilter(tokens)
        results = list(keywordfilter.get_tokens())

        expect = ['TokenScanner', 'unittest']

        self.assertListEqual(results, expect)


class TokensHandlerTestCase(unittest.TestCase):
    def test_get_token(self):
        tokens = ['b', 'b', 'a', 'a', 'a', 'c']
        handler = TokensHandler(tokens)
        results = handler.get_tokens()
        expect = [('a', 3), ('b', 2), ('c', 1)]
        self.assertListEqual(results, expect)


if __name__ == '__main__':
    import sys
    if len(sys.argv) == 1:
        unittest.main(verbosity=2)
        sys.exit()

    project = sys.argv[1]
    if project != 'all':
        tokens = get_tokens(project)
        handler_tokens(project, tokens)
        sys.exit()
    else:
        all_tokens = []
        for code_dir in os.listdir('./codes'):
            if os.path.isdir(os.path.join('./codes', code_dir)):
                tokens = get_tokens(code_dir)
                handler_tokens(code_dir, tokens)
                all_tokens.extend(tokens)

        handler_tokens('all', all_tokens)
        sys.exit()
