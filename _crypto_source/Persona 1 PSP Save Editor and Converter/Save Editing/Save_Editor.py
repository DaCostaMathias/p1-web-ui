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
global exitMenu
global playerList
global ps1Header
global ps1Footer
global sfoOut
global locString
global timeString
#functions
def isHex(string):
    try:
        int(string, 16)
        return True
    except ValueError:
        return False
        
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

def personaStatGet(saveInfoString,index):
    i = 1328+((int(index)-1)*200)
    personaStats = []
    #Persona Name
    personaStats.append(personaID.get(saveInfoString[i:i+2],"Corrupt"))
    #SP Cost
    i = i+88
    temp = saveInfoString[i:i+2]
    personaStats.append(int(temp, 16))
    #Level
    i = i+2
    temp = saveInfoString[i:i+2]
    personaStats.append(int(temp, 16))
    i = i+4
    #Stats
    for x in range(5):
        temp2 = saveInfoString[i:i+2]
        personaStats.append(int(temp2, 16))
        i = i+2
    #Rank
    i = i+2
    temp = saveInfoString[i:i+2]
    personaStats.append(int(temp, 16))
    #Character Name
    i = i+38
    temp = saveInfoString[i:i+2]
    charTemp = charDict.get(temp,"Corrupt")
    #OMP
    i = i-160
    temp = saveInfoString[i:i+4]
    temp = "".join(reversed([temp[i:i+2] for i in range(0, len(temp), 2)]))
    personaStats.append(int(temp, 16))
    #DMP
    i = i+4
    temp = saveInfoString[i:i+4]
    temp = "".join(reversed([temp[i:i+2] for i in range(0, len(temp), 2)]))
    personaStats.append(int(temp, 16))
    personaStats.append(charTemp)
    return([str(x) for x in personaStats])

def nickNameGet(hexString):
    namesList = []
    j = 128
    k = 128
    for x in range(5):
        j = k
        pspNickNameString = []
        pspNickNameHex = hexString[j:j+32]
        for x in range(8):
            if hexString[j:j+4] == "ffff" or hexString[j:j+4] == "0000":
                break
            printHex = symbolDictrev.get(hexString[j:j+4],"?")
            if printHex == "00":
                printHex = " "
            pspNickNameString.append(printHex)
            j = j + 4
        namesList.append(''.join(pspNickNameString))
        k = k + 256
    return namesList

def charStatGet(hexString,index):
    #i is start of player ID, j is start of player stats, k is HP/SP, s is status, v is added stats, w is weapon stats, p is persona lvl, g is persona exp, e is character exp
    i = 124+((int(index)-1)*256)
    j = 212+((int(index)-1)*256)
    k = 0+((int(index)-1)*256)
    s = 208+((int(index)-1)*256)
    v = 224 + ((int(index)-1)*256)
    w = 92 + ((int(index)-1)*256)
    p = 234 + ((int(index)-1)*256)
    g = 56 + ((int(index)-1)*256)
    e = 32 + ((int(index)-1)*256)
    charStat = []
    for x in range(6):
        stats = hexString[j:j+2]
        charStat.append(int(stats, 16))
        j = j+2
    for x in range(5):
        aStats = hexString[v:v+2]
        charStat.append(int(aStats, 16))
        v = v+2
    for x in range(4):
        wStats = hexString[w:w+4]
        wStats = "".join(reversed([wStats[i:i+2] for i in range(0, len(wStats), 2)]))
        charStat.append(int(wStats, 16))
        w = w+4
    pLvl = hexString[p:p+2]
    charStat.append(int(pLvl, 16))
    pEXP = hexString[g:g+8]
    pEXP = "".join(reversed([pEXP[i:i+2] for i in range(0, len(pEXP), 2)]))
    charStat.append(int(pEXP, 16))
    for x in range(4):
        temp3 = hexString[k:k+4]
        temp3 = "".join(reversed([temp3[i:i+2] for i in range(0, len(temp3), 2)]))
        charStat.append(str(int(temp3, 16)))
        k = k + 8
    charExp = hexString[e:e+8]
    charExp = "".join(reversed([charExp[i:i+2] for i in range(0, len(charExp), 2)]))
    charStat.append(int(charExp, 16))
    statu = hexString[s:s+2]
    charStat.append(statusID.get(statu,"Corrupt"))
    char = hexString[i:i+2]
    charStat.append(charDict.get(char,"Corrupt"))
    return([str(x) for x in charStat])

def charMenu():
    global hexString
    global exitMenu
    global playerList
    global locString
    global timeString
    locString = ""
    exitMenu = False
    if config['Settings']['Language'] == 'Japanese':
        print("\n\n\nセーブ・エディター")
        print("項目を選択して編集します")
        print("\t\tLevel\tSTR\tVIT\tTEC\tAGL\tLUK\tHP\tSP\t状態")
    else:
        print("\n\n\nSave Editor")
        print("Save Location: " + locFind(hexString))
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
        print("\nSelect an item to edit")
        print("\t\tLevel\tSTR\tVIT\tTEC\tAGL\tLUK\tHP\tSP\tStatus")
    #i is start of player ID, j is start of player stats, k is HP/SP, s is status
    i,j,k,s = 124,212,0,208
    playerList = []
    for x in range(5):
        temp = hexString[i:i+2]
        if temp != "00":
            playerList.append(charDict.get(temp,"Corrupt"))
        print(str(x+1) , ". " , charDict.get(temp,"Corrupt"),"\t", end="")
        for x in range(6):
            temp2 = hexString[j:j+2]
            print(int(temp2, 16), "\t", end="")
            j = j+2
        for x in range(4):
            temp3 = hexString[k:k+4]
            temp3 = "".join(reversed([temp3[i:i+2] for i in range(0, len(temp3), 2)]))
            if int(x) % 2 == 0:
                print(str(int(temp3, 16)) + "/", end="")
            else:
                print(str(int(temp3, 16)), end="")
            k = k + 8
            if int(x) == 1:
                print("\t", end="")
        temp4 = hexString[s:s+2]
        print("\t"+statusID.get(temp4,"Corrupt"), end="")
        i = 256 + i
        j = j + 244
        k = k + 224
        s = s + 256
        print('')
    if config['Settings']['Language'] == 'Japanese':
        print("6.ペルソナ\n7.装備\n8.アイテム\n9.スペルカード\n10. ¥, 場所, 等\n11. 保存先")
    else:
        print("6. Personas\n7. Equipment\n8. Items\n9. Spell Cards\n10.Money, Location, Flags, etc\n11.Save File")
    player = input()
    if player.casefold() == "exit":
        exit()
    if player.isdigit() == False:
        player = 0
    if hexString[124+((int(player)-1)*256):126+((int(player)-1)*256)] == "00" and int(player) in range(1,6):
        print("ERROR: EMPTY CHARACTER SLOT")
        player = 0
    while int(player) not in range(1,12):
        print("Invalid choice")
        player = input()
        if player.casefold() == "exit":
            exit()
        if player.isdigit() == False:
            player = 0
        if hexString[124+((int(player)-1)*256):126+((int(player)-1)*256)] == "00" and int(player) in range(1,6):
            print("ERROR: EMPTY CHARACTER SLOT")
            player = 0
    player = int(player)
    if player == 6:
        while True:
            hexString = personaMenu(hexString)
            if(exitMenu == True):
                break
        charMenu()
    if player == 7:
        hexString = equipMenu(hexString)
        charMenu()
    if player == 8:
        hexString = itemsMenu(hexString)
        charMenu()
    if player == 9:
        hexString = spellCardEdit(hexString)
        charMenu()
    if player == 10:
        hexString = extraEdits(hexString)
        charMenu()
    if player == 11:
        saveFile(hexString)
        charMenu()
    hexString = saveEdit(hexString,player,playerList[player-1])
    if player <= 5:
        charMenu()
        
def itemsMenu(saveInfoString):
    while True:
        itemCHGSel = 0
        i = 8224
        itemIDList = ['manual','exit']
        if config['Settings']['Language'] == 'Japanese':
            print("項目\t金額")
        else:
            print("Item\t\t\t\tAmount")
        for x in range(387):
            temp = saveInfoString[i:i+2]
            temp2 = saveInfoString[i+2:i+4]
            temp2Int = int(temp2, 16)
            temp3 = ''
            itemAmount = 0
            if temp2Int%2 == 0:
                temp3 = '00'
                itemAmount = int(temp2Int/2)
            else:
                temp3 = '01'
                itemAmount = int((temp2Int-1)/2)
            itemHex = temp + temp3 
            space = 28-len(itemsID.get(itemHex,"Corrupt"))
            if temp != '00':
                if int(x+1) < 10:
                    print(str(int(x+1))+".  "+itemsID.get(itemHex,"Corrupt"),end="")
                    for y in range (int(space)):
                        print(" ",end="")
                    print(str(itemAmount))
                elif int(x+1) < 100:
                    print(str(int(x+1))+". "+itemsID.get(itemHex,"Corrupt"),end="")
                    for y in range (int(space)):
                        print(" ",end="")
                    print(str(itemAmount))
                else:
                    print(str(int(x+1))+"."+itemsID.get(itemHex,"Corrupt"),end="")
                    for y in range (int(space)):
                        print(" ",end="")
                    print(str(itemAmount))
                itemIDList.append(str(x+1))
            i = i+4
        if config['Settings']['Language'] == 'Japanese':
            print("項目を選択するか、「manual」 と入力して手動で項目を挿入する （戻るには 「exit」 と入力する）")
        if config['Settings']['Debug'] == 'on':print(itemIDList)
        itemSel = input("Select an item or enter 'manual' to manually insert item (Type exit to go back)")
        while itemSel.casefold() not in itemIDList:
            print("Invalid Option")
            itemSel = input("Select an item or enter 'manual' to manually insert item (Type exit to go back)")
        if itemSel.casefold() == "exit":
            if config['Settings']['Debug'] == 'on': print("exited")
            return saveInfoString
        if itemSel.casefold() == "manual":
            saveInfoString = itemsManual(saveInfoString)
        if itemSel != "manual":
            if config['Settings']['Language'] == 'Japanese':print("1.項目の変更\n2.金額の変更")
            itemCHGSel = input("1.Change Item\n2.Change Amount")
            if itemCHGSel.isdigit() == False:itemCHGSel = 0
            while int(itemCHGSel) not in range(1, 3):
                print("Invaild Value")
                itemCHGSel = input("1.Change Item\n2.Change Amount")
                if itemCHGSel.isdigit() == False:itemCHGSel = 0
            if int(itemCHGSel) == 1: #moved to right
                if config['Settings']['Language'] == 'Japanese':print("項目を選択 （大文字小文字）")
                itemName = input("Select an item (case sensitive)")
                invaild = True
                while invaild:
                    if itemName in itemsIDrev.keys():
                        invalid = False
                        if config['Settings']['Debug'] == 'on':print("pass")
                        itemHex = itemsIDrev[itemName]
                        itemHex = itemHex[0:2]
                        print(itemHex)
                        break
                    else:
                        print("Invaild Item")
                        itemName = input("Select an item (case sensitive)")
                i = 8224+(4*(int(itemSel)-1))
                for x in range(2):
                    saveInfoString = saveInfoString[:i] + itemHex[x] + saveInfoString[i + 1:]
                    i = i + 1
            k = 8224+(4*(int(itemSel)-1))
            temp = saveInfoString[k:k+2]
            temp2 = saveInfoString[k+2:k+4]
            temp2Int = int(temp2, 16)
            if temp2Int%2 == 0:
                temp2 = '00'
            else:
                temp2 = '01'
            itemName = itemsID[(temp + temp2)]
            if int(itemCHGSel) == 2:
                k = 8224+(4*(int(itemSel)-1))
                itemHex = saveInfoString[k:k+2]
                temp2 = saveInfoString[k+2:k+4]
                temp2Int = int(temp2, 16)
                if temp2Int%2 == 0:
                    temp2 = '00'
                else:
                    temp2 = '01'
                if config['Settings']['Language'] == 'Japanese':print("の数は " + itemName + " (1-99)")
                itemAmountSel = input("How many of " + itemName + " (1-99)")
                if itemAmountSel.isdigit() == False:itemAmountSel = 0
                while int(itemAmountSel) not in range(1, 100):
                    print("Invalid Value")
                    itemAmountSel = input("How many of " + itemName + " (1-99)")
                    if itemAmountSel.isdigit() == False:itemAmountSel = 0
                itemAmountSel = int(itemAmountSel)
                if temp2 == '00':
                    itemAmountHex = itemAmountSel*2
                    itemAmountHex = '{0:02x}'.format(int(itemAmountHex))
                else:
                    itemAmountHex = (itemAmountSel*2)+1
                    itemAmountHex = '{0:02x}'.format(int(itemAmountHex))
                itemHex = itemHex + itemAmountHex
                print(itemHex)
                i = 8224+(4*(int(itemSel)-1))
                for x in range(4):
                    saveInfoString = saveInfoString[:i] + itemHex[x] + saveInfoString[i + 1:]
                    i = i + 1
                    
