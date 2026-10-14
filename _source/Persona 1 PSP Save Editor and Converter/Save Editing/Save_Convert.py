#imports
import sys
import os
import platform
import subprocess
import shutil
import time
import json 
import binascii
import configparser
import tkinter as tk
from tkinter import filedialog
from tkinter.filedialog import asksaveasfile
from tkinter.filedialog import askopenfilename
import time
import random
#Global Variables
global saveInfo
global saveType
global saveTypeConv
global exitMenu
global playerList
global ps1Header
global ps1Footer
global psp2ps1
global timeString
#functions
def checksumCalc(hb):
    checksum = 0
    for el in hb:
        checksum ^= (el)
    checksum = '{:02x}'.format(checksum)
    return checksum

def checksumCheck(saveInfoString):
    hexCheck = 0
    hexCheckStr = saveInfoString[256:28670]
    hexByte = binascii.unhexlify(hexCheckStr)
    hexChecksum = checksumCalc(hexByte)
    if saveInfoString[28670:28672] == hexChecksum:
        hexCheck = hexCheck + 1
    hexCheckStr = saveInfoString[0:254]
    hexByte = binascii.unhexlify(hexCheckStr)
    hexChecksum = checksumCalc(hexByte)
    if saveInfoString[254:256] == hexChecksum:
        hexCheck = hexCheck + 1
    return hexCheck

def locFind(hexString):
    global locString
    foundLoc = False
    locHex = hexString[10472:10476]
    warpHex = hexString[10600:10604]
    #2D Map suspend save
    if hexString[10464:10468] == "0200":
        locString = "Mikage-cho Map"
        foundLoc = True
    #3D Overworld Suspend save
    elif hexString[10464:10468] == "0000":
        for x in warpsDict.keys():
            if locHex in warpsDict[x][0]:
                locString = warpsDict[x][1]
                foundLoc = True
                break
    #Normal Save
    elif locHex != "9b00" and hexString[10474:10476] != "04":
        for x in locationsDict.keys():
            if locHex in locationsDict[x][0]:
                locString = locationsDict[x][1]
                foundLoc = True
                break
    #3D Overworld Warp save
    else:
        for x in warpsDict.keys():
            if warpHex in warpsDict[x][0]:
                locString = warpsDict[x][1]
                foundLoc = True
                break
    if foundLoc == False:
        locString = "Unknown"
    return locString

def saveFile(saveInfoString):
    global saveType
    global ps1Header
    global ps1Footer
    global saveTypeConv
    if saveTypeConv != "PSP":
        #Characters/Persona/Money Translation Config checks
        if saveTypeConv in ["PS1US","PS1USRAW"] and config['Converter']['Personas'] == 'on':
            saveInfoString = personaTranslate(saveInfoString)
        if saveTypeConv in ["PS1US","PS1USRAW"] and config['Converter']['Characters'] in ['on','capitalize', 'caps']:
            saveInfoString = characterTranslate(saveInfoString)
        if config['Converter']['Money'] == 'on':
            i = 5712
            moneyHex = saveInfoString[i:i+8]
            moneyHex = "".join(reversed([moneyHex[j:j+2] for j in range(0, len(moneyHex), 2)]))
            moneyInt = int(moneyHex,16)
            if saveType in ["PC", "PC SUSPEND", "PS1JP", "PS1JPCONT", "PS1JPRAW", "PS1JPCONTRAW", "PSP"] and saveTypeConv in ["PS1US","PS1USRAW"]:
                moneyInt = round(int(moneyHex,16)/100)
            elif saveType in ["PS1US","PS1USRAW"] and saveTypeConv in ["PC", "PC SUSPEND", "PS1JP", "PS1JPCONT", "PS1JPRAW", "PS1JPCONTRAW"]:
                moneyInt = int(moneyHex,16)*100
            moneyHex = '{0:08x}'.format(int(moneyInt))
            moneyHex = "".join(reversed([moneyHex[j:j+2] for j in range(0, len(moneyHex), 2)]))
            for x in range(8):
                saveInfoString = saveInfoString[:i] + moneyHex[x] + saveInfoString[i + 1:]
                i = i + 1
        #writing checksum for save data
        hexCheckStr2 = saveInfoString[256:28670]
        hexByte = binascii.unhexlify(hexCheckStr2)
        hexCheck2 = checksumCalc(hexByte)
        i = 28670
        for x in range(2):
            saveInfoString = saveInfoString[:i] + hexCheck2[x] + saveInfoString[i + 1:]
            i = i + 1
        #writing checksum for save tag
        hexCheckStr1 = saveInfoString[0:254]
        hexByte = binascii.unhexlify(hexCheckStr1)
        hexCheck1 = checksumCalc(hexByte)
        i = 254
        for x in range(2):
            saveInfoString = saveInfoString[:i] + hexCheck1[x] + saveInfoString[i + 1:]
            i = i + 1
        #Asks for save slot
        saveSlot = input("Save Slot? (0-6)")
        if saveSlot.isdigit() == False:saveSlot = -1
        while int(saveSlot) not in range(0, 7):
            print("Invalid Value")
            saveSlot = input("Save Slot? (0-6)")
            if saveSlot.isdigit() == False:saveSlot = -1
    if config['Converter']['Money'] == 'on' and saveTypeConv == "PSP" and saveType in ["PS1US","PS1USRAW"]:
        i = 8208
        moneyHex = saveInfoString[i:i+8]
        moneyHex = "".join(reversed([moneyHex[j:j+2] for j in range(0, len(moneyHex), 2)]))
        moneyInt = int(moneyHex,16)*100
        moneyHex = '{0:08x}'.format(int(moneyInt))
        moneyHex = "".join(reversed([moneyHex[j:j+2] for j in range(0, len(moneyHex), 2)]))
        for x in range(8):
            saveInfoString = saveInfoString[:i] + moneyHex[x] + saveInfoString[i + 1:]
            i = i + 1
    if saveTypeConv == "PC":
        slotString = "Perdata.S0"+saveSlot
    elif saveTypeConv == "PC SUSPEND":
        slotString = "Perdata.C0"+saveSlot
    elif saveTypeConv == "PS1US":
        slotString = "BASLUS-00339S"+saveSlot+".mcs"
    elif saveTypeConv == "PS1JP":
        slotString = "BISLPS-00500S"+saveSlot+".mcs"
    elif saveTypeConv == "PS1JPCONT":
        slotString = "BISLPS-00500C"+saveSlot+".mcs"
    elif saveTypeConv == "PS1JPRAW":
        slotString = "BISLPS-00500S"+saveSlot+"."
    elif saveTypeConv == "PS1USRAW":
        slotString = "BASLUS-00339S"+saveSlot+"."
    elif saveTypeConv == "PS1JPCONTRAW":
        slotString = "BISLPS-00500C"+saveSlot+"."
    elif saveTypeConv == "PSP":
        slotString = "PERSONA.SAV"
    else:
        slotString = "UNKNOWN"
    #Fixes header for PS1
    if saveTypeConv in ["PS1JP","PS1US","PS1JPCONT"]:
        saveInfoString = ps1Header + saveInfoString + ps1Footer
        saveInfoString = ps1TagEdit(saveInfoString,saveSlot)
    elif saveTypeConv in ["PS1JPRAW","PS1USRAW","PS1JPCONTRAW"]:
        saveInfoString = ps1Header + saveInfoString + ps1Footer
        saveInfoString = ps1TagEdit(saveInfoString,saveSlot)
        saveInfoString = saveInfoString[256:33026]
    #Convert save to binary and prompts save slot
    if config['Settings']['Encrypt'] == 'on' and saveTypeConv == "PSP":
        path = ""
        pspEncrypt(saveInfoString)
    else:
        newSave = binascii.unhexlify(saveInfoString)
        if os.name == 'nt':
            path = filedialog.asksaveasfilename(initialfile = slotString,defaultextension="*.*",filetypes=[("All Files","*.*"),("Playstation Single Save","*.mcs"),("PSP Single Save","*.SAV")])
        else:
            path = filedialog.asksaveasfilename(initialfile = slotString)
    if path == "":
        print("Save Canceled\n")
        return saveInfoString
    with open(path, 'wb') as f:  
        f.write(newSave)
    f.close()
    print("Your save has been created")
    exit(10)

def personaTranslate(saveInfoString):
    #All Personas
    i = 1264
    for x in range(31):
        #Persona Name
        personaHex = hexString[i:i+2]
        personaName = (personaID.get(personaHex,"?"))
        personaName = personaName.strip()
        personaNameSplit = list(personaName)
        if (len(personaNameSplit) < 10):
            personaNameSplit.append("ff")
        if (len(personaNameSplit) < 10):
            for x in range(10-len(personaNameSplit)):
                personaNameSplit.append("00")
        personaps1nameHex = [symbolDictPS1.get(symbol,"00") for symbol in personaNameSplit]
        personaps1nameHexFinal = ''.join(personaps1nameHex)
        if personaHex == "00":
            personaps1nameHexFinal = "00"*10
        i = i + 2
        for x in range(20):
            saveInfoString = saveInfoString[:i] + personaps1nameHexFinal[x] + saveInfoString[i + 1:]
            i = i + 1
        i = i + 106
    return saveInfoString

