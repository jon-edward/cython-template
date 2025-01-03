## Taken from https://github.com/RaubCamaioni/CythonPEG/blob/main/cython_peg.py 
## with some modifications. Namely, hiding cdef functions from being generated in class definitions 
## and fixing nested docstrings.

from pyparsing import *
import textwrap
from functools import partial
from typing import Union, List, IO, Tuple, Callable

def partial_cython_2_python(type_str: str) -> str:
    """partial type component"""
    return type_str

def complete_cython_2_python(type_str: str) -> str:
    """complete type component"""
    return type_str

# indent used
INDENT = "    "

def set_indent(indent: str):
    global INDENT
    INDENT = indent
    
def set_type_converter_partial(func: Callable[[str], str]):
    global partial_cython_2_python
    partial_cython_2_python = func
    
def set_type_converter_complete(func: Callable[[str], str]):
    global complete_cython_2_python
    complete_cython_2_python = func

# helper functions
def parentheses_suppress(content: ParserElement) -> ParserElement:
    return Suppress("(") + Optional(content) + Suppress(")")

def bracket_suppress(content: ParserElement) -> ParserElement:
    return Suppress("[") + Optional(content) + Suppress("]")

def curl_suppress(content: ParserElement) -> ParserElement:
    return Suppress("{") + Optional(content) + Suppress("}")

def extend_empty(tokens: List[ParserElement], n: int):
    if len(tokens) == 0:
        tokens.extend([""]*n)
    return tokens

def EmptyDefault(input: ParserElement, n: int=1) -> ParserElement:
    """returns empty string ParserResult of size n"""
    return Optional(input).addParseAction(partial(extend_empty, n=n))

# literal definitions
CLASS = Literal("class")
STRUCT = Literal("struct")
DEF = Literal("def")
CPDEF = Literal("cpdef")
CDEF = Literal("cdef")
STRUCT = Literal("struct")
DATACLASS = Literal("dataclass")
DOT = Suppress('.')
COMMA = Suppress(',')
EQUALS = Suppress('=')
COLON = Suppress(':')
PLUS = Literal('+')
MINUS = Literal('-')
MULT = Literal('*')
DIV = Literal('/')
RETURN = Literal("->")
SELF = Literal("self")

# object definitions
VARIABLE = Word("_"+alphanums+"_"+"*"+".")
INTEGER = Word("+-" + nums) + ~FollowedBy(".")
FLOAT = Combine(Word("+-" + nums) + "." + Word(nums))
TRUE = Literal("True")
FALSE = Literal("False")
NONE = Literal("None")
STRING = QuotedString(quoteChar="'", unquote_results=False) | QuotedString(quoteChar='"', unquote_results=False)
ENUM = Word(alphanums + '.' + '_')
PRIMATIVE = (FLOAT | INTEGER | TRUE | FALSE | NONE | STRING)
OBJECT = Forward()
MEMMORYVIEW = Word(":" + nums) + (FollowedBy(Literal(",")) | FollowedBy(Literal("]")))
LIST = Group(bracket_suppress(delimitedList(OBJECT)))("list")
TUPLE = Group(parentheses_suppress(delimited_list(OBJECT)))("tuple")
DICT = Group(curl_suppress(delimitedList(Group(OBJECT + Suppress(":") + OBJECT))))("dict")
SET = Group(curl_suppress(delimited_list(OBJECT)))("set")
CLASS_CONSTRUCTOR = Group(VARIABLE+delimited_list(parentheses_suppress(OBJECT)))("class")
NONPRIMATIVE = (LIST | TUPLE | DICT | SET | ENUM | CLASS_CONSTRUCTOR )
OBJECT << (NONPRIMATIVE | PRIMATIVE)

# EXPRESSION definition
EXPRESSION = Forward()
ATOM = OBJECT | Group(Literal('(') + EXPRESSION + Literal(')'))
EXPRESSION << infixNotation(ATOM, [(MULT | DIV, 2, opAssoc.LEFT), (PLUS | MINUS, 2, opAssoc.LEFT),])