def itemsManual(saveInfoString):
    if config['Settings']['Language'] == 'Japanese':print("スロット番号を入力 (1-387)")
    itemSlot = input("Enter a slot to enter item (1-387)")
    if itemSlot.isdigit() == False:itemSlot = 0
    while int(itemSlot) not in range(1, 388):
        print("Invalid Value")
        itemSlot = input("Enter a slot to enter item (1-387)")
        if itemSlot.isdigit() == False:itemSlot = 0
    itemSlot = int(itemSlot)
    if config['Settings']['Language'] == 'Japanese':print("項目を選択 (大文字小文字)")
    itemName = input("Select an item (case sensitive)")
    invaild = True
    while invaild:
        if itemName in itemsIDrev.keys():
            invalid = False
            if config['Settings']['Debug'] == 'on':print("pass")
            itemHex = itemsIDrev[itemName]
            if config['Settings']['Debug'] == 'on':print(itemHex)
            break
        else:
            print("Invaild Item")
            itemName = input("Select an item (case sensitive)")
    if config['Settings']['Language'] == 'Japanese':print("の数は " + itemName + " (1-99)")
    itemAmountSel = input("How many of " + itemName + " (1-99)")
    if itemAmountSel.isdigit() == False:itemAmountSel = 0
    while int(itemAmountSel) not in range(1, 100):
        print("Invalid Value")
        itemAmountSel = input("How many of " + itemName + " (1-99)")
        if itemAmountSel.isdigit() == False:itemAmountSel = 0
    if itemHex[2:4] == '00':
        itemAmountHex = int(itemAmountSel)*2
        itemAmountHex = '{0:02x}'.format(int(itemAmountHex))
    else:
        itemAmountHex = (int(itemAmountSel)*2)+1
        itemAmountHex = '{0:02x}'.format(int(itemAmountHex))
    itemHex = itemHex[0:2]
    itemHex = itemHex + itemAmountHex
    i = 8224+(4*(int(itemSlot)-1))
    for x in range(4):
        saveInfoString = saveInfoString[:i] + itemHex[x] + saveInfoString[i + 1:]
        i = i + 1
    return saveInfoString
        
def equipMenu(saveInfoString):
    print("\n")
    while True:
        i = 64
        k = 124
        for x in range(5):
            print(str(int(x+1))+"."+charDict.get(saveInfoString[k:k+2],"Corrupt"))
            for x in range(7):
                print(equipDict.get(saveInfoString[i:i+4],"Corrupt"))
                i = i + 4
            print()
            i = i + 228
            k = k + 256
        if config['Settings']['Language'] == 'Japanese':print("装備を編集するキャラクターを選ぶ (1-5) (戻るには終了をタイプする）")
        charSel = input("Choose a character to edit equipment (1-5) (Type exit to go back)")
        if charSel.casefold() == "exit":
            exitMenu = True
            if config['Settings']['Debug'] == 'on':print("exited")
            return saveInfoString
        if charSel.isdigit() == False:charSel = 0
        while int(charSel) not in range(1, 6):
            print("Invalid Value")
            charSel = input("Choose a character to edit equipment (1-5) (Type exit to go back)") 
            if charSel.casefold() == "exit":
                exitMenu = True
                if config['Settings']['Debug'] == 'on':print("exited")
                return saveInfoString
            if charSel.isdigit() == False:charSel = 0
        k = 124 + ((int(charSel)-1)*256)
        saveInfoString = equipEdits(saveInfoString,charSel,charDict.get(saveInfoString[k:k+2],"Corrupt"))

def equipEdits(saveInfoString,charSel,NAME):
    #Start value for Equipment name
    while True:
        i = 64  + ((int(charSel)-1)*256)
        if config['Settings']['Language'] == 'Japanese':
            print(NAME+"'s 装備")
        else:
            print(NAME+"'s Equipment")
        for x in range(7):
            print(str(int(x+1))+"."+equipDict.get(saveInfoString[i:i+4],"Corrupt"))
            i = i + 4
        equipSel = input("Choose equipment to edit (1-7) (Type exit to go back)")
        if equipSel.casefold() == "exit":
            if config['Settings']['Debug'] == 'on':print("exited")
            return saveInfoString
        if equipSel.isdigit() == False:equipSel = 0
        while int(equipSel) not in range(1, 8):
            print("Invalid Value")
            equipSel = input("Choose equipment to edit (1-7) (Type exit to go back)") 
            if equipSel.casefold() == "exit":
                if config['Settings']['Debug'] == 'on':print("exited")
                return saveInfoString
            if equipSel.isdigit() == False:equipSel = 0
        equipSel = int(equipSel)
        equipCHG = input("Select a equipment to change (case sensitive)")
        invaild = True
        i = 64 + ((int(charSel)-1)*256) + (4*(equipSel-1))
        while invaild:
            if equipCHG in equipDictrev.keys():
                invalid = False
                if config['Settings']['Debug'] == 'on':print("pass")
                equipCHGHex = equipDictrev[equipCHG]
                if config['Settings']['Debug'] == 'on':print(equipCHGHex)
                for x in range(4):
                    saveInfoString = saveInfoString[:i] + equipCHGHex[x] + saveInfoString[i + 1:]
                    i = i + 1
                break
            else:
                print("Invaild equipment")
                equipCHG = input("Select a equipment to change (case sensitive)")
                if equipCHG.casefold() == "exit":
                    break
                       
def personaMenu(saveInfoString):
    global exitMenu
    #Start value for Persona name
    i = 1328
    if config['Naming Scheme']['Persona'] == 'Japanese':
        print("   Persona\t\t   SP\tLevel\tStr\tVi\tTech\tAg\tLu\t格\tOMP\tDMP\t人物")
    else:
        print("   Persona\t   SP\tLevel\tStr\tVi\tTech\tAg\tLu\tRank\tOMP\tDMP\tPlayer")
    #prints out all Persona Info and Stats
    for x in range(31):
        #Persona Name
        if int(x) >= 9:
            print(str(int(x+1)),personaID.get(saveInfoString[i:i+2],"Corrupt"),end="")
        else:
            print(int(x+1),"",personaID.get(saveInfoString[i:i+2],"Corrupt"),end="")
        if config['Naming Scheme']['Persona'] != 'Japanese':
            extraSpace = 16-len(personaID.get(saveInfoString[i:i+2],"Corrupt"))
        else:
            extraSpace = abs(24-(len(personaID.get(saveInfoString[i:i+2],"Corrupt"))*2))
        for x in range(extraSpace):
            print(" ", end="")
        #SP Cost
        i = i+88
        temp = saveInfoString[i:i+2]
        print(int(temp, 16), "\t", end="")
        #Level
        i = i+2
        temp = saveInfoString[i:i+2]
        print(int(temp, 16), "\t", end="")
        i = i+4
        #Stats
        for x in range(5):
            temp2 = saveInfoString[i:i+2]
            print(int(temp2, 16), "\t", end="")
            i = i+2
        #Rank
        i = i+2
        temp = saveInfoString[i:i+2]
        print(int(temp, 16), "\t", end="")
        #Character Name
        i = i+38
        temp = saveInfoString[i:i+2]
        charTemp = charDict.get(temp,"Corrupt")
        #OMP
        i = i-160
        temp = saveInfoString[i:i+4]
        temp = "".join(reversed([temp[i:i+2] for i in range(0, len(temp), 2)]))
        print(int(temp, 16), "\t",end="")
        #DMP
        i = i+4
        temp = saveInfoString[i:i+4]
        temp = "".join(reversed([temp[i:i+2] for i in range(0, len(temp), 2)]))
        print(int(temp, 16), "\t", end="")
        print(charTemp, "\t",end="")
        i = i+212
        print("\n")
    if config['Settings']['Language'] == 'Japanese':
        print("32. ペルソナストック\n")
        print("33. 大要\n")
        print("ペルソナを選択する （戻るには exit と入力する）")
    else:
        print("32. Equipped Personas\n")
        print("33. Compendium\n")
    personaSel = input("Select a Persona (Type exit to go back)")
    if personaSel == "32":
        saveInfoString = equipPersonaEdit(saveInfoString)
    if personaSel == "33":
        saveInfoString = compendiumEdit(saveInfoString)
    if personaSel.casefold() == "exit":
        exitMenu = True
        if config['Settings']['Debug'] == 'on':print("exited")
        return saveInfoString
    if personaSel.isdigit() == False:personaSel = -1
    while int(personaSel) not in range(1, 34):
        print("Invalid Value")
        personaSel = input("Select a Persona (Type exit to go back) (0-32)") 
        if personaSel.casefold() == "exit":
            exitMenu = True
            if config['Settings']['Debug'] == 'on':print("exited")
            return saveInfoString
        if personaSel.isdigit() == False:personaSel = -1
    if int(personaSel) in range(1, 32):
        saveInfoString = personaEdit(saveInfoString,personaSel)
    return saveInfoString