def characterTranslate(saveInfoString):
    #j is name strings
    j = 572
    for x in range(4):
        charHex = hexString[j:j+2]
        ps1NickNameString = charDictPS1.get(charHex,"?")
        if config['Converter']['Characters'] in ['capitalize', 'caps']:
            ps1NickNameString = ps1NickNameString.upper()
        ps1NickNameString = ps1NickNameString.strip()
        ps1NickNameString = list(ps1NickNameString)
        if (len(ps1NickNameString) < 8):
            ps1NickNameString.append("ff")
        if (len(ps1NickNameString) < 8):
            for x in range(8-len(ps1NickNameString)):
                ps1NickNameString.append("00")
        ps1nameHex = [symbolDictPS1.get(symbol,"00") for symbol in ps1NickNameString]
        ps1teamNameHexFinal = ''.join(ps1nameHex)
        if charHex == "00":
            ps1teamNameHexFinal = "00"*8
        j = j + 2
        for x in range(16):
            saveInfoString = saveInfoString[:j] + ps1teamNameHexFinal[x] + saveInfoString[j + 1:]
            j = j + 1
        j = j + 174
    return saveInfoString
        
def ps1TagEdit(saveInfoString,saveSlot):
    global saveType
    i = 0
    #Searches for save header
    for x in saveInfoString:
        if saveInfoString[i:i+24] == "4241534c55532d3030333339": #PS1US Save Header
            break
        elif saveInfoString[i:i+24] == "4249534c50532d3030353030": #PS1JP Save Header
            break
        i = i + 1
    #Edits correct slot for PS1 file header
    saveSlotFileName = 30 + int(saveSlot)
    saveSlotFileName = str(saveSlotFileName)
    j = i + 26
    for x in range(2):
        saveInfoString = saveInfoString[:j] + saveSlotFileName[x] + saveInfoString[j + 1:]
        j = j + 1
    #Correct checksum for PS1 file header
    hexCheckStr = saveInfoString[0:254]
    hexByte = binascii.unhexlify(hexCheckStr)
    hexCheck = checksumCalc(hexByte)
    k = i + 234
    for x in range(2):
        saveInfoString = saveInfoString[:k] + hexCheck[x] + saveInfoString[k + 1:]
        k = k + 1
    #correct PS1 Bios Save Tag
    levelTag = saveInfoString[1430:1432]
    timeTag = saveInfoString[8416:8424]
    levelTag = str(int(levelTag,16))
    if int(levelTag) < 10:
        levelTag = '0' + levelTag
    levelSJS = []
    s = 0
    for x in levelTag:
        levelSJS.append(int(levelTag[s]))
        s = s + 1
    s = 0
    for x in levelSJS:
        if levelSJS[0] == 0:
            levelSJS[s] = '8140'
        else:
            levelSJS[s] = '82' + '{0:02x}'.format(int(levelSJS[s])+79)
        s = s + 1
    levelSJS = ''.join(levelSJS) + '8140'
    timeTag = timeTag[0:6]
    timeSJS = []
    timeList = [timeTag[i:i + 2] for i in range(0, len(timeTag), 2)]
    s = 0
    for x in timeList:
        if int(timeList[s],16) < 10:
           timeList[s] = '0' + str(int(timeList[s],16))
        else:
            timeList[s] = str(int(timeList[s],16))
        s = s + 1
    s = 0
    for x in range (len(timeList)):
        q = 0
        for x in timeList[s]:
            timeSJS.append('82' + '{0:02x}'.format(int(timeList[s][q])+79))
            q = q + 1
        s = s + 1    
    if timeSJS[0] == '824f':
        timeSJS[0] = '8140'
    i = 2
    while i < len(timeSJS):
        timeSJS.insert(i, '8146')
        i += (2+1)
    timeSJS = ''.join(timeSJS)
    shiftJSInsert = levelSJS + timeSJS
    i = 340
    for x in range(44):
        saveInfoString = saveInfoString[:i] + shiftJSInsert[x] + saveInfoString[i + 1:]
        i = i + 1
    saveSlotJS = '82' + '{0:02x}'.format((int(saveSlot)+1)+79)
    i = 324
    for x in range(4):
        saveInfoString = saveInfoString[:i] + saveSlotJS[x] + saveInfoString[i + 1:]
        i = i + 1
    return saveInfoString    

def searchMemCard(hexString):
    saveHeaders = []
    saveTags = []
    saveOffsets = []
    i = 0
    j = u = 1
    for x in hexString:
        if hexString[i:i+24] == "4241534c55532d3030333339": #PS1US Save Header
            saveHeaders.append(hexString[i-20:(i-20)+256])
        elif hexString[i:i+24] == "4249534c50532d3030353030": #PS1JP Save Header
            saveHeaders.append(hexString[i-20:(i-20)+256])
        if hexString[i:i+40] == "8f97905f88d995b7985e81408379838b835c8369": #PS1JP Tag
            saveTags.append(bytes.fromhex(hexString[i:i+128]).decode('shift-jis'))
            saveOffsets.append(i-8)
            #print(i-8)
        elif hexString[i:i+28] == "826f826482718272826e826d8260": #PS1US Tag
            saveTags.append(bytes.fromhex(hexString[i:i+124]).decode('shift-jis'))
            saveOffsets.append(i-12)
            #print(i-16)
        i = i + 1
    if len(saveTags) == 0:
        print("No Persona save data detected in memory card")
        exit(8)
    for x in range (len(saveTags)):
        print(str(int(x+1))+ ". ",end="")
        try:
            print(saveTags[int(x)])
        except:
            print("Save File " + str(int(x+1)))
    saveSel = input("Select a save file to open\n")
    if saveSel.casefold() == "exit":
        exit()
    if saveSel.isdigit() == False:
        saveSel = 0
    while int(saveSel) not in range (1,len(saveTags)+1):
        print("Invalid selection")
        saveSel = input("Select a save file to open\n")
        if saveSel.casefold() == "exit":
            exit()
        if saveSel.isdigit() == False:
            saveSel = 0
    saveSel = int(saveSel)-1
    return saveHeaders[saveSel]+hexString[int(saveOffsets[saveSel]):(32768+int(saveOffsets[saveSel]))]