# IMPORTS
IMPORT = Literal("import")
FROM = Literal("from")
import_as_definition = Group(VARIABLE + EmptyDefault(Suppress(Literal("as")) + VARIABLE))
import_definition = Group(Suppress(IMPORT) + Group(delimited_list(import_as_definition)))("import")
from_import_defintion = Group(Suppress(FROM) + VARIABLE + Suppress(IMPORT) + Optional(Suppress(Literal('('))) + Group(delimited_list(import_as_definition)) + Optional(Suppress(Literal(')'))))("from")
import_and_from_import_definition = (from_import_defintion | import_definition)("import")
import_section = OneOrMore(import_and_from_import_definition)("import_section")

# default_definition (python and cython)
default_definition = (EQUALS + EXPRESSION)("default")

# type definitions (python and cython)
type_forward = Forward()
type_bracket = bracket_suppress(delimited_list(type_forward))
type_definition = Group((VARIABLE | MEMMORYVIEW) + EmptyDefault(Group(type_bracket)) + EmptyDefault(default_definition + ~Literal(')')))("type")
type_forward << type_definition

# return definitions
python_return_definition = Suppress(RETURN) + type_definition

# argument definition
python_argument_definition = Group(VARIABLE("name") + EmptyDefault(COLON + type_definition, 1) + EmptyDefault(default_definition))("argument")
cython_argument_definition = Group((type_definition + VARIABLE("name") + EmptyDefault(default_definition)) | SELF)("arguments")

# arguments definition
python_arguments_definition = parentheses_suppress(delimited_list(python_argument_definition))("arguments")
cython_arguments_definition = parentheses_suppress(delimited_list(cython_argument_definition))("arguments")

# recursive definitions 
recursive_class_definition = Forward()
recursive_def_definition = Forward()
recursive_cython_def_definition = Forward()
recursive_cython_class_definition = Forward()
recursive_cython_struct_definition = Forward()

# docstring definition
docstring = QuotedString('"""', multiline=True, escQuote='""""')

# python class definition
python_class_parent = Word(alphanums+'_'+'.')
python_class_arguments = parentheses_suppress(python_class_parent)
python_class_declaration = Group(Suppress(CLASS) + VARIABLE + EmptyDefault(python_class_arguments) + Suppress(":"))("class_declaration")
python_class_body = IndentedBlock(recursive_class_definition, recursive=True)
python_class_definition = (python_class_declaration + Optional(docstring, default="") + python_class_body)("class")

# python function definitions
python_function_declaration = Group(Suppress(DEF) + VARIABLE + Group(python_arguments_definition) + Optional(python_return_definition, "") + Suppress(":"))("def_declaration")
python_function_body = IndentedBlock(recursive_def_definition, recursive=True)
python_function_definition = (python_function_declaration + Optional(docstring, default="") + python_function_body)("def")

# cython function definition
cython_cpdef_function_declaration = Group(Suppress((CPDEF)) + Optional(type_definition + ~cython_arguments_definition, default="") + VARIABLE + Group(cython_arguments_definition) + Optional(VARIABLE, default="") + Suppress(":"))("cpdef_function_declaration")
cython_cdef_function_declaration = Group(Suppress(CDEF) + Optional(type_definition + ~cython_arguments_definition, default="") + VARIABLE + Group(cython_arguments_definition) + Optional(VARIABLE, default="") + Suppress(":"))("cdef_function_declaration")
cython_function_body = IndentedBlock(recursive_cython_def_definition, recursive=True)
cython_function_definition = ((python_function_declaration | cython_cpdef_function_declaration | cython_cdef_function_declaration) + Optional(docstring, default="") + cython_function_body)("cdef")

# cython class definition
cython_class_declaration = Group(Suppress(CDEF + CLASS) + VARIABLE +  EmptyDefault(python_class_arguments) + Suppress(":"))("cclass_declaration")
cython_class_body = IndentedBlock(recursive_cython_class_definition, recursive=True)
cython_class_definition = (cython_class_declaration + Optional(docstring, default="") + cython_class_body)("cclass")

