import sys 
import string
import os
import pickle
#import numpy as np
import math

class CSC_ANALYZE_RESYNC(object):

    #__INIT__#
    def __init__(self,inputFileName=None):
        self.inputFileName = inputFileName
        self.inputFile = None
        self.allBoards = None
        self.goodTrigs = {}
        self.trigListOffset = {}
        self.outputFileName = "output_cscAnalyze_resyncData.pkl"
        self.goodTriggerCount = 0
        self.doResync = False

        #constants
        self.constant_maxTimeDiff = 50
        self.constant_maxGoodRms = 50
        self.constant_recoverNumSkip = 2
        self.constant_recoverTestRange = 5
        self.constant_minRmsDiff = 200


    def getData(self):
        if self.inputFileName == None:
            print("Could not find input file name, quitting")
            return None
        #check if data exists
        isFile = os.path.isfile(self.inputFileName) 
        if isFile == False:
            print("Could not find input file, quitting")
            return
        with open(self.inputFileName, 'rb') as f:
            self.allBoards = pickle.load(f)  
        return None


    def checkData(self):
        if self.allBoards == None :
            return
        numBoards = len(self.allBoards)
        for boardId in self.allBoards:
            boardTrigs = self.allBoards[boardId]
            numTrigs = len(boardTrigs)

            #loop over triggers, print hit info
            print( "Board ID ",boardId, "\tNumber of Triggers ", numTrigs )
            #for trig in boardTrigs:
            for trigNum in range (0,numTrigs,1):
                if trigNum > 2:
                    break
                trig = boardTrigs[trigNum]
                trigCount = trig[0]
                trigBcid = trig[1]
                hits = trig[2]
                numHits = len(hits)
                print("\tBoard ID ",boardId,"\tTrig counter ",trigCount,"\tTrig BCID ",trigBcid,"\t# of Hits ",numHits)
                continue
                for hit in hits :
                    ch = hit[0]
                    pdo = hit[1]
                    tdo = hit[2]
                    trigTime = hit[3]
                    print("\t\tChan # " + str(hit[0]) + "\tPDO " + str(hit[1]) + "\tTime " + str(hit[2]) + "\tTrig Time " + str(hit[3]) )
        return None


    def resyncData(self):
        if self.allBoards == None :
            return None
        if len(self.allBoards) == 0:
            return None
        numBoards = len(self.allBoards)

        #determine the number of triggers in each board
        minNumTrigs = self.getMinNumTriggers()
        if minNumTrigs == None :
            return None

        #init trigger offsets
        for boardId in self.allBoards:
            self.trigListOffset[boardId] = 0

        #loop through triggers, note starting at trigger number 1
        trigNum = 0
        missedTriggerCount = 0
        while trigNum < minNumTrigs-self.constant_recoverNumSkip:
            trigNum = trigNum + 1
            if trigNum % 1000 == 0 :
            #if True :
                print("TRIG NUM ",trigNum)
            #get trigger differences, require valid number for each board
            prevTrigBcid = self.updatePrevTrigBcid(trigNum-1) #note trigger # offset!
            boardTrigDiffs = self.updateBoardTrigDiffs(trigNum,prevTrigBcid)
            if boardTrigDiffs == None :
                continue
            if all( value != None for value in boardTrigDiffs.values() ) == False:
                continue
            #calculate trigger difference RMS, use to identify missed triggers
            boardTrigDiffRms = self.calcStd(boardTrigDiffs)
            if boardTrigDiffRms == None :
                boardTrigDiffRms = 0
            if (boardTrigDiffRms < self.constant_maxGoodRms) or (numBoards == 1) or (self.doResync == False):
                #good event, save to output container
                self.saveSyncedEvent(trigNum,boardTrigDiffs)
            elif boardTrigDiffRms >= self.constant_maxGoodRms :
                #detected a skipped trigger here, skip ahead, identify bad boards and try recovery
                missedTriggerCount = missedTriggerCount + 1
                trigNum = trigNum + self.constant_recoverNumSkip
                badBoards = self.getBadBoards(boardTrigDiffs)
                self.recoverBoards(trigNum,badBoards,boardTrigDiffRms)
                print("BAD TRIGGER TRIG NUM ",trigNum,"\tboardTrigDiffRms ",boardTrigDiffRms,"\tBAD BOARDS ",badBoards)
                for boardId in boardTrigDiffs :
                    print("\tBoard ",boardId,"\tDIFF ",boardTrigDiffs[boardId])
                #print("\tTRIG DIFFs ",boardTrigDiffs)

        print("goodTriggerCount ",self.goodTriggerCount,"\tmissedTriggerCount ",missedTriggerCount)
        return None                
    #end resyncData

    
    def getMinNumTriggers(self):
        if self.allBoards == None :
            return None

        minNumTrigs = len(list(self.allBoards.values())[0])
        for boardId in self.allBoards:
            boardTrigs = self.allBoards[boardId]
            numTrigs = len(boardTrigs)
            if numTrigs < minNumTrigs :
                minNumTrigs = numTrigs
        return minNumTrigs


    def getBadBoards(self,boardTrigDiffs=None):
        if boardTrigDiffs == None :
            return None
        if len(boardTrigDiffs) == 0 :
            return None

        badBoards = []
        boards1 = []
        boards2 = []
        firstBoardId = list(boardTrigDiffs.keys())[0]
        firstBoard_trigDiff = boardTrigDiffs[firstBoardId]
        boards1.append(firstBoardId)            
        for boardId in boardTrigDiffs:
            #print("\tBAD TRIG board ID ", boardId,"\tDIFF ",boardTrigDiffs[boardId])
            if boardId == firstBoardId :
                continue
            trigDiff = boardTrigDiffs[boardId]
            if trigDiff - firstBoard_trigDiff > -1*self.constant_maxTimeDiff and trigDiff - firstBoard_trigDiff < self.constant_maxTimeDiff :
                boards1.append(boardId)
            else:
                boards2.append(boardId)       
        badBoards = boards1
        if len(boards2) < len(badBoards):
            badBoards = boards2
        return badBoards


    def updatePrevTrigBcid(self,trigNum=0,testBoard=None,badBoards=None,testOffset=None):
        if self.allBoards == None :
            return None

        prevTrigBcid = {}
        for boardId in self.allBoards:
            boardTrigs = self.allBoards[boardId]
            if len(boardTrigs) == 0 :
                prevTrigBcid[boardId] = None
                continue
            offset = self.trigListOffset[boardId]

            #section for testing offsets during recovery
            if ( testBoard != None) and (badBoards != None) and (testOffset != None):
                if boardId == testBoard :
                    offset = offset + testOffset
                elif boardId in badBoards :
                    continue

            currTrigNum = trigNum + offset
            if currTrigNum >= len(boardTrigs) or currTrigNum < 0 :
                prevTrigBcid[boardId] = None
                continue
            boardTrig = boardTrigs[currTrigNum]
            trigBcid = boardTrig[1]
            prevTrigBcid[boardId] = trigBcid
        return prevTrigBcid


    def updateBoardTrigDiffs(self,trigNum=0,prevTrigBcid=None,testBoard=None,badBoards=None,testOffset=None):
        if self.allBoards == None :
            return None
        if prevTrigBcid == None :
            return None

        #measure new trigger difference wrt previous event
        boardTrigDiffs = {}
        for boardId in self.allBoards:
            boardTrigs = self.allBoards[boardId]
            offset = self.trigListOffset[boardId]

            #section for testing offsets during recovery
            if (testBoard != None) and (badBoards != None) and (testOffset != None) :
                if boardId == testBoard :
                    offset = offset + testOffset
                elif boardId in badBoards :
                    continue

            currTrigNum = trigNum + offset
            if currTrigNum >= len(boardTrigs) or currTrigNum < 0 :
                boardTrigDiffs[boardId] = None
                continue
            if prevTrigBcid[boardId] == None :
                boardTrigDiffs[boardId] = None
                continue
            boardTrig = boardTrigs[currTrigNum]
            trigBcid = boardTrig[1]
            trigDiff = trigBcid - prevTrigBcid[boardId]
            if trigDiff < 0 :
                trigDiff = 4095 + trigDiff
            #if testBoard == None :
            #    print("\tBoard ID ",boardId,"\ttrigBcid ",trigBcid,"\tprevTrigBcid " , prevTrigBcid[boardId],"\ttrigDiff ", trigDiff)
            boardTrigDiffs[boardId] = trigDiff
        return boardTrigDiffs


    def saveSyncedEvent(self, trigNum=0,boardTrigDiffs=None):
        if self.allBoards == None :
            return None
        if boardTrigDiffs == None :
            return None
        if len(boardTrigDiffs) == 0 :
            return None
        for boardId in self.allBoards:
            boardTrigs = self.allBoards[boardId]
            offset = self.trigListOffset[boardId]
            currTrigNum = trigNum + offset
            if currTrigNum >= len(boardTrigs) :
                #print("saveSyncedEvent: Ran out of data, should only have synced event")
                continue
            boardTrig = boardTrigs[currTrigNum]
            #add to relevant container
            if self.goodTriggerCount not in self.goodTrigs:
                self.goodTrigs[self.goodTriggerCount] = []
            self.goodTrigs[self.goodTriggerCount].append([boardId,boardTrigDiffs[boardId],boardTrig])
        self.goodTriggerCount = self.goodTriggerCount + 1
        return None


    def recoverBoards(self,trigNum=0,badBoards=None,boardTrigDiffRms=None):
        if badBoards == None or boardTrigDiffRms == None:
            print("recoverBoards: did not receive valid info, break")
            return None

        #test difference trigger offsets to see if board recovered
        newBoardOffsets = {}
        for testBoard in badBoards:
            #print("\tBAD BOARD ",testBoard)
            minRms = boardTrigDiffRms
            minTestOffset = None
            for testOffset in range(-1*self.constant_recoverTestRange,self.constant_recoverTestRange,1):
                #print("\t\tTEST OFFSET ",testOffset)

                #reset prevBCID dictionary
                testPrevTrigBcid = self.updatePrevTrigBcid(trigNum,testBoard,badBoards,testOffset)
                if testPrevTrigBcid == None :
                    continue

                #check if recovery worked, note offset in trigger number
                testBoardTrigDiffs = self.updateBoardTrigDiffs(trigNum+1,testPrevTrigBcid,testBoard,badBoards,testOffset)

                #check if any boards out of data given offset
                if testBoardTrigDiffs == None :
                    continue
                if all( value != None for value in testBoardTrigDiffs.values() ) == False:
                    continue

                #check if RMS improves
                testBoardTrigDiffRms = self.calcStd(testBoardTrigDiffs)
                if testBoardTrigDiffRms == None :
                    continue
                if testBoardTrigDiffRms < minRms :
                    minTestOffset = testOffset
                    minRms = testBoardTrigDiffRms
                #print("\t\tTEST OFFSET ",testOffset,"\tTEST TRIG DIFF RMS ",testBoardTrigDiffRms)
                
            #print("\tTEST Board ID ",testBoard,"\tboardTrigDiffRms ", boardTrigDiffRms,"\tminRms ",minRms,"\tminTestOffset ",minTestOffset)
            if minTestOffset != None and (minRms < boardTrigDiffRms - self.constant_minRmsDiff or minRms < self.constant_maxGoodRms) :
                newBoardOffsets[testBoard] = minTestOffset

        #apply new offsets
        for testBoard in newBoardOffsets :
            self.trigListOffset[testBoard] = self.trigListOffset[testBoard] + newBoardOffsets[testBoard]
        return None

    
    #calculate std-dev in case numpy, statistics not available
    def calcStd(self,boardTrigDiffs=None):
        if boardTrigDiffs == None :
            return None
        vals = list(boardTrigDiffs.values())
        if len(vals) < 2 :
            return None
        if all( value != None for value in vals ) == False:
            return None

        corrVals = vals
        if all( value < 4050 for value in vals ) == False:
            corrVals = []
            for val in vals:
                if val < 2050 :
                    corrVals.append(val)
                else :
                    corrVals.append(val - 4096)

        mean = sum(corrVals) / len(vals)
        var  = sum(pow(value-mean,2) for value in corrVals) / len(corrVals)

        if var < 0:
            return None
        std  = math.sqrt(var)
        return std

    def outputData(self):
        with open(self.outputFileName, 'wb') as f:
            pickle.dump(self.goodTrigs, f,2)
        return None
#END CSC_ANALYZE CLASS


def main():

    if len(sys.argv) != 2 :
        print("cscAnalyze_resyncData: need to provide input file name")
        return
    fileName = sys.argv[1]
    cscResync = CSC_ANALYZE_RESYNC(fileName)

    cscResync.getData()
    #cscResync.checkData()
    cscResync.resyncData()
    cscResync.outputData()

if __name__ == '__main__':
    main()