def PSP2PS1(hexString):
    global saveTypeConv
    psp2ps1 = []
    nameChoice = "1"
    #Save Tag
    if saveTypeConv in ["PS1US","PS1USRAW"]:
        nameChoice = input("Which Name would you like to transfer over?\n1.Nick Name\n2.Last Name\n3.First Name\n4.Custom\n")
        while nameChoice.casefold() not in ["1","2","3","4"]:
            print("Invalid Option")
            nameChoice = input("Which Name would you like to transfer over?\n1.Nick Name\n2.Last Name\n3.First Name\n4.Custom\n")
        ps1firstNameHex = "0000"*5
        ps1lastNameHex = "0000"*5
    elif saveTypeConv in ["PS1JP","PS1JPRAW", "PC", "PC SUSPEND"]:
        #Last Name Entry
        name = input("Last Name? (Limit 5 Characters)")
        while len(name) > 5:
            print("Name too long")
            name = input("Last Name? (Limit 5 Characters)")
        name = name.strip()
        nameSplit = list(name)
        if (len(nameSplit) < 5):
            for x in range(5-len(nameSplit)):
                nameSplit.append("00")
        nameHex = [symbolDictPS1.get(symbol,"00") for symbol in nameSplit]
        j=0
        #splits data between "80" hex values
        for x in range(5):
            nameHex = nameHex[:j] + ["80"] + nameHex[j:]
            j = j+2
        ps1lastNameHex = ''.join(nameHex)
        #First Name Entry
        name = input("First Name? (Limit 5 Characters)")
        while len(name) > 5:
            print("Name too long")
            name = input("First Name? (Limit 5 Characters)")
        name = name.strip()
        nameSplit = list(name)
        if (len(nameSplit) < 5):
            for x in range(5-len(nameSplit)):
                nameSplit.append("00")
        nameHex = [symbolDictPS1.get(symbol,"00") for symbol in nameSplit]
        i=0
        #splits data between "80" hex values
        for x in range(5):
            nameHex = nameHex[:i] + ["80"] + nameHex[i:]
            i = i+2
        ps1firstNameHex = ''.join(nameHex)
    #Nickname conversion
    pspNickNameString = []
    if nameChoice == "1":
        i = 10384
        pspNickNameHex = hexString[10384:10416]
    elif nameChoice == "2":
        i = 10304
        pspNickNameHex = hexString[10304:10336]
    elif nameChoice == "3":
        i = 10336
        pspNickNameHex = hexString[10336:10368]
    elif nameChoice == "4":
        i = 10384
        pspNickNameHex = hexString[10384:10416]
    #print(pspNickNameHex)
    for x in range(8):
        if hexString[i:i+4] == "ffff" or hexString[i:i+4] == "0000":
            break
        pspNickNameString.append((symbolDictrev.get(hexString[i:i+4],"?")))
        i = i + 4
    #print(pspNickNameString)
    if saveTypeConv in ["PS1JP","PS1JPRAW", "PC", "PC SUSPEND"]:
        for x in range(len(pspNickNameString)):
            pspNickNameString[x] = pspNickNameString[x].upper()
    if (len(pspNickNameString) < 8):
        pspNickNameString.append("ff")
    if (len(pspNickNameString) < 8):
        for x in range(8-len(pspNickNameString)):
            pspNickNameString.append("00")
    ps1nameHex = [symbolDictPS1.get(symbol,"00") for symbol in pspNickNameString]
    ps1nameHexFinal = ''.join(ps1nameHex)
    if nameChoice == "4":
        name = input("Nick Name? (Limit 8 Characters)")
        while len(name) > 8:
            print("Name too long")
            name = input("Nick Name? (Limit 8 Characters)")
        name = name.strip()
        nameSplit = list(name)
        if (len(nameSplit) < 8):
            nameSplit.append("ff")
        if (len(nameSplit) < 8):
            for x in range(8-len(nameSplit)):
                nameSplit.append("00")
        ps1nameHex = [symbolDictPS1.get(symbol,"00") for symbol in nameSplit]
        ps1nameHexFinal = ''.join(ps1nameHex)
    #print(ps1nameHexFinal)
    psp2ps1.append(ps1nameHexFinal)
    #MC level
    mcLevel = hexString[212:214]
    psp2ps1.append(mcLevel)
    #Time
    timeHex = hexString[35384:35392]
    timeHex = "".join(reversed([timeHex[i:i+2] for i in range(0, len(timeHex), 2)]))
    timeTotal = int(timeHex, 16)
    timeHR = timeTotal // 3600
    timeMin = (timeTotal%3600) // 60
    timeSec = (timeTotal%3600)%60
    #PS1/PC time can't go over 99:99
    if timeHR > 99:
        timeHR = 99
        timeMin = 59
    timeHR = '{0:02x}'.format(int(timeHR))
    timeMin =  '{0:02x}'.format(int(timeMin))
    timeSec =  '{0:02x}'.format(int(timeSec))
    timeTotal = timeHR+timeMin+timeSec+"00"
    #print(timeTotal)
    psp2ps1.append(timeTotal)
    #White space and Save Slot Checksum
    psp2ps1.append("00"*115)
    #MC Stats
    #first half and nick name
    i = 0
    psp2ps1.append(hexString[i:i+126] + ps1nameHexFinal)
    #Second half
    i = 204
    psp2ps1.append(hexString[i:i+34])
    i = i + 36
    psp2ps1.append(hexString[i:i+16])
    #Other teamates
    teamChoice = input("Would you like to transfer teammate's names?\n1.Yes\n2.US Defaults\n3.PSP Defaults\n")
    while teamChoice.casefold() not in ["1","2","3"]:
        print("Invalid Option")
        teamChoice = input("Would you like to transfer teammate's names?\n1.Yes\n2.US Defaults\n3.PSP Defaults\n")
    #i is main teammate strings, k keeps track of name placement, j is names, z is character hex ID
    i = 256
    k = 384
    j = 384
    z = 380
    for x in range(4):
        #first half and nick name
        j = k
        charHex = hexString[z:z+2]
        pspNickNameString = []
        pspNickNameHex = hexString[j:j+32]
        #print(pspNickNameHex)
        for x in range(8):
            if hexString[j:j+4] == "ffff" or hexString[j:j+4] == "0000":
                break
            pspNickNameString.append((symbolDictrev.get(hexString[j:j+4],"?")))
            j = j + 4
        if teamChoice == "2":
            pspNickNameString = charDictPS1.get(charHex,"?")
            pspNickNameString = pspNickNameString.strip()
            pspNickNameString = list(pspNickNameString)
        if teamChoice == "3":
            pspNickNameString = charDict.get(charHex,"?")
            pspNickNameString = pspNickNameString.strip()
            pspNickNameString = list(pspNickNameString)
        if saveTypeConv in ["PS1JP","PS1JPRAW", "PC", "PC SUSPEND"]:
            for x in range(len(pspNickNameString)):
                pspNickNameString[x] = pspNickNameString[x].upper()
        if (len(pspNickNameString) < 8):
            pspNickNameString.append("ff")
        if (len(pspNickNameString) < 8):
            for x in range(8-len(pspNickNameString)):
                pspNickNameString.append("00")
        ps1nameHex = [symbolDictPS1.get(symbol,"00") for symbol in pspNickNameString]
        ps1teamNameHexFinal = ''.join(ps1nameHex)
        if charHex == "00":
            ps1teamNameHexFinal = "00"*8
        psp2ps1.append(hexString[i:i+126] + ps1teamNameHexFinal)
        #Second half
        i = i + 204
        psp2ps1.append(hexString[i:i+34])
        i = i + 36
        psp2ps1.append(hexString[i:i+16])
        i = i + 16
        k = k + 256
        z = z + 256
    #All Personas
    i = 1280
    for x in range(31):
        #first half
        tempString = hexString[i:i+50]
        psp2ps1.append(hexString[i:i+50])
        #Persona Name
        personaHex = tempString[-2:]
        personaName = (personaID.get(personaHex,"?"))
        if saveTypeConv in ["PS1JP","PS1JPRAW", "PC", "PC SUSPEND"]:
            personaName = personaName.upper()
        personaName = personaName.strip()
        personaNameSplit = list(personaName)
        if (len(personaNameSplit) < 10):
            personaNameSplit.append("ff")
        if (len(personaNameSplit) < 10):
            for x in range(10-len(personaNameSplit)):
                personaNameSplit.append("00")
        personaps1nameHex = [symbolDictPS1.get(symbol,"00") for symbol in personaNameSplit]
        personaps1nameHexFinal = ''.join(personaps1nameHex)
        #For empty personas slots
        if personaHex == "00":
            personaps1nameHexFinal = "00"*10
        #print(personaps1nameHexFinal)
        psp2ps1.append(personaps1nameHexFinal)
        #Second half
        i = i + 136
        psp2ps1.append(hexString[i:i+58])
        i = i + 64
    #Teammate and compendium data
    i = 7680
    psp2ps1.append(hexString[i:i+48])
    #Form data
    choice = input("Would you like to import form data? [y/n] (WARNING! IMPORTING MAY LEAD TO CRASHES!)\n")
    while choice.casefold() not in ["y","n"]:
        print("Invalid Option")
        choice = input("Would you like to import form data? [y/n] (WARNING! IMPORTING MAY LEAD TO CRASHES!)\n")
    if choice == "y":
        i = 7728
        formHexList = []
        for x in range(9):
            formHexList.append(hexString[i:i+50])
            i = i + 50
        formHexList.reverse()
        formHexList = "".join(formHexList)
        psp2ps1.append(formHexList)
    elif choice == "n":
        print("Creating new form data...")
        players = []
        formHex = []
        #checks and see how many players in form data
        i = 7680
        for x in range(5):
            players.append(hexString[i:i+2])
            i = i + 2
        #Removes empty players
        players = [i for i in players if i != "ff"]
        playerLen = len(players)
        #makes form data
        players = []
        j = 0
        for x in range(playerLen):
            players.append('{0:02x}'.format(int(j)))
            j = j + 1
        for x in range(len(players)):
            formHex.append(players[x])
            formHex.append("ff")
        for x in range(25 - len(players)*2):
            formHex.append("ff")
        formHex = "".join(formHex)
        psp2ps1.append(formHex*9)
    i = 8178
    psp2ps1.append(hexString[i:i+1582])
    #Spell cards
    i = 10272
    psp2ps1.append(hexString[i:i+32])
    psp2ps1.append(ps1lastNameHex + ps1firstNameHex + ps1nameHexFinal + ("00"*8))
    #Location Data and Tag?
    i = 10432
    psp2ps1.append(hexString[i:i+16])
    #Location Hex
    i = 10472
    locHex = hexString[i:i+4]
    foundLoc = False
    for x in locationsDict.keys():
        if locHex == locationsDict[x][0]:
            locHex = locationsDict[x][7]
            foundLoc = True
            break
    if foundLoc == False:
        for x in warpsDict.keys():
                if locHex == warpsDict[x][0]:
                    locHex = warpsDict[x][2]
                    #print(locHex)
                    foundLoc = True
                    break
    #Sun Mall Patch
    if locHex == "4800" and hexString[10480:10482] == "01":
        locHex = "4900"
    i = 10464
    locType = hexString[i:i+2]
    if locType == "02":
        print("Mikage-cho Map Location, defaulting to Mikage-cho Tree")
        locHex = "3b02"
        foundLoc = True
    if foundLoc == False:
        print("Location unknown, defaulting to Mikage-cho Tree")
        locHex = "3b02"
    psp2ps1.append(locHex)
    #Game Flags
    i = 10664
    psp2ps1.append(("00"*14) + hexString[i:i+98])
    #Finisher, all zeroed out
    psp2ps1.append(("00"*10579))
    psp2ps1Final = ''.join(psp2ps1)
    #print(psp2ps1Final)
    #Finishing Edits
    #Time
    i = 7392
    for x in range(8):
        psp2ps1Final = psp2ps1Final[:i] + timeTotal[x] + psp2ps1Final[i + 1:]
        i = i + 1
    #Demon Analyze
    j = 11176
    demonAnalyzeHex = hexString[j:j+40]
    i = 7672
    for x in range(40):
        psp2ps1Final = psp2ps1Final[:i] + demonAnalyzeHex[x] + psp2ps1Final[i + 1:]
        i = i + 1
    #print("\n" + psp2ps1Final)
    return psp2ps1Final