# cython struct definition
cython_struct_declaration = Group(Suppress(CDEF + STRUCT) + VARIABLE + Suppress(":"))
cython_struct_body = IndentedBlock(Group(type_definition + VARIABLE), recursive=True)
cython_struct_definition = (cython_struct_declaration + Optional(docstring, default="") + cython_struct_body)("cstruct")

# dataclass definition
dataclass_declaration = (Suppress(Literal("@") + DATACLASS + CLASS) + VARIABLE + Suppress(":"))
dataclass_body = IndentedBlock(rest_of_line, recursive=True)
dataclass_definition = (dataclass_declaration + Optional(docstring, default="") + dataclass_body)("dataclass")

# recursive definitions (could be individually assigned for parsing performance improvements: i.e cython_class never defined inside python_function)
definitions = (python_class_definition | python_function_definition | cython_function_definition | cython_class_definition | cython_struct_definition | restOfLine)
recursive_class_definition         << definitions
recursive_def_definition           << definitions
recursive_cython_def_definition    << definitions
recursive_cython_class_definition  << definitions
recursive_cython_struct_definition << definitions

# full recursive definition
cython_parser = python_class_definition | python_function_definition | cython_function_definition | cython_class_definition | cython_struct_definition | dataclass_definition | import_section

def expression2str(expression: Union[ParseResults, str]):
    """EXPRESSION parsed tree to string"""
    
    if isinstance(expression, ParseResults):
        expression_string = ""

        if expression.getName() == 'list':
            expression_string += "[" + ', '.join(expression2str(e) for e in expression) + "]"

        elif expression.getName() == 'set':
            expression_string += "{" + ', '.join(expression2str(e) for e in expression) + "}"
            
        elif expression.getName() == 'tuple':
            expression_string += "(" + ', '.join(expression2str(e) for e in expression) + ")"
            
        elif expression.getName() == 'dict':
            expression_string += "{" + ', '.join(f"{expression2str(k)} : {expression2str(v)}" for k, v in expression) + "}"
        else:
            for e in expression:
                expression_string += expression2str(e)

        return expression_string
            
    elif isinstance(expression, str):
        return expression

def type2str(type_tree: ParseResults):
    """type_definition parsed tree to string"""
    
    def _type2_str(type_tree: ParseResults):
        type_name, type_bracket, type_default = type_tree
        
        if type_bracket:
            bracket_str = "["+", ".join(_type2_str(arg) for arg in type_bracket)+"]" if type_bracket else ""
        else:
            bracket_str = ""
            
        type_default_str = f'={expression2str(type_default)}' if type_default else ''
        
        return f"{partial_cython_2_python(type_name)}{bracket_str}{type_default_str}"
    
    return complete_cython_2_python(_type2_str(type_tree))

def arg2str(arg: ParseResults):
    """python_argument_definition parsed tree to string"""

    arg_name, arg_type, arg_default = arg

    if isinstance(arg_type, ParseResults):
        type_str = type2str(arg_type)
    else:
        type_str = ""

    type_str = f': {type_str}' if type_str else ''
    arg_default_str = f'={expression2str(arg_default)}' if arg_default else ''

    return f'{arg_name}{type_str}{arg_default_str}'
    
def args2str(args: ParseResults, newlines: bool=False):
    """python_arguments_definition parsed tree to string"""
    joiner = f',\n{INDENT}' if newlines else ', '
    return joiner.join(arg2str(arg) for arg in args)

def def2str(result: ParseResults):
    """function_definition parsed tree to string"""
    
    declaration, docs, _ = result
    name, args, ret = declaration

    docs = textwrap.indent(textwrap.dedent(docs), INDENT)
            
    return_str = type2str(ret) if ret else ""
    return_str = f" -> {return_str}" if return_str else ''
    doc_str = f'\n{INDENT}\"""{docs}{INDENT}\"""' if docs else ''
    
    arg_str = args2str(args)
    if len(arg_str) > 100:
        arg_str = args2str(args, newlines=True)

    return f"def {name}({arg_str}){return_str}:{doc_str}\n{INDENT}...\n"

