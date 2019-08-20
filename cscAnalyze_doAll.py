import sys 
import string
import os

from cscAnalyze_processBinary_board import CSC_ANALYZE_BINARY
from cscAnalyze_resyncData import CSC_ANALYZE_RESYNC
from cscAnalyze_analyzeUnsyncedData import CSC_ANALYZE_UNSYNC
#from cscAnalyze_writeRootTree import CSC_ANALYZE_WRITE_TREE
#from analyzeGoodCscHitData import CSC_ANALYZE

def main():

    if len(sys.argv) != 2 :
        print("cscAnalyze_doAll: need to provide input file name")
        return
    fileName = sys.argv[1]

    cscBinaryData = CSC_ANALYZE_BINARY(fileName)

    print("PARSING BINARY")
    cscBinaryData.getData()
    #cscBinaryData.dumpData()
    cscBinaryData.findHeaders()
    cscBinaryData.checkPackets()
    cscBinaryData.parsePackets()

    #print("RESYNCING DATA")
    #cscResync = CSC_ANALYZE_RESYNC()
    #cscResync.allBoards = cscBinaryData.allBoards
    #cscResync.resyncData()

    #print("WRITE ROOT TREE")
    #cscWriteTree = CSC_ANALYZE_WRITE_TREE()
    #cscWriteTree.allTrigs = cscResync.goodTrigs
    #cscWriteTree.writeRootTree()

    cscAnalyze = CSC_ANALYZE_UNSYNC()
    cscAnalyze.allBoards = cscBinaryData.allBoards
    cscAnalyze.plotAll()

    #cscAnalyze = CSC_ANALYZE()
    #cscAnalyze.allTrigs = cscResync.goodTrigs
    #cscAnalyze.plotAll()

if __name__ == '__main__':
    main()
