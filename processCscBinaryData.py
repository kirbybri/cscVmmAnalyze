import struct
import sys 
import string
import socket
import time
import os
import pickle

class CSC_BINARY(object):

    #__INIT__#
    def __init__(self,inputFileName):
        self.inputFileName = inputFileName
        self.inputFile = None
        self.fileContent = None
        self.fileArray = []
        self.headerPosList = []
        self.packetPosList = []
        self.allTrigs = {}

        #constants
        self.headerWord = 0x00a8c0
        self.footerWord = 0xffffffff

        self.getData()
        self.findHeaders()
        self.checkPackets()
        self.parsePackets()
        #self.checkData()
        #self.filterData()
        self.outputData()

    def getData(self):
        #check if data exists
        isFile = os.path.isfile(self.inputFileName) 
        if isFile == False:
            print("Could not find input file, quitting")
            return
        #put binary data into memory
        self.input_file = open(self.inputFileName,'rb')
        self.fileContent = self.input_file.read()     
        print("Read input file of length (bytes): ", len(self.fileContent))

        #loop over input file 4 bytes at a time, load into array
        for pos in range(0, len(self.fileContent), 4):
            #note need to assume network byte ordering
            line = struct.unpack('!I', self.fileContent[pos:pos+4])
            if len(line) != 1:
                print("findHeaders: error parsing input file, quitting")
                return
            data = line[0]
            self.fileArray.append(data)        


    def findHeaders(self):
        if len(self.fileArray) == None:
            return

        #loop over input file 4 bytes at a time, look for packet header words
        for lineNum in range(0,len(self.fileArray),1):
            line = self.fileArray[lineNum]
            #check for header field, add to list
            if (line & 0xFFFFFF) == self.headerWord :
                self.headerPosList.append(lineNum)

    def checkPackets(self):
        if len(self.headerPosList) == 0 :
            return

        #loop through list of headers, find footer word, check if packet is OK
        for headerNum in range(0, len(self.headerPosList), 1):
            headerPos = self.headerPosList[headerNum]

            #check if packet contains footer
            footerPos = -1
            lineNum = headerPos + 1
            while lineNum < len(self.fileArray) :
                line = self.fileArray[lineNum]
                #print(hex(line))
            
                #check for footer field, add to list
                if line == self.footerWord :
                    footerPos = lineNum
                    break

                #check if another header is encountered
                #if (line & 0xFFFF) == self.headerWord :
                #    break
                
                lineNum = lineNum + 1

            #check if footer not found
            if footerPos < 0 :
                print("checkPackets: Footer not found, weird, skip header")
                input("Press button")
                continue

            #have a good packet here
            self.packetPosList.append([headerPos,footerPos])
            #print(headerNum,"\t",len(self.headerPosList),"\t",headerPos,"\t",footerPos)


    def parsePackets(self):
        if self.fileContent == None or len(self.packetPosList) == 0 :
            return
        
        #loop through packets, get hit info
        for packetNum in range(0, len(self.packetPosList), 1):
            headerPos = self.packetPosList[packetNum][0]
            footerPos = self.packetPosList[packetNum][1]
 
            #do some safety checks
            if headerPos < 0 or headerPos >= len(self.fileArray) :
                print("parsePackets: bad packet, skip")
            if footerPos < 0 or footerPos >= len(self.fileArray) :
                print("parsePackets: bad packet, skip")
           
            word0 = self.fileArray[headerPos]
            word1 = self.fileArray[headerPos+1]
            word2 = self.fileArray[headerPos+2]
            word3 = self.fileArray[headerPos+3]
            triggerBcid = (word3 & 0xFFFF00) >> 8
            triggerCount = (word2 & 0xFFFFFFFF)
            boardId = (word0 & 0xFF000000) >> 24

            #loop over hit info
            hitList = []
            for pos in range(headerPos+4, footerPos, 2):
                dataWord0 = self.fileArray[pos]
                dataWord1 = self.fileArray[pos+1]

                if (dataWord0 == self.footerWord) or (dataWord1 == self.footerWord) :
                    print("WEIRD")
                    break

                #get hit info
                pdo = dataWord0 & 0x3ff
                gray = (dataWord0 & 0x3ffc00) >> 10
                tdo = (dataWord0 & 0x3fc00000) >> 22
                flag = (dataWord1 & 0x1)
                threshold = (dataWord1 & 0x2) >> 1
                vmm_channel = (dataWord1 & 0xfc) >> 2
                bcid = self.decodeGray('{0:012b}'.format(gray))
                trigTime = bcid - triggerBcid

                #filter hits here
                if trigTime < -4 or trigTime > 0:
                        continue
                hitList.append([vmm_channel,pdo,tdo]) #add what's necessary

            #add hits to trigger container
            if triggerCount not in self.allTrigs:
                self.allTrigs[triggerCount] = []
            self.allTrigs[triggerCount].append([boardId,hitList])


    def decodeGray(self,bin_list):
        b = [bin_list[0]]
        for i in range(1, 12):
            b += str(int(b[i - 1] != bin_list[i]))
        out = 0
        for bit in b:
            out = (out << 1) | int(bit)
        return out


    def checkData(self):
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


    def filterData(self):
        numTrigs = len(self.allTrigs)
        for key in self.allTrigs:
            trigNum = int(key)
            allBoards = self.allTrigs[key]
            numBoards = len(allBoards)

            #loop over triggers
            print( "Trigger # ",trigNum, "\tNumber of Boards ", len(allBoards) )
            for board in allBoards:
                boardId = board[0]
                hits = board[1]
                numHits = len(hits)
                goodHits = []
                print("\tBoard ID ",boardId,"\t# of Hits ",numHits)
                for hit in hits :
                    if hit[2] < -4 or hit[2] > 0:
                        continue
                    print("\t\tChan # ",hit[0],"\tPDO ",hit[1],"\tTime ", hit[2])
                    goodHits.append(hit)

    def outputData(self):
        with open("output_processCscBinaryData.pkl", 'wb') as f:
            pickle.dump(self.allTrigs, f,2)

#END CSC_BINARY CLASS

def main():

    if len(sys.argv) != 2 :
        print("processCscBinary: need to provide input file name")
        return
    fileName = sys.argv[1]
    cscBinaryData = CSC_BINARY(fileName)

if __name__ == '__main__':
    main()