def cythonargs2str(args: ParseResults, newlines: bool=False):
    """cython_arguments_definition parsed tree to string"""

    def format_arg(arg):
        if arg[0] == "self": return "self" # handle unique case cdef inside class
        t, n, d = arg
        type_str = type2str(t)
        default_str = f' = {expression2str(d)}' if d else ''
        return f'{n}: {type_str}{default_str}'

    joiner = f',\n{INDENT}' if newlines else ', '
    return joiner.join([format_arg(arg) for arg in args])

def cdef2str(result: ParseResults):
    """cython_function_definition parsed tree to string"""
    declaration, docs, _ = result
    ret, name, args, _ = declaration

    docs = textwrap.indent(textwrap.dedent(docs), INDENT)
            
    doc_str = f'\n{INDENT}\"""{docs}{INDENT}\"""' if docs else ''
    ret_str = type2str(ret) if ret else "" 
    ret_str = f" -> {ret_str}" if ret_str else ''
    arg_str = cythonargs2str(args)
    if len(arg_str) > 100:
        arg_str = cythonargs2str(args, newlines=True)
    return f"def {name}({arg_str}){ret_str}:{doc_str}\n{INDENT}..." + '\n'

def enum2str(result: ParseResults):
    """python_class_definition parsed tree to string (enum)"""
    
    declaration, docs, body = result
    name, parent = declaration
            
    class_str = ""
    doc_str = f'\n{INDENT}\"""{docs}\"""' if docs else ''
    class_str += f"class {name}{f'({parent})' if parent else ''}:{doc_str}" + '\n'

    for b in body:
        class_str += INDENT + b + '\n'
        
    return class_str
            
def class2str(result: ParseResults):
    """python_class_definition parsed tree to string (enum)"""
    
    declaration, docs, body = result
    name, parent = declaration
    
    if parent == "Enum":
        return enum2str(result)
            
    doc_str = f'\n{INDENT}\"""{docs}\"""' if docs else ''
    class_str = f"class {name}{f'({parent})' if parent else ''}:{doc_str}\n\n"

    element_string = []
    for i, b in enumerate(body):
        
        if not isinstance(b, ParseResults):
            continue
        
        parser_name = b.getName()
        if parser_name == "class_declaration":
            result = (b, body[i+1], body[i+2])
            element_string.append(textwrap.indent(class2str(result), INDENT))

        elif parser_name == "def_declaration":
            result = (b, body[i+1], body[i+2])
            element_string.append(textwrap.indent(def2str(result), INDENT))
    
    if not len(element_string):
        class_str += f"{INDENT}...\n"
    else:
        class_str += "\n".join(element_string)

    return class_str

def struct2str(result):
    """cython_struct_definition parsed tree to string"""
    
    declaration, docs, body = result
    parent = ""
    
    class_str = ""
    doc_str = f'\n{INDENT}\"""{docs}\"""' if docs else ''
    class_str += f"class {declaration[0]}{f'({parent})' if parent else ''}:{doc_str}\n"

    element_string = []
    for b in body:
        type_str, name = b
        element_string.append(f"{INDENT}{name}: {type2str(type_str)}")
    
    return class_str + "\n".join(element_string) + '\n'

def cclass2str(result: ParseResults):
    """cython_class_definition parsed tree to string"""
    
    declaration, docs, body = result
    name, parent = declaration
                
    class_str = ""
    doc_str = f'\n{INDENT}\"""{docs}\"""' if docs else ''
    class_str += f"class {name}{f'({parent})' if parent else ''}:{doc_str}\n\n"

    element_string = []
    for i, b in enumerate(body):

        if not isinstance(b, ParseResults):
            continue
        
        parser_name = b.getName()
        if parser_name == "cclass_declaration":
            result = (b, body[i+1], body[i+2])
            element_string.append(textwrap.indent(cclass2str(result), INDENT))
        elif parser_name == "cpdef_function_declaration":
            result = (b, body[i+1], body[i+2])
            element_string.append(textwrap.indent(cdef2str(result), INDENT))
        elif parser_name == "def_declaration":
            result = (b, body[i+1], body[i+2])
            element_string.append(textwrap.indent(def2str(result), INDENT))
    
    if not len(element_string):
        class_str += f"{INDENT}...\n"
    else:
        class_str += "\n".join(element_string)
        
    return class_str

