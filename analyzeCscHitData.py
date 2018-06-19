import struct
import sys 
import string
import socket
import time
import os
import pickle

from ROOT import gROOT, gPad, TCanvas, TF1, TH1F, TH2I, TH2F, TProfile, TGraph, TFile
gROOT.Reset()

#define ROOT canvases, histrograms + graphs
c1 = TCanvas( 'c1', '', 1500, 1000 )
h_hitChVsBoard = TH2F("h_hitChVsBoard","",4,100-0.5,104-0.5,64,0-0.5,64-0.5)

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
        numTrigs = len(self.allTrigs)
        for key in self.allTrigs:
            trigNum = int(key)
            allBoards = self.allTrigs[key]
            numBoards = len(allBoards)

            #loop over triggers, print hit info
            print( "Trigger # ",trigNum, "\tNumber of Boards ", len(allBoards) )
            for board in allBoards:
                boardId = board[0]
                hits = board[1]
                numHits = len(hits)
                print("\tBoard ID ",boardId,"\t# of Hits ",numHits)
                for hit in hits :
                    print("\t\tChan # ",hit[0],"\tPDO ",hit[1],"\tTime ", hit[2])
                    h_hitChVsBoard.Fill(boardId,hit[0])

#END CSC_ANALYZE CLASS

def main():

    if len(sys.argv) != 2 :
        print("processCscAnalyze: need to provide input file name")
        return
    fileName = sys.argv[1]
    cscAnalyzeData = CSC_ANALYZE(fileName)

    c1.Clear()
    h_hitChVsBoard.Draw("COLZ")
    c1.Update()
    input("Press key to continue")

if __name__ == '__main__':
    main()
