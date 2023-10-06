// This file is part of nand2tetris, as taught in The Hebrew University, and
// was written by Aviv Yaish. It is an extension to the specifications given
// [here](https://www.nand2tetris.org) (Shimon Schocken and Noam Nisan, 2017),
// as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0
// Unported [License](https://creativecommons.org/licenses/by-nc-sa/3.0/).

// The program should swap between the max. and min. elements of an array.
// Assumptions:
// - The array's start address is stored in R14, and R15 contains its length
// - Each array value x is between -16384 < x < 16384
// - The address in R14 is at least >= 2048
// - R14 + R15 <= 16383
//
// Requirements:
// - Changing R14, R15 is not allowed.

// Put your code here.
@R14
D=M
@index
M=D
@max_index
M=D
@min_index
M=D

(LOOP)
    @R14
    D=M
    @R15
    D=D+M

    @index
    D = D-M
    @UPDATE
    D;JEQ

    @index
    A=M
    D=M

    @max_index
    A=M
    D=M-D
    @UPDATE_MAX
    D;JLT
    
    @index
    A=M
    D=M
    
    @min_index
    A=M
    D=M-D
    @UPDATE_MIN
    D;JGE

    @INCREASE
    0;JMP

    (UPDATE_MAX)
        @index
        D=M
        @max_index
        M=D

        @INCREASE
        0;JMP

    (UPDATE_MIN)
        @index
        D=M
        @min_index
        M=D
    
    (INCREASE)
        @index
        M=M+1
        @LOOP
        0;JMP

(UPDATE)
    @max_index
    A=M
    D=M
    @tmp
    M=D

    @min_index
    A=M
    D=M
    @max_index
    A=M
    M=D

    @tmp
    D=M
    @min_index
    A=M
    M=D

(END)
    @END
    0;JMP