def name_alias_2_str(name, alias):
    alias_str = f" as {alias}" if alias else ""
    return f"{name}{alias_str}"
    
def import2str(result: ParseResults, newlines=True):
    """import2str_definition parsed tree to string"""
    
    import_str =""
    if len(result) == 1:
        import_str += f"import {', '.join(name_alias_2_str(n, a) for n, a in result[0])}"
        
    elif len(result) == 2:

        if newlines and len(result[1]) > 2:
            # import_str += f"from {result[0]} import (\n"
            # for i, r in enumerate(result[1]):
            #     import_str += f"{INDENT}{r}"
            #     import_str += "\n" if len(result[1]) == i+1 else ",\n"
            # import_str += ')'
            
            nl = '\n'
            tab = '\t'
            import_str += f"from {result[0]} import ({nl}{f',{nl}'.join(f'{tab}{name_alias_2_str(n, a)}' for n, a in result[1])}{nl})"
        else:
            import_str += f"from {result[0]} import {', '.join(name_alias_2_str(n, a) for n, a in result[1])}"
        
    return import_str

def import_section2str(result: ParseResults):
    """import_section2str_definition parsed tree to string"""
    return "\n".join([import2str(imp) for imp in result]) + '\n'

def dataclass2str(result: ParseResults):
    name, docs, body = result
    dataclass_str = ""
    dataclass_str += "@dataclass" + '\n'
    dataclass_str += f"class {name}:" + '\n'
    dataclass_str += f'{INDENT}\"""{docs}\"""\n' 
    dataclass_str += textwrap.indent(recursive_body(body), INDENT)
    return dataclass_str

def unimplimented2str(result: ParseResults):
    return ""

def recursive_body(body: ParseResults):
    """IndentedBlock(restOfLine) parsed tree to string"""
    element_string = []
    for b in body:
        
        if isinstance(b, ParseResults):
            element_string.append(textwrap.indent(recursive_body(b), INDENT))
            
        elif isinstance(b, str):
            element_string.append(b)
            
    return '\n'.join(element_string) + '\n'
    
def cython_string_2_stub(input_code: str) -> Tuple[str, str]:
    """tree traversal and translation of ParseResults to string representation"""
    
    # indentblock needs newline as sentinal
    input_code += "\n"
    
    # PEG top down scan generator
    tree = cython_parser.scan_string(input_code)
    
    # 3.8+ compatible switch
    parser = {
        "def": def2str,
        "cdef": cdef2str,
        "cclass": cclass2str,
        "cstruct": struct2str, 
        "class": class2str,
        "dataclass": dataclass2str,
        "import_section": import_section2str,
    }
    
    # ParseResults -> Python Stub Element
    def parse_branch(branch: Tuple[ParseResults, int, int]):
        result, start, end = branch
        return parser.get(result.getName(), unimplimented2str)(result), start, end
    tree_str, start, end = zip(*[parse_branch(b) for b in tree])
    
    # TODO: this code is ugly
    mutable_string = list(input_code+" ")
    for s, e in zip(start, end):
        for i in range(s, e):
            mutable_string[i] = ""
            
    stub_file = "\n".join(tree_str)
    unparsed_lines = "".join(mutable_string).strip()
    
    return stub_file, unparsed_lines

def cython_file_2_stub(file: IO[str]) -> Tuple[str, str]:
    with open(file, mode="r") as f:
        input_code = f.read()
    return cython_string_2_stub(input_code)