def PS12PSP(hexString):
    global saveType
    ps12psp = []
    ps1NickNameString = []
    #Last Name and First Name
    #if save is JP, then you can choose to transfer names, if save is US, then you will need to input first and last names
    if saveType in ["PC", "PC SUSPEND", "PS1JP", "PS1JPCONT", "PS1JPRAW", "PS1JPCONTRAW"]:
        nameChoice = input("Would you like to transfer your first, last, and nick names? (ONLY COMPATIBLE WITH ASCII NAMES) [y/n]\n")
        while nameChoice.casefold() not in ["y","n"]:
            print("Invalid Option")
            nameChoice = input("Would you like to transfer your first, last, and nick names? (ONLY COMPATIBLE WITH ASCII NAMES) [y/n]\n")
    elif saveType in ["PS1US", "PS1USRAW"]:
        nameChoice = "US"
    if nameChoice == "n":
        #Nick Name Entry
        name = input("Nick Name? (Limit 8 Characters)")
        while len(name) > 8:
            print("Name too long")
            name = input("Nick Name? (Limit 8 Characters)")
        name = name.strip()
        nameSplit = list(name)
        if (len(nameSplit) < 8):
            nameSplit.append("FF")
        if (len(nameSplit) < 8):
            for x in range(8-len(nameSplit)):
                nameSplit.append("WS")
        nameHex = [symbolDict.get(symbol,"0000") for symbol in nameSplit]
        pspnameHexFinal = ''.join(nameHex)
        #Last Name Entry
        name = input("Last Name? (Limit 8 Characters)")
        while len(name) > 8:
            print("Name too long")
            name = input("Last Name? (Limit 8 Characters)")
        name = name.strip()
        nameSplit = list(name)
        if (len(nameSplit) < 8):
            for x in range(8-len(nameSplit)):
                nameSplit.append("WS")
        nameHex = [symbolDict.get(symbol,"0000") for symbol in nameSplit]
        lastNameHexFinal = ''.join(nameHex)
        #First Name Entry
        name = input("First Name? (Limit 8 Characters)")
        while len(name) > 8:
            print("Name too long")
            name = input("First Name? (Limit 8 Characters)")
        name = name.strip()
        nameSplit = list(name)
        if (len(nameSplit) < 8):
            for x in range(8-len(nameSplit)):
                nameSplit.append("WS")
        nameHex = [symbolDict.get(symbol,"0000") for symbol in nameSplit]
        firstNameHexFinal = ''.join(nameHex)
    elif nameChoice == "y":
        #Nickname conversion
        i = 382
        for x in range(8):
            if hexString[i:i+2] == "ff":
                break
            ps1NickNameString.append((symbolDictPS1rev.get(hexString[i:i+2],"?")))
            i = i + 2
        if (len(ps1NickNameString) < 8):
            ps1NickNameString.append("FF")
        if (len(ps1NickNameString) < 8):
            for x in range(8-len(ps1NickNameString)):
                ps1NickNameString.append("WS")
        if config['Settings']['Debug'] == 'on':print(ps1NickNameString)
        pspnameHex = [symbolDict.get(symbol,"0000") for symbol in ps1NickNameString]
        pspnameHexFinal = ''.join(pspnameHex)
        #Last Name Conversion
        ps1FirstNameString = []
        ps1LastNameString = []
        i = 7298
        for x in range(5):
            if hexString[i+2:i+4] == "ff":
                break
            ps1FirstNameString.append((symbolDictPS1rev.get(hexString[i:i+2],"?")))
            i = i + 4
        if (len(ps1FirstNameString) < 8):
            for x in range(8-len(ps1FirstNameString)):
                ps1FirstNameString.append("WS")
        if config['Settings']['Debug'] == 'on':print(ps1FirstNameString)
        pspnameHex = [symbolDict.get(symbol,"0000") for symbol in ps1FirstNameString]
        lastNameHexFinal = ''.join(pspnameHex)
        #First Name Conversion
        i = 7318
        for x in range(5):
            if hexString[i+2:i+4] == "ff":
                break
            ps1LastNameString.append((symbolDictPS1rev.get(hexString[i:i+2],"?")))
            i = i + 4
        if (len(ps1LastNameString) < 8):
            for x in range(8-len(ps1LastNameString)):
                ps1LastNameString.append("WS")
        if config['Settings']['Debug'] == 'on':print(ps1LastNameString)
        pspnameHex = [symbolDict.get(symbol,"0000") for symbol in ps1LastNameString]
        firstNameHexFinal = ''.join(pspnameHex)
    elif nameChoice == "US":
        #Nickname conversion
        i = 382
        for x in range(8):
            if hexString[i:i+2] == "ff":
                break
            ps1NickNameString.append((symbolDictPS1rev.get(hexString[i:i+2],"?")))
            i = i + 2
        if (len(ps1NickNameString) < 8):
            ps1NickNameString.append("FF")
        if (len(ps1NickNameString) < 8):
            for x in range(8-len(ps1NickNameString)):
                ps1NickNameString.append("WS")
        if config['Settings']['Debug'] == 'on':print(ps1NickNameString)
        pspnameHex = [symbolDict.get(symbol,"0000") for symbol in ps1NickNameString]
        pspnameHexFinal = ''.join(pspnameHex)
        #Last Name Entry
        name = input("Last Name? (Limit 8 Characters)")
        while len(name) > 8:
            print("Name too long")
            name = input("Last Name? (Limit 8 Characters)")
        name = name.strip()
        nameSplit = list(name)
        if (len(nameSplit) < 8):
            for x in range(8-len(nameSplit)):
                nameSplit.append("WS")
        nameHex = [symbolDict.get(symbol,"0000") for symbol in nameSplit]
        lastNameHexFinal = ''.join(nameHex)
        #First Name Entry
        name = input("First Name? (Limit 8 Characters)")
        while len(name) > 8:
            print("Name too long")
            name = input("First Name? (Limit 8 Characters)")
        name = name.strip()
        nameSplit = list(name)
        if (len(nameSplit) < 8):
            for x in range(8-len(nameSplit)):
                nameSplit.append("WS")
        nameHex = [symbolDict.get(symbol,"0000") for symbol in nameSplit]
        firstNameHexFinal = ''.join(nameHex)
    if config['Settings']['Debug'] == 'on':print(pspnameHexFinal)
    if config['Settings']['Debug'] == 'on':print(lastNameHexFinal)
    if config['Settings']['Debug'] == 'on':print(firstNameHexFinal)
    #MC Stats
    #First half
    i = 256
    ps12psp.append(hexString[i:i+126] + "00" + pspnameHexFinal + "00"*22)
    #Second half
    i = 398
    ps12psp.append(hexString[i:i+34] + "00")
    i = i + 34
    ps12psp.append(hexString[i:i+16])
    #Other teamates
    teamChoice = input("Would you like to transfer teammate's names? (ONLY COMPATIBLE WITH ASCII NAMES)\n1.Yes\n2.US Defaults\n3.PSP Defaults\n")
    while teamChoice.casefold() not in ["1","2","3"]:
        print("Invalid Option")
        teamChoice = input("Would you like to transfer teammate's names?\n1.Yes\n2.US Defaults\n3.PSP Defaults\n")
    #i is main teamate strings, k keeps track of name placement, j is names, z is character hex ID
    i = 448
    k = 574
    j = 574
    z = 572
    for x in range(4):
        #first half and nick name
        j = k
        charHex = hexString[z:z+2]
        ps1NickNameString = []
        ps1NickNameHex = hexString[j:j+16]
        #print(pspNickNameHex)
        for x in range(8):
            if hexString[j:j+2] == "ff":
                break
            ps1NickNameString.append((symbolDictPS1rev.get(hexString[j:j+2],"?")))
            j = j + 2
        if teamChoice == "2":
            ps1NickNameString = charDictPS1.get(charHex,"?")
            ps1NickNameString = ps1NickNameString.strip()
            ps1NickNameString = list(ps1NickNameString)
        if teamChoice == "3":
            ps1NickNameString = charDict.get(charHex,"?")
            ps1NickNameString = ps1NickNameString.strip()
            ps1NickNameString = list(ps1NickNameString)
        if (len(ps1NickNameString) < 8):
            ps1NickNameString.append("FF")
        if (len(ps1NickNameString) < 8):
            for x in range(8-len(ps1NickNameString)):
                ps1NickNameString.append("00")
        pspnameHex = [symbolDict.get(symbol,"0000") for symbol in ps1NickNameString]
        pspteamNameHexFinal = ''.join(pspnameHex)
        if charHex == "00":
            pspteamNameHexFinal = "00"*16
        ps12psp.append(hexString[i:i+126] + "00" + pspteamNameHexFinal + "00"*22)
        #Second half
        i = i + 142
        ps12psp.append(hexString[i:i+34] + "00")
        i = i + 34
        ps12psp.append(hexString[i:i+16])
        i = i + 16
        k = k + 192
        z = z + 192
    #All Personas
    i = 1216
    for x in range(31):
        #first half
        ps12psp.append(hexString[i:i+50] + "00"*41)
        #Second half
        i = i + 66
        ps12psp.append(hexString[i:i+62] + "00"*3)
        i = i + 62
    ps12psp.append(("00"*96) + "ff" + ("00"*3))
    #Teammate and compendium data
    i = 5184
    ps12psp.append(hexString[i:i+48])
    #Form data
    i = 5232
    formHexList = []
    for x in range(9):
        formHexList.append(hexString[i:i+50])
        i = i + 50
    formHexList.reverse()
    formHexList = "".join(formHexList)
    ps12psp.append(formHexList)
    i = 5682
    ps12psp.append(hexString[i:i+1582] + "00"*256)
    #Spell cards
    i = 7264
    ps12psp.append(hexString[i:i+32])
    
    ps12psp.append(lastNameHexFinal + firstNameHexFinal + "00"*8 + pspnameHexFinal + "00"*8)
    #Location Tag?
    i = 7368
    ps12psp.append(hexString[i:i+16] + "00"*8 + "03" + "00"*3)
    #Location Hex
    i = 7384
    locHex = hexString[i:i+4]
    locSel = ""
    foundLoc = False
    for x in locationsDict.keys():
        if locHex in locationsDict[x][0]:
            print("Location detected: " + locationsDict[x][1])
            locSel = x
            foundLoc = True
            break
    if foundLoc == False:
        print("Location unknown, defaulting to Mikage-cho Tree")
        locHex = "3b02"
        locSel = "4"
    ps12psp.append(locHex + "00"*94)
    #Game flags
    i = 7416
    ps12psp.append(hexString[i:i+98])
    #Temp finisher
    ps12psp.append("00"*13951 + "78563412")
    #Finishing Edits
    ps12pspFinal = ''.join(ps12psp)
    #Demon Analyze
    j = 7672
    demonAnalyzeHex = hexString[j:j+40]
    i = 11176
    for x in range(40):
        ps12pspFinal = ps12pspFinal[:i] + demonAnalyzeHex[x] + ps12pspFinal[i + 1:]
        i = i + 1
    #Time
    timeHR = int(hexString[18:20],16)
    timeMin = int(hexString[20:22],16)
    timeSec = int(hexString[22:24],16)
    timeTotal = (int(timeHR)*3600)+(int(timeMin)*60)+int(timeSec)
    timeTotalHex = '{0:08x}'.format(int(timeTotal))
    timeTotalHex = "".join(reversed([timeTotalHex[i:i+2] for i in range(0, len(timeTotalHex), 2)]))
    i = 35384
    for x in range(8):
        ps12pspFinal = ps12pspFinal[:i] + timeTotalHex[x] + ps12pspFinal[i + 1:]
        i = i + 1
    #Location and warp fix
    #warp
    warp = locationsDict[locSel][2]
    i = 10600
    for x in range(4):
        ps12pspFinal = ps12pspFinal[:i] + warp[x] + ps12pspFinal[i + 1:]
        i = i + 1
    #floor
    floor = locationsDict[locSel][3]
    i = 10604
    for x in range(4):
        ps12pspFinal = ps12pspFinal[:i] + floor[x] + ps12pspFinal[i + 1:]
        i = i + 1
    i = 10480
    for x in range(4):
        ps12pspFinal = ps12pspFinal[:i] + floor[x] + ps12pspFinal[i + 1:]
        i = i + 1
    #X position
    xPos = locationsDict[locSel][4]
    i = 10608
    for x in range(4):
        ps12pspFinal = ps12pspFinal[:i] + xPos[x] + ps12pspFinal[i + 1:]
        i = i + 1
    i = 10488
    for x in range(4):
        ps12pspFinal = ps12pspFinal[:i] + xPos[x] + ps12pspFinal[i + 1:]
        i = i + 1
    #Y position
    yPos = locationsDict[locSel][5]
    i = 10612
    for x in range(4):
        ps12pspFinal = ps12pspFinal[:i] + yPos[x] + ps12pspFinal[i + 1:]
        i = i + 1
    i = 10496
    for x in range(4):
        ps12pspFinal = ps12pspFinal[:i] + yPos[x] + ps12pspFinal[i + 1:]
        i = i + 1
    #direction
    direction = locationsDict[locSel][6]
    i = 10616
    for x in range(4):
        ps12pspFinal = ps12pspFinal[:i] + direction[x] + ps12pspFinal[i + 1:]
        i = i + 1
    #First battle fix
    i = 10836
    fbFix = "01"
    for x in range(2):
        ps12pspFinal = ps12pspFinal[:i] + fbFix[x] + ps12pspFinal[i + 1:]
        i = i + 1
    #nurse door fix
    i = 38384
    for x in range(2):
        ps12pspFinal = ps12pspFinal[:i] + fbFix[x] + ps12pspFinal[i + 1:]
        i = i + 1
    #print("\n" + ps12pspFinal)
    return ps12pspFinal
    
