"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing


class JackTokenizer:
    """Removes all comments from the input stream and breaks it
    into Jack language tokens, as specified by the Jack grammar.
    
    # Jack Language Grammar

    A Jack file is a stream of characters. If the file represents a
    valid program, it can be tokenized into a stream of valid tokens. The
    tokens may be separated by an arbitrary number of whitespace characters, 
    and comments, which are ignored. There are three possible comment formats: 
    /* comment until closing */ , /** API comment until closing */ , and 
    // comment until the lines end.

    - xxx: quotes are used for tokens that appear verbatim (terminals).
    - xxx: regular typeface is used for names of language constructs 
           (non-terminals).
    - (): parentheses are used for grouping of language constructs.
    - x | y: indicates that either x or y can appear.
    - x?: indicates that x appears 0 or 1 times.
    - x*: indicates that x appears 0 or more times.

    ## Lexical Elements

    The Jack language includes five types of terminal elements (tokens).

    - keyword: 'class' | 'constructor' | 'function' | 'method' | 'field' | 
               'static' | 'var' | 'int' | 'char' | 'boolean' | 'void' | 'true' |
               'false' | 'null' | 'this' | 'let' | 'do' | 'if' | 'else' | 
               'while' | 'return'
    - symbol: '{' | '}' | '(' | ')' | '[' | ']' | '.' | ',' | ';' | '+' | 
              '-' | '*' | '/' | '&' | '|' | '<' | '>' | '=' | '~' | '^' | '#'
    - integerConstant: A decimal number in the range 0-32767.
    - StringConstant: '"' A sequence of Unicode characters not including 
                      double quote or newline '"'
    - identifier: A sequence of letters, digits, and underscore ('_') not 
                  starting with a digit. You can assume keywords cannot be
                  identifiers, so 'self' cannot be an identifier, etc'.

    ## Program Structure

    A Jack program is a collection of classes, each appearing in a separate 
    file. A compilation unit is a single class. A class is a sequence of tokens 
    structured according to the following context free syntax:
    
    - class: 'class' className '{' classVarDec* subroutineDec* '}'
    - classVarDec: ('static' | 'field') type varName (',' varName)* ';'
    - type: 'int' | 'char' | 'boolean' | className
    - subroutineDec: ('constructor' | 'function' | 'method') ('void' | type) 
    - subroutineName '(' parameterList ')' subroutineBody
    - parameterList: ((type varName) (',' type varName)*)?
    - subroutineBody: '{' varDec* statements '}'
    - varDec: 'var' type varName (',' varName)* ';'
    - className: identifier
    - subroutineName: identifier
    - varName: identifier

    ## Statements

    - statements: statement*
    - statement: letStatement | ifStatement | whileStatement | doStatement | 
                 returnStatement
    - letStatement: 'let' varName ('[' expression ']')? '=' expression ';'
    - ifStatement: 'if' '(' expression ')' '{' statements '}' ('else' '{' 
                   statements '}')?
    - whileStatement: 'while' '(' 'expression' ')' '{' statements '}'
    - doStatement: 'do' subroutineCall ';'
    - returnStatement: 'return' expression? ';'

    ## Expressions
    
    - expression: term (op term)*
    - term: integerConstant | stringConstant | keywordConstant | varName | 
            varName '['expression']' | subroutineCall | '(' expression ')' | 
            unaryOp term
    - subroutineCall: subroutineName '(' expressionList ')' | (className | 
                      varName) '.' subroutineName '(' expressionList ')'
    - expressionList: (expression (',' expression)* )?
    - op: '+' | '-' | '*' | '/' | '&' | '|' | '<' | '>' | '='
    - unaryOp: '-' | '~' | '^' | '#'
    - keywordConstant: 'true' | 'false' | 'null' | 'this'
    
    Note that ^, # correspond to shiftleft and shiftright, respectively.
    """

    def __init__(self, input_stream: typing.TextIO) -> None:
        """Opens the input stream and gets ready to tokenize it.

        Args:
            input_stream (typing.TextIO): input stream.
        """
        input_lines = input_stream.read().splitlines()

        # Each element in this list, is a list that 
        # represents tokens parsed from one line.
        self.__tokens_lines = []
        
        # Parsing lines in the following way:
        # String constant tokens are stored in one element in the
        # array even if they're included in a comment.
        for i in range(len(input_lines)):
            last_add = -1
            new_line = []
            curr = -1
            while curr+1 < len(input_lines[i]):
                curr += 1
                if input_lines[i][curr] == '"':
                    closing_str = input_lines[i].find('"', curr+1)
                    if closing_str == -1:
                        new_line.extend(input_lines[i][last_add+1:].split())
                        break
                    else:
                        new_line.extend(input_lines[i][last_add+1:curr].split())
                        new_line.append(input_lines[i][curr:closing_str+1])
                        last_add = closing_str
                        curr = closing_str
                else:
                    if curr == len(input_lines[i])-1:
                        new_line.extend(input_lines[i][last_add+1:].split())
            # Skip empty lines
            if len(new_line) > 0:
                self.__tokens_lines.append(new_line)

        # Resetting current token to beginning of file.
        self.__line_index = -1
        self.__token_index = -1
        self.__token_range = (-1, -1)

    def __find_next_token(self) -> list:
        """Returns the next token, that isn't a comment or whitespace
        
        Return values:
        (x,y) tuple such that x is the line number, and y is the token index
        None in case there are no tokens left in the current file."""

        tmp_line = self.__line_index
        tmp_token = self.__token_index
        if tmp_line != -1:
            token_full = self.__tokens_lines[tmp_line][tmp_token]
            (first, last) = self.__token_range

            if last+1 < len(token_full):
                parsed_token = self.__parse_token(token_full, last+1)
                if parsed_token is None:
                    return None
                
                return [tmp_line, tmp_token, parsed_token[0], parsed_token[1]]
        # This flag indicates that we have met a "/*" 
        # and we are expecting the closing "*/"
        comment_multi_line = False
        tmp_token += 1

        tmp_line = tmp_line if tmp_line != -1 else 0

        while tmp_line < len(self.__tokens_lines):
            while tmp_token < len(self.__tokens_lines[tmp_line]):
                token = self.__tokens_lines[tmp_line][tmp_token]
                # Skip empty 
                if len(token) == 0:
                    tmp_token += 1
                    continue

                if comment_multi_line:
                    comment_ending = token.find("*/")
                    if comment_ending != -1:
                        comment_multi_line = False
                        
                        # move to next token properly
                        if comment_ending != len(token)-2:
                            self.__tokens_lines[tmp_line].insert(tmp_token+1, token[comment_ending+2:])
                            self.__tokens_lines[tmp_line][tmp_token] = token[:comment_ending+2]

                    tmp_token += 1
                    continue
                
                if token[0] != '"':
                    comment_starting1 = token.find("/*")
                    if comment_starting1 > 0:
                        self.__tokens_lines[tmp_line].insert(tmp_token+1, token[comment_starting1:])
                        self.__tokens_lines[tmp_line][tmp_token] = token[:comment_starting1]
                        continue

                    comment_starting2 = token.find("//")
                    if comment_starting2 > 0:
                        self.__tokens_lines[tmp_line].insert(tmp_token+1, token[comment_starting2:])
                        self.__tokens_lines[tmp_line][tmp_token] = token[:comment_starting2]
                        continue

                # In this case, we are starting a multi-line comment
                # We set the proper flag to 'True', and start looking 
                # for the closing '*/'
                if token[:2] == "/*" or token[:3] == "/**":
                    comment_multi_line = True
                    tmp_token += 1
                    continue

                # Skip one complete line.
                if token[:2] == "//":
                    break

                # We found a good token, parse it.
                token_full = self.__tokens_lines[tmp_line][tmp_token]
                parsed_token = self.__parse_token(token_full, 0)
                if parsed_token is None:
                    return None
                return [tmp_line, tmp_token, parsed_token[0], parsed_token[1]]
            
            # Update indexes properly to move to next line.
            tmp_token = 0
            tmp_line += 1
    
        # We found no token yet, then return None.
        return None


    def has_more_tokens(self) -> bool:
        """Do we have more tokens in the input?

        Returns:
            bool: True if there are more tokens, False otherwise.
        """
        next_token = self.__find_next_token()
        return False if next_token is None else True
        
    def __parse_token(self, token, first) -> tuple:
        # Check if it's a string.
        if token[first] == '"':
            return (first, token.find('"', first+1))

        # Check if it's a symbol
        elif token[first] in { '{' , '}' , '(' , ')' , '[' , ']' , '.' , ',' , ';' , '+' , 
              '-' , '*' , '/' , '&' , '|' , '<' , '>' , '=' , '~' , '^' , '#' }:
            return (first, first)

        # check if it's an integer constant.
        elif token[first].isnumeric():
            for i in range(first+1, len(token)):
                if not token[i].isnumeric():
                    return (first, i-1)
                
            return (first, len(token)-1)
            
        # keyword
        elif token[first].isalpha():
            keyword_dict = {'class' , 'constructor' , 'function' , 
                            'method' , 'field' , 'static' , 
                            'var' , 'int' , 'char' , 'boolean' , 'void' , 
                            'true' , 'false' , 'null' , 'this' , 'let' , 'do' , 
                            'if' , 'else' , 'while' , 'return'}
            last = -1
            identifier = False
            for i in range(first+1, len(token)):
                if token[i] == '_' or token[i].isnumeric():
                    identifier = True
                    break

                if token[i].isalpha():
                    continue
                last = i-1
                break
            else:
                last = len(token)-1

            if not identifier and token[first:last+1] in keyword_dict:
                return (first, last)
        
        # identifier
        for i in range(first, len(token)):
            if not (token[i].isnumeric() or token[i].isalpha() or token[i] == '_'):
                return (first, i-1)
        return (first, len(token)-1)
            

    def advance(self) -> None:
        """Gets the next token from the input and makes it the current token. 
        This method should be called if has_more_tokens() is true. 
        Initially there is no current token.
        """
        next_token_info = self.__find_next_token()
        self.__line_index = next_token_info[0]
        self.__token_index = next_token_info[1]
        self.__token_range = (next_token_info[2], next_token_info[3])

    def peek(self) -> tuple:
        next_token_info = self.__find_next_token()
        if next_token_info:
            line = next_token_info[0]
            token = next_token_info[1]
            first, last = next_token_info[2], next_token_info[3]
            token_full = self.__tokens_lines[line][token]
            return token_full[first:last+1]
        return None

    def token_type(self) -> str:
        """
        Returns:
            str: the type of the current token, can be
            "KEYWORD", "SYMBOL", "IDENTIFIER", "INT_CONST", "STRING_CONST"
        """
        token_full = self.__tokens_lines[self.__line_index][self.__token_index]
        first, last = self.__token_range
        token = token_full[first:last+1]
        if token[0] == '"':
            return "STRING_CONST"
        
        if token in { '{' , '}' , '(' , ')' , '[' , ']' , '.' , ',' , ';' , '+' , 
              '-' , '*' , '/' , '&' , '|' , '<' , '>' , '=' , '~' , '^' , '#' }:
            return "SYMBOL"
        
        if token in {'class' , 'constructor' , 'function' , 'method' , 'field' , 
               'static' , 'var' , 'int' , 'char' , 'boolean' , 'void' , 'true' ,
               'false' , 'null' , 'this' , 'let' , 'do' , 'if' , 'else' , 
               'while' , 'return'}:
            return "KEYWORD"
        
        if token.isnumeric():
            return "INT_CONST"

        return "IDENTIFIER"
    
    def keyword(self) -> str:
        """
        Returns:
            str: the keyword which is the current token.
            Should be called only when token_type() is "KEYWORD".
            Can return "CLASS", "METHOD", "FUNCTION", "CONSTRUCTOR", "INT", 
            "BOOLEAN", "CHAR", "VOID", "VAR", "STATIC", "FIELD", "LET", "DO", 
            "IF", "ELSE", "WHILE", "RETURN", "TRUE", "FALSE", "NULL", "THIS"
        """
        token_full = self.__tokens_lines[self.__line_index][self.__token_index]
        first, last = self.__token_range
        token = token_full[first:last+1]
        return token

    def symbol(self) -> str:
        """
        Returns:
            str: the character which is the current token.
            Should be called only when token_type() is "SYMBOL".
            Recall that symbol was defined in the grammar like so:
            symbol: '{' | '}' | '(' | ')' | '[' | ']' | '.' | ',' | ';' | '+' | 
              '-' | '*' | '/' | '&' | '|' | '<' | '>' | '=' | '~' | '^' | '#'
        """
        token_full = self.__tokens_lines[self.__line_index][self.__token_index]
        first, last = self.__token_range
        token = token_full[first:last+1]
        return token

    def identifier(self) -> str:
        """
        Returns:
            str: the identifier which is the current token.
            Should be called only when token_type() is "IDENTIFIER".
            Recall that identifiers were defined in the grammar like so:
            identifier: A sequence of letters, digits, and underscore ('_') not 
                  starting with a digit. You can assume keywords cannot be
                  identifiers, so 'self' cannot be an identifier, etc'.
        """
        token_full = self.__tokens_lines[self.__line_index][self.__token_index]
        first, last = self.__token_range
        token = token_full[first:last+1]
        return token

    def int_val(self) -> int:
        """
        Returns:
            str: the integer value of the current token.
            Should be called only when token_type() is "INT_CONST".
            Recall that integerConstant was defined in the grammar like so:
            integerConstant: A decimal number in the range 0-32767.
        """
        token_full = self.__tokens_lines[self.__line_index][self.__token_index]
        first, last = self.__token_range
        token = token_full[first:last+1]
        return int(token)

    def string_val(self) -> str:
        """
        Returns:
            str: the string value of the current token, without the double 
            quotes. Should be called only when token_type() is "STRING_CONST".
            Recall that StringConstant was defined in the grammar like so:
            StringConstant: '"' A sequence of Unicode characters not including 
                      double quote or newline '"'
        """
        token_full = self.__tokens_lines[self.__line_index][self.__token_index]
        first, last = self.__token_range
        token = token_full[first:last+1]
        return token[1:-1]
