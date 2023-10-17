"""
This file is part of nand2tetris, as taught in The Hebrew University, and
was written by Aviv Yaish. It is an extension to the specifications given
[here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""


class Code:
    """Translates Hack assembly language mnemonics into binary codes."""
    
    @staticmethod
    def dest(mnemonic: str) -> str:
        """
        Args:
            mnemonic (str): a dest mnemonic string.

        Returns:
            str: 3-bit long binary code of the given mnemonic.
        """
        dest_keys = {"null": "000", "M": "001", "D": "010", 
                     "MD": "011", "A": "100", "AM": "101", 
                     "AD": "110", "AMD": "111"}
        return dest_keys[mnemonic]

    @staticmethod
    def comp(mnemonic: str) -> str:
        """
        Args:
            mnemonic (str): a comp mnemonic string.

        Returns:
            str: the binary code of the given mnemonic.
        """
        comp_keys = {"0":   "101010",
                     "1":   "111111",
                     "-1":  "111010",
                     "D":   "001100",
                     "A":   "110000",
                     "!D":  "001101",
                     "!A":  "110001",
                     "-D":  "001111",
                     "-A":  "110011",
                     "D+1": "011111",
                     "A+1": "110111",
                     "D-1": "001110",
                     "A-1": "110010",
                     "D+A": "000010",
                     "D-A": "010011",
                     "A-D": "000111",
                     "D&A": "000000",
                     "D|A": "010101"}
        
        extended_keys = {"A<<": "1010100000",
                         "D<<": "1010110000",
                         "M<<": "1011100000",
                         "A>>": "1010000000",
                         "D>>": "1010010000",
                         "M>>": "1011000000"}
        
        # Check if mnemonic is in the extend list:
        if mnemonic in list(extended_keys.keys()):
            return extended_keys[mnemonic]
        
        # Check if it is in the standard comp list
        if 'M' in mnemonic:
            replaced_mnemonic = mnemonic.replace("M", "A")
            return "1111" + comp_keys[replaced_mnemonic]
        else:
            return "1110" + comp_keys[mnemonic]

        

    @staticmethod
    def jump(mnemonic: str) -> str:
        """
        Args:
            mnemonic (str): a jump mnemonic string.

        Returns:
            str: 3-bit long binary code of the given mnemonic.
        """
        jump_keys = {"null": "000", "JGT": "001", "JEQ": "010",
                      "JGE": "011", "JLT": "100", "JNE":"101",
                      "JLE": "110", "JMP": "111"}
        return jump_keys[mnemonic]