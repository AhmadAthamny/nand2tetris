"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing


class Parser:
    """Encapsulates access to the input code. Reads an assembly program
    by reading each command line-by-line, parses the current command,
    and provides convenient access to the commands components (fields
    and symbols). In addition, removes all white space and comments.
    """

    def __init__(self, input_file: typing.TextIO) -> None:
        """Opens the input file and gets ready to parse it.

        Args:
            input_file (typing.TextIO): input file.
        """
        self.__input_lines = input_file.read().splitlines()
        for i in range(len(self.__input_lines)):

            # Remove any space in the line.
            self.__input_lines[i] = self.__input_lines[i].replace(" ", "")

            # Check for a comment in the line, and remove starting from it.
            comment_index = self.__input_lines[i].find("//")
            if comment_index != -1:
                self.__input_lines[i] = self.__input_lines[i][:comment_index] # excludes the //

        # A pointer to which line in the file we are in.
        self.__reached = -1

    def has_more_commands(self) -> bool:
        """Are there more commands in the input?

        Returns:
            bool: True if there are more commands, False otherwise.
        """
        for n in range(self.__reached+1, len(self.__input_lines)):

            # Empty line check
            if len(self.__input_lines[n]) == 0:
                continue

            return True
        return False

    def advance(self) -> None:
        """Reads the next command from the input and makes it the current command.
        Should be called only if has_more_commands() is true.
        """
        n = self.__reached
        while True:
            n += 1
            if len(self.__input_lines[n]) == 0:
                continue
            if self.__input_lines[n][0:2] == "//":
                continue
            break
        self.__reached = n

    def reset_to_top(self) -> None:
        self.__reached = -1

    def command_type(self) -> str:
        """
        Returns:
            str: the type of the current command:
            "A_COMMAND" for @Xxx where Xxx is either a symbol or a decimal number
            "C_COMMAND" for dest=comp;jump
            "L_COMMAND" (actually, pseudo-command) for (Xxx) where Xxx is a symbol
        """
        cur_cmd = self.__input_lines[self.__reached]
        if cur_cmd[0] == '@':
            return "A_COMMAND"
        if cur_cmd[0] == '(':
            return "L_COMMAND"
        else:
            return "C_COMMAND"


    def symbol(self) -> str:
        """
        Returns:
            str: the symbol or decimal Xxx of the current command @Xxx or
            (Xxx). Should be called only when command_type() is "A_COMMAND" or 
            "L_COMMAND".
        """
        cur_cmd = self.__input_lines[self.__reached]
        if self.command_type() == "A_COMMAND":
            return cur_cmd[1:]
        else:
            return cur_cmd[1:-1]
        

    def dest(self) -> str:
        """
        Returns:
            str: the dest mnemonic in the current C-command. Should be called 
            only when commandType() is "C_COMMAND".
        """
        cur_cmd = self.__input_lines[self.__reached]
        if '=' not in cur_cmd:
            return "null"
        
        index = cur_cmd.find("=")
        return cur_cmd[0:index]
        

    def comp(self) -> str:
        """
        Returns:
            str: the comp mnemonic in the current C-command. Should be called 
            only when commandType() is "C_COMMAND".
        """
        cur_cmd = self.__input_lines[self.__reached]
        start_index = cur_cmd.find("=") + 1
        comma_index = cur_cmd.find(";")

        if comma_index != -1:
            return cur_cmd[start_index:comma_index]
        else:
            return cur_cmd[start_index:]

    def jump(self) -> str:
        """
        Returns:
            str: the jump mnemonic in the current C-command. Should be called 
            only when commandType() is "C_COMMAND".
        """
        cur_cmd = self.__input_lines[self.__reached]
        comma_index = cur_cmd.find(";")
        if comma_index == -1:
            return "null"
        return cur_cmd[comma_index+1:]

