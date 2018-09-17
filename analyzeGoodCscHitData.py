import struct
import sys 
import string
import socket
import time
import os
import pickle
import numpy as np

class CSC_ANALYZE(object):

    #__INIT__#
    def __init__(self,inputFileName):
        self.inputFileName = inputFileName
        self.inputFile = None
        self.allTrigs = None

        #constants

        self.getData()
        self.checkData()

    def getData(self):
        #check if data exists
        isFile = os.path.isfile(self.inputFileName) 
        if isFile == False:
            print("Could not find input file, quitting")
            return
        with open(self.inputFileName, 'rb') as f:
            self.allTrigs = pickle.load(f)  

    def checkData(self):
        if self.allTrigs == None :
            return

        for key in self.allTrigs:
            trigNum = key
            boardList = self.allTrigs[key]
            numBoard = len(boardList)
            print("TRIGGER NUMBER",trigNum,"\tNumber of Boards ",numBoard)
            for boardInfo in boardList:
                if len(boardInfo) != 2 :
                    print("WEIRD")
                    continue
                boardId = boardInfo[0]
                boardData = boardInfo[1]
                if len(boardData) != 3 :
                    print("WEIRD")
                trigCount = boardData[0]
                trigBCID = boardData[1]
                hits = boardData[2]
                print("\tboardId ",boardId,"\tTrig Count ", trigCount, "\tTrig BCID ", trigBCID)
                for hit in hits:
                    if len(hit) != 4 :
                        print("WEIRD")
                    ch = hit[0]
                    pdo = hit[1]
                    tdo = hit[2]
                    trigTime = hit[3]
                    print("\t\tChan # ",ch,"\tPDO ",pdo,"\tTDO ",tdo,"\tTrig Time ", trigTime )
            """
            boardId = int(key)
            boardTrigs = self.allTrigs[key]
            numTrigs = len(boardTrigs)

            #loop over triggers, print hit info
            print( "Board ID ",boardId, "\tNumber of Triggers ", numTrigs )
            #for trig in boardTrigs:
            for trigNum in range (0,numTrigs,1):
                if trigNum > 10 :
                    break
                trig = boardTrigs[trigNum]
                trigCount = trig[0]
                trigBcid = trig[1]
                hits = trig[2]
                numHits = len(hits)
                #if numHits == 0 :
                #    continue
                print("\tBoard ID ",boardId,"\tTrig counter ",trigCount,"\t# of Hits ",numHits)
                for hit in hits :
                    ch = hit[0]
                    pdo = hit[1]
                    tdo = hit[2]
                    trigTime = hit[3]
                    print("\t\tChan # " + str(hit[0]) + "\tPDO " + str(hit[1]) + "\tTime " + str(hit[2]) + "\tTrig Time " + str(hit[3]) )        
            """
#END CSC_ANALYZE CLASS

def main():

    if len(sys.argv) != 2 :
        print("processCscAnalyze: need to provide input file name")
        return
    fileName = sys.argv[1]
    cscAnalyzeData = CSC_ANALYZE(fileName)

if __name__ == '__main__':
    main()
