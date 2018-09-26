import sys 
import string
import os

from cscAnalyze_processBinary_board import CSC_ANALYZE_BINARY
from cscAnalyze_resyncData import CSC_ANALYZE_RESYNC
from cscAnalyze_writeRootTree import CSC_ANALYZE_WRITE_TREE

def main():

    if len(sys.argv) != 2 :
        print("cscAnalyze_doAll: need to provide input file name")
        return
    fileName = sys.argv[1]

    cscBinaryData = CSC_ANALYZE_BINARY(fileName)

    print("PARSING BINARY")
    cscBinaryData.getData()
    cscBinaryData.findHeaders()
    cscBinaryData.checkPackets()
    cscBinaryData.parsePackets()

    print("RESYNCING DATA")
    cscResync = CSC_ANALYZE_RESYNC()
    cscResync.allBoards = cscBinaryData.allBoards
    cscResync.resyncData()

    print("WRITE ROOT TREE")
    cscWriteTree = CSC_ANALYZE_WRITE_TREE()
    cscWriteTree.allTrigs = cscResync.goodTrigs
    cscWriteTree.writeRootTree()

if __name__ == '__main__':
    main()
