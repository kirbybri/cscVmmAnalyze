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
        self.goodTrigs = {}

        #constants

        self.getData()
        #self.checkData()
        self.checkTriggers()
        self.outputData()

    def getData(self):
        #check if data exists
        isFile = os.path.isfile(self.inputFileName) 
        if isFile == False:
            print("Could not find input file, quitting")
            return
        with open(self.inputFileName, 'rb') as f:
            self.allTrigs = pickle.load(f)  
        return None


    def checkData(self):
        if self.allTrigs == None :
            return
        numBoards = len(self.allTrigs)
        for key in self.allTrigs:
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
        return None


    def checkTriggers(self):
        if self.allTrigs == None :
            return None
        numBoards = len(self.allTrigs)

        #determine the number of triggers in each board
        minNumTrigs = len(list(self.allTrigs.values())[0])
        for key in self.allTrigs:
            boardId = int(key)
            boardTrigs = self.allTrigs[key]
            numTrigs = len(boardTrigs)
            if numTrigs < minNumTrigs :
                minNumTrigs = numTrigs

        #need to determine first trigger for each board
        minTrig = {}
        maxTrig = {}
        #first initialize dictionaries
        for key in self.allTrigs:
            boardId = int(key)
            if boardId not in minTrig:
               minTrig[boardId] = 1000000000
            else:
               print("checkTriggers: ERROR, repeated key in dictionry self.allTrigs, exit")
            if boardId not in maxTrig:
               maxTrig[boardId] = -1
            else:
               print("checkTriggers: ERROR, repeated key in dictionry self.allTrigs, exit")

        #scan data and find min and max trigger counter value
        for key in self.allTrigs:
            boardId = int(key)
            boardTrigs = self.allTrigs[key]
            numTrigs = len(boardTrigs)
            for trigNum in range (0,numTrigs,1):
                trig = boardTrigs[trigNum]
                trigCount = trig[0]
                if (boardId not in maxTrig) or (boardId not in minTrig):
                    print("checkTriggers: ERROR, key not found, WEIRD")
                if trigCount < minTrig[boardId] :
                    minTrig[boardId] = trigCount
                if trigCount > maxTrig[boardId] :
                    maxTrig[boardId] = trigCount

        #require minimum triggers to agree between boards
        minTrigVal = list(minTrig.values())[0]
        #if all(value == minTrigVal for value in minTrig.values()) == False:
        #    print("checkTriggers: ERROR, repeated key in dictionry self.allTrigs, exit")
        #    return None

        #check if minimum triggers are compatible
        minTrigVals = []
        for key in minTrig:
            minTrigVals.append(minTrig[key])

        trigListOffset = {}
        for key in self.allTrigs:
            boardId = int(key)
            trigListOffset[boardId] = 0

        #get first trigger BCID
        prevTrigBcid = {}
        for key in self.allTrigs:
            boardId = int(key)
            boardTrigs = self.allTrigs[key]
            trig = boardTrigs[0]
            trigBcid = trig[1]
            prevTrigBcid[boardId] = trigBcid

        #loop through triggers, note starting at trigger number 1
        trigNum = -1
        missedTriggerCount = 0
        goodTriggerCount = 0
        while trigNum < minNumTrigs-5:
            trigNum = trigNum + 1
            print("\tTRIG NUM ",trigNum)

            #loop over boards, check if trigger values consistent
            boardTrigDiffs = {}
            isOverflow = False
            for key in self.allTrigs:
                boardId = int(key)
                boardTrigs = self.allTrigs[key]
                offset = trigListOffset[boardId]
                currTrigNum = trigNum + offset
                if currTrigNum >= len(boardTrigs) :
                    print("checkTriggers: Ran out of data, ending")
                    isOverflow = True
                    continue
                boardTrig = boardTrigs[currTrigNum]
                trigCount = boardTrig[0]
                trigBcid = boardTrig[1]
                trigDiff = trigBcid - prevTrigBcid[boardId]
                if trigDiff < 0 :
                    trigDiff = 4095 + trigDiff
                print("\tBoard ID ",boardId,"\ttrigBcid ",trigBcid,"\tprevTrigBcid " , prevTrigBcid[boardId],"\ttrigDiff ", trigDiff)
                boardTrigDiffs[boardId] = trigDiff
                #update prev trigger variable
                prevTrigBcid[boardId] = trigBcid

            if isOverflow == True :
                break

            #ignore events were trigger difference is too close to "wrap around" at 0 and 4095
            if all(value > 10 for value in boardTrigDiffs.values()) == False:
                #print("SKIP TRIG NUM ",trigNum,"\tboardTrigDiff ",boardTrigDiffs)
                continue
            if all(value < 4085 for value in boardTrigDiffs.values()) == False:
                #print("SKIP TRIG NUM ",trigNum,"\tboardTrigDiff ",boardTrigDiffs)
                continue

            #calculate RMS of various trigger differences
            boardTrigDiffRms = np.std( list(boardTrigDiffs.values()) , ddof=0)
            if boardTrigDiffRms < 50 :
                #GOOD TRIGGER HERE, SAVE
                for key in self.allTrigs:
                    boardId = int(key)
                    boardTrigs = self.allTrigs[key]
                    offset = trigListOffset[boardId]
                    currTrigNum = trigNum + offset
                    if currTrigNum >= len(boardTrigs) :
                        print("checkTriggers: Ran out of data, ending")
                        isOverflow = True
                        continue
                    boardTrig = boardTrigs[currTrigNum]
                    #add to relevant container
                    if goodTriggerCount not in self.goodTrigs:
                        self.goodTrigs[goodTriggerCount] = []
                    self.goodTrigs[goodTriggerCount].append([boardId,boardTrigDiffs[boardId],boardTrig])
                goodTriggerCount = goodTriggerCount + 1
                continue
            print("BAD TRIGGER TRIG NUM ",trigNum,"\tboardTrigDiffRms",boardTrigDiffRms)
            missedTriggerCount = missedTriggerCount + 1

            #detected a skipped trigger here, try to identify bad boards
            """
            #print(boardTrigDiffs)
            badBoards = []
            for key in boardTrigDiffs:
                #get copy of dictionary recording trigger BCID diffs WITHOUT entry from specified board
                boardId = int(key)
                #print("\tEXCLUDE ",boardId)
                truncatedDiff = {x: boardTrigDiffs[x] for x in boardTrigDiffs if x != boardId }
                #print("\t",truncatedDiff)
                truncatedTrigDiffRms = np.std( list(truncatedDiff.values()) , ddof=0)
                print("\ttruncatedTrigDiffRms ",truncatedTrigDiffRms,"\tboardTrigDiffRms ", boardTrigDiffRms)
                if truncatedTrigDiffRms < boardTrigDiffRms - 50 :
                    #print("BAD BOARD ",boardId)
                    #identified a bad board, try to increment it trigger offset to recover
                    badBoards.append(boardId)
                    trigListOffset[boardId] = trigListOffset[boardId] - 1
            print("badBoards",badBoards)
            #if can't identify a bad board, try a guess?
            if len( badBoards ) == 0 :
                badBoards.append(list(boardTrigDiffs.keys())[0])
            if len(list(boardTrigDiffs.keys())) > 1 :
                badBoards.append(list(boardTrigDiffs.keys())[1])

            numBoards = len(self.allTrigs)
            if numBoards - len( badBoards ) < 2 :
                print("too few good boards, try skipping")
                continue
            """
            badBoards = []
            boards1 = []
            boards2 = []
            firstBoardId = list(boardTrigDiffs.keys())[0]
            firstBoard_trigDiff = boardTrigDiffs[firstBoardId]
            boards1.append(firstBoardId)
            
            for key in boardTrigDiffs:
                boardId = int(key)
                if boardId == firstBoardId :
                    continue
                trigDiff = boardTrigDiffs[boardId]
                if trigDiff - firstBoard_trigDiff > -50 and trigDiff - firstBoard_trigDiff < 50 :
                    boards1.append(boardId)
                else:
                    boards2.append(boardId)
            
            badBoards = boards1
            if len(boards2) < len(badBoards):
                badBoards = boards2
            #print(boards1,"\t",boards2,"\t",firstBoardId)
            #print( badBoards )

            #test difference trigger offsets to see if board recovered
            trigNum = trigNum + 5
            newBoardOffsets = {}
            for testBoard in badBoards:
                print("\tBAD BOARD ",testBoard)
                minRms = boardTrigDiffRms
                minTestOffset = 15
                for testOffset in range(-5,5,1):
                    #print("\t\tTEST OFFSET ",testOffset)

                    #reset prevBCID dictionary
                    for key in self.allTrigs:
                        boardId = int(key)
                        boardTrigs = self.allTrigs[key]
                        offset = trigListOffset[boardId]
                        if boardId == testBoard :
                            offset = offset + testOffset
                        elif boardId in badBoards :
                            continue
                        currTrigNum = trigNum + offset
                        if currTrigNum >= len(boardTrigs) :
                            #print("WEIRD")
                            continue
                        boardTrig = boardTrigs[currTrigNum]
                        trigCount = boardTrig[0]
                        trigBcid = boardTrig[1]
                        prevTrigBcid[boardId] = trigBcid
                        #print("\t\tNEW Board ID ",boardId,"\ttrigBcid ",trigBcid)

                    #check if recovery worked
                    testTrigNum = trigNum + 1
                    testBoardTrigDiffs = {}
                    for key in self.allTrigs:
                        boardId = int(key)
                        boardTrigs = self.allTrigs[key]
                        offset = trigListOffset[boardId]
                        if boardId == testBoard :
                            offset = offset + testOffset
                        elif boardId in badBoards :
                            continue
                        currTrigNum = testTrigNum + offset
                        if currTrigNum >= len(boardTrigs) :
                            print("WEIRD")
                            continue
                        boardTrig = boardTrigs[currTrigNum]
                        trigCount = boardTrig[0]
                        trigBcid = boardTrig[1]
                        trigHits = boardTrig[2]
                        trigDiff = trigBcid - prevTrigBcid[boardId]
                        if trigDiff < 0 :
                            trigDiff = 4095 + trigDiff
                        #print("\t\t\tTEST Board ID ",boardId,"\ttrigBcid ",trigBcid,"\tprevTrigBcid " , prevTrigBcid[boardId],"\ttrigDiff ", trigDiff)
                        testBoardTrigDiffs[boardId] = trigDiff

                    #check if RMS improves
                    testBoardTrigDiffRms = np.std( list(testBoardTrigDiffs.values()) , ddof=0)
                    if testBoardTrigDiffRms < minRms :
                        minTestOffset = testOffset
                        minRms = testBoardTrigDiffRms
                    print("\t\tTEST OFFSET ",testOffset,"\tTEST TRIG DIFF RMS ",testBoardTrigDiffRms)
                
                print("\tTEST Board ID ",testBoard,"\tboardTrigDiffRms ", boardTrigDiffRms,"\tminRms ",minRms,"\tminTestOffset ",minTestOffset)
                #if minTestOffset < 15  :
                if minTestOffset < 15 and minRms < boardTrigDiffRms - 200 :
                    #trigListOffset[testBoard] = trigListOffset[testBoard] + minTestOffset
                    #print("Trig num ", trigNum,"\tminTestOffset",minTestOffset)
                    newBoardOffsets[testBoard] = minTestOffset

            #if trigNum > 80000 :
            #    break

            #apply new offsets
            for testBoard in newBoardOffsets :
                trigListOffset[testBoard] = trigListOffset[testBoard] + newBoardOffsets[testBoard]

            #reset prevBCID dictionary
            for key in self.allTrigs:
                boardId = int(key)
                boardTrigs = self.allTrigs[key]
                offset = trigListOffset[boardId]
                currTrigNum = trigNum + offset
                if currTrigNum >= len(boardTrigs) :
                    continue
                boardTrig = boardTrigs[currTrigNum]
                trigCount = boardTrig[0]
                trigBcid = boardTrig[1]
                prevTrigBcid[boardId] = trigBcid

        print("goodTriggerCount ",goodTriggerCount,"\tmissedTriggerCount ",missedTriggerCount)
        return None                
    #end check Triggers         

    def outputData(self):
        with open("output_analyzeCscHitData_board_goodTrigs.pkl", 'wb') as f:
            pickle.dump(self.goodTrigs, f,2)
        return None
#END CSC_ANALYZE CLASS


def main():

    if len(sys.argv) != 2 :
        print("processCscAnalyze: need to provide input file name")
        return
    fileName = sys.argv[1]
    cscAnalyzeData = CSC_ANALYZE(fileName)

if __name__ == '__main__':
    main()