def equipPersonaEdit(saveInfoString):
    while True:
        global playerList
        empty = "ff"
        hexEdit = True
        i = 7696
        compendium = []
        personaReplaced = False
        for x in range(16):
            compendium.append(saveInfoString[i:i+2])
            i = i + 2
        if config['Settings']['Debug'] == 'on':print("compendium: ", compendium)
        #charSel = 0
        #Start value of MC Persona Slots
        i = 240
        for x in range(len(playerList)):
            print(playerList[x], "'s Personas")
            for y in range(3):
                equipValue = int(saveInfoString[i:i+2], 16)
                #print("char value ", saveInfoString[i:i+2])
                #Start value of Persona ID
                if equipValue != 255:
                    j = 1328 + (equipValue*200)
                    print(int(y+1),personaID.get(saveInfoString[j:j+2],"Corrupt"))
                else:
                    print(int(y+1),"EMPTY")
                i = i+2
            i = i + 250
            print("")
        print("Note: Any Persona replaced will automatically be put into the compendium")
        while True:
            charSel = input("Select a character (case sensitive) (enter exit to go back)")
            if charSel.isdigit() == True and int(charSel) in range (1,len(playerList)+1):
                charIndex = int(charSel)-1
                break
            elif charSel.isdigit() == False:
                break
            print("Invalid Character")
        if charSel.casefold() == "exit":
            return saveInfoString
        while charSel not in playerList and charSel.isdigit() == False:
            print("Invalid Character")
            charSel = input("Select a character (case sensitive)")
            if charSel.isdigit() == True and int(charSel) in range (1,len(playerList)):
                charIndex = int(charSel)-1
                break
            if charSel.casefold() == "exit":
                return saveInfoString
        if charSel.isdigit() == False:
            charIndex = playerList.index(charSel)
        if config['Settings']['Debug'] == 'on':print("Char Index ", str(charIndex))
        slotSel = input("Select a slot to change from " + playerList[charIndex] + "'s Persona list")
        if slotSel.casefold() == "exit":
            return saveInfoString
        if slotSel.isdigit() == False:slotSel = 0
        while int(slotSel) not in range(1,4):
            print("Invalid Value")
            slotSel = input("Select a slot to change from " + playerList[charIndex] + "'s Persona list")
            if slotSel.casefold() == "exit":
                return saveInfoString
            if slotSel.isdigit() == False:slotSel = 0
        slotSel = int(slotSel)
        #Getting Orignal Persona Slot
        i = 240 + ((slotSel-1)*2) + ((charIndex)*256)
        origPersonaSlot = int(saveInfoString[i:i+2],16)
        if config['Settings']['Debug'] == 'on':print("origPersonaSlot: ", str(origPersonaSlot))
        #Editing Persona Slot value
        personaSel = input("Select a Persona to change from the compendium above (1-31)")
        if personaSel.casefold() == "exit":
            return saveInfoString
        if personaSel.isdigit() == False:personaSel = -1
        while int(personaSel) not in range(1,32):
            print("Invalid Value")
            personaSel = input("Select a Persona to change from the compendium above (1-31)")
            if personaSel.casefold() == "exit":
                return saveInfoString
            if personaSel.isdigit() == False:personaSel = -1
        i = 240 + ((charIndex)*256) + ((slotSel-1)*2)
        personaSel = int(personaSel) - 1
        j = 1472 + ((personaSel)*200)
        h = 1328 + ((personaSel)*200)
        if config['Settings']['Debug'] == 'on':print("ORIG PERSONA OWNER ID " + saveInfoString[j:j+2])
        personaSel = '{0:02x}'.format(int(personaSel))
        #Checks to see if hex can be edited
        if personaSel == '{0:02x}'.format(int(origPersonaSlot)):
            print("ERROR: SAME PERSONA")
            hexEdit = False
        elif saveInfoString[j:j+2] != "ff":
            if personaSel != "-1":
                print("ERROR: PERSONA BELONGS TO SOMEONE")
            hexEdit = False
        elif saveInfoString[h:h+2] == "00":
            print("ERROR: EMPTY PERSONA ID")
            hexEdit = False
        if hexEdit == True:
            if config['Settings']['Debug'] == 'on':print("Persona Slot Hex Position ", "240 + ",  ((charIndex)*256), " + ", + ((slotSel-1)*2))
            if config['Settings']['Debug'] == 'on':print("Persona Slot Hex Position ", i)
            if config['Settings']['Debug'] == 'on':print("Persona Slot Value ", personaSel)
            for x in range(2):
                saveInfoString = saveInfoString[:i] + personaSel[x] + saveInfoString[i + 1:]
                i = i + 1
            #Start of Persona Char Value (FF means in compendium)
            j = 1472 + ((origPersonaSlot)*200)
            if config['Settings']['Debug'] == 'on':print("Original Slot Hex Position ", j)
            for x in range(2):
                saveInfoString = saveInfoString[:j] + empty[x] + saveInfoString[j + 1:]
                j = j + 1
            personaSel = int(personaSel,16)
            if config['Settings']['Debug'] == 'on':print("personaSel ", personaSel)
            j = 1472 + ((personaSel)*200)
            h = 1328 + ((personaSel)*200)
            if config['Settings']['Debug'] == 'on':print("New Slot Hex Position ", j)
            if charSel.isdigit() == True:
                charID = charDictrev.get(playerList[charIndex],'{0:02x}'.format(int(charSel)))
            else:
                charID = charDictrev.get(playerList[charIndex],0)
            for x in range(2):
                saveInfoString = saveInfoString[:j] + charID[x] + saveInfoString[j + 1:]
                j = j + 1
            #Puts Persona in compendium list
            i = 7696
            #Checks to see if the persona you are replacing is in the compendium
            personaSel = '{0:02x}'.format(int(personaSel))
            origPersonaSlot = '{0:02x}'.format(int(origPersonaSlot))
            if config['Settings']['Debug'] == 'on':print("DEBUG " + personaSel)
            dupPer = False
            #Checks if persona is already present in compendium
            for x in range(16):
                if saveInfoString[i:i+2] == origPersonaSlot:
                    dupPer = True
                    break
                i = i + 2
            i = 7696
            #Takes persona out of compendium and replaces with the persona that is being replaced
            for x in range(16):
                if saveInfoString[i:i+2] == personaSel:
                    write = origPersonaSlot
                    if dupPer == True: #if persona already in compendium, then an empty spot will be created in its place
                        write = empty
                        print("Persona already present in compendium")
                    j = i
                    for x in range(2):
                        saveInfoString = saveInfoString[:j] + write[x] + saveInfoString[j + 1:]
                        j = j + 1
                    personaReplaced = True
                    if config['Settings']['Debug'] == 'on':print("Replaced")
                    break
                i = i + 2
            #Adds persona in compendium if not present
            if personaReplaced == False:
                i = 7696
                print("Original Persona not in compendium, adding into new slot")
                for x in range(16):
                    if saveInfoString[i:i+2] == empty:
                        j = i
                        for x in range(2):
                            saveInfoString = saveInfoString[:j] + origPersonaSlot[x] + saveInfoString[j + 1:]
                            j = j + 1
                        break
                    i = i + 2
            if config['Settings']['Debug'] == 'on':print(compendium)
        elif personaSel == "-1":
            k = 240 + ((charIndex)*256) + ((slotSel-1)*2)
            i = 7696
            origPersonaSlot = '{0:02x}'.format(int(origPersonaSlot))
            if config['Settings']['Debug'] == 'on':print("Gonna add that empty for you bud")
            print("Clearing Slot")
            for x in range(16):
                if saveInfoString[i:i+2] == empty:
                    j = i
                    for x in range(2):
                        saveInfoString = saveInfoString[:j] + origPersonaSlot[x] + saveInfoString[j + 1:]
                        j = j + 1
                    break
                i = i + 2
            for x in range(2):
                saveInfoString = saveInfoString[:k] + empty[x] + saveInfoString[k + 1:]
                k = k + 1
            j = 1472 + ((int(origPersonaSlot,16))*200)
            for x in range(2):
                saveInfoString = saveInfoString[:j] + empty[x] + saveInfoString[j + 1:]
                j = j + 1
        
def compendiumEdit(saveInfoString):
    global playerList
    while True:
        empty = "ff"
        i = 7696
        compendium = []
        compendiumSlot = []
        for x in range(16):
            compendiumSlot.append(int(saveInfoString[i:i+2],16))
            j = 1328 + ((compendiumSlot[x])*200)
            if (compendiumSlot[x]) < 32:
                if x < 9:
                    print(str(x+1) + ".  " + personaID.get(saveInfoString[j:j+2],"Corrupt"))
                else:
                    print(str(x+1) + ". " + personaID.get(saveInfoString[j:j+2],"Corrupt"))
                compendium.append(personaID.get(saveInfoString[j:j+2],"Corrupt"))
            else:
                if x < 9:
                    print(str(x+1) + ".  " + "EMPTY")
                else:
                    print(str(x+1) + ". " + "EMPTY")
                compendium.append("EMPTY")
            i = i + 2
        perSel = input("Select a entry to edit (1-16)")
        if perSel.casefold() == "exit":
            return saveInfoString
        if perSel.isdigit() == False:perSel = 0
        while int(perSel) not in range(1,17):
            print("Invalid selection")
            perSel = input("Select a entry to edit (1-16)")
            if perSel.casefold() == "exit":
                return saveInfoString
            if perSel.isdigit() == False:perSel = 0
        replaceSel = input("Select a Persona to change from the compendium above (1-31)")
        if replaceSel.casefold() == "exit":
            return saveInfoString
        if replaceSel.isdigit() == False:replaceSel = 0
        while int(replaceSel) not in range(1,32):
            print("Invalid Value")
            replaceSel = input("Select a Persona to change from the compendium above (1-31)")
            if replaceSel.casefold() == "exit":
                return saveInfoString
            if replaceSel.isdigit() == False:replaceSel = 0
        j = 1328 + ((int(replaceSel)-1)*200)
        if personaID[saveInfoString[j:j+2]] in compendium:
            print("\nPersona is already in the compendium\n")
        else:
            j = 7696 + ((int(perSel)-1)*2)
            replaceSel = '{0:02x}'.format(int(replaceSel)-1)
            for x in range(2):
                saveInfoString = saveInfoString[:j] + replaceSel[x] + saveInfoString[j + 1:]
                j = j + 1
            j = 1472 + ((int(replaceSel,16))*200)
            for x in range(2):
                saveInfoString = saveInfoString[:j] + empty[x] + saveInfoString[j + 1:]
                j = j + 1
            i = 240
            getBreak = False
            for x in range(len(playerList)):
                for y in range(3):
                    if saveInfoString[i:i+2] == replaceSel:
                        print("Taken Persona out of " + playerList[x] + "'s list")
                        for x in range(2):
                            saveInfoString = saveInfoString[:i] + empty[x] + saveInfoString[i + 1:]
                            i = i + 1
                        getBreak = True
                        break
                    i = i+2
                i = i + 250
                if getBreak == True:
                    break
        print("\n")
       
def personaEdit(saveInfoString,personaSel):
    while True:
        i = 1328 + ((int(personaSel)-1)*200)
        pStats = personaStatGet(saveInfoString,int(personaSel))
        pStatStr = ','.join(pStats[3:8])
        print("\n1. Persona             (" + pStats[0] + ")\n2. SP Cost             (" + pStats[1] + ")\n3. Level               (" + pStats[2] + ")\n4. Stats               (" + pStatStr + ")\n5. Rank                (" + pStats[8] + ")\n6. OMP/DMP             (" + pStats[9] + "/" + pStats[10] + ")\n7. Character Ownership (" + pStats[11] + ")\n8. Moves")
        #Persona Name
        prsCHGHex = saveInfoString[i:i+2]
        menuSel = input("Select a value to edit (enter exit to go back)")
        if menuSel.casefold() == "exit":
            return saveInfoString
        if menuSel.isdigit() == False:menuSel = 0
        while int(menuSel) not in range(1,9):
            print("Invalid option")
            menuSel = input("Select a value to edit (enter exit to go back)")
            if menuSel.casefold() == "exit":
                return saveInfoString
            if menuSel.isdigit() == False:menuSel = 0
        menuSel = int(menuSel)
        if menuSel == 1:
            prsCHG = input("Enter Persona Name (Case sensitive)")
            prsCHGHex = ""
            while True:
                if prsCHG in personaIDrev.keys():
                    if config['Settings']['Debug'] == 'on':print("pass")
                    prsCHGHex = personaIDrev.get(prsCHG,"ff")
                    if config['Settings']['Debug'] == 'on':print(prsCHGHex)
                    for x in range(2):
                        saveInfoString = saveInfoString[:i] + prsCHGHex[x] + saveInfoString[i + 1:]
                        i = i + 1
                    break
                else:
                    print("Invaild Persona")
                    prsCHG = input("Enter Persona Name (Case sensitive)")
        elif menuSel == 2:
            #SP Cost
            i = i+88
            spCost = input(personaID.get(prsCHGHex,"Corrupt") + " SP Cost? (0-99)")
            if spCost.isdigit() == False:spCost = -1
            while int(spCost) not in range(0, 100):
                print("Invalid Value")
                spCost = input(personaID.get(prsCHGHex,"Corrupt") + " SP Cost? (0-99)")
                if spCost.isdigit() == False:spCost = -1
            spCost = '{0:02x}'.format(int(spCost))
            for x in range(2):
                saveInfoString = saveInfoString[:i] + spCost[x] + saveInfoString[i + 1:]
                i = i + 1
        elif menuSel == 3:
            #Level
            i = i+90
            perLevel = input(personaID.get(prsCHGHex,"Corrupt") + " Level? (0-99)")
            if perLevel.isdigit() == False:perLevel = -1
            while int(perLevel) not in range(0, 100):
                print("Invalid Value")
                perLevel = input(personaID.get(prsCHGHex,"Corrupt") + " Level? (0-99)")
                if perLevel.isdigit() == False:perLevel = -1
            perLevel = '{0:02x}'.format(int(perLevel))
            for x in range(2):
                saveInfoString = saveInfoString[:i] + perLevel[x] + saveInfoString[i + 1:]
                i = i + 1
        elif menuSel == 4:
            #Stats
            i = i+94
            statString = ["Strength","Vitality","Tech","Agility","Luck"]
            for x in range(5):
                perStat = input(personaID.get(prsCHGHex,"Corrupt") + "'s " + statString[int(x)] + "? (0-99)")
                if perStat.isdigit() == False:perStat = -1
                while int(perStat) not in range(0, 100):
                    print("Invalid Value")
                    perStat = input(personaID.get(prsCHGHex,"Corrupt") + "'s " + statString[int(x)] + "? (0-99)")
                    if perStat.isdigit() == False:perStat = -1
                perStat = '{0:02x}'.format(int(perStat))
                for x in range(2):
                    saveInfoString = saveInfoString[:i] + perStat[x] + saveInfoString[i + 1:]
                    i = i + 1
        elif menuSel == 5:
            #Rank
            i = i+106
            perRank = input(personaID.get(prsCHGHex,"Corrupt") + " Rank? (0-8)")
            if perRank.isdigit() == False:perRank = -1
            while int(perRank) not in range(0, 9):
                print("Invalid Value")
                perRank = input(personaID.get(prsCHGHex,"Corrupt") + " Rank? (0-8)")
                if perRank.isdigit() == False:perRank = -1
            perRank = '{0:02x}'.format(int(perRank))
            for x in range(2):
                saveInfoString = saveInfoString[:i] + perRank[x] + saveInfoString[i + 1:]
                i = i + 1
        elif menuSel == 7:
            #Character Name
            i = i+144
            charSel = input(personaID.get(prsCHGHex,"Corrupt") + " Owner? (0-9)")
            if charSel.isdigit() == False:charSel = -1
            while int(charSel) not in range(0, 10):
                print("Invalid Value")
                charSel = input(personaID.get(prsCHGHex,"Corrupt") + " Owner? (0-9)")
                if charSel.isdigit() == False:charSel = -1
            charSel = '{0:02x}'.format(int(charSel))
            for x in range(2):
                saveInfoString = saveInfoString[:i] + charSel[x] + saveInfoString[i + 1:]
                i = i + 1
        elif menuSel == 6:
            #OMP
            i = i-16
            perOMP = input(personaID.get(prsCHGHex,"Corrupt") + " OMP? (0-999)")
            if perOMP.isdigit() == False:perOMP = -1
            while int(perOMP) not in range(0, 1000):
                print("Invalid Value")
                perOMP = input(personaID.get(prsCHGHex,"Corrupt") + " OMP? (0-999)")
                if perOMP.isdigit() == False:perOMP = -1
            perOMP = '{0:04x}'.format(int(perOMP))
            perOMP = "".join(reversed([perOMP[i:i+2] for i in range(0, len(perOMP), 2)]))
            for x in range(4):
                saveInfoString = saveInfoString[:i] + perOMP[x] + saveInfoString[i + 1:]
                i = i + 1
            #DMP
            perDMP = input(personaID.get(prsCHGHex,"Corrupt") + " DMP? (0-999)")
            if perDMP.isdigit() == False:perDMP = -1
            while int(perDMP) not in range(0, 1000):
                print("Invalid Value")
                perDMP = input(personaID.get(prsCHGHex,"Corrupt") + " DMP? (0-999)")
                if perDMP.isdigit() == False:perDMP = -1
            perDMP = '{0:04x}'.format(int(perDMP))
            perDMP = "".join(reversed([perDMP[i:i+2] for i in range(0, len(perDMP), 2)]))
            for x in range(4):
                saveInfoString = saveInfoString[:i] + perDMP[x] + saveInfoString[i + 1:]
                i = i + 1
        elif menuSel == 8:
            saveInfoString = personaMovesEdit(saveInfoString,personaSel,personaID.get(prsCHGHex,"Corrupt"))
    
