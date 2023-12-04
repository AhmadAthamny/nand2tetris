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
from VMWriter import VMWriter

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
        self.__vmWriter = VMWriter(output_stream)
        self.__indentation = 0
        self.__class_name = None

        self.__lbl_counter = 0

        # Start compiling
        self.__tokenizer.advance()
        self.compile_class()

    def __indentation_inc(self) -> None:
        self.__indentation += 2

    def __indentation_dec(self) -> None:
        self.__indentation -= 2

    def __indentation_print(self) -> None:
        #self.__output_file.write(" " * self.__indentation)
        pass

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
            val_dict = {"KEYWORD": self.__tokenizer.keyword, "SYMBOL": self.__tokenizer.symbol, 
                        "IDENTIFIER": self.__tokenizer.identifier}
            return_val = val_dict[token_type]()
        
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

    def __convertOpToVM(self, symbol: str) -> str:
        output = None
        if symbol == '+':
            output = "add"
        elif symbol == '-':
            output = "sub"
        elif symbol == '&':
            output = "and"
        elif symbol == '|':
            output = "or"
        elif symbol == '=':
            output = "eq"
        elif symbol == '>':
            output = "gt"
        elif symbol == '<':
            output = "lt"
        elif symbol == '*':
            output = "mult"
        elif symbol == "/":
            output = "div"
        return output
    
    def __convertVarToVM(self, var_name: str) -> tuple:
        kind = self.__symbol_table.kind_of(var_name)
        index = self.__symbol_table.index_of(var_name)
        if kind == "FIELD":
            return "this", str(index)
        elif kind == "STATIC":
            return "static", str(index)
        elif kind == "ARG":
            return "argument", str(index)
        elif kind == "VAR":
            return "local", str(index)
        
        # This is an error.
        return None
        
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
        self.__symbol_table.start_subroutine()

        kind = self.__eat()  # constructor/method/function
        self.__eat()  # type
        sub_name = self.__eat()
        sub_name = self.__class_name + '.' + sub_name # subroutine name
        
        self.__eat()  # eat '('
        
        self.compile_parameter_list()
        self.__eat()  # eat ')'

        self.__compile_subroutine_body(sub_name, kind)

        self.__close_bracket("subroutineDec")

    def __compile_subroutine_body(self, sub_name:str, kind: str) -> None:
        self.__open_bracket("subroutineBody")
        self.__eat()  # eat '{'

        var_count = 0
        # Read subroutine var dec.
        if self.__TokenType("KEYWORD"):
            while self.__tokenizer.keyword() == "var":
                var_count += self.compile_var_dec()

        self.__vmWriter.write_function(sub_name, var_count)

        if kind == "constructor":
            field_count = self.__symbol_table.var_count("FIELD")
            self.__vmWriter.write_push("constant", field_count)
            self.__vmWriter.write_call("Memory.alloc", 1)
            self.__vmWriter.write_pop("pointer", 0)

        elif kind == "method":
            self.__addSymbol("this", self.__class_name, "ARG")
            self.__vmWriter.write_push("pointer", 0)
            self.__vmWriter.write_pop("argument", 0)


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
            param_type = self.__eat()  # type
            param_name = self.__eat()  # parameter name
            self.__addSymbol(param_name, param_type, "ARG")

            # Eat more parameters
            while self.__tokenizer.symbol() != ')':
                self.__eat()  # eat ','
                param_type = self.__eat()  # eat type
                param_name = self.__eat()  # eat identifier
                self.__addSymbol(param_name, param_type, "ARG")

        self.__close_bracket("parameterList")

    def compile_var_dec(self) -> int:
        """Compiles a var declaration."""
        self.__open_bracket("varDec")
        self.__eat()  # var
        var_count = 0

        var_type = self.__eat()  # type
        var_name = self.__eat()  # varName
        var_count += 1
        self.__addSymbol(var_name, var_type, "VAR")

        while self.__tokenizer.symbol() != ';':
            self.__eat()  # symbol ,
            var_name = self.__eat()  # varName
            self.__addSymbol(var_name, var_type, "VAR")
            var_count += 1
            
        self.__eat()  # symbol ;
        self.__close_bracket("varDec")
        return var_count

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

        # remove the placeholder of a void function
        self.__vmWriter.write_pop("temp", 0)
        self.__close_bracket("doStatement")

    def __compile_subroutine_call(self) -> None:
        subroutine_name = self.__eat()  # first identifier

        expression_count = 0
        # In case it's a method
        if self.__TokenType("SYMBOL") and self.__tokenizer.symbol() == ".":
            # Check if it belongs to an object that we have
            if self.__symbol_table.kind_of(subroutine_name):
                segment, index = self.__convertVarToVM(subroutine_name)
                self.__vmWriter.write_push(segment, index)
                expression_count = 1

            subroutine_name += self.__eat()  # eat symbol
            subroutine_name += self.__eat()  # eat subroutine name
        
        self.__eat()  # symbol '('
        expression_count += self.compile_expression_list()
        self.__eat()  # symbol ')'

        self.__vmWriter.write_call(subroutine_name, expression_count)


    def compile_let(self) -> None:
        """Compiles a let statement."""
        self.__open_bracket("letStatement")

        self.__eat()  # keyword 'let'
        var_name = self.__eat()  # identifier 'varName'

        segment, index = self.__convertVarToVM(var_name)

        isArray = False
        
        if self.__tokenizer.symbol() == '[':
            isArray = True

            self.__eat()  # symbol '['
            self.compile_expression()
            self.__eat()  # symbol ']'

            self.__vmWriter.write_arithmetic("add")


        self.__eat()  # eat '='
        self.compile_expression()
        self.__eat()  # eat ';'


        if isArray:
            self.__vmWriter.write_pop("temp", 0)
            self.__vmWriter.write_pop("pointer", 1)
            self.__vmWriter.write_push("temp", 0)
            self.__vmWriter.write_pop("that", 0)
        else:
            self.__vmWriter.write_pop(segment, index)

        self.__close_bracket("letStatement")

    def compile_while(self) -> None:
        """Compiles a while statement."""
        self.__open_bracket("whileStatement")
        self.__eat()  # keyword 'while'
        self.__lbl_counter += 1
        while_ctr = self.__lbl_counter
        self.__vmWriter.write_label("while" + str(while_ctr))

        # Check if the condition is true
        self.__eat()  # symbol '('
        self.compile_expression()
        self.__vmWriter.write_arithmetic("not")
        self.__vmWriter.write_if("while_end" + str(while_ctr))
        self.__eat()  # symbol ')'

        # Perform the statements, then go back to the while label again.
        self.__eat()  # symbol '{'
        self.compile_statements()
        self.__vmWriter.write_goto("while" + str(while_ctr))
        self.__eat()  # symbol '}'

        # Write the label which is after the while
        self.__vmWriter.write_label("while_end" + str(while_ctr))

        self.__close_bracket("whileStatement")

    def compile_return(self) -> None:
        """Compiles a return statement."""
        self.__open_bracket("returnStatement")
        self.__eat()  # keyword 'return'
        if not self.__TokenType("SYMBOL") or self.__tokenizer.symbol() != ';':
            self.compile_expression()
        else:
            # void function
            self.__vmWriter.write_push("constant", 0)

        self.__vmWriter.write_return()

        self.__eat()  # symbol ';'
        self.__close_bracket("returnStatement")

    def compile_if(self) -> None:
        """Compiles a if statement, possibly with a trailing else clause."""
        self.__open_bracket("ifStatement")

        self.__eat()  # 'if' keyword
        self.__eat()  # symbol '('
        self.compile_expression()
        self.__eat()  # symbol ')'


        self.__vmWriter.write_arithmetic("not")
        self.__lbl_counter += 1
        if_ctr = self.__lbl_counter
        self.__vmWriter.write_if("else_lbl" + str(if_ctr))
        self.__eat()  # symbol '{'
        self.compile_statements()
        self.__eat()  # symbol '}'
        self.__vmWriter.write_goto("if_done" + str(if_ctr))

        self.__vmWriter.write_label("else_lbl" + str(if_ctr))
        if self.__TokenType("KEYWORD") and self.__tokenizer.keyword() == "else":
            self.__eat()  # keyword else
            self.__eat()  # symbol '{'
            self.compile_statements()
            self.__eat()  # symbol '}'

        self.__vmWriter.write_label("if_done" + str(if_ctr))
        self.__close_bracket("ifStatement")

    def compile_expression(self) -> None:
        """Compiles an expression."""
        self.__open_bracket("expression")
        self.compile_term()
        while self.__TokenType("SYMBOL") and self.__convertOpToVM(self.__tokenizer.symbol()):
            op = self.__convertOpToVM(self.__tokenizer.symbol())
            self.__eat()  # eat operator
            self.compile_term()
            if op == "mult":
                self.__vmWriter.write_call("Math.multiply", 2)
            elif op == "div":
                self.__vmWriter.write_call("Math.divide", 2)
            else:
                self.__vmWriter.write_arithmetic(op)
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
                var_name = self.__eat()  # identifier
                segment, index = self.__convertVarToVM(var_name)
                self.__vmWriter.write_push(segment, index)
                self.__eat()  # symbol '['
                self.compile_expression()
                self.__eat()  # ']'
                self.__vmWriter.write_arithmetic("add")
                self.__vmWriter.write_pop("pointer", 1)
                self.__vmWriter.write_push("that", 0)

            # calling a subroutine (method)
            elif peaked in {".", "("}:
                self.__compile_subroutine_call()
            
            # normal variable
            else:
                var_name = self.__eat()  # get variable name
                segment, index = self.__convertVarToVM(var_name)
                self.__vmWriter.write_push(segment, index)
                              
        elif self.__TokenType("INT_CONST"):
            const_value = self.__eat()
            self.__vmWriter.write_push("constant", const_value)
        
        elif self.__TokenType("STRING_CONST"):
            const_str = self.__eat()
            str_length = len(const_str)
            self.__vmWriter.write_push("constant", str_length)
            self.__vmWriter.write_call("String.new", 1)
            for char in const_str:
                self.__vmWriter.write_push("constant", ord(char))
                self.__vmWriter.write_call("String.appendChar", 2)
            
        elif self.__TokenType("KEYWORD"):
            if self.__tokenizer.keyword() in {"true", "false", "null", "this"}:
                keyword = self.__eat()  # eat keyword
                if keyword == "true":
                    self.__vmWriter.write_push("constant", 1)
                    self.__vmWriter.write_arithmetic("neg")
                elif keyword == "false" or keyword == "null":
                    self.__vmWriter.write_push("constant", 0)
                elif keyword == "this":
                    self.__vmWriter.write_push("pointer", 0)

        elif self.__TokenType("SYMBOL"):
            symbol = self.__tokenizer.symbol()
            if symbol == '(':
                self.__eat()  # symbol '('
                self.compile_expression()
                self.__eat()  # symbol ')'

            else:
                # unary op
                self.__eat()
                self.compile_term()
                symbol_dict = {"-": "neg", "~": "not", "^": "shiftleft", "#": "shiftright"}
                self.__vmWriter.write_arithmetic(symbol_dict[symbol])


        self.__close_bracket("term")

    def compile_expression_list(self) -> int:
        """Compiles a (possibly empty) comma-separated list of expressions."""
        self.__open_bracket("expressionList")

        expressions_count = 0

        if not (self.__TokenType("SYMBOL") and self.__tokenizer.symbol() == ')'):
            expressions_count += 1
            self.compile_expression()

            while self.__TokenType("SYMBOL") and self.__tokenizer.symbol() == ',':

                expressions_count += 1
                self.__eat()  # eat ','
                self.compile_expression() 

        self.__close_bracket("expressionList")
        return expressions_count
