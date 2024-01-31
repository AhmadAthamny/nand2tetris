"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing


class Parser:
    """
    # Parser
    
    Handles the parsing of a single .vm file, and encapsulates access to the
    input code. It reads VM commands, parses them, and provides convenient 
    access to their components. 
    In addition, it removes all white space and comments.

    ## VM Language Specification

    A .vm file is a stream of characters. If the file represents a
    valid program, it can be translated into a stream of valid assembly 
    commands. VM commands may be separated by an arbitrary number of whitespace
    characters and comments, which are ignored. Comments begin with "//" and
    last until the lines end.
    The different parts of each VM command may also be separated by an arbitrary
    number of non-newline whitespace characters.

    - Arithmetic commands:
      - add, sub, and, or, eq, gt, lt
      - neg, not, shiftleft, shiftright
    - Memory segment manipulation:
      - push <segment> <number>
      - pop <segment that is not constant> <number>
      - <segment> can be any of: argument, local, static, constant, this, that, 
                                 pointer, temp
    - Branching (only relevant for project 8):
      - label <label-name>
      - if-goto <label-name>
      - goto <label-name>
      - <label-name> can be any combination of non-whitespace characters.
    - Functions (only relevant for project 8):
      - call <function-name> <n-args>
      - function <function-name> <n-vars>
      - return
    """

    def __init__(self, input_file: typing.TextIO) -> None:
        """Gets ready to parse the input file.

        Args:
            input_file (typing.TextIO): input file.
        """

        # read all lines, split each line in a seperated element in a list
        self.__input_lines = input_file.read().splitlines()

        # tuple structure: ("COMMAND_TEXT", "ARG_1", "ARG_2", ...)
        self.__commands = []  # each tuple is a command.

        for i in range(len(self.__input_lines)):

            # remove comment if exists
            comment_start = self.__input_lines[i].find("//")
            if comment_start != -1:
                self.__input_lines[i] = self.__input_lines[i][:comment_start]

            # remove extra whitespace at the beginning and at the end
            self.__input_lines[i] = self.__input_lines[i].strip()

            # split the command into elements
            # skip line if it is empty at this point
            command_splitted = self.__input_lines[i].split()
            if len(command_splitted) == 0:
                continue

            # parse the line into commands (in case one line can have more than one command)
            elem = 0
            while elem < len(command_splitted):
                arg_amount = self.__get_arg_amount(command_splitted[elem])
                command = tuple(arg for arg in command_splitted[elem:arg_amount+1])
                self.__commands.append(command)
                elem += arg_amount + 1

        self.__current_command = -1

    def __get_arg_amount(self, keyword: str) -> int:
        if keyword in {"add", "sub", "and", "or", "eq", "gt", "lt", "neg",
                        "not", "shiftleft", "shiftright"}:
            return 0
        elif keyword in {"push", "pop"}:
            return 2

    def has_more_commands(self) -> bool:
        """Are there more commands in the input?

        Returns:
            bool: True if there are more commands, False otherwise.
        """
        return self.__current_command + 1 < len(self.__commands)

    def advance(self) -> None:
        """Reads the next command from the input and makes it the current 
        command. Should be called only if has_more_commands() is true. Initially
        there is no current command.
        """
        self.__current_command += 1

    def command_type(self) -> str:
        """
        Returns:
            str: the type of the current VM command.
            "C_ARITHMETIC" is returned for all arithmetic commands.
            For other commands, can return:
            "C_PUSH", "C_POP", "C_LABEL", "C_GOTO", "C_IF", "C_FUNCTION",
            "C_RETURN", "C_CALL".
        """
        cur_cmd = self.__commands[self.__current_command][0]
        if cur_cmd in {"add", "sub", "and", "or", "eq", "gt", "lt",
                       "neg", "not", "shiftleft", "shiftright"}:
            return "C_ARITHMETIC"
        elif cur_cmd == "push":
            return "C_PUSH"
        elif cur_cmd == "pop":
            return "C_POP"

    def arg1(self) -> str:
        """
        Returns:
            str: the first argument of the current command. In case of 
            "C_ARITHMETIC", the command itself (add, sub, etc.) is returned. 
            Should not be called if the current command is "C_RETURN".
        """
        cur_cmd_tuple = self.__commands[self.__current_command]
        if self.command_type() == "C_ARITHMETIC":
            return cur_cmd_tuple[0]
        else:
            return cur_cmd_tuple[1]
        
    def arg2(self) -> int:
        """
        Returns:
            int: the second argument of the current command. Should be
            called only if the current command is "C_PUSH", "C_POP", 
            "C_FUNCTION" or "C_CALL".
        """
        
        cur_cmd_tuple = self.__commands[self.__current_command]
        return cur_cmd_tuple[2]