def personaMovesEdit(saveInfoString,personaSel,NAME):
    cont = True
    while cont:
        i = 1436 + ((int(personaSel)-1)*200)
        print("Selected Persona: " + NAME)
        print("Learned Moves\n")
        j = 1
        for x in range(7):
            temp = saveInfoString[i:i+2]
            temp2 = movesID.get(temp,"Corrupt")
            print(j , ". " , temp2 , "\n")
            i = i+2
            j = j+1
        print("Inherited Moves to be learnt\n")
        for x in range(7):
            temp = saveInfoString[i:i+2]
            temp2 = movesID.get(temp,"Corrupt")
            print(int(x+8) , ". " , temp2 , "\n")
            i = i+2
        moveInput = input("Select a move to change (1-14) (type exit to go back)")
        if moveInput.casefold() == "exit":
            break
        if moveInput.isdigit() == False:moveInput = 0
        while int(moveInput) not in range(1, 15):
            print("Invalid Value")
            moveInput = input("Select a move to change (1-14)")
            if moveInput.casefold() == "exit":
                return saveInfoString
            if moveInput.isdigit() == False:moveInput = 0
        i = 1436 + ((int(personaSel)-1)*200) + ((int(moveInput)-1)*2)
        moveCHG = input("Select a move to change (case sensitive)")
        invaild = True
        while invaild:
            if moveCHG in movesIDrev.keys():
                invalid = False
                if config['Settings']['Debug'] == 'on':print("pass")
                moveCHGHex = movesIDrev.get(moveCHG,"00")
                if config['Settings']['Debug'] == 'on':print(moveCHGHex)
                for x in range(2):
                    saveInfoString = saveInfoString[:i] + moveCHGHex[x] + saveInfoString[i + 1:]
                    i = i + 1
                break
            else:
                print("Invaild move")
                moveCHG = input("Select a move to change (case sensitive)")
    return saveInfoString

def extraEdits(saveInfoString):
    global timeString
    global locString
    #Non player stat edits
    while True:
        #Gets Money, Coins, Time, and Difficulty Values to show
        v = 8208
        moneyStr = saveInfoString[v:v+8]
        moneyStr = "".join(reversed([moneyStr[i:i+2] for i in range(0, len(moneyStr), 2)]))
        moneyStr = str(int(moneyStr,16))
        v = 8216
        coinStr = saveInfoString[v:v+8]
        coinStr = "".join(reversed([coinStr[i:i+2] for i in range(0, len(coinStr), 2)]))
        coinStr = str(int(coinStr,16))
        v = 35120
        difHex = saveInfoString[v:v+2]
        if difHex == "00":
            difStr = "Normal"
        elif difHex == "01":
            difStr = "Beginner"
        elif difHex == "02":
            difStr = "Expert"
        else:
            difStr = "Unknown"
        #Menu
        editSel = input("\nSelect a value to edit (enter exit to go back)\n1.Money      (" + moneyStr + ")\n2.Coins      (" + coinStr + ")\n3.Location   (" + locFind(saveInfoString) + ")\n4.Time       (" + timeString + ")\n5.Story Flags\n6.Difficulty (" + difStr + ")\n7.Tools\n")
        if editSel == '1':
            #Money
            money = input("Money?")
            if money.isdigit() == False:money = -1
            while int(money) not in range(0, 1000000000):
                print("Invalid Value")
                money = input("Money?")
                if money.isdigit() == False:money = -1
            moneyHex = '{0:08x}'.format(int(money))
            moneyHex = "".join(reversed([moneyHex[i:i+2] for i in range(0, len(moneyHex), 2)]))
            i = 8208
            for x in range(8):
                saveInfoString = saveInfoString[:i] + moneyHex[x] + saveInfoString[i + 1:]
                i = i + 1
        elif editSel == '2':
            #Coins
            coin = input("Coins?")
            if coin.isdigit() == False:coin = -1
            while int(coin) not in range(0, 1000000000):
                print("Invalid Value")
                coin = input("Coins?")
                if coin.isdigit() == False:coin = -1
            coinHex = '{0:08x}'.format(int(coin))
            coinHex = "".join(reversed([coinHex[i:i+2] for i in range(0, len(coinHex), 2)]))
            i = 8216
            for x in range(8):
                saveInfoString = saveInfoString[:i] + coinHex[x] + saveInfoString[i + 1:]
                i = i + 1
        elif editSel == '3':
            #Location
            while True:
                print("\nLocation type:")
                locationType = int(saveInfoString[10464:10466],16)
                if locationType == 0:
                    print("3D Overworld (SUSPEND)")
                elif locationType == 2:
                    print("2D Map (SUSPEND)")
                elif locationType == 3:
                    print("2D Overworld (Default)")
                else:
                    print("Unknown")
                print("\nSelect a way to edit")
                print("1.Manual Simple Hex entry\n2.Manual Advanced Hex entry\n3.Points of Interest\n4.Change Location Type")
                locEditSel = input()
                if locEditSel.casefold() == "exit":
                    break
                if locEditSel.isdigit() == False:locEditSel = 0
                while int(locEditSel) not in range(1, 5):
                    print("Invalid Value")
                    locEditSel = input("Select a way to edit ")
                    if locEditSel.casefold() == "exit":
                        break
                    if locEditSel.isdigit() == False:locEditSel = 0
                if locEditSel == "1":
                    loc = input("Location (XXXX) Hex entry?")
                    while (len(loc) != 4) or isHex(loc) == False:
                        print("Invalid Value")
                        loc = input("Location (XXXX) Hex entry?")
                    loc = loc.casefold()
                    i = 10472
                    for x in range(4):
                        saveInfoString = saveInfoString[:i] + loc[x] + saveInfoString[i + 1:]
                        i = i + 1
                if locEditSel == "2":
                    #location
                    loc = input("Location (XXXX) Hex entry?")
                    while (len(loc) != 4) or isHex(loc) == False:
                        print("Invalid Value")
                        loc = input("Location (XXXX) Hex entry?")
                    loc = loc.casefold()
                    i = 10472
                    for x in range(4):
                        saveInfoString = saveInfoString[:i] + loc[x] + saveInfoString[i + 1:]
                        i = i + 1
                    #warp
                    warp = input("Warp Location (XXXX) Hex entry?")
                    while (len(warp) != 4) or isHex(warp) == False:
                        print("Invalid Value")
                        warp = input("Warp Location (XXXX) Hex entry?")
                    warp = warp.casefold()
                    i = 10600
                    for x in range(4):
                        saveInfoString = saveInfoString[:i] + warp[x] + saveInfoString[i + 1:]
                        i = i + 1
                    #floor
                    floor = input("Floor number (XXXX) Hex entry?")
                    while (len(floor) != 4) or isHex(floor) == False:
                        print("Invalid Value")
                        floor = input("Floor number (XXXX) Hex entry?")
                    floor = floor.casefold()
                    i = 10604
                    for x in range(4):
                        saveInfoString = saveInfoString[:i] + floor[x] + saveInfoString[i + 1:]
                        i = i + 1
                    i = 10480
                    for x in range(4):
                        saveInfoString = saveInfoString[:i] + floor[x] + saveInfoString[i + 1:]
                        i = i + 1
                    #X position
                    xPos = input("X position (XXXX) Hex entry?")
                    while (len(xPos) != 4) or isHex(xPos) == False:
                        print("Invalid Value")
                        xPos = input("X position (XXXX) Hex entry?")
                    xPos = xPos.casefold()
                    i = 10608
                    for x in range(4):
                        saveInfoString = saveInfoString[:i] + xPos[x] + saveInfoString[i + 1:]
                        i = i + 1
                    i = 10488
                    for x in range(4):
                        saveInfoString = saveInfoString[:i] + xPos[x] + saveInfoString[i + 1:]
                        i = i + 1
                    #Y position
                    yPos = input("Y position (XXXX) Hex entry?")
                    while (len(yPos) != 4) or isHex(yPos) == False:
                        print("Invalid Value")
                        yPos = input("Y position (XXXX) Hex entry?")
                    yPos = yPos.casefold()
                    i = 10612
                    for x in range(4):
                        saveInfoString = saveInfoString[:i] + yPos[x] + saveInfoString[i + 1:]
                        i = i + 1
                    i = 10496
                    for x in range(4):
                        saveInfoString = saveInfoString[:i] + yPos[x] + saveInfoString[i + 1:]
                        i = i + 1
                    #direction
                    direction = input("Direction [NSEW] (XXXX) Hex entry?")
                    while (len(direction) != 4) or isHex(direction) == False:
                        print("Invalid Value")
                        direction = input("Direction [NSEW] (XXXX) Hex entry?")
                    direction = direction.casefold()
                    i = 10616
                    for x in range(4):
                        saveInfoString = saveInfoString[:i] + direction[x] + saveInfoString[i + 1:]
                        i = i + 1
                    i = 10504
                    for x in range(4):
                        saveInfoString = saveInfoString[:i] + direction[x] + saveInfoString[i + 1:]
                        i = i + 1
                    #location bug fix
                    i = 10456
                    locationBugFix = "0000"
                    for x in range(4):
                        saveInfoString = saveInfoString[:i] + locationBugFix[x] + saveInfoString[i + 1:]
                        i = i + 1
                if locEditSel == "3" and locationType == 2:
                    print("\nSelect a location\n1.Tranquil Mikage-cho\n2.Apocalypse Mikage-cho\n3.Ideal Mikage-cho\n4.Change ward\n5.Reset Player Position")
                    locWrite = 4
                    locSel = input(":")
                    if locSel.casefold() == "exit":
                        break
                    if locSel.isdigit() == False:locSel = 0
                    while int(locSel) not in range(1, 6):
                        print("Invalid Value")
                        locSel = input("Select a location: ")
                        if locSel.casefold() == "exit":
                            break
                        if locSel.isdigit() == False:locSel = 0
                    if locSel.casefold() == "exit":
                        break
                    i = 10472
                    if locSel == "1":
                        loc = "0000"
                    elif locSel == "2":
                        loc = "0100"
                    elif locSel == "3":
                        loc = "0200"    
                    elif locSel == "4":
                        loc = input("Choose ward location (0-5)")
                        if loc.isdigit() == False:loc = 0
                        while int(loc) not in range(0, 6):
                            print("Invalid Value")
                            loc = input("Select a location: ")
                            if loc.isdigit() == False:loc = 0
                        i = 10480
                        loc = '{0:04x}'.format(int(loc))
                        loc = "".join(reversed([loc[j:j+2] for j in range(0, len(loc), 2)]))
                    elif locSel == "5":
                        i = 10484
                        loc = "00"*22
                        locWrite = 44
                    for x in range(locWrite):
                        saveInfoString = saveInfoString[:i] + loc[x] + saveInfoString[i + 1:]
                        i = i + 1
                if locEditSel == "3" and locationType != 2:
                    print("\nSelect a location ")
                    print("[SEBEC Quest]")
                    for x in locationsDict.keys():
                        print(x + ". " + locationsDict[x][1])
                        if int(x) == 50:
                            print("[Snow Queen Quest]")
                        if int(x) == 57:
                            print("[Miscellaneous]")
                    locSel = input(":")
                    if locSel.casefold() == "exit":
                        break
                    if locSel.isdigit() == False:locSel = 0
                    while int(locSel) not in range(1, 60):
                        print("Invalid Value")
                        locSel = input("Select a location: ")
                        if locSel.casefold() == "exit":
                            break
                        if locSel.isdigit() == False:locSel = 0
                    if locSel.casefold() == "exit":
                        break
                    #location
                    if saveInfoString[10464:10468] == "0000":
                        loc = locationsDict[locSel][2]
                    elif saveInfoString[10464:10468] == "0300": 
                        loc = locationsDict[locSel][0]
                    else:
                        #Not really needed anymore
                        print("ERROR: LOCATION CHANGES CAN ONLY BE USED FOR 3D AND 2D OVERWORLD SAVES")
                        break
                    if config['Settings']['Debug'] == 'on':print(loc)
                    i = 10472
                    for x in range(4):
                        saveInfoString = saveInfoString[:i] + loc[x] + saveInfoString[i + 1:]
                        i = i + 1
                    #warp
                    warp = locationsDict[locSel][2]
                    i = 10600
                    for x in range(4):
                        saveInfoString = saveInfoString[:i] + warp[x] + saveInfoString[i + 1:]
                        i = i + 1
                    #floor
                    floor = locationsDict[locSel][3]
                    i = 10604
                    for x in range(4):
                        saveInfoString = saveInfoString[:i] + floor[x] + saveInfoString[i + 1:]
                        i = i + 1
                    i = 10480
                    for x in range(4):
                        saveInfoString = saveInfoString[:i] + floor[x] + saveInfoString[i + 1:]
                        i = i + 1
                    #X position
                    xPos = locationsDict[locSel][4]
                    i = 10608
                    for x in range(4):
                        saveInfoString = saveInfoString[:i] + xPos[x] + saveInfoString[i + 1:]
                        i = i + 1
                    i = 10488
                    for x in range(4):
                        saveInfoString = saveInfoString[:i] + xPos[x] + saveInfoString[i + 1:]
                        i = i + 1
                    #Y position
                    yPos = locationsDict[locSel][5]
                    i = 10612
                    for x in range(4):
                        saveInfoString = saveInfoString[:i] + yPos[x] + saveInfoString[i + 1:]
                        i = i + 1
                    i = 10496
                    for x in range(4):
                        saveInfoString = saveInfoString[:i] + yPos[x] + saveInfoString[i + 1:]
                        i = i + 1
                    #direction
                    direction = locationsDict[locSel][6]
                    i = 10616
                    for x in range(4):
                        saveInfoString = saveInfoString[:i] + direction[x] + saveInfoString[i + 1:]
                        i = i + 1
                    i = 10504
                    for x in range(4):
                        saveInfoString = saveInfoString[:i] + direction[x] + saveInfoString[i + 1:]
                        i = i + 1
                    #location bug fix
                    i = 10456
                    locationBugFix = "0000"
                    for x in range(4):
                        saveInfoString = saveInfoString[:i] + locationBugFix[x] + saveInfoString[i + 1:]
                        i = i + 1
                if locEditSel == "4":
                    print("\nSelect Location type")
                    locType = input("\n1.2D Overworld/Agastya Tree (Default)\n2.3D Overworld (SUSPEND)\n3.2D Map (SUSPEND)\n")
                    if locType.isdigit() == False:locType = 0
                    while int(locType) not in range(1, 4):
                        print("Invalid Value")
                        locType = input("\n1.2D Overworld/Agastya Tree (Default)\n2.3D Overworld (SUSPEND)\n3.2D Map\n")
                        if locType.isdigit() == False:locType = 0
                    if locType == "1":
                        locTypeHex = "0300"
                    elif locType == "2":
                        locTypeHex = "0000"
                    elif locType == "3":
                        locTypeHex = "0200"
                    i = 10464
                    for x in range(4):
                        saveInfoString = saveInfoString[:i] + locTypeHex[x] + saveInfoString[i + 1:]
                        i = i + 1
        elif editSel == '4':
            #Time
            timeHR = input("Hours played? (0-999)")
            if timeHR.isdigit() == False:timeHR = -1
            while int(timeHR) not in range(0, 1000):
                print("Invalid Value")
                timeHR = input("Hours played? (0-999)")
                if timeHR.isdigit() == False:timeHR = -1
            timeMin = input("Minutes played? (0-59)")
            if timeMin.isdigit() == False:timeMin = -1
            while int(timeMin) not in range(0, 60):
                print("Invalid Value")
                timeMin = input("Minutes played? (0-59)")
                if timeMin.isdigit() == False:timeMin = -1
            timeSec = input("Seconds played? (0-59)")
            if timeSec.isdigit() == False:timeSec = -1
            while int(timeSec) not in range(0, 60):
                print("Invalid Value")
                timeSec = input("Seconds played? (0-59)")
                if timeSec.isdigit() == False:timeSec = -1
            timeTotal = (int(timeHR)*3600)+(int(timeMin)*60)+int(timeSec)
            timeTotalHex = '{0:08x}'.format(int(timeTotal))
            timeTotalHex = "".join(reversed([timeTotalHex[i:i+2] for i in range(0, len(timeTotalHex), 2)]))
            timeString = "%d:%02d" % (int(timeHR), int(timeMin))
            #Save File Time
            i = 35384
            for x in range(8):
                saveInfoString = saveInfoString[:i] + timeTotalHex[x] + saveInfoString[i + 1:]
                i = i + 1
            #writing checksum for save tag (Unused)
            #hexCheckStr1 = saveInfoString[0:254]
            #hexByte = binascii.unhexlify(hexCheckStr1)
            #hexCheck1 = checksumCalc(hexByte)
            #i = 254
            #for x in range(2):
                #saveInfoString = saveInfoString[:i] + hexCheck1[x] + saveInfoString[i + 1:]
                #i = i + 1
        elif editSel == '5':
            saveInfoString = storyEdit(saveInfoString)
        elif editSel == '6':
            difWrite = "00"
            difsel = input("Choose a diffculty\n1.Normal\n2.Beginner\n3.Expert\n")
            if difsel.casefold() == "exit":
                break
            if difsel.isdigit() == False:difsel = 0
            while int(difsel) not in range(1, 4):
                print("Invalid Value")
                difsel = input("Choose a diffculty\n1.Normal\n2.Beginner\n3.Expert\n")
                if difsel.casefold() == "exit":
                    break
                if difsel.isdigit() == False:difsel = 0
            if difsel.casefold() == "exit":
                break
            if difsel == "1":
                difWrite = "00"
            elif difsel == "2":
                difWrite = "01"
            elif difsel == "3":
                difWrite = "02"
            i = 35120
            for x in range(2):
                saveInfoString = saveInfoString[:i] + difWrite[x] + saveInfoString[i + 1:]
                i = i + 1
        elif editSel == '7':
            toolBox(saveInfoString)
        elif editSel == 'exit':
            return saveInfoString

