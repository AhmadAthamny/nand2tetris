"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import os
import sys
import typing
from SymbolTable import SymbolTable
from Parser import Parser
from Code import Code


def assemble_file(
        input_file: typing.TextIO, output_file: typing.TextIO) -> None:
    """Assembles a single file.

    Args:
        input_file (typing.TextIO): the file to assemble.
        output_file (typing.TextIO): writes all output to this file.
    """
    # initializing the symbol table
    symbol_table = SymbolTable()

    # creating the parser object
    parser = Parser(input_file)
    
    # current available index at the ROM
    rom_index = 0

    # first pass
    while parser.has_more_commands():
        parser.advance()
        if parser.command_type() == "L_COMMAND":
            ins_symbol = parser.symbol()
            symbol_table.add_entry(ins_symbol, rom_index)
        else:
            rom_index += 1

    # reset parser to read from the beginning of the program
    parser.reset_to_top()

    # second pass
    address_available = 16
    while parser.has_more_commands():
        parser.advance()

        # Parse A-Instruction
        if parser.command_type() == "A_COMMAND":

            # Get the address
            ins_symbol = parser.symbol()
            if not ins_symbol.isnumeric():
                if symbol_table.contains(ins_symbol):
                    a_address = symbol_table.get_address(ins_symbol)
                else:
                    symbol_table.add_entry(ins_symbol, address_available)
                    a_address = address_available
                    address_available += 1
            else:
                a_address = ins_symbol

            # We write to ROM the binary value of a_address
            a_address = int(a_address)
            to_rom = format(a_address, "b").zfill(16)

        # Parse C-Instruction 
        elif parser.command_type() == "C_COMMAND":
            to_rom = Code.comp(parser.comp())  # parse the computation
            to_rom += Code.dest(parser.dest())  # parse the dest
            to_rom += Code.jump(parser.jump())  # parse the jump

        else:
            continue
        output_file.write(to_rom + "\n")



if "__main__" == __name__:
    # Parses the input path and calls assemble_file on each input file.
    # This opens both the input and the output files!
    # Both are closed automatically when the code finishes running.
    # If the output file does not exist, it is created automatically in the
    # correct path, using the correct filename.
    if not len(sys.argv) == 2:
        sys.exit("Invalid usage, please use: Assembler <input path>")
    argument_path = os.path.abspath(sys.argv[1])
    if os.path.isdir(argument_path):
        files_to_assemble = [
            os.path.join(argument_path, filename)
            for filename in os.listdir(argument_path)]
    else:
        files_to_assemble = [argument_path]
    for input_path in files_to_assemble:
        filename, extension = os.path.splitext(input_path)
        if extension.lower() != ".asm":
            continue
        output_path = filename + ".hack"
        with open(input_path, 'r') as input_file, \
                open(output_path, 'w') as output_file:
            assemble_file(input_file, output_file)