def pspDecrypt(path):
    if os.name != 'nt':
        print("Decryption tool only compatible with Windows\n")
        exit(6)
    print("Attempting decryption\n")
    pPath = '"{}"'.format(path)#f'"{path}"'
    realPath = os.path.realpath(os.path.dirname(__file__)) + "\\data\\Tools"
    parent = os.path.dirname(path)
    fileName =  os.path.basename(path)
    dPath = realPath + "\\PERSONA.OUT"
    CmdCom = "cd " + realPath + " && " + "psp-save-w32.exe -d Key.bin 5 " + pPath + " PERSONA.OUT && exit"
    if config['Settings']['Debug'] == 'on':print(path + "\n" + pPath + "\n" + realPath + "\n" + parent + "\n" + CmdCom)
    subprocess.call(CmdCom, shell=True)
    for x in range (5):
        try: 
            f = open(dPath, 'rb')
        except Exception:
            print("File not found, retrying")
            time.sleep(3.5)
            pass
    try: 
        file = f.read()
    except Exception:
        print("\nDecryption Failed\nThe program will exit\n")
        exit(6)
    byteData = binascii.hexlify(file)
    hexString = byteData.decode()
    f.close()
    print("Decryption Successful")
    if os.path.exists(dPath):
      os.remove(dPath)
    else:
      print("Temp Save not found\nTemp not deleted\n")
    return hexString
    