def storyEdit(saveInfoString):
    while True:
        print("\nStory Flag Editor\n")
        flagHex = [None,None,10684,10668,10676,10680,10680,10682,10690,10750]
        paintMom = []
        #Tranquility
        i = 10668
        print("1. Tranquility: ", end="")
        if saveInfoString[10676:10678] in ["0f", "df", "ff", "0c", "1f", "0e"]:
            print("Ideal Mikoage")
        elif int(saveInfoString[i:i+2],16) >= 48 or int(saveInfoString[i+4:i+6],16) >= 128:
            print("Apocalypse")
        elif int(saveInfoString[i:i+2],16) < 48 or int(saveInfoString[i+4:i+6],16) < 128:
            print("Tranquil")
        else:
            print("??")
        #Good/Bad Ending
        i = 10684
        print("2. Ending: ", end="")
        if saveInfoString[i:i+2] in ["a9","e9"]:
            print("Good")
        elif saveInfoString[i:i+2] in ["b0","80","f1","71"]:
            print("Bad")
        else:
            print("??")
        #MC other self totems
        #Hospital
        print("3. Saved Nurse in Hospital: ", end="")
        i = 10668
        if saveInfoString[i:i+2] in ["f0","ff"]:
            print("Yes")
        elif saveInfoString[i:i+2] in ["70","00"]:
            print("No")
        else:
            print("??")
        #Red/Blue Button
        print("4. Button pressed: ", end="")
        i = 10676
        if saveInfoString[i:i+2] in ["ff","1f","df","0e"]:#OE questionable, needs clarification
            print("Red")
        elif saveInfoString[i:i+2] in ["0c","00"]: #questionable, needs clarification
            print("Blue")
        else:
            print("??")
        #Painting
        print("5. Painting liked: ", end="")
        i = 10680
        if saveInfoString[i:i+2] in ["f5","b5"]:
            if config['Naming Scheme']['Characters'] == "Revelations":
                print("Mary's", end="")
            else:
                print("Maki's", end="")
        elif saveInfoString[i:i+2] in ["f4","b4"]: #B4 questionable, needs clarification
            if config['Naming Scheme']['Characters'] == "Revelations":
                print("Selina's", end="")
            else:
                print("Chisato's", end="")
        else:
            print("??", end="")
        print()
        #Maki's Mom
        print("6. Did you lower your weapon: ", end="")
        i = 10680
        if saveInfoString[i:i+2] in ["f5","f4"]:
            print("Yes")
        elif saveInfoString[i:i+2] in ["b5","b4"]: #B4 questionable, needs clarification
            print("No")
        else:
            print("??")
        #Kandori/Guido
        i = 10682
        if config['Naming Scheme']['Characters'] == "Revelations":
            print("7. Did you inspire Guido: ", end="")
        else:
            print("7. Did you inspire Kandori: ", end="")
        if saveInfoString[i:i+2] in ["ef","27"]:
            print("Yes")
        elif saveInfoString[i:i+2] in ["e1","21","23"]: 
            print("No")
        else:
            print("??")
        #Maki Forest
        i = 10690
        if config['Naming Scheme']['Characters'] == "Revelations":
            print("8. Did you motivate Mary: ", end="")
        else:
            print("8. Did you motivate Maki: ", end="")
        if saveInfoString[i:i+2] in ["df"]:
            print("Yes")
        elif saveInfoString[i:i+2] in ["17","57","d7"]:
            print("No")
        else:
            print("??")
        #Totems
        i = 10750
        print("9. Totems acquired: ", end="")
        if saveInfoString[i:i+4] in ["f900"]:
            print("MC and Maki")
        elif saveInfoString[i:i+4] in ["7800"]: 
            print("MC")
        elif saveInfoString[i:i+4] in ["f901"]: 
            print("All party members")
        elif saveInfoString[i:i+4] in ["f940","f941","7840","7940","7b40"]: 
            print("Already acquired")
        else:
            print("None")
        flagEdit = input("Select a flag to edit: ")
        if flagEdit.casefold() == "exit":
            return saveInfoString
        if flagEdit.isdigit() == False:flagEdit = -1
        while int(flagEdit) not in range(1, 10):
            print("Invalid Value")
            flagEdit = input("Select a flag to edit: ")
            if flagEdit.casefold() == "exit":
                return saveInfoString
            if flagEdit.isdigit() == False:flagEdit = -1
        if flagEdit == "1":
            print("Choose a flag to insert: ")
            print("1.Tranquil\n2.Apocalypse\n3.Ideal Mikoage")
            flagChoice = input()
            if flagChoice.isdigit() == False:flagChoice = 0
            while int(flagChoice) not in range(1, 4):
                print("Invalid Value")
                flagChoice = input()
                if flagChoice.isdigit() == False:flagChoice = 0
            if flagChoice == "1":
                flagInsert = "00"
                flagInsert2 = "00"
                j = 10676
                for x in range(2):
                    saveInfoString = saveInfoString[:j] + flagInsert2[x] + saveInfoString[j + 1:]
                    j = j + 1
            elif flagChoice == "2":
                flagInsert = "f0"
                flagInsert2 = "00"
                j = 10676
                for x in range(2):
                    saveInfoString = saveInfoString[:j] + flagInsert2[x] + saveInfoString[j + 1:]
                    j = j + 1
            elif flagChoice == "3":
                flagInsert = "f0"
                flagInsert2 = "df"
                j = 10676
                for x in range(2):
                    saveInfoString = saveInfoString[:j] + flagInsert2[x] + saveInfoString[j + 1:]
                    j = j + 1
            i = 10668
            for x in range(2):
                saveInfoString = saveInfoString[:i] + flagInsert[x] + saveInfoString[i + 1:]
                i = i + 1
            i = 10672
            for x in range(2):
                saveInfoString = saveInfoString[:i] + flagInsert[x] + saveInfoString[i + 1:]
                i = i + 1
        if flagEdit == "2":
            print("Choose a flag to insert: ")
            print("1.Good Ending\n2.Bad Ending\n")
            flagChoice = input()
            if flagChoice.isdigit() == False:flagChoice = 0
            while int(flagChoice) not in range(1, 3):
                print("Invalid Value")
                flagChoice = input()
                if flagChoice.isdigit() == False:flagChoice = 0
            if flagChoice == "1":
                flagInsert = "a9"
            elif flagChoice == "2":
                flagInsert = "b0"
            i = flagHex[int(flagEdit)]
            for x in range(2):
                saveInfoString = saveInfoString[:i] + flagInsert[x] + saveInfoString[i + 1:]
                i = i + 1
        elif flagEdit == "3":
            print("Choose a flag to insert: ")
            print("1.You saved the nurse\n2.You didn't save the nurse\n")
            flagChoice = input()
            if flagChoice.isdigit() == False:flagChoice = 0
            while int(flagChoice) not in range(1, 3):
                print("Invalid Value")
                flagChoice = input()
                if flagChoice.isdigit() == False:flagChoice = 0
            if flagChoice == "1":
                flagInsert = "f0"
            elif flagChoice == "2":
                flagInsert = "70"
            i = flagHex[int(flagEdit)]
            for x in range(2):
                saveInfoString = saveInfoString[:i] + flagInsert[x] + saveInfoString[i + 1:]
                i = i + 1
        elif flagEdit == "4":
            print("Choose a flag to insert: ")
            print("1.You pressed the red button\n2.You pressed the blue button\n")
            flagChoice = input()
            if flagChoice.isdigit() == False:flagChoice = 0
            while int(flagChoice) not in range(1, 3):
                print("Invalid Value")
                flagChoice = input()
                if flagChoice.isdigit() == False:flagChoice = 0
            if flagChoice == "1":
                flagInsert = "df"
            elif flagChoice == "2":
                flagInsert = "0c"
            i = flagHex[int(flagEdit)]
            for x in range(2):
                saveInfoString = saveInfoString[:i] + flagInsert[x] + saveInfoString[i + 1:]
                i = i + 1
        elif flagEdit in ["5","6"]:
            print("Choose a flag to insert: ")
            print("1.You liked Maki's painting and lowered your weapon\n2.You liked Chisato's painting and lowered your weapon\n3.You liked Maki's painting and didn't lower your weapon\n4.You liked Chisato's painting and didn't lower your weapon")
            flagChoice = input()
            if flagChoice.isdigit() == False:flagChoice = 0
            while int(flagChoice) not in range(1, 5):
                print("Invalid Value")
                flagChoice = input()
                if flagChoice.isdigit() == False:flagChoice = 0
            if flagChoice == "1":
                flagInsert = "f5"
            elif flagChoice == "2":
                flagInsert = "f4"
            elif flagChoice == "3":
                flagInsert = "b5"
            elif flagChoice == "4":
                flagInsert = "b4"
            i = flagHex[int(flagEdit)]
            for x in range(2):
                saveInfoString = saveInfoString[:i] + flagInsert[x] + saveInfoString[i + 1:]
                i = i + 1
        elif flagEdit == "7":
            print("Choose a flag to insert: ")
            print("1.You inspired Kandori\n2.You didn't inspire Kandori\n")
            flagChoice = input()
            if flagChoice.isdigit() == False:flagChoice = 0
            while int(flagChoice) not in range(1, 3):
                print("Invalid Value")
                flagChoice = input()
                if flagChoice.isdigit() == False:flagChoice = 0
            if flagChoice == "1":
                flagInsert = "ef"
            elif flagChoice == "2":
                flagInsert = "e1"
            i = flagHex[int(flagEdit)]
            for x in range(2):
                saveInfoString = saveInfoString[:i] + flagInsert[x] + saveInfoString[i + 1:]
                i = i + 1
        elif flagEdit == "8":
            print("Choose a flag to insert: ")
            print("1.You motivated Maki\n2.You didn't motivate Maki\n")
            flagChoice = input()
            if flagChoice.isdigit() == False:flagChoice = 0
            while int(flagChoice) not in range(1, 3):
                print("Invalid Value")
                flagChoice = input()
                if flagChoice.isdigit() == False:flagChoice = 0
            if flagChoice == "1":
                flagInsert = "df"
            elif flagChoice == "2":
                flagInsert = "d7"
            i = flagHex[int(flagEdit)]
            for x in range(2):
                saveInfoString = saveInfoString[:i] + flagInsert[x] + saveInfoString[i + 1:]
                i = i + 1
        elif flagEdit == "9":
            print("Choose a flag to insert: ")
            print("1.MC and Maki get the totems\n2.MC get a totem\n3.All get totems\n4.No one gets a totem\n5.MC already got totem\n6.MC and Maki already got the totems\n7.All already got the totems")
            flagChoice = input()
            if flagChoice.isdigit() == False:flagChoice = 0
            while int(flagChoice) not in range(1, 8):
                print("Invalid Value")
                flagChoice = input()
                if flagChoice.isdigit() == False:flagChoice = 0
            if flagChoice == "1":
                flagInsert = "f900"
            elif flagChoice == "2":
                flagInsert = "7800"
            elif flagChoice == "3":
                flagInsert = "f901"
            elif flagChoice == "4":
                flagInsert = "0000"
            elif flagChoice == "5":
                flagInsert = "7840"
            elif flagChoice == "6":
                flagInsert = "f940"
            elif flagChoice == "7":
                flagInsert = "f941"
            i = flagHex[int(flagEdit)]
            for x in range(4):
                saveInfoString = saveInfoString[:i] + flagInsert[x] + saveInfoString[i + 1:]
                i = i + 1    

