#!/usr/bin/env python
# -*- coding: utf-8 -*-

#  mfdread.py - Mifare dumps parser in human readable format
#  Pavel Zhovner <pavel@zhovner.com>
#  https://github.com/zhovner/mfdread



import codecs
import sys
from struct import unpack 
from datetime import datetime
from bitstring import BitArray


if len(sys.argv) == 1:
    print('''
------------------
Usage: mfdread.py ./dump.mfd
Mifare dumps reader. 
''')
    sys.exit();




class bashcolors:
    BLUE = '\033[34m'
    RED = '\033[91m'
    GREEN = '\033[32m'
    WARNING = '\033[93m'
    ENDC = '\033[0m'


def accbits_for_blocknum(accbits_str, blocknum):
    '''
    Decodes the access bit string for block "blocknum".
    Returns the three access bits for the block or False if the
    inverted bits do not match the access bits.
    '''
    bits = BitArray([0])
    inverted = BitArray([0])
    # Block 0 access bits
    if blocknum == 0:
        bits = BitArray([accbits_str[11], accbits_str[23], accbits_str[19]])
        inverted = BitArray([accbits_str[7], accbits_str[3], accbits_str[15]])

    # Block 0 access bits
    elif blocknum == 1:
        bits = BitArray([accbits_str[10], accbits_str[22], accbits_str[18]])
        inverted = BitArray([accbits_str[6], accbits_str[2], accbits_str[14]])
    # Block 0 access bits
    elif blocknum == 2:
        bits = BitArray([accbits_str[9], accbits_str[21], accbits_str[17]])
        inverted = BitArray([accbits_str[5], accbits_str[1], accbits_str[13]])
    # Sector trailer / Block 3 access bits
    elif blocknum == 3:
        bits = BitArray([accbits_str[8], accbits_str[20], accbits_str[16]])
        inverted = BitArray([accbits_str[4], accbits_str[0], accbits_str[12]])

    # Check the decoded bits
    inverted.invert()
    if bits.bin == inverted.bin:
        return bits
    else:
        return False




def accbit_info(accbits):
    '''
    Returns  a dictionary of a access bits for all three blocks in a sector.
    If the access bits for block could not be decoded properly, the value is set to False.
    '''
    decAccbits = {}
    # Decode access bits for all 4 blocks of the sector
    for i in range(0, 4):
        decAccbits[i] = accbits_for_blocknum(accbits, i)
    return decAccbits





def print_info(data):

    blocksmatrix = []
    blockrights = {}

    # determine what dump we get 1k or 4k
    if len(data) == 4096:
        cardsize = 64
    elif len(data) == 1024:
        cardsize = 16
    else: 
        print("Wrong file size: %d bytes.\nOnly 1024 or 4096 allowed." % len(data))
        sys.exit();

    # read all sectors
    for i in range(0, cardsize):
        start = i * 64
        end   = (i + 1) * 64
        sector = data[start:end]
        sector = codecs.encode(sector, 'hex')
        if not type(sector) is str:
            sector = str(sector, 'ascii')
        blocksmatrix.append([sector[x:x+32] for x in range(0, len(sector), 32)])

    # add colors for each keyA, access bits, KeyB
    for c in range(0, len(blocksmatrix)):
        # Fill in the access bits
        blockrights[c] = accbit_info(BitArray('0x'+blocksmatrix[c][3][12:20]))
        # Prepare colored output of the sector trailor
        keyA =  bashcolors.RED + blocksmatrix[c][3][0:12] + bashcolors.ENDC
        accbits = bashcolors.GREEN + blocksmatrix[c][3][12:20] + bashcolors.ENDC
        keyB =  bashcolors.BLUE + blocksmatrix[c][3][20:32] + bashcolors.ENDC
        blocksmatrix[c][3] = keyA + accbits + keyB


    print("File size: %d bytes. Expected %d sectors" %(len(data),cardsize))
    print("\n\tUID:  " + blocksmatrix[0][0][0:8])
    print("\tBCC:  " + blocksmatrix[0][0][8:10])
    print("\tSAK:  " + blocksmatrix[0][0][10:12])
    print("\tATQA: " + blocksmatrix[0][0][12:14])
    print("                   %sKey A%s    %sAccess Bits%s    %sKey B%s" %(bashcolors.RED,bashcolors.ENDC,bashcolors.GREEN,bashcolors.ENDC,bashcolors.BLUE,bashcolors.ENDC))
    print("╔═════════╦═════╦══════════════════════════════════╦═══════════════╗")
    print("║  Sector ║Block║            Data                  ║  Access Bits  ║")
    for q in range(0, len(blocksmatrix)):
        print("╠═════════╬═════╬══════════════════════════════════╬═══════════════╣")

        # z is the block in each sector
        for z in range(0, len(blocksmatrix[q])):
            # Format the access bits. Print ERR in case of an error
            accbits = ""
            if isinstance(blockrights[q][z], BitArray):
                accbits = bashcolors.GREEN + blockrights[q][z].bin + bashcolors.ENDC
            else:
                accbits = bashcolors.WARNING + "ERR" + bashcolors.ENDC

            # Add Padding after the sector number
            padLen = max(1, 5 - len(str(q)))
            padding = " " * padLen
            # Only print the sector number in the second third row
            if (z == 2):
                print("║    %d%s║  %d  ║ %s ║      %s      ║"  %(q,padding,z,blocksmatrix[q][z], accbits))
            else:
                print("║         ║  %d  ║ %s ║      %s      ║"  %(z,blocksmatrix[q][z], accbits))
    print("╚═════════╩═════╩══════════════════════════════════╩═══════════════╝")


def main(filename):
    with open(filename, "rb") as f:
        data = f.read()
        print_info(data)
 
if __name__ == "__main__":
    main(sys.argv[1])