def pspEncrypt(saveInfoString):
    global sfoOut
    global locString
    global timeString
    sfMode = "CUSTOM"
    sedMode = "SED-PC.exe"
    if os.name != 'nt':
        print("Encryption tool only compatible with Windows\n")
        config['Settings']['Encrypt'] = 'off'
        return
    #Asks if they'd like to tranfer SFO
    sfChoice = input("Would you like to import your own PARAM.SFO? (y,n)")
    while sfChoice.casefold() not in ("y","n"):
        print("Invalid choice")
        sfChoice = input("Would you like to import your own PARAM.SFO? (y,n)")
    if sfChoice.casefold() == "y":
        sfMode = "IMPORT"
    elif sfChoice.casefold() == "n":
        sfMode = "CUSTOM"
    if sfMode == "CUSTOM":
        #Asks for save slot
        saveSlot = input("Save Slot? (0-127)")
        if saveSlot == "128": saveSlot = "-1"
        if saveSlot.casefold() in ["suspend","continue","cnti","cont"]:saveSlot = "128"
        if saveSlot.isdigit() == False:saveSlot = "-1"
        while int(saveSlot) not in range(0, 129):
            print("Invalid Value")
            saveSlot = input("Save Slot? (0-127)")
            if saveSlot == "128": saveSlot = "-1"
            if saveSlot.casefold() in ["suspend","continue","cnti","cont"]:saveSlot = "128"
            if saveSlot.isdigit() == False:saveSlot = "-1"
        saveSlot = "{:04d}".format(int(saveSlot))
    print("Attempting encryption\n")
    iconPath = os.path.realpath(os.path.dirname(__file__)) + "\\data\\Icons"
    realPath = os.path.realpath(os.path.dirname(__file__)) + "\\data\\Tools"
    dPath = realPath + "\\PERSONA.DECRYPT"
    dpPath = '"{}"'.format(dPath)#f'"{dPath}"'
    ePath = realPath + "\\PERSONA.SAV"
    if sfMode == "IMPORT":
        eSFOPath = realPath + "\\PARAM.SFO"
        eSFOpPath = '"{}"'.format(eSFOPath)#f'"{eSFOPath}"'
    elif sfMode == "CUSTOM":
        eSFOPath = realPath + "\\INPUT.SFO"
        eSFOpPath = '"{}"'.format(eSFOPath)#f'"{eSFOPath}"'
    #Opening SFO file
    if sfMode == "IMPORT":
        #Opening SFO file to copy to data folder
        sfoPath = filedialog.askopenfilename(title="Select your PARAM.SFO", filetypes=[("All Files","*.*"),("PARAM.SFO","*.SFO")])
        if sfoPath == "":
            return
        sfopPath = '"{}"'.format(sfoPath)#f'"{sfoPath}"'
        for x in range (5):
            try: 
                f = open(sfoPath, 'rb')
            except Exception:
                print("File not found, retrying")
                time.sleep(3.5)
                pass
        try: 
            file = f.read()
        except Exception:
            print("\nEncryption Failed\nThe program will exit\n")
            exit(7)
    elif sfMode == "CUSTOM":
        for x in range (5):
            try: 
                f = open(eSFOPath, 'rb')
            except Exception:
                print("File not found, retrying")
                time.sleep(3.5)
                pass
        try: 
            file = f.read()
        except Exception:
            print("\nEncryption Failed\nThe program will exit\n")
            exit(7)
        eSFOPath = realPath + "\\OUTPUT.SFO"
        eSFOpPath = '"{}"'.format(eSFOPath)#f'"{eSFOPath}"'
    byteData = binascii.hexlify(file)
    hexData = byteData.decode()
    if sfMode == "CUSTOM":
        #Getting save tag data
        nameString = ""
        i = 10384
        for x in range(8):
            if saveInfoString[i:i+4] == "ffff" or saveInfoString[i:i+4] == "0000":
                break
            printHex = symbolDictrev.get(saveInfoString[i:i+4],"?")
            if printHex == "00":
                nameString = nameString + " "
            else:
                nameString = nameString + printHex
            i = i + 4
        level = str(int(saveInfoString[212:214], 16))
        i = 35120
        difHex = saveInfoString[i:i+2]
        if difHex == "00":
            difString = "NORMAL"
        elif difHex == "01":
            difString = "BEGINNER"
        elif difHex == "02":
            difString = "EXPERT"
        else:
            difString = "UNKNOWN"
        #Adding custom save tag
        saveTag = nameString + " Lv" + level + "\n*mathewstar100*\n" + locString + "\n" + timeString + " " + difString
        saveTag = (saveTag.encode())
        saveTagHex = binascii.hexlify(saveTag).decode() 
        i = 544
        for x in range(len(saveTagHex)):
            hexData = hexData[:i] + saveTagHex[x] + hexData[i + 1:]
            i = i + 1
        #Adding folder name as save slot given
        if saveSlot == "0128":
            saveSlot = "CNTI"
        folderName = "ULUS10432"+saveSlot
        folderEncode = (folderName.encode())
        folderHex = binascii.hexlify(folderEncode).decode() 
        i = 2592
        for x in range(26):
            hexData = hexData[:i] + folderHex[x] + hexData[i + 1:]
            i = i + 1
    elif sfMode == "IMPORT":
        i = 2592
        folderHex = hexData[i:i+26]
        folderDecode = binascii.unhexlify(folderHex)
        folderName = str(folderDecode.decode())
    newSave = binascii.unhexlify(hexData)
    with open(eSFOPath, 'wb') as f:  
        f.write(newSave)
    f.close()
    #Opening Save file to encrypt
    newSave = binascii.unhexlify(saveInfoString)
    with open(dPath, 'wb') as f:
        f.write(newSave)
    f.close()
    #XP Patch
    if platform.release() == "XP":
        sedMode = "SED-XP.exe"
    #CmdCom = "cd " + realPath + " && " + "psp-save-w32.exe -e Key.bin 5 " + dpPath + " PERSONA.ENCRYPT name " + sfopPath + " PARAM.OUT && exit"
    CmdCom = "cd " + realPath + " && " + sedMode + " -e " + dpPath + " " + eSFOpPath +  " PERSONA.SAV " +  " Key.bin && exit"
    if config['Settings']['Debug'] == 'on':print(path + "\n" + realPath + "\n" + parent + "\n" + CmdCom)
    subprocess.call(CmdCom, shell=True)
    #Save to folder
    if config['Settings']['SaveAs'] in ["Folder","folder"]:
        saveFolder = filedialog.askdirectory(title="Select a folder to save to")
        if saveFolder == "":
            return
        saveFolderCOPY = saveFolder
        saveFolder = saveFolder + "\\" + folderName
        try:
            os.mkdir(saveFolder) 
        except Exception:
            print("Failed to create folder, defaulting to a folder named \'PERSONASAVE\'\n")
            saveFolder = saveFolderCOPY + "\\PERSONASAVE" + str(random.randint(1,9999))
            os.mkdir(saveFolder)
            pass
    #Saving Encrypted Save
    for x in range (5):
        try: 
            f = open(ePath, 'rb')
        except Exception:
            print("File not found, retrying")
            time.sleep(3.5)
            pass
    try: 
        file = f.read()
    except Exception:
        print("\nEncryption Failed\nThe program will exit\n")
        exit(7)
    byteData = binascii.hexlify(file)
    hexData = byteData.decode()
    newSave = binascii.unhexlify(hexData)
    if config['Settings']['SaveAs'] in ["Folder","folder"]:
        enPath = saveFolder + "\\PERSONA.SAV"
    else:
        enPath = filedialog.asksaveasfilename(initialfile = "PERSONA.SAV",defaultextension="*.*",filetypes=[("All Files","*.*"),("PSP Single Save","*.SAV")])
        if enPath == "":
            return
    with open(enPath, 'wb') as f:  
        f.write(newSave)
    f.close()
    #Saving Encrypted SFO
    for x in range (5):
        try: 
            f = open(eSFOPath, 'rb')
        except Exception:
            print("File not found, retrying")
            time.sleep(3.5)
            pass
    try: 
        file = f.read()
    except Exception:
        print("\nEncryption Failed\nThe program will exit\n")
        exit(7)
    byteData = binascii.hexlify(file)
    hexData = byteData.decode()
    newSave = binascii.unhexlify(hexData)
    if config['Settings']['SaveAs'] in ["Folder","folder"]:
        enSFOPath = saveFolder + "\\PARAM.SFO"
    else:
        enSFOPath = filedialog.asksaveasfilename(initialfile = "PARAM.SFO",defaultextension="*.*",filetypes=[("All Files","*.*"),("PSP PARAM.SFO","*.SFO")])
        if enSFOPath == "":
            return
    with open(enSFOPath, 'wb') as f:  
        f.write(newSave)
    f.close()
    #Copys custom PSP Icons
    iconDST = os.path.dirname(enPath)
    try: 
        shutil.copy2(iconPath + "\\ICON0.png", iconDST)
        shutil.copy2(iconPath + "\\PIC1.png", iconDST)
    except Exception:
        print("Failed to copy over PSP icons")
        pass
    print("Encryption Successful")
    #Removes Temp files
    if os.path.exists(dPath):
        os.remove(dPath)
    else:
        print("Temp Save not found\nTemp not deleted\n")
    if os.path.exists(ePath):
        os.remove(ePath)
    else:
        print("Temp Save not found\nTemp not deleted\n")
    if os.path.exists(eSFOPath):
        os.remove(eSFOPath)
    else:
        print("Temp Save not found\nTemp not deleted\n")
    print("Your save has been created")
    exit(10)

#main code
#create and loads config
config = configparser.ConfigParser()
config['Settings'] = {'Language': 'English','Encrypt': 'on', 'SaveAs': 'folder', 'Debug': 'off'}
config['Naming Scheme'] = {'Characters': 'PSP','Persona': 'PSP','Moves':'PSP','Items': 'PSP','Equipment': 'PSP','Demons': 'PSP','Locations': 'PSP'}
config['Converter'] = {'Characters': 'off','Personas': 'off','Money': 'on'}
if os.path.isfile('config.ini') == False:
    with open('config.ini', 'w') as configfile:
        config.write(configfile)
else:
    try:
        config.read('config.ini')
    except Exception as e:
        print(e)
        exit(14)
#loading dictonaries
try:
    #Font
    with open('data/Persona Symbol System.json') as f: 
        data = f.read()
    with open('data/Persona Symbol System PS1.json') as n: 
        data2 = n.read()
    #Locations
    if config['Naming Scheme']['Locations'] == 'Revelations':
        with open('data/Locations (Revelations).json') as g: 
            data9 = g.read()
        with open('data/Warps (Revelations).json') as z: 
            dataA = z.read()
    elif config['Naming Scheme']['Locations'] == 'PSP':
        with open('data/Locations (PSP).json') as g: 
            data9 = g.read()
        with open('data/Warps (PSP).json') as z: 
            dataA = z.read()
    elif config['Naming Scheme']['Locations'] == 'Japanese':
        with open('data/Locations (Japanese).json', encoding='utf-8') as g: 
            data9 = g.read()
        with open('data/Warps (Japanese).json', encoding='utf-8') as z: 
            dataA = z.read()
    else:
        with open('data/Locations (PSP).json') as g: 
            data9 = g.read()
        with open('data/Warps (PSP).json') as z: 
            dataA = z.read()
    #Locations PS1
    if config['Naming Scheme']['Locations'] == 'Revelations':
        with open('data/Locations PS1 (Revelations).json') as b: 
            data10 = b.read()
    elif config['Naming Scheme']['Locations'] == 'PSP':
        with open('data/Locations PS1 (PSP).json') as b: 
            data10 = b.read()
    elif config['Naming Scheme']['Locations'] == 'Japanese':
        with open('data/Locations PS1 (Japanese).json', encoding='utf-8') as b: 
            data10 = b.read()
    else:
        with open('data/Locations PS1 (Revelations).json') as b: 
            data10 = b.read()
    #Personas
    with open('data/Persona ID (Revalations).json') as h: 
        data3 = h.read()
    #Characters
    with open('data/Characters.json') as k: 
        data5 = k.read()
    with open('data/Characters (Revalations).json') as j: 
        data4 = j.read()
except Exception as e:
    print(e)
    exit(11)
#Loading dictonaries
try:
    symbolDict = json.loads(data)
    symbolDictrev = {v: k for k, v in symbolDict.items()}
    symbolDictPS1 = json.loads(data2)
    symbolDictPS1rev = {v: k for k, v in symbolDictPS1.items()}
    locationsDict = json.loads(data9)
    locationsDictPS1 = json.loads(data10)
    warpsDict = json.loads(dataA)
    personaID = json.loads(data3)
    personaIDrev = {v: k for k, v in personaID.items()}
    charDict = json.loads(data5)
    charDictrev = {v: k for k, v in charDict.items()}
    charDictPS1 = json.loads(data4)
    charDictPS1rev = {v: k for k, v in charDictPS1.items()}
except Exception as e:
    print(e)
    exit(13)