def saveFile(saveInfoString):
    global saveType
    global ps1Header
    global ps1Footer
    #writing checksum for save data
    hexCheckStr2 = saveInfoString[256:28670]
    hexByte = binascii.unhexlify(hexCheckStr2)
    hexCheck2 = checksumCalc(hexByte)
    i = 28670
    for x in range(2):
        saveInfoString = saveInfoString[:i] + hexCheck2[x] + saveInfoString[i + 1:]
        i = i + 1
    #Asks for save slot
    #saveSlot = input("Save Slot? (0-6)")
    #if saveSlot.isdigit() == False:saveSlot = -1
    #while int(saveSlot) not in range(0, 7):
        #print("Invalid Value")
        #saveSlot = input("Save Slot? (0-6)")
        #if saveSlot.isdigit() == False:saveSlot = -1
    if saveType == "PC":
        slotString = "Perdata.S0"+saveSlot
    elif saveType == "PC SUSPEND":
        slotString = "Perdata.C0"+saveSlot
    elif saveType == "PS1US":
        slotString = "BASLUS-00339S"+saveSlot+".mcs"
    elif saveType == "PS1JP":
        slotString = "BISLPS-00500S"+saveSlot+".mcs"
    elif saveType == "PS1JPCONT":
        slotString = "BISLPS-00500C"+saveSlot+".mcs"
    elif saveType == "PS1JPRAW":
        slotString = "BISLPS-00500S"+saveSlot+"."
    elif saveType == "PS1JPCONTRAW":
        slotString = "BISLPS-00500C"+saveSlot+"."
    elif saveType == "PS1USRAW":
        slotString = "BASLUS-00339S"+saveSlot+"."
    elif saveType == "PSP":
        slotString = "PERSONA.SAV"
    else:
        slotString = "UNKNOWN"
    #Fixes header for PS1
    if saveType == "PS1JP" or saveType == "PS1US":
        saveInfoString = ps1Header + saveInfoString + ps1Footer
        saveInfoString = ps1TagEdit(saveInfoString,saveSlot)
    elif saveType == "PS1JPRAW" or saveType == "PS1USRAW":
        saveInfoString = ps1Header + saveInfoString + ps1Footer
    #Convert save to binary and prompts save slot
    if config['Settings']['Encrypt'] == 'on':
        path = ""
        pspEncrypt(saveInfoString)
    else:
        newSave = binascii.unhexlify(saveInfoString)
        if os.name == 'nt':
            path = filedialog.asksaveasfilename(initialfile = slotString,defaultextension="*.*",filetypes=[("All Files","*.*"),("PSP Single Save","*.SAV")])
        else:
            path = filedialog.asksaveasfilename(initialfile = slotString)
    if path == "":
        print("Save Canceled")
        return saveInfoString
    with open(path, 'wb') as f:  
        f.write(newSave)
    f.close()
    print("Your save has been created")
    exit(10)

#Unused
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
    
