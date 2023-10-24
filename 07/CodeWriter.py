"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing


class CodeWriter:
    """Translates VM commands into Hack assembly code."""

    def __init__(self, output_stream: typing.TextIO) -> None:
        """Initializes the CodeWriter.

        Args:
            output_stream (typing.TextIO): output stream.
        """
        self.__output_file = output_stream
        self.__lbl_ctr = -1
    def set_file_name(self, filename: str) -> None:
        """Informs the code writer that the translation of a new VM file is 
        started.

        Args:
            filename (str): The name of the VM file.
        """
        self.__file_name = filename

    def __binaryFunc(self, operation) -> str:
        return "@SP\n" + \
                "M=M-1\n" + \
                "A=M\n" + \
                "D=M\n" + \
                "@SP\n" + \
                "M=M-1\n" + \
                "A=M\n" + \
                "M=M" + operation + "D\n" + \
                "@SP\n" + \
                "M=M+1\n"
    
    def __compareFunc(self, operation) -> str:
        operation = "J" + operation.upper()
        cntr = str(self.__lbl_ctr)
        return "@SP\n" + \
                "M=M-1\n" + \
                "A=M\n" + \
                "D=M\n" + \
                "@R15\n" + \
                "M=D\n" + \
                "@SP\n" + \
                "M=M-1\n" + \
                "@R15\n" + \
                "D=M\n" + \
                "@YPos_" + cntr + "\n" + \
                "D;JGT\n" + \
                "@SP\n" + \
                "D=M\n" + \
                "@YNegXPos_" + cntr + "\n" + \
                "D;JGT\n" + \
                "@R15\n" + \
                "D=M\n" + \
                "@SP\n" + \
                "A=M\n" + \
                "D=D-M\n" + \
                "@CHECK_" + cntr + "\n" + \
                "0;JMP\n" + \
                "(YNegXPos_" + cntr + ")\n" + \
                "D=1\n" + \
                "@CHECK_" + cntr + "\n" + \
                "0;JMP\n" + \
                "(YPos_" + cntr + ")\n" + \
                "@SP\n" + \
                "A=M\n" + \
                "D=M\n" + \
                "@YPosXPos_" + cntr + "\n" + \
                "D;JGT\n" + \
                "D=-1\n" + \
                "@CHECK_" + cntr + "\n" + \
                "0;JMP\n" + \
                "(YPosXPos_" + cntr + ")\n" + \
                "@R15\n" + \
                "D=M\n" + \
                "@SP\n" + \
                "A=M\n" + \
                "D=M-D\n" + \
                "@CHECK_" + cntr + "\n" + \
                "0;JMP\n" + \
                "(CHECK_" + cntr + ")\n" + \
                "@COND_TRUE_" + cntr + "\n" + \
                "D;" + operation + "\n" + \
                "@SP\n" + \
                "A=M\n" + \
                "M=0\n" + \
                "@FINISH_" + cntr + "\n" + \
                "0;JMP\n" + \
                "(COND_TRUE_" + cntr + ")\n" + \
                "@SP\n" + \
                "A=M\n" + \
                "M=-1\n" + \
                "@FINISH_" + cntr + "\n" + \
                "0;JMP\n" + \
                "(FINISH_" + cntr + ")\n" + \
                "@SP\n" + \
                "M=M+1\n" 
    
    def __unaryFunc(self, operation) -> str:
        return "@SP\n" + \
                "M=M-1\n" + \
                "A=M\n" + \
                "M=" + operation + "\n" + \
                "@SP\n" + \
                "M=M+1\n"

    def __addConstant(self, value: str) -> str:
        """Adds the value to the stack, must be a non-negative value
        Args:
            value (int): the value to add.
        """
        return "@" + value + "\n" + \
                "D=A\n" + \
                "@SP\n" + \
                "A=M\n" + \
                "M=D\n" + \
                "@SP\n" + \
                "M=M+1\n"
    
    def __pushIndex(self, from_segment: str, index: str) -> str:
        """Adds the value to the stack, from local/argument/this/that"""

        if from_segment == "TMP":
            read_source =   "@5\n" + \
                            "D=A\n" + \
                            "@" + index + "\n" + \
                            "A=D+A\n"
        else:
            read_source =   "@" + index + "\n" + \
                            "D=A\n" + \
                            "@" + from_segment + "\n" + \
                            "A=M+D\n" 
            
        return read_source + \
                "D=M\n" + \
                "@SP\n" + \
                "A=M\n" + \
                "M=D\n" + \
                "@SP\n" + \
                "M=M+1\n"
    
    def __popIndex(self, to_segment: str, index: str) -> str:
        """Pops the last value from the stack, and adds it to the desired segment"""

        if to_segment == "TMP":
            # save index in case of segment is TMP
            output =    "@" + index + "\n" + \
                        "D=A\n" + \
                        "@5\n" + \
                        "D=D+A\n" 
        else:
            # save index in case of segment in {LCL, ARG, THIS, THAT}
            output =    "@" + index + "\n" + \
                        "D=A\n" + \
                        "@" + to_segment + "\n" + \
                        "D=M+D\n"
            
        return output + \
        "@R13\n" + \
        "M=D\n" + \
        "@SP\n" + \
        "M=M-1\n" + \
        "A=M\n" + \
        "D=M\n" + \
        "@R13\n" + \
        "A=M\n" + \
        "M=D\n"
    
    def __pushPointer(self, segment: str) -> str:
        return "@" + segment + "\n" + \
        "D=M\n" + \
        "@SP\n" + \
        "A=M\n" + \
        "M=D\n" + \
        "@SP\n" + \
        "M=M+1\n" 
    
    def __popPointer(self, segment: str) -> str:
        return "@SP\n" + \
        "AM=M-1\n" + \
        "D=M\n" + \
        "@" + segment + "\n" + \
        "M=D\n"
    
    def __pushStatic(self, index: str) -> str:
        var_name = self.__file_name + "." + index
        return "@" + var_name + "\n" + \
        "D=M\n" + \
        "@SP\n" + \
        "AM=M+1\n" + \
        "A=A-1\n" + \
        "M=D\n"

    def __popStatic(self, index: str) -> str:
        var_name = self.__file_name + "." + index
        return "@SP\n" + \
        "AM=M-1\n" + \
        "D=M\n" + \
        "@" + var_name + "\n" + \
        "M=D\n" 

    def write_arithmetic(self, command: str) -> None:
        """Writes assembly code that is the translation of the given 
        arithmetic command. For the commands eq, lt, gt, you should correctly
        compare between all numbers our computer supports, and we define the
        value "true" to be -1, and "false" to be 0.

        Args:
            command (str): an arithmetic command.
        """
        # to prevent mixing labels up
        self.__lbl_ctr += 1

        binary_dict = {"add": "+", "sub": "-", "and": "&", "or": "|"}
        compare_set = {"eq", "gt", "lt"}
        unary_dict = {"neg": "-M", "not": "!M", "shiftleft": "M<<", "shiftright": "M>>"}

        if command in list(binary_dict.keys()):
            output = self.__binaryFunc(binary_dict[command])
        
        elif command in compare_set:
            output = self.__compareFunc(command)

        elif command in list(unary_dict.keys()):
            output = self.__unaryFunc(unary_dict[command])
        
        self.__output_file.write(output)

    def write_push_pop(self, command: str, segment: str, index: int) -> None:
        """Writes assembly code that is the translation of the given 
        command, where command is either C_PUSH or C_POP.

        Args:
            command (str): "C_PUSH" or "C_POP".
            segment (str): the memory segment to operate on.
            index (int): the index in the memory segment.
        """
        # Your code goes here!
        # Note: each reference to "static i" appearing in the file Xxx.vm should
        # be translated to the assembly symbol "Xxx.i". In the subsequent
        # assembly process, the Hack assembler will allocate these symbolic
        # variables to the RAM, starting at address 16.

        # Converting index to int
        if command == 'C_PUSH':
            if segment == 'constant':
                output = self.__addConstant(str(index))

            
            elif segment in {"local", "argument", "this", "that", "temp"}:
                location = {"local": "LCL", "argument": "ARG", "this": "THIS", 
                            "that": "THAT", "temp": "TMP"}[segment]
                output = self.__pushIndex(location, str(index))

            elif segment == "pointer":
                if index == 0:
                    output = self.__pushPointer("THIS")
                else:
                    output = self.__pushPointer("THAT")

            elif segment == "static":
                output = self.__pushStatic(str(index))
            
    

        elif command == 'C_POP':
            if segment in {"local", "argument", "this", "that", "temp"}:
                location = {"local": "LCL", "argument": "ARG", "this": "THIS", 
                            "that": "THAT", "temp": "TMP"}[segment]
                output = self.__popIndex(location, str(index))

            elif segment == "pointer":
                if index == 0:
                    output = self.__popPointer("THIS")
                else:
                    output = self.__popPointer("THAT")

            elif segment == "static":
                output = self.__popStatic(str(index))

        self.__output_file.write(output)


    def write_label(self, label: str) -> None:
        """Writes assembly code that affects the label command. 
        Let "Xxx.foo" be a function within the file Xxx.vm. The handling of
        each "label bar" command within "Xxx.foo" generates and injects the symbol
        "Xxx.foo$bar" into the assembly code stream.
        When translating "goto bar" and "if-goto bar" commands within "foo",
        the label "Xxx.foo$bar" must be used instead of "bar".

        Args:
            label (str): the label to write.
        """
        # This is irrelevant for project 7,
        # you will implement this in project 8!
        pass
    
    def write_goto(self, label: str) -> None:
        """Writes assembly code that affects the goto command.

        Args:
            label (str): the label to go to.
        """
        # This is irrelevant for project 7,
        # you will implement this in project 8!
        pass
    
    def write_if(self, label: str) -> None:
        """Writes assembly code that affects the if-goto command. 

        Args:
            label (str): the label to go to.
        """
        # This is irrelevant for project 7,
        # you will implement this in project 8!
        pass
    
    def write_function(self, function_name: str, n_vars: int) -> None:
        """Writes assembly code that affects the function command. 
        The handling of each "function Xxx.foo" command within the file Xxx.vm
        generates and injects a symbol "Xxx.foo" into the assembly code stream,
        that labels the entry-point to the function's code.
        In the subsequent assembly process, the assembler translates this 
        symbol into the physical address where the function code starts.

        Args:
            function_name (str): the name of the function.
            n_vars (int): the number of local variables of the function.
        """
        # This is irrelevant for project 7,
        # you will implement this in project 8!
        # The pseudo-code of "function function_name n_vars" is:
        # (function_name)       // injects a function entry label into the code
        # repeat n_vars times:  // n_vars = number of local variables
        #   push constant 0     // initializes the local variables to 0
        pass
    
    def write_call(self, function_name: str, n_args: int) -> None:
        """Writes assembly code that affects the call command. 
        Let "Xxx.foo" be a function within the file Xxx.vm.
        The handling of each "call" command within Xxx.foo's code generates and
        injects a symbol "Xxx.foo$ret.i" into the assembly code stream, where
        "i" is a running integer (one such symbol is generated for each "call"
        command within "Xxx.foo").
        This symbol is used to mark the return address within the caller's 
        code. In the subsequent assembly process, the assembler translates this
        symbol into the physical memory address of the command immediately
        following the "call" command.

        Args:
            function_name (str): the name of the function to call.
            n_args (int): the number of arguments of the function.
        """
        # This is irrelevant for project 7,
        # you will implement this in project 8!
        # The pseudo-code of "call function_name n_args" is:
        # push return_address   // generates a label and pushes it to the stack
        # push LCL              // saves LCL of the caller
        # push ARG              // saves ARG of the caller
        # push THIS             // saves THIS of the caller
        # push THAT             // saves THAT of the caller
        # ARG = SP-5-n_args     // repositions ARG
        # LCL = SP              // repositions LCL
        # goto function_name    // transfers control to the callee
        # (return_address)      // injects the return address label into the code
        pass
    
    def write_return(self) -> None:
        """Writes assembly code that affects the return command."""
        # This is irrelevant for project 7,
        # you will implement this in project 8!
        # The pseudo-code of "return" is:
        # frame = LCL                   // frame is a temporary variable
        # return_address = *(frame-5)   // puts the return address in a temp var
        # *ARG = pop()                  // repositions the return value for the caller
        # SP = ARG + 1                  // repositions SP for the caller
        # THAT = *(frame-1)             // restores THAT for the caller
        # THIS = *(frame-2)             // restores THIS for the caller
        # ARG = *(frame-3)              // restores ARG for the caller
        # LCL = *(frame-4)              // restores LCL for the caller
        # goto return_address           // go to the return address
        pass