#Loading PS1 Memory Card inserts
try:
    with open('data/PS1USInput.bin', 'rb') as g: 
        USInsert = g.read()
    byteData = binascii.hexlify(USInsert)
    USInsertHex = byteData.decode()
    with open('data/PS1JPInput.bin', 'rb') as h: 
        JPInsert = h.read()
    byteData = binascii.hexlify(JPInsert)
    JPInsertHex = byteData.decode()
    with open('data/PS1JPCONTInput.bin', 'rb') as z: 
        JPCONTInsert = z.read()
    byteData = binascii.hexlify(JPCONTInsert)
    JPCONTInsertHex = byteData.decode()
except Exception as e:
    print(e)
    exit(15)
USHeader = USInsertHex[0:1024]
USFooter = USInsertHex[1024:4352]
JPHeader = JPInsertHex[0:1024]
JPFooter = JPInsertHex[1024:4352]
JPCONTHeader = JPCONTInsertHex[0:1024]
JPCONTFooter = JPCONTInsertHex[1024:4352]

#Loading Save File
path = ""
if len(sys.argv) <= 1:
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askopenfilename()
    if path == "":
        print("No file choosen. Exiting.")
        exit()
    f = open(path, 'rb')
else:
    f = open(sys.argv[1], 'rb')
    path = sys.argv[1]
file = f.read()
byteData = binascii.hexlify(file)
hexString = byteData.decode()
#Checks for memory card
fileType = os.path.splitext(f.name)
if fileType[1] in {'.mcd','.gme','.mcr','.VM1','.mci'}:
    hexString = searchMemCard(hexString)
#Decodes Save Type
saveType = ""
saveAbnormal = False
#PS1 Single Saves
if hexString[20:44] == "4241534c55532d3030333339": #PS1 US MCS
    saveType = "PS1US"
    hexString = hexString[1024:29696]
elif hexString[20:46] == "4249534c50532d303035303053": #PS1 JP MCS
    saveType = "PS1JP"
    hexString = hexString[1024:29696]
elif hexString[20:46] == "4249534c50532d303035303043": #PS1 JP Suspend MCS
    saveType = "PS1JPCONT"
    hexString = hexString[1024:29696]
#PC Saves
elif fileType[1].casefold() in {'.s00','.s01','.s02','.s03','.s04','.s05','.s06'} and os.path.getsize(f.name) == 14336:
    saveType = "PC"
elif fileType[1].casefold() in {'.c00','.c01','.c02','.c03','.c04','.c05','.c06'} and os.path.getsize(f.name) == 14336:
    saveType = "PC SUSPEND"
#PC Saves, file size is abnormal, passes checksum test
elif fileType[1].casefold() in {'.s00','.s01','.s02','.s03','.s04','.s05','.s06'} and os.path.getsize(f.name) in range(14000,15000) and os.path.getsize(f.name) != 14336 and checksumCheck(hexString) == 2:
    saveType = "PC"
    saveAbnormal = True
elif fileType[1].casefold() in {'.c00','.c01','.c02','.c03','.c04','.c05','.c06'} and os.path.getsize(f.name) in range(14000,15000) and os.path.getsize(f.name) != 14336 and checksumCheck(hexString) == 2:
    saveType = "PC SUSPEND"
    saveAbnormal = True
#PS1 Raw Saves
elif hexString[8:68] == "8140826f826482718272826e826d8260814082658268826b826481408194": #PS1US RAW
    saveType = "PS1USRAW"
    hexString = hexString[768:29440]
elif hexString[8:68] == "8f97905f88d995b7985e81408379838b835c8369814082728366815b835e": #PS1JP RAW
    saveType = "PS1JPRAW"
    hexString = hexString[768:29440]
elif hexString[8:68] == "8f97905f88d995b7985e81408379838b835c8369814082628366815b835e": #PS1JP RAW
    saveType = "PS1JPCONTRAW"
    hexString = hexString[768:29440]
#PC Saves, file size correct, file type is abnormal, passes checksum test
elif fileType[1].casefold() not in {'.s00','.s01','.s02','.s03','.s04','.s05','.s06','.c00','.c01','.c02','.c03','.c04','.c05','.c06','.mcd','.gme','.mcr','.VM1','.mci', ".mcs"} and os.path.getsize(f.name) == 14336 and checksumCheck(hexString) == 2:
    saveType = "PC"
#PC Saves, file size correct, file type is abnormal, fails checksum test
elif fileType[1].casefold() not in {'.s00','.s01','.s02','.s03','.s04','.s05','.s06','.c00','.c01','.c02','.c03','.c04','.c05','.c06','.mcd','.gme','.mcr','.VM1','.mci', ".mcs"} and os.path.getsize(f.name) == 14336 and checksumCheck(hexString) != 2:
    saveType = "PC"
    saveAbnormal = True
#PC Saves, file size abnormal, file type is abnormal, fails checksum test
elif fileType[1].casefold() not in {'.s00','.s01','.s02','.s03','.s04','.s05','.s06','.c00','.c01','.c02','.c03','.c04','.c05','.c06','.mcd','.gme','.mcr','.VM1','.mci', ".mcs"} and os.path.getsize(f.name) in range(14000,15000) and os.path.getsize(f.name) != 14336 and checksumCheck(hexString) != 2:
    saveType = "PC"
    saveAbnormal = None
#PSP saves
elif hexString[38664:38672] == "78563412" and fileType[1].casefold() == '.sav' and os.path.getsize(f.name) == 19336:
    saveType = "PSP"
#PSP Encrypted saves
elif fileType[1].casefold() == '.sav' and os.path.getsize(f.name) == 19352:
    saveType = "PSP"
    saveAbnormal = None
#PSP JPN saves
elif fileType[1].casefold() == '.sav' and (os.path.getsize(f.name) == 18556 or os.path.getsize(f.name) == 18572):
    saveType = "PSPJPN"
#PSP Saves, file size correct, fails 'checksum' test
elif hexString[38664:38672] != "78563412" and os.path.getsize(f.name) == 19336 and fileType[1].casefold() == '.sav':
    saveType = "PSP"
    saveAbnormal = True
#PSP Saves, file size correct, file type is abnormal, fails 'checksum' test
elif hexString[38664:38672] != "78563412" and os.path.getsize(f.name) == 19336 and fileType[1].casefold() != '.sav':
    saveType = "PSP"
    saveAbnormal = True
#PSP Saves, file size is abnormal, file type is abnormal, passes 'checksum' test
elif hexString[38664:38672] == "78563412" and os.path.getsize(f.name) in range(19000,20000) and fileType[1].casefold() != '.sav':
    saveType = "PSP"
    saveAbnormal = None
#PSP Saves, file size is abnormal, fails 'checksum' test
elif hexString[38664:38672] != "78563412" and os.path.getsize(f.name) in range(19000,20000) and fileType[1].casefold() == '.sav':
    saveType = "PSP"
    saveAbnormal = None
#Invalid Save
else:
    #print("This is not a Persona save file gtfo")
    print("This is not a valid Persona save file")
    exit(3)
if saveType == "PSPJPN":
    print("Japanese PSP saves are not compatible with this editor")
    exit(5)
if saveAbnormal == True:
    print("Did you remember to decrypt your save?\nAbnormal Save! Proceed with caution!")
elif saveAbnormal == None:
    while True:
        abChoice = input("Encrypted save found, decrypt save? (y,n)")
        while abChoice.casefold() not in ("y","n"):
            print("Invalid choice")
            abChoice = input("Encrypted save found, decrypt save? (y,n)")
        if abChoice.casefold() == "y":
            hexString = pspDecrypt(path)
            break
        elif abChoice.casefold() == "n":
            print("Warning! Save may be corrupted or unreadable")
            break
#Prints out Save type, tag, and location
print("\n\nDetected Save: " + saveType)
print("Save Location: ",end="")
if saveType in ["PC", "PC SUSPEND", "PS1US", "PS1JP", "PS1JPCONT", "PS1USRAW", "PS1JPRAW", "PS1JPCONTRAW"]:
    locString = ""
    locHex = hexString[7384:7388]
    foundLoc = False
    for x in locationsDictPS1.keys():
        if locHex in locationsDictPS1[x][0]:
            print(locationsDictPS1[x][1])
            locString = locationsDictPS1[x][1]
            foundLoc = True
            break
    if foundLoc == False:
        print("Unknown")
        locString = "Unknown"
    print("Save Tag: ", end="")
    i = 0
    for x in range(8):
        if hexString[i:i+2] not in ["00","ff"]:
            print(symbolDictPS1rev.get(hexString[i:i+2],"?"),end="")
        elif hexString[i:i+2] == "ff":
            break
        else:
            print(" ",end="")
        i = i + 2
    print(" LV. ",end="")
    print(str(int(hexString[16:18], 16)),end="")
    print(" TIME: ",end="")
    if int(hexString[20:22], 16) < 10:
        print(str(int(hexString[18:20], 16)) + ":0" + str(int(hexString[20:22], 16)),end="")
        timeString = str(int(hexString[18:20], 16)) + ":0" + str(int(hexString[20:22], 16))
    else:
        print(str(int(hexString[18:20], 16)) + ":" + str(int(hexString[20:22], 16)),end="")
        timeString = str(int(hexString[18:20], 16)) + ":" + str(int(hexString[20:22], 16))
    print("\n")