def saveEdit(saveInfoString,player,NAME):
    global saveInfo
    while True:
        nName = nickNameGet(saveInfoString)[player-1]
        charStat = charStatGet(saveInfoString,player)
        charStatStr = ','.join(charStat[1:6])
        charAddStatStr = ','.join(charStat[6:11])
        charWepStr = ','.join(charStat[11:15])
        charHPStr = '/'.join(charStat[17:19])
        charSPStr = '/'.join(charStat[19:21])
        print("\n1.  Names              (" + nName + ")\n2.  Level              (" + charStat[0] + ")\n3.  Stats              (" + charStatStr + ")\n4.  Added Stats        (" + charAddStatStr + ")\n5.  Weapon Stats       (" + charWepStr + ")\n6.  Persona Level      (" + charStat[15] + ")\n7.  Persona EXP        (" + charStat[16] + ")\n8.  HP                 (" + charHPStr + ")\n9.  SP                 (" + charSPStr + ")\n10. EXP                (" + charStat[21] + ")\n11. Status             (" + charStat[22] + ")\n12. Character Modifier (" + charStat[23] + ")")
        inputText = "Select data to edit for " + NAME + " (enter exit to go back)"
        statEdit = input(inputText)
        if statEdit.casefold() == "exit":
            return saveInfoString
        if statEdit.isdigit() == False:statEdit = 0
        while int(statEdit) not in range(1, 13):
            print("Invalid Option")
            statEdit = input(inputText)
            if statEdit.casefold() == "exit":
                return saveInfoString
            if statEdit.isdigit() == False:statEdit = 0
        statEdit = int(statEdit)
        #Player Stat edits
        if statEdit == 1:
            if (player == 1):
                name = input("Nickname? (Limit 8 Characters)")
                while len(name) > 8:
                    print("Name too long")
                    name = input("Nickname? (Limit 8 Characters)")
                name = name.strip()
                nameSplit = list(name)
                if (len(nameSplit) < 8):
                    nameSplit.append("FF")
                if (len(nameSplit) < 8):
                    for x in range(8-len(nameSplit)):
                        nameSplit.append("WS")
                nameHex = [symbolDict[symbol] for symbol in nameSplit]
                nameHexFinal = ''.join(nameHex)
                #editing save data
                i = 128
                for x in range(32):
                    saveInfoString = saveInfoString[:i] + nameHexFinal[x] + saveInfoString[i + 1:]
                    i = i + 1
                i = 10384
                for x in range(32):
                    saveInfoString = saveInfoString[:i] + nameHexFinal[x] + saveInfoString[i + 1:]
                    i = i + 1
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
                nameHex = [symbolDict[symbol] for symbol in nameSplit]
                nameHexFinal = ''.join(nameHex)
                i = 10304
                for x in range(32):
                    saveInfoString = saveInfoString[:i] + nameHexFinal[x] + saveInfoString[i + 1:]
                    i = i + 1
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
                nameHex = [symbolDict[symbol] for symbol in nameSplit]
                nameHexFinal = ''.join(nameHex)
                i = 10336
                for x in range(32):
                    saveInfoString = saveInfoString[:i] + nameHexFinal[x] + saveInfoString[i + 1:]
                    i = i + 1
            
            if player != 1:
                name = input("Nickname? (Limit 8 Characters)")
                name = name.strip()
                nameSplit = list(name)
                if (len(nameSplit) < 8):
                    nameSplit.append("FF")
                if (len(nameSplit) < 8):
                    for x in range(8-len(nameSplit)):
                        nameSplit.append("WS")
                nameHex = [symbolDict[symbol] for symbol in nameSplit]
                nameHexFinal = ''.join(nameHex)
                i = 128 + ((player-1)*256)
                for x in range(32):
                    saveInfoString = saveInfoString[:i] + nameHexFinal[x] + saveInfoString[i + 1:]
                    i = i + 1
        #Level
        if statEdit == 2:
            level = input(NAME + " level? (0-99)")
            if level.isdigit() == False:level = -1
            while int(level) not in range(0, 100):
                print("Invalid Value")
                level = input("MC level? (0-99)")
                if level.isdigit() == False:level = -1
            level = '{0:02x}'.format(int(level))
            i = 212 + ((player-1)*256)
            for x in range(2):
                saveInfoString = saveInfoString[:i] + level[x] + saveInfoString[i + 1:]
                i = i + 1
        if statEdit == 3:
            #Strength
            strength = input(NAME + " Strength? (0-99)")
            if strength.isdigit() == False:strength = -1
            while int(strength) not in range(0, 100):
                print("Invalid Value")
                strength = input(NAME + " Strength? (0-99)")
                if strength.isdigit() == False:strength = -1
            strength = '{0:02x}'.format(int(strength))
            #Vitality
            vitality = input(NAME + " Vitality? (0-99)")
            if vitality.isdigit() == False:vitality = -1
            while int(vitality) not in range(0, 100):
                print("Invalid Value")
                vitality = input(NAME + " Vitality? (0-99)")
                if vitality.isdigit() == False:vitality = -1
            vitality = '{0:02x}'.format(int(vitality))
            #Tech
            tech = input(NAME + " Tech? (0-99)")
            if tech.isdigit() == False:tech = -1
            while int(tech) not in range(0, 100):
                print("Invalid Value")
                tech = input(NAME + " Tech? (0-99)")
                if tech.isdigit() == False:tech = -1
            tech = '{0:02x}'.format(int(tech))
            #Agility
            agility = input(NAME + " Agility? (0-99)")
            if agility.isdigit() == False:agility = -1
            while int(agility) not in range(0, 100):
                print("Invalid Value")
                agility = input(NAME + " Agility? (0-99)")
                if agility.isdigit() == False:agility = -1
            agility = '{0:02x}'.format(int(agility))
            #Luck
            luck = input(NAME + " Luck? (0-99)")
            if luck.isdigit() == False:luck = -1
            while int(luck) not in range(0, 100):
                print("Invalid Value")
                luck = input(NAME + " Luck? (0-99)")
                if luck.isdigit() == False:luck = -1
            luck = '{0:02x}'.format(int(luck))
            mcStats = strength+vitality+tech+agility+luck
            i = 214 + ((player-1)*256)
            for x in range(10):
                saveInfoString = saveInfoString[:i] + mcStats[x] + saveInfoString[i + 1:]
                i = i + 1
        if statEdit == 4:
            #Added Stats
            #Strength
            strength = input(NAME + " added Strength? (0-99)")
            if strength.isdigit() == False:strength = -1
            while int(strength) not in range(0, 100):
                print("Invalid Value")
                strength = input(NAME + " added Strength? (0-99)")
                if strength.isdigit() == False:strength = -1
            strength = '{0:02x}'.format(int(strength))
            #Vitality
            vitality = input(NAME + " added Vitality? (0-99)")
            if vitality.isdigit() == False:vitality = -1
            while int(vitality) not in range(0, 100):
                print("Invalid Value")
                vitality = input(NAME + " added Vitality? (0-99)")
                if vitality.isdigit() == False:vitality = -1
            vitality = '{0:02x}'.format(int(vitality))
            #Tech
            tech = input(NAME + " added Tech? (0-99)")
            if tech.isdigit() == False:tech = -1
            while int(tech) not in range(0, 100):
                print("Invalid Value")
                tech = input(NAME + " added Tech? (0-99)")
                if tech.isdigit() == False:tech = -1
            tech = '{0:02x}'.format(int(tech))
            #Agility
            agility = input(NAME + " added Agility? (0-99)")
            if agility.isdigit() == False:agility = -1
            while int(agility) not in range(0, 100):
                print("Invalid Value")
                agility = input(NAME + " added Agility? (0-99)")
                if agility.isdigit() == False:agility = -1
            agility = '{0:02x}'.format(int(agility))
            #Luck
            luck = input(NAME + " added Luck? (0-99)")
            if luck.isdigit() == False:luck = -1
            while int(luck) not in range(0, 100):
                print("Invalid Value")
                luck = input(NAME + " added Luck? (0-99)")
                if luck.isdigit() == False:luck = -1
            luck = '{0:02x}'.format(int(luck))
            mcStats2 = strength+vitality+tech+agility+luck
            i = 224 + ((player-1)*256)
            for x in range(10):
                saveInfoString = saveInfoString[:i] + mcStats2[x] + saveInfoString[i + 1:]
                i = i + 1
        if statEdit == 5:
            #Weapons Stats
            #Weapon Attack
            wepAtk = input("Weapon Attack? (0-999)")
            if wepAtk.isdigit() == False:wepAtk = -1
            while int(wepAtk) not in range(0, 1000):
                print("Invalid Value")
                wepAtk = input("Weapon Attack? (0-999)")
                if wepAtk.isdigit() == False:wepAtk = -1
            wepAtk = '{0:04x}'.format(int(wepAtk))
            wepAtk = "".join(reversed([wepAtk[i:i+2] for i in range(0, len(wepAtk), 2)]))
            #Weapon Accuracy
            wepAcc = input("Weapon Accuracy? (0-999)")
            if wepAcc.isdigit() == False:wepAcc = -1
            while int(wepAcc) not in range(0, 1000):
                print("Invalid Value")
                wepAcc = input("Weapon Accuracy? (0-999)")
                if wepAcc.isdigit() == False:wepAcc = -1
            wepAcc = '{0:04x}'.format(int(wepAcc))
            wepAcc = "".join(reversed([wepAcc[i:i+2] for i in range(0, len(wepAcc), 2)]))
            #Gun Attack
            gunAtk = input("Gun Attack? (0-999)")
            if gunAtk.isdigit() == False:gunAtk = -1
            while int(gunAtk) not in range(0, 1000):
                print("Invalid Value")
                gunAtk = input("Gun Attack? (0-999)")
                if gunAtk.isdigit() == False:gunAtk = -1
            gunAtk = '{0:04x}'.format(int(gunAtk))
            gunAtk = "".join(reversed([gunAtk[i:i+2] for i in range(0, len(gunAtk), 2)]))
            #Gun Accuracy
            gunAcc = input("Gun Accuracy? (0-999)")
            if gunAcc.isdigit() == False:gunAcc = -1
            while int(gunAcc) not in range(0, 1000):
                print("Invalid Value")
                gunAcc = input("Gun Accuracy? (0-999)")
                if gunAcc.isdigit() == False:gunAcc = -1
            gunAcc = '{0:04x}'.format(int(gunAcc))
            gunAcc = "".join(reversed([gunAcc[i:i+2] for i in range(0, len(gunAcc), 2)]))
            weaponStats = wepAtk + wepAcc + gunAtk + gunAcc
            if config['Settings']['Debug'] == 'on':print(weaponStats)
            i = 92 + ((player-1)*256)
            for x in range(16):
                saveInfoString = saveInfoString[:i] + weaponStats[x] + saveInfoString[i + 1:]
                i = i + 1
        if statEdit == 6:
            #Persona Level
            i = 234 + ((player-1)*256)
            perLevel = input("Persona Level? (1-99)")
            if perLevel.isdigit() == False:perLevel = -1
            while int(perLevel) not in range(0, 100):
                print("Invalid Value")
                perLevel = input("Persona Level? (1-99)")
                if perLevel.isdigit() == False:perLevel = -1
            perLevel = '{0:02x}'.format(int(perLevel))
            for x in range(2):
                saveInfoString = saveInfoString[:i] + perLevel[x] + saveInfoString[i + 1:]
                i = i + 1
        if statEdit == 7:
            #Persona EXP
            perExp = input("Persona EXP?")
            if perExp.isdigit() == False:perExp = -1
            while int(perExp) not in range(0, 1000000000):
                print("Invalid Value")
                perExp = input("Persona EXP?")
                if perExp.isdigit() == False:perExp = -1
            perExpHex = '{0:08x}'.format(int(perExp))
            perExpHex = "".join(reversed([perExpHex[i:i+2] for i in range(0, len(perExpHex), 2)]))
            i = 56 + ((player-1)*256)
            for x in range(8):
                saveInfoString = saveInfoString[:i] + perExpHex[x] + saveInfoString[i + 1:]
                i = i + 1
        if statEdit == 8:
            #Health and SP
            #Max health
            healthMAX = input("Max Health? (1-999)")
            if healthMAX.isdigit() == False:healthMAX = -1
            while int(healthMAX) not in range(1, 1000):
                print("Invalid Value")
                healthMAX = input("Max Health? (1-999)")
                if healthMAX.isdigit() == False:healthMAX = -1
            healthMAX = '{0:04x}'.format(int(healthMAX))
            healthMAX = "".join(reversed([healthMAX[i:i+2] for i in range(0, len(healthMAX), 2)]))
            #Health Left
            healthLeft = input("Health Left? (0-999)")
            if healthLeft.isdigit() == False:healthLeft = -1
            while int(healthLeft) not in range(0, 1000):
                print("Invalid Value")
                healthLeft = input("Health Left? (0-999)")
                if healthLeft.isdigit() == False:healthLeft = -1
            healthLeft = '{0:04x}'.format(int(healthLeft))
            healthLeft = "".join(reversed([healthLeft[i:i+2] for i in range(0, len(healthLeft), 2)]))
            mcHealth = healthLeft + "0000" + healthMAX
            i = 0 + ((player-1)*256)
            for x in range(12):
                saveInfoString = saveInfoString[:i] + mcHealth[x] + saveInfoString[i + 1:]
                i = i + 1
        if statEdit == 9:
            #Max SP
            spMAX = input("Max SP? (1-999)")
            if spMAX.isdigit() == False:spMAX = -1
            while int(spMAX) not in range(1, 1000):
                print("Invalid Value")
                spMAX = input("Max SP? (1-999)")
                if spMAX.isdigit() == False:spMAX = -1
            spMAX = '{0:04x}'.format(int(spMAX))
            spMAX = "".join(reversed([spMAX[i:i+2] for i in range(0, len(spMAX), 2)]))
            #SP Left
            spLeft = input("SP Left? (0-999)")
            if spLeft.isdigit() == False:spLeft = -1
            while int(spLeft) not in range(0, 1000):
                print("Invalid Value")
                spLeft = input("SP Left? (0-999)")
                if spLeft.isdigit() == False:spLeft = -1
            spLeft = '{0:04x}'.format(int(spLeft))
            spLeft = "".join(reversed([spLeft[i:i+2] for i in range(0, len(spLeft), 2)]))
            mcSP = spLeft + "0000" + spMAX
            i = 16 + ((player-1)*256)
            for x in range(12):
                saveInfoString = saveInfoString[:i] + mcSP[x] + saveInfoString[i + 1:]
                i = i + 1
        #EXP
        if statEdit == 10:
            exp = input("EXP?")
            if exp.isdigit() == False:exp = -1
            while int(exp) not in range(0, 1000000000):
                print("Invalid Value")
                exp = input("EXP?")
                if exp.isdigit() == False:exp = -1
            expHex = '{0:08x}'.format(int(exp))
            expHex = "".join(reversed([expHex[i:i+2] for i in range(0, len(expHex), 2)]))
            i = 32 + ((player-1)*256)
            for x in range(8):
                saveInfoString = saveInfoString[:i] + expHex[x] + saveInfoString[i + 1:]
                i = i + 1
        if statEdit == 11:
            #Status
            i = 208 + ((player-1)*256)
            status = input("Status? (case sensitive)")
            while status not in statusIDrev.keys():
                print("Invalid option")
                status = input("Status? (case sensitive)")
            statusHex = statusIDrev[status]
            for x in range(2):
                saveInfoString = saveInfoString[:i] + statusHex[x] + saveInfoString[i + 1:]
                i = i + 1
        if statEdit == 12:
            #Character Modifier
            i = 124 + ((player-1)*256)
            players = input("Character Modifier? (1-9)")
            if players.isdigit() == False:players = -1
            while int(players) not in range(1, 10):
                print("Invalid Value")
                players = input("Character Modifier? (1-9)")
                if players.isdigit() == False:players = -1
            players = '{0:02x}'.format(int(players))
            for x in range(2):
                saveInfoString = saveInfoString[:i] + players[x] + saveInfoString[i + 1:]
                i = i + 1
    
