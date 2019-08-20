import struct
import sys 
import string
import socket
import time
import os
import pickle
import numpy as np
import PyQt5
import matplotlib
matplotlib.use("Qt5Agg") #no tkinter
#matplotlib.use("agg") #no tkinter
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.stats import norm

class CSC_ANALYZE(object):

    #__INIT__#
    def __init__(self,inputFileName=None):
        self.inputFileName = inputFileName
        self.inputFile = None
        self.allTrigs = None

        #constants
        self.allBoards = [100,101,102,103,104,105,106,107]
        #self.allBoards = [100,107]
        self.constant_lowHitTdc = -10
        self.constant_highHitTdc = 25

        self.getData()
        #self.plotAll()
        self.plotGood()
        #self.checkTimeSpread()
        #self.analyzeData_checkData()
        #self.analyzeData_checkCorr()
        #self.analyzeData_goodEvents()
        #self.analyzeData_checkEff()
        #self.analyzeData_checkTimeDist()
        #self.analyzeData_checkPosRes()
        #self.analyzeData_checkChDist()
        #self.analyzeData_coincDist()
        #self.analyzeData_checkEff_layer()
        #self.analyzeData_posEff()
        #self.analyzeData_goodEvents_qDist()

    def getData(self):
        #check if data exists
        isFile = os.path.isfile(self.inputFileName) 
        if isFile == False:
            print("Could not find input file, quitting")
            return
        with open(self.inputFileName, 'rb') as f:
            self.allTrigs = pickle.load(f)  

    def analyzeData_checkData(self):
        if self.allTrigs == None :
            return

        for key in self.allTrigs:
            trigNum = key
            boardList = self.allTrigs[key]
            numBoard = len(boardList)
            print("TRIGGER NUMBER",trigNum,"\tNumber of Boards ",numBoard)
            for boardInfo in boardList:
                if len(boardInfo) != 3 :
                    print("WEIRD")
                    continue
                boardId = boardInfo[0]
                boardTrigDiff = boardInfo[1]
                boardData = boardInfo[2]
                if len(boardData) != 3 :
                    print("WEIRD")
                trigCount = boardData[0]
                trigBCID = boardData[1]
                hits = boardData[2]
                print("\tboardId ",boardId,"\tTrig Count ", trigCount, "\tTrig BCID ", trigBCID,"\tTrig Diff ",boardTrigDiff)
                #continue
                for hit in hits:
                    if len(hit) != 4 :
                        print("WEIRD")
                    ch = hit[0]
                    pdo = hit[1]
                    tdo = hit[2]
                    trigTime = hit[3]
                    print("\t\tChan # ",ch,"\tPDO ",pdo,"\tTDO ",tdo,"\tTrig Time ", trigTime )

    def plotAll(self):
        if self.allTrigs == None :
            return

        xPlot = []
        yPlot = []

        for key in self.allTrigs:
            trigNum = key
            boardList = self.allTrigs[key]
            for boardInfo in boardList:
                if len(boardInfo) != 3 :
                    print("WEIRD")
                    continue
                boardId = boardInfo[0]
                boardTrigDiff = boardInfo[1]
                boardData = boardInfo[2]
                if len(boardData) != 3 :
                    print("WEIRD")
                trigCount = boardData[0]
                trigBCID = boardData[1]
                #xPlot.append(trigBCID)
                hits = boardData[2]
                for hit in hits:
                    if len(hit) != 4 :
                        print("WEIRD")
                    ch = hit[0]
                    pdo = hit[1]
                    tdo = hit[2]
                    trigTime = hit[3]
                    xPlot.append(trigTime)
                    yPlot.append(pdo)

        #results
        fig = plt.figure()

        plt.subplot(2, 1, 1)
        #plt.hist(xPlot, 100, facecolor='g')
        plt.hist(xPlot, range(-25,50,1), facecolor='g')
        plt.xlabel("Hit Time - Trigger Tim")
        plt.ylabel("Number of Hits")

        plt.subplot(2, 1, 2)
        plt.hist(yPlot, 100, facecolor='g')
        plt.xlabel("PDO (ADC)")
        plt.ylabel("Number of Hits")

        #plt.plot()
        plt.show()
        plt.savefig("output_plotAll.png")

        return None

    def analyzeData_getGoodHitPos(self,boardList=None):
        if self.allTrigs == None :
            return None
        if boardList == None :
            return None
        if len(boardList) == 0 :
            return None

        #boardList = self.allTrigs[key]
        goodBoardHits = {}
        for boardInfo in boardList:
            if len(boardInfo) != 3 :
                continue
            boardId = boardInfo[0]
            boardTrigDiff = boardInfo[1]
            boardData = boardInfo[2]
            if len(boardData) != 3 :
                continue
            trigCount = boardData[0]
            trigBCID = boardData[1]
            hits = boardData[2]
            numHits = len(hits)
            for hit in hits:
                if len(hit) != 4 :
                    continue
                ch = hit[0]
                pdo = hit[1]
                tdo = hit[2]
                trigTime = hit[3]
                #if trigTime < -4 or trigTime > 0 : #cosmic
                #if trigTime < -4 or trigTime > 20 :
                #if trigTime < -4 or trigTime > 30 : # very wide
                if trigTime < self.constant_lowHitTdc or trigTime > self.constant_highHitTdc : # very wide
                    continue
                #good hit here
                if boardId not in goodBoardHits:
                    goodBoardHits[boardId] = []
                goodBoardHits[boardId].append(ch)
            
        #require "good" hits
        goodBoardHitPos = {}
        for board in goodBoardHits:
            #cut for up to 3 adjacent hits
            if len(goodBoardHits[board]) == 0 or len(goodBoardHits[board]) > 3 :
            #if len(goodBoardHits[board]) == 0 :
                continue
            if len(goodBoardHits[board]) == 1 :
                goodBoardHitPos[board] = goodBoardHits[board][0]
                continue
            chRms = np.std( goodBoardHits[board] , ddof=1)
            #RMS cut for 3 adjacent hits
            if chRms > 1.5 :
                continue
            goodBoardHitPos[board] = np.mean(goodBoardHits[board])
        return goodBoardHitPos

    def analyzeData_getGoodHits(self,boardList=None):
        if self.allTrigs == None :
            return None
        if boardList == None :
            return None
        if len(boardList) == 0 :
            return None

        #boardList = self.allTrigs[key]
        tempBoardHits = {}
        for boardInfo in boardList:
            if len(boardInfo) != 3 :
                continue
            boardId = boardInfo[0]
            boardTrigDiff = boardInfo[1]
            boardData = boardInfo[2]
            if len(boardData) != 3 :
                continue
            trigCount = boardData[0]
            trigBCID = boardData[1]
            hits = boardData[2]
            numHits = len(hits)
            for hit in hits:
                if len(hit) != 4 :
                    continue
                ch = hit[0]
                pdo = hit[1]
                tdo = hit[2]
                trigTime = hit[3]
                if trigTime < self.constant_lowHitTdc or trigTime > self.constant_highHitTdc : # very wide
                    continue
                #good hit here
                if boardId not in tempBoardHits:
                    tempBoardHits[boardId] = []
                tempBoardHits[boardId].append([ch,trigTime,pdo])
            
        #require "good" hits
        goodBoardHits = {}
        for boardId in tempBoardHits:
            #cut for up to 3 adjacent hits
            tempHits = tempBoardHits[boardId]
            if len(tempHits) == 0 or len(tempHits) > 3 :
                continue
            if len(tempHits) == 1 :
                goodBoardHits[boardId] = tempHits
                continue
            chList = []
            for hit in tempHits :
                chList.append(hit[0])
            chRms = np.std( chList , ddof=1)
            #RMS cut for 3 adjacent hits
            if (len(chList) == 2) and (chRms > 0.8):
                continue
            if (len(chList) == 3) and (chRms > 1.2):
                continue
            goodBoardHits[boardId] = tempHits
        return goodBoardHits

    
    def getHitPos(self,goodHits = None):
        if goodHits == None :
            return None
        if len(goodHits) == 0 :
            return None

        tempHitPos = []
        for hit in goodHits :
            ch = hit[0]
            tempHitPos.append(ch)
        hitPos = np.mean(tempHitPos)
        return hitPos


    def plotGood(self):
        if self.allTrigs == None :
            return

        xPlot = []
        yPlot = []
        totalTrig = 0
        totalGood = 0

        for trigNum in self.allTrigs:
            boardList = self.allTrigs[trigNum]

            #get good hits
            goodBoardHits = self.analyzeData_getGoodHits(boardList)
            if goodBoardHits == None :
                continue
            totalTrig = totalTrig + 1

            #select good event
            print("TRIG NUM ", trigNum)
            for boardId in goodBoardHits :
                goodHits = goodBoardHits[boardId]
                print("\tBoard ",boardId)
                #print("\t\t",goodHits)
                hitPos = self.getHitPos(goodHits)
                if hitPos == None :
                    print("\t\tINVALID POS")
                    continue
                #print("\t\tPos ",hitPos)
                numHits = len(goodHits)
                if numHits != 3 :
                    continue
                for hit in goodHits :
                    #print("\t\t",hit)
                    ch = hit[0]
                    trigTime = hit[1]
                    pdo = hit[2]
                    xPlot.append(trigTime)
                    yPlot.append(pdo)

        #results
        print("Total trig ",totalTrig,"\tTotal good ",totalGood)
        fig = plt.figure()

        #plt.plot(xPlot, yPlot, 'o', color='black')
        plt.subplot(2, 1, 1)
        #plt.hist(xPlot, 100, facecolor='g')
        plt.hist(xPlot, range(-25,50,1), facecolor='g')
        plt.xlabel("Hit Time - Trigger Tim")
        plt.ylabel("Number of Hits")

        plt.subplot(2, 1, 2)
        plt.hist(yPlot, 100, facecolor='g')
        plt.xlabel("PDO (ADC)")
        plt.ylabel("Number of Hits")

        #plt.plot()
        plt.show()
        plt.savefig("output_plotAll.png")

        return None

            
    def analyzeData_checkCorr(self):
        if self.allTrigs == None :
            return

        totalTrig = 0
        totalGood = 0

        xPlot_x = []
        yPlot_x = []
        zPlot_x = []

        xPlot_y = []
        yPlot_y = []
        zPlot_y = []

        zPlot = []

        for key in self.allTrigs:
            trigNum = key
            boardList = self.allTrigs[key]
            #get good hits
            goodBoardHitPos = self.analyzeData_getGoodHitPos(boardList)
            if goodBoardHitPos == None :
                continue
            totalTrig = totalTrig + 1

            #select good event
            isGoodEvent = True
            #cut 0 = require hits in layers
            reqBoards = [100,101,102,103,104,105]
            for board in reqBoards :
                #does event have hit in required layer
                if board not in goodBoardHitPos:
                    isGoodEvent = False
                    continue
            if isGoodEvent == False:
                continue
            #cut 1 = position cuts
            reqBoards = []
            for board in reqBoards :
                if board not in goodBoardHitPos:
                    isGoodEvent = False
                    continue
                if goodBoardHitPos[board] < 29.9 :
                    isGoodEvent = False
                if goodBoardHitPos[board] > 30.1 :
                    isGoodEvent = False
            if isGoodEvent == False:
                continue
            #cut 2 = position cuts in alterative dimensions
            reqBoards = [100,102,104] #y-coord alternative
            #reqBoards = [101,103,105] #x-coord alternative
            for board in reqBoards :
                if board not in goodBoardHitPos:
                    isGoodEvent = False
                    continue
                if goodBoardHitPos[board] < 10 :
                    isGoodEvent = False
                if goodBoardHitPos[board] > 53 :
                    isGoodEvent = False
            if isGoodEvent == False:
                continue
            totalGood = totalGood + 1

            #zPred_x = -0.46*goodBoardHitPos[100] + 43.8
            #zPred_x = 1.43*goodBoardHitPos[102] - 12.7
            #zPred_x = -0.46*goodBoardHitPos[100] + 1.43*goodBoardHitPos[102] + 1.1

            #zPred_y = -0.47*goodBoardHitPos[101] + 44.0
            #zPred_y = 1.45*goodBoardHitPos[103] - 13.45
            zPred_y = -0.47*goodBoardHitPos[101] + 1.45*goodBoardHitPos[103] + 0.1

            #if( goodBoardHitPos[104] - zPred > 5) or (goodBoardHitPos[104] - zPred < -5 ) :
            #if( goodBoardHitPos[105] - zPred_y > 4) or (goodBoardHitPos[105] - zPred_y < -4 ) :
            #    continue

            #record positions
            xPlot_x.append(goodBoardHitPos[100])
            yPlot_x.append(goodBoardHitPos[102])
            zPlot_x.append(goodBoardHitPos[104])

            xPlot_y.append(goodBoardHitPos[101])
            yPlot_y.append(goodBoardHitPos[103])
            zPlot_y.append(goodBoardHitPos[105])

            #zPlot.append(goodBoardHitPos[105] )
            zPlot.append(goodBoardHitPos[105] - zPred_y )

        print("Total trig ",totalTrig,"\tTotal good ",totalGood)
        fig = plt.figure()
        #ax = fig.add_subplot(111, projection='3d')
        #ax.scatter(xPlot_y, yPlot_y, zPlot_y, c='r', marker='o')
        #ax.set_xlabel('X Label')
        #ax.set_ylabel('Y Label')
        #ax.set_zlabel('Z Label')

        #par = np.polyfit(xPlot_y, zPlot, 1, full=True)
        #print(par)
        #plt.plot(xPlot_y, zPlot, 'o', color='black');

        plt.hist(zPlot, 100, density=True, facecolor='g', alpha=0.75)
        
        plt.show()

    def analyzeData_goodEvents(self):
        if self.allTrigs == None :
            return

        totalTrig = 0
        totalGood = 0

        for key in self.allTrigs:
            trigNum = key
            boardList = self.allTrigs[key]

            #get good hits
            goodBoardHitPos = self.analyzeData_getGoodHitPos(boardList)
            if goodBoardHitPos == None :
                continue
            totalTrig = totalTrig + 1

            #select good event
            isGoodEvent = True
            reqBoards = self.allBoards
            for board in reqBoards :
                #does event have hit in required layer
                if board not in goodBoardHitPos:
                    isGoodEvent = False
                    continue
                #position cuts
                #if goodBoardHitPos[board] < 10 :
                #    isGoodEvent = False
                #if goodBoardHitPos[board] > 53 :
                #    isGoodEvent = False
            if isGoodEvent == False:
                continue

            #try straight line cut
            diff_x = 0
            diff_y = 0
            if (100 in goodBoardHitPos) and (102 in goodBoardHitPos) and (104 in goodBoardHitPos) :
                pred_x = -0.46*goodBoardHitPos[100] + 1.43*goodBoardHitPos[102] + 1.1
                diff_x = goodBoardHitPos[104] - pred_x
            if (101 in goodBoardHitPos) and (103 in goodBoardHitPos) and (105 in goodBoardHitPos) :
                pred_y = -0.47*goodBoardHitPos[101] + 1.45*goodBoardHitPos[103] + 0.1
                diff_y = goodBoardHitPos[105] - pred_y           
            if diff_x < -5 or diff_x > 5 :
                continue
            if diff_y < -5 or diff_y > 5 :
                continue

            #good event here
            totalGood = totalGood + 1
            print("Good event, trigger ",trigNum)
            continue
            for boardInfo in boardList:
                if len(boardInfo) != 3 :
                    print("WEIRD")
                    continue
                boardId = boardInfo[0]
                boardTrigDiff = boardInfo[1]
                boardData = boardInfo[2]
                if len(boardData) != 3 :
                    print("WEIRD")

                trigCount = boardData[0]
                trigBCID = boardData[1]
                hits = boardData[2]
                print("\tboardId ",boardId,"\tTrig Count ", trigCount, "\tTrig BCID ", trigBCID,"\tTrig Diff ",boardTrigDiff)
                for hit in hits:
                    if len(hit) != 4 :
                        print("WEIRD")
                    ch = hit[0]
                    pdo = hit[1]
                    tdo = hit[2]
                    trigTime = hit[3]

                    if trigTime < -4 or trigTime > 30 :
                        continue

                    print("\t\tChan # ",ch,"\tPDO ",pdo,"\tTDO ",tdo,"\tTrig Time ", trigTime )

        #results
        print("Total trig ",totalTrig,"\tTotal good ",totalGood)

    def analyzeData_checkPosRes(self):
        if self.allTrigs == None :
            return

        totalTrig = 0
        totalGood = 0
        diffPlot_x = []
        diffPlot_y = []

        for key in self.allTrigs:
            trigNum = key
            boardList = self.allTrigs[key]

            #get good hits
            goodBoardHitPos = self.analyzeData_getGoodHitPos(boardList)
            if goodBoardHitPos == None :
                continue
            totalTrig = totalTrig + 1

            #select good event
            isGoodEvent = True
            #reqBoards = [100,101,102,103,104,105]
            reqBoards = [100,101,102,103]
            for board in reqBoards :
                #does event have hit in required layer
                if board not in goodBoardHitPos:
                    isGoodEvent = False
                    continue
                #position cuts
                if goodBoardHitPos[board] < 10 :
                    isGoodEvent = False
                if goodBoardHitPos[board] > 53 :
                    isGoodEvent = False
            if isGoodEvent == False:
                continue

            #try straight line cut
            diff_x = None
            diff_y = None
            if (100 in goodBoardHitPos) and (102 in goodBoardHitPos) and (104 in goodBoardHitPos) :
                pred_x = -0.46*goodBoardHitPos[100] + 1.43*goodBoardHitPos[102] + 1.1
                diff_x = goodBoardHitPos[104] - pred_x
            if (101 in goodBoardHitPos) and (103 in goodBoardHitPos) and (105 in goodBoardHitPos) :
                pred_y = -0.47*goodBoardHitPos[101] + 1.45*goodBoardHitPos[103] + 0.1
                diff_y = goodBoardHitPos[105] - pred_y           
            #if diff_x < -5 or diff_x > 5 :
            #    continue
            #if diff_y < -5 or diff_y > 5 :
            #    continue

            if diff_x != None:
                diffPlot_x.append( diff_x )
            if diff_y != None:
                diffPlot_y.append( diff_y )

        #(mu, sigma) = norm.fit(diffPlot_y)
        #print(mu,"\t",sigma)
        print("Total trig ",totalTrig,"\tTotal 104 ",len(diffPlot_x),"\tTotal 105 ",len(diffPlot_y))

        fig = plt.figure(num=None, figsize=(8, 6), dpi=80)

        plt.subplot(2, 1, 1)
        #plt.hist(diffPlot_x, 100, facecolor='g')
        plt.hist(diffPlot_x, range(-64,64,1), facecolor='g')
        plt.xlabel("Board 104 Pos - Pred Pos (ch)")
        plt.ylabel("Number of Hits")

        plt.subplot(2, 1, 2)
        plt.hist(diffPlot_y, range(-64,64,1), facecolor='g')
        plt.xlabel("Board 105 Pos - Pred Pos (ch)")
        plt.ylabel("Number of Hits")
         
        #plt.plot()
        #plt.show()
        plt.savefig("output_checkPosReg.png")

        #fig = plt.figure()
        #plt.hist(diffPlot_y, range(-10,10,1), density=True, facecolor='g', alpha=0.75)      
        #plt.show()

    def analyzeData_checkChDist(self):
        if self.allTrigs == None :
            return
        self.analyzeData_checkChDist_board(100)
        self.analyzeData_checkChDist_board(101)
        self.analyzeData_checkChDist_board(102)
        self.analyzeData_checkChDist_board(103)
        self.analyzeData_checkChDist_board(104)
        self.analyzeData_checkChDist_board(105)
        self.analyzeData_checkChDist_board(106)
        self.analyzeData_checkChDist_board(107)


    def analyzeData_checkChDist_board(self, testBoard = None):
        if self.allTrigs == None :
            return
        if testBoard == None :
            return

        totalTrig = 0
        totalGood = 0
        chDist = []

        for key in self.allTrigs:
            trigNum = key
            boardList = self.allTrigs[key]

            #get good hits
            goodBoardHitPos = self.analyzeData_getGoodHitPos(boardList)
            if goodBoardHitPos == None :
                continue
            totalTrig = totalTrig + 1

            #select good event
            isGoodEvent = True
            reqBoards = self.allBoards
            for board in reqBoards :
                #does event have hit in required layer
                if board not in goodBoardHitPos:
                    isGoodEvent = False
                    continue
                #position cuts
                #if goodBoardHitPos[board] < 10 :
                #    isGoodEvent = False
                #if goodBoardHitPos[board] > 53 :
                #    isGoodEvent = False
            if isGoodEvent == False:
                continue

            #try straight line cut
            diff_x = 0
            diff_y = 0
            if (100 in goodBoardHitPos) and (102 in goodBoardHitPos) and (104 in goodBoardHitPos) :
                pred_x = -0.46*goodBoardHitPos[100] + 1.43*goodBoardHitPos[102] + 1.1
                diff_x = goodBoardHitPos[104] - pred_x
            if (101 in goodBoardHitPos) and (103 in goodBoardHitPos) and (105 in goodBoardHitPos) :
                pred_y = -0.47*goodBoardHitPos[101] + 1.45*goodBoardHitPos[103] + 0.1
                diff_y = goodBoardHitPos[105] - pred_y           
            if diff_x < -5 or diff_x > 5 :
                continue
            if diff_y < -5 or diff_y > 5 :
                continue

            #good event here
            totalGood = totalGood + 1
            for boardInfo in boardList:
                if len(boardInfo) != 3 :
                    print("WEIRD")
                    continue
                boardId = boardInfo[0]
                if boardId != testBoard :
                    continue
                boardTrigDiff = boardInfo[1]
                boardData = boardInfo[2]
                if len(boardData) != 3 :
                    print("WEIRD")
                trigCount = boardData[0]
                trigBCID = boardData[1]
                hits = boardData[2]
                #print("\tboardId ",boardId,"\tTrig Count ", trigCount, "\tTrig BCID ", trigBCID,"\tTrig Diff ",boardTrigDiff)
                for hit in hits:
                    if len(hit) != 4 :
                        print("WEIRD")
                    ch = hit[0]
                    pdo = hit[1]
                    tdo = hit[2]
                    trigTime = hit[3]

                    if trigTime < -4 or trigTime > 30 :
                        continue

                    #print("\t\tChan # ",ch,"\tPDO ",pdo,"\tTDO ",tdo,"\tTrig Time ", trigTime )
                    chDist.append(ch)

        #results
        #print("Total trig ",totalTrig,"\tTotal good ",totalGood)
        print("Board ", testBoard )
        fig = plt.figure()
        plt.hist(chDist, range(0,64,1), density=True, facecolor='g', alpha=0.75)
        plotTitle = "Good Track Channel Hit Distribution, Board " + str(testBoard)
        plotFile = "output_analyzeGoodCscHitData_goodChDist_" + str(testBoard) + ".png"
        plt.xlabel("Channel #")
        plt.ylabel("Number of Hits")
        plt.title(plotTitle)
        plt.plot()
        #plt.show()
        plt.savefig(plotFile)


    def analyzeData_checkEff(self):
        if self.allTrigs == None :
            return
        self.analyzeData_checkEff_board(100)
        self.analyzeData_checkEff_board(101)
        self.analyzeData_checkEff_board(102)
        self.analyzeData_checkEff_board(103)
        self.analyzeData_checkEff_board(104)
        self.analyzeData_checkEff_board(105)
        self.analyzeData_checkEff_board(106)
        self.analyzeData_checkEff_board(107)

    def analyzeData_checkEff_board(self,testBoard = None):
        if self.allTrigs == None :
            return
        if testBoard == None :
            return

        totalTrig = 0
        totalGood = 0

        xPlot = []
        yPlot = []
        zPlot = []

        for trigNum in self.allTrigs:
            boardList = self.allTrigs[trigNum]

            #get good hits
            goodBoardHits = self.analyzeData_getGoodHits(boardList)
            if goodBoardHits == None :
                continue

            #select good event
            isGoodEvent = True
            reqBoards = self.allBoards
            for board in reqBoards :
                #does event have hit in required layer
                if board == testBoard :
                    continue
                if board not in goodBoardHits:
                    isGoodEvent = False
                    continue
                #position cuts
                print(goodBoardHits[board])
                if self.getHitPos( goodBoardHits[board] ) < 10 :
                    isGoodEvent = False
                if self.getHitPos( goodBoardHits[board] ) > 53 :
                    isGoodEvent = False
            if isGoodEvent == False:
                continue

            #try straight line cut
            diff_x = 0
            diff_y = 0
            if (100 in goodBoardHits) and (102 in goodBoardHits) and (104 in goodBoardHits) :
                pred_x = -0.46*self.getHitPos(goodBoardHits[100]) + 1.43*self.getHitPos(goodBoardHits[102]) + 1.1
                diff_x = goodBoardHits[104] - pred_x
            if (101 in goodBoardHits) and (103 in goodBoardHits) and (105 in goodBoardHits) :
                pred_y = -0.47*self.getHitPos(goodBoardHits[101]) + 1.45*self.getHitPos(goodBoardHits[103]) + 0.1
                diff_y = goodBoardHits[105] - pred_y           
            if diff_x < -5 or diff_x > 5 :
                continue
            if diff_y < -5 or diff_y > 5 :
                continue
            #good event here
            totalTrig = totalTrig + 1
            if testBoard in goodBoardHits :
                totalGood = totalGood + 1

        #results
        print("Board ", testBoard )
        print("Total trig ",totalTrig,"\tTotal good ",totalGood)
        if totalTrig > 0 :
            print( totalGood/totalTrig)

    def analyzeData_checkTimeDist(self):
        if self.allTrigs == None :
            return
        self.analyzeData_checkTimeDist_board(100)
        self.analyzeData_checkTimeDist_board(101)
        self.analyzeData_checkTimeDist_board(102)
        self.analyzeData_checkTimeDist_board(103)
        self.analyzeData_checkTimeDist_board(104)
        self.analyzeData_checkTimeDist_board(105)
        self.analyzeData_checkTimeDist_board(106)
        self.analyzeData_checkTimeDist_board(107)

    def analyzeData_checkTimeDist_board(self,testBoard = None):
        if self.allTrigs == None :
            return
        if testBoard == None :
            return

        totalTrig = 0
        totalGood = 0
        xPlot = []

        for key in self.allTrigs:
            trigNum = key
            boardList = self.allTrigs[key]

            #get good hits
            goodBoardHitPos = self.analyzeData_getGoodHitPos(boardList)
            if goodBoardHitPos == None :
                continue

            #select good event
            isGoodEvent = True
            reqBoards = self.allBoards
            for board in reqBoards :
                #does event have hit in required layer
                if board == testBoard :
                    continue
                if board not in goodBoardHitPos:
                    isGoodEvent = False
                    continue
                #position cuts
                if goodBoardHitPos[board] < 10 :
                    isGoodEvent = False
                if goodBoardHitPos[board] > 53 :
                    isGoodEvent = False
            if isGoodEvent == False :
                continue

            #try straight line cut
            diff_x = 0
            diff_y = 0
            if (100 in goodBoardHitPos) and (102 in goodBoardHitPos) and (104 in goodBoardHitPos) :
                pred_x = -0.46*goodBoardHitPos[100] + 1.43*goodBoardHitPos[102] + 1.1
                diff_x = goodBoardHitPos[104] - pred_x
            if (101 in goodBoardHitPos) and (103 in goodBoardHitPos) and (105 in goodBoardHitPos) :
                pred_y = -0.47*goodBoardHitPos[101] + 1.45*goodBoardHitPos[103] + 0.1
                diff_y = goodBoardHitPos[105] - pred_y           
            if diff_x < -5 or diff_x > 5 :
                continue
            if diff_y < -5 or diff_y > 5 :
                continue

            #good event here
            #have selected event, get time distribution
            for boardInfo in boardList:
                if len(boardInfo) != 3 :
                    continue
                boardId = boardInfo[0]
                if boardId != testBoard :
                    continue
                boardTrigDiff = boardInfo[1]
                boardData = boardInfo[2]
                if len(boardData) != 3 :
                    continue
                trigCount = boardData[0]
                trigBCID = boardData[1]
                hits = boardData[2]
                numHits = len(hits)
                for hit in hits:
                    if len(hit) != 4 :
                        continue
                    ch = hit[0]
                    pdo = hit[1]
                    tdo = hit[2]
                    trigTime = hit[3]
                    xPlot.append(trigTime)
        #results
        print("Board ", testBoard )
        fig = plt.figure()
        plt.hist(xPlot, 50, density=True, facecolor='g', alpha=0.75)
        plotTitle = "Trigger Hit Time Distribution Board " + str(testBoard)
        plotFile = "output_analyzeGoodCscHitData_trigTimeDiff_" + str(testBoard) + ".png"
        plt.xlabel("Hit Time - Trigger Time")
        plt.ylabel("Number of Hits")
        plt.title(plotTitle)
        plt.plot()
        plt.savefig(plotFile)

    def analyzeData_coincDist(self) :
        if self.allTrigs == None :
            return

        coincPlot_100 = []
        coincPlot_101 = []
        coincPlot_102 = []
        coincPlot_103 = []
        coincPlot_104 = []
        coincPlot_105 = []
        coincPlot_106 = []
        coincPlot_107 = []

        xPlot = []
        yPlot = []

        xPlot_layer = []
        yPlot_layer = []

        layerMap = {}
        layerMap[100] = 0
        layerMap[101] = 0
        layerMap[102] = 1
        layerMap[103] = 1
        layerMap[104] = 2
        layerMap[105] = 2
        layerMap[106] = 3
        layerMap[107] = 3

        for key in self.allTrigs:
            trigNum = key
            boardList = self.allTrigs[key]

            #get good hits
            goodBoardHitPos = self.analyzeData_getGoodHitPos(boardList)
            if goodBoardHitPos == None :
                continue

            for board in goodBoardHitPos :
                if 100 in goodBoardHitPos and board != 100 :
                    coincPlot_100.append(board)
                    xPlot.append(100)
                    yPlot.append(board)
                if 101 in goodBoardHitPos and board != 101 :
                    coincPlot_101.append(board)
                    xPlot.append(101)
                    yPlot.append(board)
                if 102 in goodBoardHitPos and board != 102 :
                    coincPlot_102.append(board)
                    xPlot.append(102)
                    yPlot.append(board)
                if 103 in goodBoardHitPos and board != 103 :
                    coincPlot_103.append(board)
                    xPlot.append(103)
                    yPlot.append(board)
                if 104 in goodBoardHitPos and board != 104 :
                    coincPlot_104.append(board)
                    xPlot.append(104)
                    yPlot.append(board)
                if 105 in goodBoardHitPos and board != 105 :
                    coincPlot_105.append(board)
                    xPlot.append(105)
                    yPlot.append(board)
                if 106 in goodBoardHitPos and board != 106 :
                    coincPlot_106.append(board)
                    xPlot.append(106)
                    yPlot.append(board)
                if 107 in goodBoardHitPos and board != 107 :
                    coincPlot_107.append(board)
                    xPlot.append(107)
                    yPlot.append(board)

                if ( (100 in goodBoardHitPos) or (101 in goodBoardHitPos) ) and board != 100 and board != 101 and board in layerMap:
                    xPlot_layer.append(0)
                    yPlot_layer.append( layerMap[board] )
                if ( (102 in goodBoardHitPos) or (103 in goodBoardHitPos) ) and board != 102 and board != 103 and board in layerMap:
                    xPlot_layer.append(1)
                    yPlot_layer.append( layerMap[board] )
                if ( (104 in goodBoardHitPos) or (105 in goodBoardHitPos) ) and board != 104 and board != 105 and board in layerMap:
                    xPlot_layer.append(2)
                    yPlot_layer.append( layerMap[board] )

        fig = plt.figure()
        #plt.hist(coincPlot_105, range(100,107,1), density=True, facecolor='g', alpha=0.75)
        #plotTitle = ""
        #plotFile = "output_analyzeGoodCscHitData_coincDist.png"
        #plt.xlabel("Board")
        #plt.ylabel("Number of Hits")
        #plt.title(plotTitle)

        #plt.hist2d(xPlot, yPlot, bins=[[100,101,102,103,104,105,106],[100,101,102,103,104,105,106]]  )
        #plt.colorbar()
        #plt.xlabel("Plane #")
        #plt.ylabel("Plane #")

        plt.hist2d(xPlot_layer, yPlot_layer, bins=[[0,1,2,3],[0,1,2,3]]  )
        plt.colorbar()
        plt.xlabel("Layer #")
        plt.ylabel("Layer #")

        #plt.plot()
        plt.show()
        #plt.savefig(plotFile)
    
        return None

    def analyzeData_checkEff_layer(self):
        if self.allTrigs == None :
            return

        totalTrig = 0
        totalGood_0 = 0
        totalGood_1 = 0

        xPlot = []
        yPlot = []
        zPlot = []

        for key in self.allTrigs:
            trigNum = key
            boardList = self.allTrigs[key]

            #get good hits
            goodBoardHitPos = self.analyzeData_getGoodHitPos(boardList)
            if goodBoardHitPos == None :
                continue

            #select good event
            isGoodEvent = True
            reqBoards = [100,101,104,105]
            for board in reqBoards :
                #does event have hit in required layer
                if board not in goodBoardHitPos:
                    isGoodEvent = False
                    continue
                #position cuts
                if goodBoardHitPos[board] < 10 :
                    isGoodEvent = False
                if goodBoardHitPos[board] > 53 :
                    isGoodEvent = False
            if isGoodEvent == False:
                continue

            #good event here
            totalTrig = totalTrig + 1
            if (102 in goodBoardHitPos) or (103 in goodBoardHitPos)  :
                totalGood_0 = totalGood_0 + 1
            if (102 in goodBoardHitPos) and (103 in goodBoardHitPos)  :
                totalGood_1 = totalGood_1 + 1

        #results
        print("Total trig ",totalTrig,"\tTotal good 0 ",totalGood_0)
        if totalTrig > 0 :
            print( totalGood_0/totalTrig)
        print("Total trig ",totalTrig,"\tTotal good 1 ",totalGood_1)
        if totalTrig > 0 :
            print( totalGood_1/totalTrig)


    def analyzeData_posEff(self):
        if self.allTrigs == None :
            return
        totalTrig = 0
        totalGood = 0

        xPlot_pred = []
        yPlot_pred = []

        xPlot_data = []
        yPlot_data = []

        xPlot_miss = []
        yPlot_miss = []


        for key in self.allTrigs:
            trigNum = key
            boardList = self.allTrigs[key]

            #get good hits
            goodBoardHitPos = self.analyzeData_getGoodHitPos(boardList)
            if goodBoardHitPos == None :
                continue
            totalTrig = totalTrig + 1

            #select good event
            isGoodEvent = True
            reqBoards = [100,101,102,103]
            for board in reqBoards :
                #does event have hit in required layer
                if board not in goodBoardHitPos:
                    isGoodEvent = False
                    continue
                #position cuts
                #if goodBoardHitPos[board] < 10 :
                #    isGoodEvent = False
                #if goodBoardHitPos[board] > 53 :
                #    isGoodEvent = False
            if isGoodEvent == False:
                continue

            #try straight line cut
            pred_x = -0.46*goodBoardHitPos[100] + 1.43*goodBoardHitPos[102] + 1.1
            pred_y = -0.47*goodBoardHitPos[101] + 1.45*goodBoardHitPos[103] + 0.1

            #good event here
            totalGood = totalGood + 1

            xPlot_pred.append(pred_x)
            yPlot_pred.append(pred_y)

            if (104 in goodBoardHitPos) and (105 in goodBoardHitPos):
                xPlot_data.append(goodBoardHitPos[104])
                yPlot_data.append(goodBoardHitPos[105])

            if (104 not in goodBoardHitPos) :
                xPlot_miss.append(pred_x)
            if (105 not in goodBoardHitPos) :
                yPlot_miss.append(pred_y)


        fig = plt.figure()

        plt.hist(yPlot_pred, range(0,64,1), facecolor='g')
        plt.hist(yPlot_miss, range(0,64,1), facecolor='r')
        plt.xlabel("Ch #")
        plt.ylabel("Number of Hits")


        #plt.hist2d(xPlot_pred, yPlot_pred, bins=[range(0,64,1),range(0,64,1)]  )
        #plt.hist2d(xPlot_pred, yPlot_pred, bins=[range(0,68,4),range(0,68,4)]  )
        #plt.hist2d(xPlot_data, yPlot_data, bins=[range(0,68,4),range(0,68,4)]  )
        #plt.colorbar()
        #plt.xlabel("Ch #")
        #plt.ylabel("Ch #")

        plt.show()

    def analyzeData_goodEvents_qDist(self):
        if self.allTrigs == None :
            return

        totalTrig = 0
        totalGood = 0

        qDist_all = []
        qDist_prompt = []
        qDist_late = []

        for key in self.allTrigs:
            trigNum = key
            boardList = self.allTrigs[key]

            #get good hits
            goodBoardHitPos = self.analyzeData_getGoodHitPos(boardList)
            if goodBoardHitPos == None :
                continue
            totalTrig = totalTrig + 1

            #select good event
            isGoodEvent = True
            reqBoards = self.allBoards
            for board in reqBoards :
                #does event have hit in required layer
                if board not in goodBoardHitPos:
                    isGoodEvent = False
                    continue
                #position cuts
                if goodBoardHitPos[board] < 10 :
                    isGoodEvent = False
                if goodBoardHitPos[board] > 53 :
                    isGoodEvent = False
            if isGoodEvent == False:
                continue

            #try straight line cut
            diff_x = 0
            diff_y = 0
            if (100 in goodBoardHitPos) and (102 in goodBoardHitPos) and (104 in goodBoardHitPos) :
                pred_x = -0.46*goodBoardHitPos[100] + 1.43*goodBoardHitPos[102] + 1.1
                diff_x = goodBoardHitPos[104] - pred_x
            if (101 in goodBoardHitPos) and (103 in goodBoardHitPos) and (105 in goodBoardHitPos) :
                pred_y = -0.47*goodBoardHitPos[101] + 1.45*goodBoardHitPos[103] + 0.1
                diff_y = goodBoardHitPos[105] - pred_y           
            if diff_x < -5 or diff_x > 5 :
                continue
            if diff_y < -5 or diff_y > 5 :
                continue

            #good event here
            totalGood = totalGood + 1
            for boardInfo in boardList:
                if len(boardInfo) != 3 :
                    print("WEIRD")
                    continue
                boardId = boardInfo[0]
                boardTrigDiff = boardInfo[1]
                boardData = boardInfo[2]
                if len(boardData) != 3 :
                    print("WEIRD")
                trigCount = boardData[0]
                trigBCID = boardData[1]
                hits = boardData[2]
                #print("\tboardId ",boardId,"\tTrig Count ", trigCount, "\tTrig BCID ", trigBCID,"\tTrig Diff ",boardTrigDiff)
                for hit in hits:
                    if len(hit) != 4 :
                        print("WEIRD")
                    ch = hit[0]
                    pdo = hit[1]
                    tdo = hit[2]
                    trigTime = hit[3]

                    if trigTime < -4 or trigTime > 30 :
                        continue

                    qDist_all.append(pdo)
                    if trigTime >= -4 and trigTime <= 0 :
                        qDist_prompt.append(pdo)
                    if trigTime > 0 and trigTime <= 30 :
                        qDist_late.append(pdo)
                    #print("\t\tChan # ",ch,"\tPDO ",pdo,"\tTDO ",tdo,"\tTrig Time ", trigTime )

        #results
        print("Total trig ",totalTrig,"\tTotal good ",totalGood)
        fig = plt.figure()

        plt.hist(qDist_prompt, 100, facecolor='g')
        plt.hist(qDist_late, 100, facecolor='r')
        plt.xlabel("Charge (ADC)")
        plt.ylabel("Number of Hits")

        #plt.show()
        plt.plot()
        plt.savefig("output_goodEvents_qDist.png")

#END CSC_ANALYZE CLASS

def main():

    if len(sys.argv) != 2 :
        print("cscAnalyze_analyzeSyncedData: need to provide input file name")
        return
    fileName = sys.argv[1]
    cscAnalyzeData = CSC_ANALYZE(fileName)

if __name__ == '__main__':
    main()
