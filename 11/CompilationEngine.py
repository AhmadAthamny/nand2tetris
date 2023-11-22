"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing
from JackTokenizer import JackTokenizer
from SymbolTable import SymbolTable

class CompilationEngine:
    """Gets input from a JackTokenizer and emits its parsed structure into an
    output stream.
    """

    def __init__(self, input_stream: "JackTokenizer", output_stream) -> None:
        """
        Creates a new compilation engine with the given input and output. The
        next routine called must be compileClass()
        :param input_stream: The input stream.
        :param output_stream: The output stream.
        """
        self.__output_file = output_stream
        self.__tokenizer = input_stream
        self.__symbol_table = SymbolTable()
        self.__indentation = 0
        self.__class_name = None

        # Start compiling
        self.__tokenizer.advance()
        self.compile_class()

    def __indentation_inc(self) -> None:
        self.__indentation += 2

    def __indentation_dec(self) -> None:
        self.__indentation -= 2

    def __indentation_print(self) -> None:
        self.__output_file.write(" " * self.__indentation)

    def __open_bracket(self, tag: str) -> None:
        self.__indentation_print()
        self.__output_file.write("//<" + tag + ">\n")
        self.__indentation_inc()

    def __close_bracket(self, tag: str) -> None:
        self.__indentation_dec()
        self.__indentation_print()
        self.__output_file.write("//</" + tag + ">\n")

    def __eat(self) -> str:
        """
        Advances to next token, prints it, and advances again.
        """
        token_type = self.__tokenizer.token_type()
        self.__indentation_print()

        ret_val = None

        if token_type in {"KEYWORD", "SYMBOL", "IDENTIFIER"}:
            tag = token_type
            val_dict = {"KEYWORD": self.__tokenizer.keyword, "SYMBOL": self.__tokenizer.symbol, 
                        "IDENTIFIER": self.__tokenizer.identifier}
            return_val = tag.lower() 
        
        elif token_type == "INT_CONST":
            val = str(self.__tokenizer.int_val())
            return_val = val
        else:
            return_val = self.__tokenizer.string_val()
            
        if self.__tokenizer.has_more_tokens():
            self.__tokenizer.advance()

        return return_val

    def __TokenType(self, type: str) -> None:
        return self.__tokenizer.token_type() == type

    def __addSymbol(self, name: str, type: str, kind: str):
        if self.__symbol_table.kind_of(name) is None:
            self.__symbol_table.define(name, type, kind)

    def compile_class(self) -> None:
        """Compiles a complete class."""

        self.__eat()  # keyword class

        # Save current class name
        self.__class_name = self.__eat()  # identifier className
        
        self.__eat()  # symbol {
        
        # Compile field variables.
        self.compile_class_var_dec()

        self.__compile_class_subroutines()

        self.__eat() # symbol }

    def compile_class_var_dec(self) -> None:
        """Compiles a static declaration or a field declaration."""

        if self.__TokenType("KEYWORD"):
            while self.__tokenizer.keyword() in {"static", "field"}:
                var_kind = self.__eat()  # static/field 
                var_type = self.__eat()  # type
                var_name = self.__eat()  # varName
                self.__addSymbol(var_name, var_type, var_kind)

                while self.__tokenizer.symbol() != ';':
                    self.__eat()  # symbol ,
                    var_name = self.__eat()  # varName
                    self.__addSymbol(var_name, var_type, var_kind)
                    
                self.__eat()  # symbol ;

    def __compile_class_subroutines(self) -> None:
        # If we don't reach the '}' symbol, then there
        # are more subroutines to compile
        while not self.__TokenType("SYMBOL"):
            self.compile_subroutine()

    def compile_subroutine(self) -> None:
        """
        Compiles a complete method, function, or constructor.
        You can assume that classes with constructors have at least one field,
        you will understand why this is necessary in project 11.
        """
        self.__open_bracket("subroutineDec")
        self.__eat()  # constructor/method/function
        self.__eat()  # type
        self.__eat()  # subroutine name
        
        self.__eat()  # eat '('
        self.compile_parameter_list()
        self.__eat()  # eat ')'

        self.__compile_subroutine_body()
        self.__close_bracket("subroutineDec")

    def __compile_subroutine_body(self) -> None:
        self.__open_bracket("subroutineBody")
        self.__eat()  # eat '{'

        # Read subroutine var dec.
        if self.__TokenType("KEYWORD"):
            while self.__tokenizer.keyword() == "var":
                self.__open_bracket("varDec")
                self.__eat()  # var
                self.__eat()  # type
                self.__eat()  # varName

                while self.__tokenizer.symbol() != ';':
                    self.__eat()  # symbol ,
                    self.__eat()  # varName
                    
                self.__eat()  # symbol ;
                self.__close_bracket("varDec")

        # Read subroutine statements.
        self.compile_statements()

        self.__eat()  # eat '}'
        self.__close_bracket("subroutineBody")

    def compile_parameter_list(self) -> None:
        """Compiles a (possibly empty) parameter list, not including the 
        enclosing "()".
        """
        # Open bracket in any case, even if there are no parameters.
        self.__open_bracket("parameterList")

        if self.__TokenType("KEYWORD"):
            self.__eat()  # type
            self.__eat()  # parameter name

            # Eat more parameters
            while self.__tokenizer.symbol() != ')':
                self.__eat()  # eat ','
                self.__eat()  # eat type
                self.__eat()  # eat identifier

        self.__close_bracket("parameterList")

    def compile_var_dec(self) -> None:
        """Compiles a var declaration."""
        # Your code goes here!
        pass

    def compile_statements(self) -> None:
        """Compiles a sequence of statements, not including the enclosing 
        "{}".
        """
        self.__open_bracket("statements")
        while self.__tokenizer.keyword() in {"do", "let", "while", "return", "if"}:
            keyword = self.__tokenizer.keyword()

            if keyword == "do":
                self.compile_do()

            elif keyword == "let":
                self.compile_let()

            elif keyword == "while":
                self.compile_while()

            elif keyword == "return":
                self.compile_return()
                
            else:
                self.compile_if()
        self.__close_bracket("statements")


    def compile_do(self) -> None:
        """Compiles a do statement."""
        self.__open_bracket("doStatement")
        self.__eat()  # keyword 'do'
        self.__compile_subroutine_call()
        self.__eat()  # symbol ';'
        self.__close_bracket("doStatement")

    def __compile_subroutine_call(self) -> None:
        self.__eat()  # first identifier

        # In case it's a method
        if self.__TokenType("SYMBOL") and self.__tokenizer.symbol() == ".":
            self.__eat()  # eat symbol
            self.__eat()  # eat subroutine name
        
        self.__eat()  # symbol '('
        self.compile_expression_list()
        self.__eat()  # symbol ')'

    def compile_let(self) -> None:
        """Compiles a let statement."""
        self.__open_bracket("letStatement")

        self.__eat()  # keyword 'let'
        self.__eat()  # identifier 'varName'
        
        if self.__tokenizer.symbol() == '[':
            self.__eat()  # symbol '['
            self.compile_expression()
            self.__eat()  # symbol ']'

        self.__eat()  # eat '='
        self.compile_expression()
        self.__eat()  # eat ';'
        self.__close_bracket("letStatement")

    def compile_while(self) -> None:
        """Compiles a while statement."""
        self.__open_bracket("whileStatement")
        self.__eat()  # keyword 'while'
        self.__eat()  # symbol '('
        self.compile_expression()
        self.__eat()  # symbol ')'
        self.__eat()  # symbol '{'
        self.compile_statements()
        self.__eat()  # symbol '}'
        self.__close_bracket("whileStatement")

    def compile_return(self) -> None:
        """Compiles a return statement."""
        self.__open_bracket("returnStatement")
        self.__eat()  # keyword 'return'

        if not self.__TokenType("SYMBOL") or self.__tokenizer.symbol() != ';':
            self.compile_expression()

        self.__eat()  # symbol ';'
        self.__close_bracket("returnStatement")

    def compile_if(self) -> None:
        """Compiles a if statement, possibly with a trailing else clause."""
        self.__open_bracket("ifStatement")

        self.__eat()  # 'if' keyword
        self.__eat()  # symbol '('
        self.compile_expression()
        self.__eat()  # symbol ')'
        self.__eat()  # symbol '{'
        self.compile_statements()
        self.__eat()  # symbol '}'

        if self.__TokenType("KEYWORD") and self.__tokenizer.keyword() == "else":
            self.__eat()  # keyword else
            self.__eat()  # symbol '{'
            self.compile_statements()
            self.__eat()  # symbol '}'

        self.__close_bracket("ifStatement")

    def compile_expression(self) -> None:
        """Compiles an expression."""
        self.__open_bracket("expression")
        self.compile_term()
        while self.__TokenType("SYMBOL") and \
            self.__tokenizer.symbol() in {'+', '-', '*', '/', '&', '|', '<', '>', '='}:
            self.__eat()  # eat operator
            self.compile_term()
        self.__close_bracket("expression")

    def compile_term(self) -> None:
        """Compiles a term. 
        This routine is faced with a slight difficulty when
        trying to decide between some of the alternative parsing rules.
        Specifically, if the current token is an identifier, the routing must
        distinguish between a variable, an array entry, and a subroutine call.
        A single look-ahead token, which may be one of "[", "(", or "." suffices
        to distinguish between the three possibilities. Any other token is not
        part of this term and should not be advanced over.
        """
        self.__open_bracket("term")
        if self.__TokenType("IDENTIFIER"):
            peaked = self.__tokenizer.peek()
            if peaked == '[':
                self.__eat()  # identifier
                self.__eat()  # symbol '['
                self.compile_expression()
                self.__eat()  # '['

            # calling a subroutine (method)
            elif peaked in {".", "("}:
                self.__compile_subroutine_call()
            
            # normal variable
            else:
                self.__eat()  # identifier
                              
        elif self.__TokenType("INT_CONST") or self.__TokenType("STRING_CONST"):
            self.__eat()  # compile integerConstant or stringConstant
            
        elif self.__TokenType("KEYWORD"):
            if self.__tokenizer.keyword() in {"true", "false", "null", "this"}:
                self.__eat()  # compile keyword

        elif self.__TokenType("SYMBOL"):
            if self.__tokenizer.symbol() == '(':
                self.__eat()  # symbol '('
                self.compile_expression()
                self.__eat()  # symbol ')'

            elif self.__tokenizer.symbol() in {"-", "~", "^", "#"}:
                self.__eat()  # symbol 
                self.compile_term()  # compile term


        self.__close_bracket("term")

    def compile_expression_list(self) -> None:
        """Compiles a (possibly empty) comma-separated list of expressions."""
        self.__open_bracket("expressionList")
        if not (self.__TokenType("SYMBOL") and self.__tokenizer.symbol() == ')'):

            self.compile_expression()

            while self.__TokenType("SYMBOL") and self.__tokenizer.symbol() == ',':
                self.__eat()  # eat ','
                self.compile_expression() 

        self.__close_bracket("expressionList")
