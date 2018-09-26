import sys 
import string
import os
import pickle
from array import array
from ROOT import TFile, TTree

class CSC_ANALYZE_WRITE_TREE(object):

    #__INIT__#
    def __init__(self,inputFileName=None):
        self.inputFileName = inputFileName
        self.inputFile = None
        self.allTrigs = None
        self.outputFileName = "output_cscAnalyze_writeRootTree.root"

        #constants

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
            self.allTrigs = pickle.load(f)
        return None 

    def checkData(self):
        if self.allTrigs == None :
            return None

        for trigNum in self.allTrigs:
            boardList = self.allTrigs[trigNum]
            numBoard = len(boardList)
            print("TRIGGER NUMBER",trigNum,"\tNumber of Boards ",numBoard)
            for boardInfo in boardList:
                if len(boardInfo) != 3 :
                    print("ERROR, incorrect number of elements in trigger dict entry")
                    continue
                boardId = boardInfo[0]
                boardTrigDiff = boardInfo[1]
                boardData = boardInfo[2]
                if len(boardData) != 3 :
                    print("ERROR, incorrect number of elements in board info list entry")
                    continue
                trigCount = boardData[0]
                trigBCID = boardData[1]
                hits = boardData[2]
                print("\tboardId ",boardId,"\tTrig Count ", trigCount, "\tTrig BCID ", trigBCID,"\tTrig Diff ",boardTrigDiff)
                for hit in hits:
                    if len(hit) != 4 :
                        print("ERROR, incorrect number of elements in hit info list entry")
                        continue
                    ch = hit[0]
                    pdo = hit[1]
                    tdo = hit[2]
                    trigTime = hit[3]
                    print("\t\tChan # ",ch,"\tPDO ",pdo,"\tTDO ",tdo,"\tTrig Time ", trigTime )
        return None


    def writeRootTree(self):
        if self.allTrigs == None :
            return None

        f = TFile( self.outputFileName, 'recreate' )
        t = TTree( 't1', 'tree' )

        maxNumBoard_t = 32
        maxNumHit_t = 32*64
        trigNum_t = array( 'i', [ 0 ] )
        numBoard_t = array( 'i', [ 0 ] )
        boardId_t = array( 'i', maxNumBoard_t*[ 0 ] )
        boardTrigDiff_t = array( 'i', maxNumBoard_t*[ 0 ] )
        boardTrigBCID_t = array( 'i', maxNumBoard_t*[ 0 ] )
        boardTrigCount_t = array( 'i', maxNumBoard_t*[ 0 ] )

        numHit_t = array( 'i', [ 0 ] )
        hitBoardId_t = array( 'i', maxNumHit_t*[ 0 ] )
        hitChId_t = array( 'i', maxNumHit_t*[ 0 ] )
        hitPDO_t = array( 'i', maxNumHit_t*[ 0 ] )
        hitTDO_t = array( 'i', maxNumHit_t*[ 0 ] )
        hitTrigTime_t = array( 'i', maxNumHit_t*[ 0 ] )

        t.Branch( 'trigNum', trigNum_t, 'trigNum/I' )
        t.Branch( 'numBoard', numBoard_t, 'numBoard/I' )
        t.Branch( 'boardId', boardId_t, 'boardId[numBoard]/I' )
        t.Branch( 'boardTrigBCID', boardTrigBCID_t, 'boardTrigBCID[numBoard]/I' )
        t.Branch( 'boardTrigCount', boardTrigCount_t, 'boardTrigCount[numBoard]/I' )

        t.Branch( 'numHit', numHit_t, 'numHit/I' )
        t.Branch( 'hitBoardId', hitBoardId_t, 'hitBoardId[numHit]/I' )
        t.Branch( 'hitChId', hitChId_t, 'hitChId[numHit]/I' )
        t.Branch( 'hitPDO', hitPDO_t, 'hitPDO[numHit]/I' )
        t.Branch( 'hitTDO', hitTDO_t, 'hitTDO[numHit]/I' )
        t.Branch( 'hitTrigTime', hitTrigTime_t, 'hitTrigTime[numHit]/I' )

        for trigNum in self.allTrigs:
            #print("TRIGGER NUMBER",trigNum,"\tNumber of Boards ",len(boardList))
            boardList = self.allTrigs[trigNum]
            trigNum_t[0] = trigNum
            boardCount = 0
            hitCount = 0
            for boardInfo in boardList:
                if len(boardInfo) != 3 :
                    print("ERROR, incorrect number of elements in trigger dict entry")
                    continue
                boardId = boardInfo[0]
                boardTrigDiff = boardInfo[1]
                boardData = boardInfo[2]
                if len(boardData) != 3 :
                    print("ERROR, incorrect number of elements in board info list entry")
                    continue
                if boardCount > maxNumBoard_t :
                    print("ERROR, exceeded maximum number of boards in event")
                    continue
                trigCount = boardData[0]
                trigBCID = boardData[1]
                hits = boardData[2]
                #print("\tboardId ",boardId,"\tTrig Count ", trigCount, "\tTrig BCID ", trigBCID,"\tTrig Diff ",boardTrigDiff)

                #fill board level tree variables
                boardId_t[boardCount] = boardId
                boardTrigDiff_t[boardCount] = boardTrigDiff
                boardTrigBCID_t[boardCount] = trigBCID
                boardTrigCount_t[boardCount] = trigCount
                boardCount = boardCount + 1

                for hit in hits:
                    if len(hit) != 4 :
                        print("ERROR, incorrect number of elements in hit info list entry")
                        continue
                    ch = hit[0]
                    pdo = hit[1]
                    tdo = hit[2]
                    trigTime = hit[3]

                    if hitCount > maxNumHit_t :
                        print("ERROR, exceeded maximum number of hits in event")
                        continue

                    hitBoardId_t[hitCount] = boardId
                    hitChId_t[hitCount] = ch
                    hitPDO_t[hitCount] = pdo
                    hitTDO_t[hitCount] = tdo
                    hitTrigTime_t[hitCount] = trigTime

                    hitCount = hitCount + 1

            #update total hit count variable
            numBoard_t[0] = boardCount
            numHit_t[0] = hitCount

            t.Fill()
 
        f.Write()
        f.Close()
        

#END CSC_ANALYZE CLASS

def main():

    if len(sys.argv) != 2 :
        print("cscAnalyze_writeRootTree: need to provide input file name")
        return
    fileName = sys.argv[1]
    cscWriteTree = CSC_ANALYZE_WRITE_TREE(fileName)

    cscWriteTree.getData()
    #cscWriteTree.checkData()
    cscWriteTree.writeRootTree()

if __name__ == '__main__':
    main()