def spellCardEdit(saveInfoString):
    #displays all spell cards
    print("\nSpell Cards")
    while True:
        i = 10272
        for x in range (12):
            if int(x) < 9:
                print(str(int(x+1))+".  "+spellCardID.get(saveInfoString[i:i+2],"Corrupt"))
            else:
                print(str(int(x+1))+". "+spellCardID.get(saveInfoString[i:i+2],"Corrupt"))
            i = i + 2
        cardSel = input("Select a card to edit or add (enter exit to go back) ")
        if cardSel.casefold() == "exit":
            return saveInfoString
        if cardSel.isdigit() == False:cardSel = 0
        while int(cardSel) not in range(1,13):
            print("Invalid Value")
            cardSel = input("Select a card to edit or add (enter exit to go back) ")
            if cardSel.casefold() == "exit":
                return saveInfoString
            if cardSel.isdigit() == False:cardSel = 0
        demonSel = input("Select a demon (case sensitive)")
        while demonSel not in spellCardIDrev.keys():
            print("Invalid Demon")
            demonSel = input("Select a demon (case sensitive)")
        demonSelHex = spellCardIDrev.get(demonSel,"00")
        #print(demonSelHex)
        j = 10272 + ((int(cardSel)-1)*2)
        for x in range(2):
            saveInfoString = saveInfoString[:j] + demonSelHex[x] + saveInfoString[j + 1:]
            j = j + 1

def toolBox(saveInfoString):
    while True:
        print("\nTools\n1. Hex Viewer\n2. Hex to Persona Data")
        tool = input("Choose a tool to use ")
        if tool.casefold() == "exit":
            return saveInfoString
        if tool.isdigit() == False:tool = 0
        while int(tool) not in range (1,3):
            print("Invalid option")
            tool = input("Choose a tool to use ")
            if tool.casefold() == "exit":
                return saveInfoString
            if tool.isdigit() == False:tool = 0
        if int(tool) == 1:
            print("\nEnter exit at any time to go back\n")
            while True:
                print("Hex Viewer")
                startOff = input("Choose start offset in hex ")
                if startOff.casefold() == "exit":
                    break
                endOff = input("Choose end offset in hex ")
                if endOff.casefold() == "exit":
                    break
                try:
                    startOff = int(startOff,16)*2
                    endOff = int(endOff,16)*2
                    s = saveInfoString[startOff:endOff].upper()
                    print(' '.join(s[i:i+2] for i in range(0, len(s), 2)))
                except Exception:
                    pass
        if int(tool) == 2:
            print("\nEnter exit at any time to go back\n")
            while True:
                print("1. Characters\n2. Personas\n3. Moves\n4. Items\n5. Spell Cards")
                cata = input("Select a catagory to convert hex values ")
                if cata.casefold() == "exit":
                    break
                if cata.isdigit() == False:cata = 0
                while int(cata) not in range (1,6):
                    print("Invalid Selection")
                    cata = input("Select a catagory to convert hex values ")
                    if cata.casefold() == "exit":
                        break
                    if cata.isdigit() == False:cata = 0
                if cata.casefold() == "exit":
                    break
                while True:
                    if int(cata) == 4:
                        hex = input("Input 2 byte hex value (XXXX)")
                    else:
                        hex = input("Input 1 byte hex value (XX)")
                    if hex.casefold() == "exit":
                        break
                    hex = hex.lower()
                    if int(cata) == 1:
                        print(hex + " = " + charDict.get(hex, "Invalid"))
                    elif int(cata) == 2:
                        print(hex + " = " + personaID.get(hex, "Invalid"))
                    elif int(cata) == 3:
                        print(hex + " = " + movesID.get(hex, "Invalid"))
                    elif int(cata) == 4:
                        print(hex + " = " + itemsID.get(hex, "Invalid"))
                    elif int(cata) == 5:
                        print(hex + " = " + spellCardID.get(hex, "Invalid"))
#Unused
def searchMemCard(hexString):
    saveHeaders = []
    saveTags = []
    saveOffsets = []
    i = 0
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

#create config
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
#opening dictonaries
try:
    #Font
    with open('data/Persona Symbol System.json') as f: 
        data = f.read()
    #Characters
    if config['Naming Scheme']['Characters'] == 'PSP':
        with open('data/Characters.json') as g: 
            data2 = g.read()
    elif config['Naming Scheme']['Characters'] == 'Revelations':
        with open('data/Characters (Revalations).json') as g: 
            data2 = g.read()
    elif config['Naming Scheme']['Characters'] == 'Japanese':
        with open('data/Characters (Japanese).json', encoding='utf-8') as g: 
            data2 = g.read()
    else:
        with open('data/Characters.json') as g: 
            data2 = g.read()
    #Personas
    if config['Naming Scheme']['Persona'] == 'PSP':
        with open('data/Persona ID.json') as h: 
            data3 = h.read()
    elif config['Naming Scheme']['Persona'] == 'Revelations':
        with open('data/Persona ID (Revalations).json') as h: 
            data3 = h.read()
    elif config['Naming Scheme']['Persona'] == 'Japanese':
        with open('data/Persona ID (Japanese).json', encoding='utf-8') as h: 
            data3 = h.read()
    else:
       with open('data/Persona ID.json') as h: 
            data3 = h.read()
    #Moves
    if config['Naming Scheme']['Moves'] == 'PSP':
        with open('data/Moves.json') as j: 
            data4 = j.read()
    elif config['Naming Scheme']['Moves'] == 'Revelations':
        with open('data/Moves (Revalations).json') as j: 
            data4 = j.read()
    elif config['Naming Scheme']['Moves'] == 'Japanese':
        with open('data/Moves (Japanese).json', encoding='utf-8') as j: 
            data4 = j.read()
    else:
        with open('data/Moves.json') as j: 
            data4 = j.read()
    #Equipment
    if config['Naming Scheme']['Equipment'] == 'PSP':
        with open('data/Equipment (PSP).json') as k: 
            data5 = k.read()
    elif config['Naming Scheme']['Equipment'] == 'Revelations':
        with open('data/Equipment.json') as k: 
            data5 = k.read()
    elif config['Naming Scheme']['Equipment'] == 'Japanese':
        with open('data/Equipment (Japanese).json', encoding='utf-8') as k: 
            data5 = k.read()
    else:
        with open('data/Equipment (PSP)') as k: 
            data5 = k.read()
    #Items
    if config['Naming Scheme']['Items'] == 'PSP':
        with open('data/Items (PSP).json') as l: 
            data6 = l.read()
    elif config['Naming Scheme']['Items'] == 'Revelations':
        with open('data/Items.json') as l: 
            data6 = l.read()
    elif config['Naming Scheme']['Items'] == 'Japanese':
        with open('data/Items (Japanese).json', encoding='utf-8') as l: 
            data6 = l.read()
    else:
        with open('data/Items (PSP).json') as l: 
            data6 = l.read()
    #Demons/Spell Cards
    if config['Naming Scheme']['Demons'] == 'PSP':
        with open('data/Spell Cards.json') as w: 
            data7 = w.read()
    elif config['Naming Scheme']['Demons'] == 'Revelations':
        with open('data/Spell Cards (Revelations).json') as w: 
            data7 = w.read()
    elif config['Naming Scheme']['Demons'] == 'Japanese':
        with open('data/Spell Cards (Japanese).json', encoding='utf-8') as w: 
            data7 = w.read()
    else:
        with open('data/Spell Cards.json') as w: 
            data7 = w.read()
    #Status
    if config['Settings']['Language'] == 'Japanese':
        with open('data/Status (Japanese).json', encoding='utf-8') as q: 
            data8 = q.read()
    else:
        with open('data/Status.json') as q: 
            data8 = q.read()
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
except Exception as e:
    print(e)
    exit(11)
#Loading dictonaries
try:
    symbolDict = json.loads(data)
    symbolDictrev = {v: k for k, v in symbolDict.items()}
    charDict = json.loads(data2)
    charDictrev = {v: k for k, v in charDict.items()}
    personaID = json.loads(data3)
    personaIDrev = {v: k for k, v in personaID.items()}
    movesID = json.loads(data4)
    movesIDrev = {v: k for k, v in movesID.items()}
    equipDict = json.loads(data5)
    equipDictrev = {v: k for k, v in equipDict.items()}
    itemsID = json.loads(data6)
    itemsIDrev = {v: k for k, v in itemsID.items()}
    spellCardID = json.loads(data7)
    spellCardIDrev = {v: k for k, v in spellCardID.items()}
    statusID = json.loads(data8)
    statusIDrev = {v: k for k, v in statusID.items()}
    locationsDict = json.loads(data9)
    warpsDict = json.loads(dataA)
except Exception as e:
    print(e)
    exit(13)
#Puts locationsDict in order for Python versions lower than 3.6
if sys.version_info[0] == 3 and sys.version_info[1] < 6:
    from collections import OrderedDict
    locationsDict = json.loads(data9, object_pairs_hook=OrderedDict)
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
if hexString[20:46] == "4241534c55532d303033333953": #PS1 US MCS
    saveType = "PS1US"
    ps1Header = hexString[0:1024]
    ps1Footer = hexString[29696:33024]
    hexString = hexString[1024:29696]
elif hexString[20:46] == "4249534c50532d303035303053": #PS1 JP MCS
    saveType = "PS1JP"
    ps1Header = hexString[0:1024]
    ps1Footer = hexString[29696:33024]
    hexString = hexString[1024:29696]
elif hexString[20:46] == "4249534c50532d303035303043": #PS1 JP Suspend MCS
    saveType = "PS1JPCONT"
    ps1Header = hexString[0:1024]
    ps1Footer = hexString[29696:33024]
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
    ps1Header = hexString[0:768]
    ps1Footer = hexString[29440:32768]
    hexString = hexString[768:29440]
elif hexString[8:68] == "8f97905f88d995b7985e81408379838b835c8369814082728366815b835e": #PS1JP RAW
    saveType = "PS1JPRAW"
    ps1Header = hexString[0:768]
    ps1Footer = hexString[29440:32768]
    hexString = hexString[768:29440]
elif hexString[8:68] == "8f97905f88d995b7985e81408379838b835c8369814082628366815b835e": #PS1JP RAW
    saveType = "PS1JPCONTRAW"
    ps1Header = hexString[0:768]
    ps1Footer = hexString[29440:32768]
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
elif os.path.getsize(f.name) in range(19000,20000):
    print("This save file could not be opened\nYour PSP save may be corrupted\n")
    exit(12)
else:
    #print("This is not a Persona save file gtfo")
    print("This is not a valid Persona save file")
    exit(3)
print("\n\nDetected Save: " + saveType)
if saveType in ["PC", "PC SUSPEND", "PS1US", "PS1JP", "PS1JPCONT", "PS1USRAW", "PS1JPRAW", "PS1JPCONTRAW"]:
    print("PC/PS1 Saves are not compatible with this editor.\nIf you'd like to edit your old PC/PS1 Saves, visit mathewstar100's GameBanana page and download the correct editor.\n")
    exit(4)
elif saveType == "PSPJPN":
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
if config['Settings']['Debug'] == 'on':print("Size: " + str(os.path.getsize(f.name)) + " bytes")
if config['Settings']['Debug'] == 'on':(print("Checksums: NOT NEEDED") if checksumCheck(hexString) == 2 else print("Checksums: NOT NEEDED"))
charMenu()