else:
    locString = ""
    print(locFind(hexString))
    print("Save Tag: ", end="")
    i = 10384
    for x in range(8):
        if hexString[i:i+4] == "ffff" or hexString[i:i+4] == "0000":
            break
        printHex = symbolDictrev.get(hexString[i:i+4],"?")
        if printHex == "00":
            printHex = " "
        print(printHex,end="")
        i = i + 4
    print(" LV. ",end="")
    print(str(int(hexString[212:214], 16)),end="")
    print(" TIME: ",end="")
    timeHex = hexString[35384:35392]
    timeHex = "".join(reversed([timeHex[i:i+2] for i in range(0, len(timeHex), 2)]))
    timeTotal = int(timeHex, 16)
    hour = timeTotal // 3600
    minutes = (timeTotal%3600) // 60
    timeString = "%d:%02d" % (hour, minutes)
    print(timeString)

while True:
    if saveType in ["PC"]:    
        menu = input("Persona 1 Save Converter\n1.PC -> US PS1 Save\n2.PC -> JP PS1 Save\n3.PC -> US PS1 RAW Save\n4.PC -> JP PS1 RAW Save\n5.PC -> PSP Save\n")
        if menu.casefold() == "exit":
            exit()
        if menu.isdigit() == False:
            menu = 0
        while int(menu) not in range(1,6):
            print("Invalid Option")
            menu = input()
            if menu.casefold() == "exit":
                exit()
            if menu.isdigit() == False:
                menu = 0
        if menu == "1":
            saveTypeConv = "PS1US"
            ps1Header = USHeader
            ps1Footer = USFooter
            saveFile(hexString)
        elif menu == "2":
            saveTypeConv = "PS1JP"
            ps1Header = JPHeader
            ps1Footer = JPFooter
            saveFile(hexString)
        elif menu == "3":
            saveTypeConv = "PS1USRAW"
            ps1Header = USHeader
            ps1Footer = USFooter
            saveFile(hexString)
        elif menu == "4":
            saveTypeConv = "PS1JPRAW"
            ps1Header = JPHeader
            ps1Footer = JPFooter
            saveFile(hexString)
        elif menu == "5":
            saveTypeConv = "PSP"
            saveFile(PS12PSP(hexString))
    elif saveType == "PC SUSPEND":
        menu = input("Persona 1 Save Converter\n1.PC Suspend -> PS1 US Save\n2.PC Suspend -> PS1 JP Save\n3.PC Suspend -> PS1 JP Suspend Save\n4.PC Suspend -> PS1 US RAW Save\n5.PC Suspend -> PS1 JP RAW Save\n6.PC Suspend ->  PS1 JP Suspend RAW Save\n7.PC Suspend -> PSP Save\n")
        if menu.casefold() == "exit":
            exit()
        if menu.isdigit() == False:
            menu = 0
        while int(menu) not in range(1,8):
            print("Invalid Option")
            menu = input()
            if menu.casefold() == "exit":
                exit()
            if menu.isdigit() == False:
                menu = 0
        if menu == "1":
            saveTypeConv = "PS1US"
            ps1Header = USHeader
            ps1Footer = USFooter
            saveFile(hexString)
        elif menu == "2":
            saveTypeConv = "PS1JP"
            ps1Header = JPHeader
            ps1Footer = JPFooter
            saveFile(hexString)
        elif menu == "3":
            saveTypeConv = "PS1JPCONT"
            ps1Header = JPCONTHeader
            ps1Footer = JPCONTFooter
            saveFile(hexString)
        elif menu == "4":
            saveTypeConv = "PS1USRAW"
            ps1Header = USHeader
            ps1Footer = USFooter
            saveFile(hexString)
        elif menu == "5":
            saveTypeConv = "PS1JPRAW"
            ps1Header = JPHeader
            ps1Footer = JPFooter
            saveFile(hexString)
        elif menu == "6":
            saveTypeConv = "PS1JPCONTRAW"
            ps1Header = JPCONTHeader
            ps1Footer = JPCONTFooter
            saveFile(hexString)
        elif menu == "7":
            saveTypeConv = "PSP"
            saveFile(PS12PSP(hexString))
    elif saveType in ["PS1US","PS1USRAW"]:
        menu = input("Persona 1 Save Converter\n1.PS1 -> PC Save\n2.PS1 US -> PS1 JP Save\n3.PS1 US -> PS1 JP RAW Save\n4.PS1 -> PSP Save\n")
        if menu.casefold() == "exit":
            exit()
        if menu.isdigit() == False:
            menu = 0
        while int(menu) not in range(1,5):
            print("Invalid Option")
            menu = input()
            if menu.casefold() == "exit":
                exit()
            if menu.isdigit() == False:
                menu = 0
        if menu == "1":
            saveTypeConv = "PC"
            saveFile(hexString)
        elif menu == "2":
            saveTypeConv = "PS1JP"
            ps1Header = JPHeader
            ps1Footer = JPFooter
            saveFile(hexString)
        elif menu == "3":
            saveTypeConv = "PS1JPRAW"
            ps1Header = JPHeader
            ps1Footer = JPFooter
            saveFile(hexString)
        elif menu == "4":
            saveTypeConv = "PSP"
            saveFile(PS12PSP(hexString))
    elif saveType in ["PS1JP","PS1JPRAW"]:
        menu = input("Persona 1 Save Converter\n1.PS1 -> PC Save\n2.PS1 JP -> PS1 US Save\n3.PS1 JP -> PS1 US RAW Save\n4.PS1 -> PSP Save\n")
        if menu.casefold() == "exit":
            exit()
        if menu.isdigit() == False:
            menu = 0
        while int(menu) not in range(1,5):
            print("Invalid Option")
            menu = input()
            if menu.casefold() == "exit":
                exit()
            if menu.isdigit() == False:
                menu = 0
        if menu == "1":
            saveTypeConv = "PC"
            saveFile(hexString)
        elif menu == "2":
            saveTypeConv = "PS1US"
            ps1Header = USHeader
            ps1Footer = USFooter
            saveFile(hexString)
        elif menu == "3":
            saveTypeConv = "PS1USRAW"
            ps1Header = USHeader
            ps1Footer = USFooter
            saveFile(hexString)
        elif menu == "4":
            saveTypeConv = "PSP"
            saveFile(PS12PSP(hexString))
    elif saveType in ["PS1JPCONT","PS1JPCONTRAW"]:
        menu = input("Persona 1 Save Converter\n1.PS1 Suspend -> PC Save\n2.PS1 Suspend -> PC Suspend Save\n3.PS1 JP -> PS1 US Save\n4.PS1 Suspend JP -> PS1 JP Save\n5.PS1 -> PSP Save\n")
        if menu.casefold() == "exit":
            exit()
        if menu.isdigit() == False:
            menu = 0
        while int(menu) not in range(1,6):
            print("Invalid Option")
            menu = input()
            if menu.casefold() == "exit":
                exit()
            if menu.isdigit() == False:
                menu = 0
        if menu == "1":
            saveTypeConv = "PC"
            saveFile(hexString)
        elif menu == "2":
            saveTypeConv = "PC SUSPEND"
            saveFile(hexString)
        elif menu == "3":
            saveTypeConv = "PS1US"
            ps1Header = USHeader
            ps1Footer = USFooter
            saveFile(hexString)
        elif menu == "4":
            saveTypeConv = "PS1JP"
            ps1Header = JPHeader
            ps1Footer = JPFooter
            saveFile(hexString)
        elif menu == "5":
            saveTypeConv = "PSP"
            saveFile(PS12PSP(hexString))
    elif saveType in ["PSP"]:
        menu = input("Persona 1 PS1/PC/PSP Save Converter\n1.PSP -> PS1 US Save\n2.PSP -> PS1 JP Save\n3.PSP -> PS1 JP Suspend Save\n4.PSP -> PS1 US RAW Save\n5.PSP -> PS1 JP RAW Save\n6.PSP -> PS1 JP Suspend RAW Save\n7.PSP -> PC Save\n8.PSP -> PC Suspend Save\n")
        if menu.casefold() == "exit":
            exit()
        if menu.isdigit() == False:
            menu = 0
        while int(menu) not in range(1,9):
            print("Invalid Option")
            menu = input()
            if menu.casefold() == "exit":
                exit()
            if menu.isdigit() == False:
                menu = 0
        if menu == "1":
            saveTypeConv = "PS1US"
            ps1Header = USHeader
            ps1Footer = USFooter
            saveFile(PSP2PS1(hexString))
        elif menu == "2":
            saveTypeConv = "PS1JP"
            ps1Header = JPHeader
            ps1Footer = JPFooter
            saveFile(PSP2PS1(hexString))
        elif menu == "3":
            saveTypeConv = "PS1JPCONT"
            ps1Header = JPCONTHeader
            ps1Footer = JPCONTFooter
            saveFile(PSP2PS1(hexString))
        elif menu == "4":
            saveTypeConv = "PS1USRAW"
            ps1Header = USHeader
            ps1Footer = USFooter
            saveFile(PSP2PS1(hexString))
        elif menu == "5":
            saveTypeConv = "PS1JPRAW"
            ps1Header = JPHeader
            ps1Footer = JPFooter
            saveFile(PSP2PS1(hexString))
        elif menu == "6":
            saveTypeConv = "PS1JPCONTRAW"
            ps1Header = JPCONTHeader
            ps1Footer = JPCONTFooter
            saveFile(PSP2PS1(hexString))
        elif menu == "7":
            saveTypeConv = "PC"
            saveFile(PSP2PS1(hexString))
        elif menu == "8":
            saveTypeConv = "PC SUSPEND"
            saveFile(PSP2PS1(hexString))
