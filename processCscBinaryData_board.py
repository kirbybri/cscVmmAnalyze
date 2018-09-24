import struct
import sys 
import string
import socket
import time
import os
import pickle

#BEGIN CSC_BINARY CLASS
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
        self.debug = True

        #constants
        self.headerWord = 0x00a8c0
        self.footerWord = 0xffffffff

        print("GET DATA")
        self.getData()
        #print("DUMP DATA")
        #self.dumpData()
        print("FIND HEADERS")
        self.findHeaders()
        print("CHECK PACKETS")
        self.checkPackets()
        print("PARSE PACKETS")
        self.parsePackets()
        #print("CHECK EVENTS")
        #self.checkData()
        print("OUTPUT EVENTS")
        self.outputData()


    def getData(self):
        #check if data exists
        isFile = os.path.isfile(self.inputFileName) 
        if isFile == False:
            print("Could not find input file, quitting")
            return None
        #put binary data into memory
        self.input_file = open(self.inputFileName,'rb')
        self.fileContent = self.input_file.read()     
        print("Read input file of length (bytes): ", len(self.fileContent))

        #loop over input file 4 bytes at a time, load into array
        for pos in range(0, len(self.fileContent), 4):
            #note need to assume network byte ordering
            line = struct.unpack('!I', self.fileContent[pos:pos+4])
            if len(line) != 1:	
                print("getData: error parsing input file, quitting")
                return None
            data = line[0]
            self.fileArray.append(data)        
        return None


    def dumpData(self):
        if len(self.fileArray) == None:
            return None

        #loop over input file 4 bytes at a time, look for packet header words
        for lineNum in range(0,len(self.fileArray),1):
            line = self.fileArray[lineNum]
            print(lineNum,"\t",hex(line))
            if lineNum > 100 :
                break
        return None


    def findHeaders(self):
        if len(self.fileArray) == None:
            return None

        #loop over input file 4 bytes at a time, look for packet header words
        foundFirstPacket = False
        #for lineNum in range(0,len(self.fileArray),1):
        for lineNum in range(1,len(self.fileArray)-3,1): #note offset from beginning and eof
            line = self.fileArray[lineNum]
            #check for header field, add to list
            if (line & 0xFFFFFF) == self.headerWord :
                #possible header word, check for header structure and values
                prevFooter = (self.fileArray[lineNum-1] & 0xFFFFFFFF)
                boardId = (self.fileArray[lineNum] & 0xFF000000) >> 24
                triggerCount = (self.fileArray[lineNum+2] & 0xFFFFFFFF)
                vmm_id = (self.fileArray[lineNum+3] & 0xFF)
                triggerBcid = (self.fileArray[lineNum+3] & 0xFFFF00) >> 8
                precision = (self.fileArray[lineNum+3] & 0xFF000000 ) >> 24

                #look for footer words preceeding header, ignore for first packet
                if foundFirstPacket == True and prevFooter != self.footerWord :
                    continue

                #require valid board ID
                if boardId < 100 or boardId > 105 :
                    continue
                
                #require valid VMM ID
                if vmm_id != 0 :
                    continue

                #require valid precision
                if precision != 0 :
                    continue
               
                #have a good header at this point
                foundFirstPacket = True
                self.headerPosList.append(lineNum)
        return None


    def checkPackets(self):
        if len(self.headerPosList) == 0 :
            return None

        #loop through list of headers, find footer word, check if packet is OK
        for headerNum in range(0, len(self.headerPosList), 1):
            headerPos = self.headerPosList[headerNum]

            #check if packet contains footer
            footerPos = -1
            lineNum = headerPos + 1
            while lineNum < len(self.fileArray) : #note,loop to end of file
                line = self.fileArray[lineNum]
            
                #check for footer field, add to list
                if line == self.footerWord :
                    footerPos = lineNum
                    break
                lineNum = lineNum + 1

            #check if footer not found
            if footerPos < 0 :
                print("checkPackets: Footer not found, weird, skip header")
                continue

            packetLength = footerPos - headerPos + 1
            if packetLength < 5 or packetLength > 517 :
                print("checkPackets: Invalid packet length, weird, skip header\t",packetLength)
                continue

            #have a good packet here
            self.packetPosList.append([headerPos,footerPos])
        return None


    def parsePackets(self):
        if self.fileContent == None or len(self.packetPosList) == 0 :
            return None

        #loop through packets, get hit info
        for packetNum in range(0, len(self.packetPosList), 1):
            if packetNum % 10000 == 0 :
                print("parsePackets: processing packet number ",packetNum,"\ttotal ",len(self.packetPosList))
            headerPos = self.packetPosList[packetNum][0]
            footerPos = self.packetPosList[packetNum][1]

            #do some safety checks
            if headerPos < 0 or headerPos >= len(self.fileArray) :
                print("parsePackets: bad packet, skip")
                continue
            if footerPos < 0 or footerPos >= len(self.fileArray) :
                print("parsePackets: bad packet, skip")
                continue

            boardId = (self.fileArray[headerPos] & 0xFF000000) >> 24
            triggerCount = (self.fileArray[headerPos+2] & 0xFFFFFFFF)
            triggerBcid = (self.fileArray[headerPos+3] & 0xFFFF00) >> 8

            #loop over hit info
            hitList = []
            for pos in range(headerPos+4, footerPos, 2):
                dataWord0 = self.fileArray[pos]
                dataWord1 = self.fileArray[pos+1]

                if (dataWord0 == self.footerWord) or (dataWord1 == self.footerWord) :
                    print("parsePackets: Unexpected footer word, breaking")
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

                #sanity checks
                if vmm_channel < 0 or vmm_channel > 63 :
                    print("parsePackets: Unexpected channel number, skipping")
                    continue

                #filter hits by time here
                #if trigTime < -4 or trigTime > -1: #cosmic
                if trigTime < -10 or trigTime > 50: #cosmic
                        continue
                hitList.append([vmm_channel,pdo,tdo,trigTime]) #add what's necessary

            #add hits to trigger container, organize by board
            if boardId not in self.allTrigs:
               self.allTrigs[boardId] = []
            self.allTrigs[boardId].append([triggerCount,triggerBcid,hitList])
        return None


    def decodeGray(self,bin_list):
        b = [bin_list[0]]
        for i in range(1, 12):
            b += str(int(b[i - 1] != bin_list[i]))
        out = 0
        for bit in b:
            out = (out << 1) | int(bit)
        return out


    def checkData(self):
        numBoards = len(self.allTrigs)
        for key in self.allTrigs:
            boardId = int(key)
            boardTrigs = self.allTrigs[key]
            numTrigs = len(boardTrigs)

            #loop over triggers, print hit info
            print( "Board ID ",boardId, "\tNumber of Boards ", numBoards )
            for trig in boardTrigs:
                trigCount = trig[0]
                trigBcid = trig[1]
                hits = trig[2]
                numHits = len(hits)
                print("\tBoard ID ",boardId,"\tTrig count ",trigCount,"\t# of Hits ",numHits)
                for hit in hits :
                    print("\t\tChan # ",hit[0],"\tPDO ",hit[1],"\tTime ", hit[2])
        return None

    def outputData(self):
        with open("output_processCscBinaryData_board.pkl", 'wb') as f:
            pickle.dump(self.allTrigs, f,2)
        return None
#END CSC_BINARY CLASS

def main():
    if len(sys.argv) != 2 :
        print("processCscBinary_board: need to provide input file name")
        return None
    fileName = sys.argv[1]
    cscBinaryData = CSC_BINARY(fileName)

if __name__ == '__main__':
    main()
