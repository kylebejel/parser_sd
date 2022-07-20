from re import I
import pandas as pd
import numpy as np
import pymongo
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import nltk

# Function to connect to database
def get_database():  
    # Creates a connection to MongoDB
    client = pymongo.MongoClient("mongodb://root:Lsfr5n3J0Jib@ec2-52-203-105-125.compute-1.amazonaws.com:27017/shoppingStories?authSource=admin&readPreference=primary&ssl=false")

    # Returns the database collection we'll be using
    return client["shoppingStories"]
 
# Allows many files can reuse the function get_database()
if __name__ == "__main__":    
    # Get the database
    db = get_database()

db = get_database()   # Creates a varibale for the database
lem = nltk.WordNetLemmatizer()  # Initializes lemmatizer
tsr = fuzz.token_set_ratio  # Scorer for string comparison

# Creates dataframes for the database collections
qualifier_df = None
people_df = pd.DataFrame(db["people"].find())
item_df = pd.DataFrame(db["ITEMS"].find())
places_df = pd.DataFrame(db["places"].find())

# Creating lists
qualifierList = ["bottle", "cask", "pair", "yard"]      # qualifier_df['word'].to_numpy()  # Creates an array of current Qualifiers
itemList = ["balsam", "rum", "breeches", "velvet"]      # item_df['name'].to_numpy()  # Creates an array of current Items
professionList = people_df['Profession'].to_numpy() # Creates an array of current profofessions
relationsList = ["mother", "father", "son", "sons", "daughter", "daughters","brother", "brothers", "sister", "sisters", "slave", 
                   "slaves", "boy", "girl", "boys", "girls", "wench", "lady", "negro", "negroes"]
keywordList = ["of", "by", "for", "the", "from", "to", "by"]
prefixList = ["Mr", "Mr.", "Mrs", "Mrs.", "Ms", "Ms.", "Miss", "Miss."]
suffixList = ["jr", "sr.", "esquire"]
possessiveList = ["your", "his", "her", "my", "their", "our"]
servicesList = ["making", "mending", "postage", "waggonage", "freight"]
placesList = None

# Initializing dictionaries
peopleObject ={"prefix": "", "firstName": "", "lastName": "", "suffix": "", "profession": "", "loacation": "", 
                    "reference": "", "relations": ""}
transactionObject ={"quantity": "", "qualifier": "", "adjectives": "", "item": "", "unitPrice": "", 
                        "totalPrice": "", "service": "", "includedItems": ""}
moneyObject = {"pounds": "", "shilling": "", "pence": ""}

# Functon for parsing entries begining with an integer
def intFirstParse(array,transDict,otherItems,peopleArray,placesArray,varientsArray,transReview):
        # Checks if the 2nd word is in the qualifier list 
        if lem.lemmatize(array[1]) in qualifierList:
            transDict["qualifier"] = lem.lemmatize(array[1])
            # Checks oif the next word is an item
            if process.extractBests(lem.lemmatize(array[2]), itemList, scorer=tsr, score_cutoff=95):
                item = process.extractBests(lem.lemmatize(array[2]), itemList, scorer=tsr, score_cutoff=95)[0][0]
                transDict["item"] = item
                i = len(item.split()) 
        # Checks if the next word is an item
        elif process.extractBests(lem.lemmatize(array[1]), itemList, scorer=tsr, score_cutoff=95):
            item =process.extractBests(lem.lemmatize(array[1]), itemList, scorer=tsr, score_cutoff=95)[0][0]
            transDict["item"] = item
            i = len(item.split()) 

# Functon for parsing entries begining with an letter
def alphaFirstParse(array,transDict,otherItems,peopleArray,placesArray,varientsArray,transReview):
    # sourcery skip: merge-duplicate-blocks, merge-nested-ifs, remove-redundant-if
    arrLength = len(array)-1    # Saves array length

    # index +1 is just a place holder
    if fuzz.ratio(lem.lemmatize(array[0]), "charge") >= 90 and arrLength >= 2:
        beginsChargeFunction(array, transDict, transReview)
    if fuzz.ratio(lem.lemmatize(array[0]), "allowance ") >= 90 and arrLength >= 2:
        pass 
    if array[0] == "cash" and arrLength >= 2:
        pass
    if array[0] in ["total", "subtotal" "sum"]:
        pass
    if array[0] in servicesList and arrLength >= 2:
        pass
    if array[0] in placesList and arrLength >= 2:
        pass
    if findName(array, 0) != 0:
        pass
    if array[0] == "sterling" and arrLength >= 2:
        pass
    if fuzz.ratio(lem.lemmatize(array[0]), "currency") >= 90 and arrLength >= 2:
        pass
    if fuzz.ratio(lem.lemmatize(array[0]), "expence") >= 85 and arrLength >= 2:
        pass
    if fuzz.ratio(lem.lemmatize(array[1]), "expence") >= 85 and arrLength >= 2:
        pass
    if array[0] == "account" and arrLength >= 2:
        pass
    if array[0] == "contra" and arrLength >= 2:
        pass
    if array[0] in ["sundries", "sundry", "sundrys"]:
        pass
    if fuzz.ratio(lem.lemmatize(array[0]), "ballance") >= 90 and arrLength >= 2:
        pass
    if array[0] in ["the", "a"] and arrLength >= 2:
        if array[0] == "contra" and arrLength >= 2:
            pass
        if fuzz.ratio(lem.lemmatize(array[0]), "ballance") >= 90 and arrLength >= 2:
            pass
        elif array[0] in professionList and arrLength >= 2:
            pass

# Functon to find name and professions, and preceding/following prefixes/suffixes
def findName(array, idx):
    newPplDict = peopleObject.copy()   # Initializes new people dictionary

    # Helper function to search for profession
    def professionFinder():  # n = need distance from end of array
        if newPplDict["profession"] != "":
            return
        if process.extractBests(array[idx], professionList, scorer=tsr, score_cutoff=95):
            match = process.extractBests(array[idx], professionList, scorer=tsr, score_cutoff=95)
            newPplDict["profession"] = match[0][0]
                
    professionFinder()
    # If profession is found, increments "i" by length of profession name
    if newPplDict["profession"] != "":  
        idx = idx + len(newPplDict["profession"].split()) 

    # Checks for prefixes
    if array[idx] in prefixList and len(array) > idx+1:
        newPplDict["prefix"] = array[idx]
        idx+=1

    # Checks if first name is in database
    if array[idx] in people_df["firstName"]:
        newPplDict["firstName"] = array[idx]
        #Checks for last name
        newPplDict["lastName"] = array[idx+1] if len(array) > idx+1 and array[idx+1] in people_df["lastName"] else "LNU"
        # Checks for suffix 
        if len(array) > idx+2 and array[idx+2] in suffixList:  
            newPplDict["suffix"] = array[idx+2]
            if idx+3 < len(array): 
                idx+=3
                professionFinder()
        else:
            idx+2
            professionFinder()
    elif array[idx] in people_df["lastName"]:  # Checks if name is a last name
        newPplDict["firstName"] = "FNU"
        newPplDict["lastName"] = array[idx]
        # Checks for suffix 
        if len(array) > idx+1 and array[idx+1] in suffixList:  
            newPplDict["suffix"] = array[idx+1]
            idx+2
            professionFinder()
        else:
            idx+1
            professionFinder(0)
    elif newPplDict["prefix"] == "" and newPplDict["profession"] == "":
        return 0  # Returns zero if no names found
    return newPplDict

# Function to look for first name or prefix if last name is found
def lastNameFound(array,idx):
    newPplDict = peopleObject.copy()   # Initializes new people dictionary
    newPplDict["lastName"] = array[idx]  # Stores last name
    if idx > 0: 
        if array[idx - 1] in people_df["firstName"]: # Checks if first name precedes last name
            newPplDict["firstName"] = array[idx-1]
            if idx > 1 and array[idx - 2] in prefixList:   # Checks if prefix precedes first name
                newPplDict["prefix"] = array[idx-2]
        elif array[idx - 1] in prefixList:   # Checks if prefix precedes last name
            newPplDict["prefix"] = array[idx-1]
        else:
            newPplDict["firstName"] = "FNU"   
    return newPplDict

# Function for finding storing price
def priceFinder(idx, array, transDict):
    if idx < len(array) and array[idx][0].isdigit() == True:   # Checks for TOTAL PRICE
            transDict["totalPrice"] = array[idx+1]
    else:
        return 0

# Function for QUANTITY-QUALIFIER-ITEM pattern
# *********** Needed: ADD "of" check after QUALIFIER *********** #
# *********** Needed: ADD QUANTITY-QUALIFIER-SERVICE Check *********** #
def QQI_function(array, idx, transDict):
    transDict["quantity"] = array[idx]  # Stores number as QUANTITY
    idx+=1

    if lem.lemmatize(array[idx]) in qualifierList:  # Checks for QUALIFIER
        transDict["qualifier"] = array[idx]
        # Checks for item
        if idx+1 < len(array) and process.extractBests(lem.lemmatize(array[idx+1]), itemList, scorer=tsr, score_cutoff=95):
            item = process.extractBests(lem.lemmatize(array[idx+1]), itemList, scorer=tsr, score_cutoff=95)[0][0]
            transDict["item"] = item
            i = len(item.split())+1
            if idx+i < len(array) and array[idx+i][0].isdigit()==True:
                transDict["totalCost"] = array[idx+i]
    elif process.extractBests(array[idx], itemList, scorer=tsr, score_cutoff=95):  # Checks for ITEM if no QUALIFIER found
        item = process.extractBests(lem.lemmatize(array[idx]), itemList, scorer=tsr, score_cutoff=95)[0][0]
        transDict["item"] = item
        i = len(item.split())
        if idx+i < len(array) and array[idx+i][0].isdigit()==True:
            transDict["totalCost"] = array[idx+i]
    elif idx+1 < len(array):     # Checks ADJECTIVES preceding the ITEM
        findAdjectives(array, idx, transDict)

# QUALIFIER-{ADJECTIVE}* -ITEM-TOTAL PRICE pattern
def QAITTP_function(array, idx, transDict):
    transDict["qualifier"] = array[idx]  # Stores qualifier

    # Checks for ITEM
    if idx+1 < len(array) and process.extractBests(array[idx+1], itemList, scorer=tsr, score_cutoff=95):
        item = process.extractBests(array[idx+1], itemList, scorer=tsr, score_cutoff=95)[0][0]
        transDict["item"] = item
        i= len(item.split())+1
        if idx+i < len(array) and array[idx+i][0].isdigit() == True:
            transDict["totalCost"] = array[idx+i]
    # Checks for 1 adjective then item
    elif idx+2 < len(array) and process.extractBests(array[idx+2], itemList, scorer=tsr, score_cutoff=95):
        item = process.extractBests(array[idx+2], itemList, scorer=tsr, score_cutoff=95)[0][0]
        transDict["item"] = item
        varientsArray = [array[idx+1]]
        transDict["varient"] = varientsArray
        i= len(item.split())+2  
        if idx+i < len(array) and array[idx+i][0].isdigit() == True:
            transDict["totalCost"] = array[idx+i]
    # Checks for 2 adjectives then item
    elif idx+3 < len(array) and process.extractBests(array[idx+3], itemList, scorer=tsr, score_cutoff=95):
        item = process.extractBests(array[idx+3], itemList, scorer=tsr, score_cutoff=95)[0][0]
        transDict["item"] = item 
        varientsArray = [array[idx+1], array[idx+2]]
        transDict["varient"] = varientsArray
        i = len(item.split())+3
        if idx+i < len(array) and array[idx+i][0].isdigit() == True:
            transDict["totalCost"] = array[idx+i]

# Function to remove associated keywords
def removeKeywords(array, idx):
    if array[idx] in ["expence", "expense"]:  # Removes other keywords associated with "expense"
        if array[idx - 1] == "the":
            array[idx - 1] = ""
        if idx >= 2 and array[idx - 2] == "of":
            array[idx - 2] = ""
        if idx >= 4 and array[idx - 4] == "for":
            array[idx - 4] = ""
    elif array[idx] == "charge":  # Removes other keywords associated with "charge"
        arrEnd = len(array)-idx-1  # Saves distance between index and array end   
        if idx > 0 and array[idx-1] == "for":
            array[idx-1] = ""
        if arrEnd > 0 and array[idx + 1] in ["of", "on"]:
            array[idx+1] = ""

# Function for "per" keyword
def perFunction(array, transReview, peopleArray, placesArray, transDict):  
    index = array.index('per')  # Gets the array index of "per"

    if index+1 < len(array):    # Prevents out of bounds index increments
        index+=1
        if array[index] == "the":   # Checks if next word is "the"
            if index+1 < len(array):  
                index+1
                pplDict = findName(array, index)   # Looks for profession/person
                if pplDict == 0:      # If no person/profession found, saves next word as a place
                    placesArray.append(array[index])
                    transReview.append("Review places")
        elif index+1 < len(array) and array[index] in relationsList:	 # Checks if word is in relationList
            index+=1
            pplDict = findName(array, index)
        elif index+2 < len(array) and array[index+1] in relationsList:    # accounts for if possessives precede the relation
            index+=2
            pplDict = findName(array, index)
        else:
            pplDict = findName(array, index)
            
    if pplDict != 0:   # Checks if person was found
        peopleArray.appand(pplDict)   # Stores name

# Function for "balance" keyword
def balanceFunction(array, idx, transDict):
    # Gets the array index for "balance"/"ballance"
    """if process.extractBests(lem.lemmatize("balance"), array, scorer=tsr, score_cutoff=87):"""
    arrLength = len(array)-1  # Saves array length
        
    # Removes other keywords attached to "balance"   
    if idx > 0 and array[idx-1] == "the":
        array[idx-1] = ""
        if idx > 1 and array[idx-2] == "for":
            array[idx-2] = ""
        transDict["item"] = "balance from"
    if idx+1 <= arrLength and array[idx+1] == "of":
        array[idx+1] = ""
        transDict["item"] = "balance from"

# Function for transactions begining with "Charge"/"Charges"
def beginsChargeFunction(array, transDict, transReview, peopleArray):
    idx = 0
    if idx+2 < len(array) and array[idx+1] == "on" and lem.lemmatize(array[idx+1]) == "merchandise":
        idx+2
        if idx == len(array)-1:
            transDict["item"] = "Charges on Merchandise"
        elif idx+1 < len(array) and array[idx+1] == "for":
            idx+1
            forFunction(array, transDict, transReview, peopleArray)
        # and array[index+1] in peopleList:
        #       do stuff
        #   elif index+1 <= arrLength array[index+1][0].isdigit():
        #       do stuff


# Function for "charge on/of" keyword pattern
def chargeFunction(array, transDict, transReview):
    index = array.index('charge')   # Gets the array index for "charge"
    arrLength = len(array)-1  # Saves distance between index and array end

    if index+2 <= arrLength and array[index + 1] in ["of", "on"]:
        # Checks for ITEM
        if process.extractBests(array[index+2], itemList, scorer=tsr, score_cutoff=95):
            item = process.extractBests(array[index+2], itemList, scorer=tsr, score_cutoff=95)[0][0]
            transDict["item"] = item  # Stores ITEM
        else:
            transReview.append("Confirm Item")
            transDict["item"] = array[index+2]  # Stores new/possible ITEM

    removeKeywords(array, index) # Removes other keywords associated with "charge"

# Function for "charged" keyword
def chargedFunction(array):
    # Gets the array index for "charged"/"chargd" and adds 1
    if 'charged' in array:
        index = array.index('charged')+1
    if 'chargd' in array:
        index = array.index('chargd')+1

    # Removes other keywords attached to "charge"   
    if array[index] == "to":
        array[index] = ""
        if array[index+2] == "by":
            array[index+2] = ""
            index = index+3
        else: 
            index = index+1

        # Makes sure that index is within array range
        if 0 <= index < len(array) == False:
            return
        
        findName(array, index)   # Searches for people

# Function for "expense"/"expence" keyword
def expenseFunction(array, peopleArray, transReview, transDict): 
    # Gets the array index for "expense"/"expence"
    if 'expence' in array:
        index = array.index('expence')
    if 'expense' in array:
        index = array.index('expense')

    arrEnd = len(array)-index  # Saves distance between index and array end

    # Checks words preceding "Expense"
    if index > 0:  # Prevents out of bounds index subtraction
        if array[index - 1] in people_df["lastName"]:   # Checks if a last name is preceding
            index = index-1
            pplDict = lastNameFound(array,index)   # Checks for first name
        elif array[index - 1] in people_df["firstName"]:  # Checks if a first name is preceding
            newPplDict = peopleObject.copy()   # Initializes new people dictionary
            newPplDict["firstName"] = array[index-1]
            if index > 1 and array[index-2] in prefixList:   # Checks if a prefix is preceding
                newPplDict["prefix"] = array[index-2]
        elif array[index-1] not in ["the", "for"]:   # Checks if "the" or "for" are preceding
            newPplDict = peopleObject.copy()   # Initializes new people dictionary
            newPplDict["Account"] = f"{array[index-1]} Expenses" # Saves Account Name
        elif array[index - 1] in suffixList and index > 1:   # Checks if suffix is preceding
            index = index-1
            pplDict = lastNameFound(array,index)   # Checks for first name
            pplDict["suffix"] = array[index]  # Stores last name

        peopleArray.append(newPplDict)  # Adds person to list
        # Remove other keywords associated with "expense"/"expence"
        removeKeywords(array, index)

    index+=1
    # Checks the following word
    if arrEnd >= 2:  # Prevents out of bounds index increments
        # Checks if following word is "for"
        if array[index] == "for":
            array[index] == ""  # Removes "for"
            index+=1
            newPplDict = findName(array, index, transReview)  # Checks for name
            if newPplDict == 0:
                pplDict = peopleObject.copy
                pplDict["Account"] = f"{array[index]} Expenses" # Saves Account Name    
                peopleArray.append(pplDict)
            else:
                peopleArray.append(newPplDict)
        if array[index] == "of":   # Checks if following word is "of" and saves folloiwing word as the item
            array[index] == ""  # Removes "of"
            index+=1
            transDict["item"] = array[index]
            transReview.append("Review Item")  # Checks if first element of following string is a digit
        elif array[index][0].isdigit() == True:
                QQI_function(array, index, transDict)  # Checks for QUANTITY, QUALIFIER, and ITEM

# Function for "account" keyword
def accountFunction(array, transReview, peopleArray):
    index = array.index('account')  # Gets the array index for "account"
    arrEnd = len(array)-index  # Saves distance between index and array end

    # Function to check preceeding words
    def helperFunction(index):
        if array[index - 1] in people_df["lastName"]:   # Checks if last name precedes word
            pplDict = lastNameFound(array,index-1)   # Checks for first name
            pplDict["lastName"] = array[index]  # Stores last name
            peopleArray.append(pplDict)
        elif array[index - 1] in people_df["firstName"]:  # Checks if first name precedes word
            pplDict = peopleObject.copy()
            pplDict["firstName"] = array[index-1]
            if index > 1 and array[index-2] in prefixList:   # Checks if prefix precedes first name
                pplDict["prefix"] = array[index-2]
            peopleArray.append(pplDict)
        elif array[index-1] in professionList:   # Checks if a professsion precedes word
                pplDict = peopleObject.copy()
                pplDict["profession"] = array[index-1]
                peopleArray.append(pplDict)

    # Checks words preceding "account"
    if index > 0:  # Prevents out of bounds index subtraction
        if array[index - 1] in people_df["lastName"]:
            helperFunction(index)  # Checks for names and professions
        elif array[index-1] == "on": # Checks if "on" precedes "account"
            array[index-1] = ""   # Removes associated keyword
            index = index-1
            if index > 0:  # Prevents out of bounds index subtraction
                helperFunction(index) #Checks for names and professions
        else:
            pplDict = peopleObject.copy()
            pplDict["account"] = f"{array[index-1]} Account"  # Saves account
            transReview.append("Review Acount name. ")
            peopleArray.append(pplDict)

    index+=1
    # Checks the following word
    if arrEnd >= 2 and array[index] == "of":  # Checks if "of" follows "account"
        array[index] == ""  # Removes "of"
        index+=1
        if findName(array, index) != 0: # Checks for name
            temp =findName(array, index)  
            peopleArray.append(temp)

# Function for "received" keyword
def receivedFunction (array,placesArray,transReview,peopleArray):
    index = array.index('received')   # Gets the array index for "charge"
    arrEnd = len(array)-index  # Saves distance between index and array end

    if arrEnd > 1: # Prevents out of bounds index increments
        index+=1
        if array[index] in ["per", "by"]:  # Checks if "per" or "by" follows
            if arrEnd > 2 and array[index+1] == "the":  # Checks if "the" follows
                array[index+1] = ""  # Removes "the" keyword
                pplDict = findName(array, index+2)
                if pplDict != 0:
                    peopleArray.append(pplDict)
                else:
                    placesArray.append(array[index+2])  # Stores Place
                    transReview.append("Review places")
            elif arrEnd > 2 and array[index+1] in relationsList:
                temp = findName(array,index+2)
                peopleArray.append(temp)
            elif array[index+1] in people_df["firstName"]:
                temp = findName(array,index)
                peopleArray.append(temp)
            else:
                placesArray.append(array[index+1])  # Stores Place
            array[index] = ""  # Removes "per" keyword

# Function for "value" keyword
def valueFunction(array, transReview,transDict):
    index = array.index('value')  # Gets the array index for "value"
    arrEnd = len(array)-index  # Saves distance between index and array end

    # Checks if "the" is preceeding and removes it
    if index > 0 and array[index - 1] == "the":
        array[index - 1] == ""

    index+=1
    if arrEnd > 1 and array[index] == "of":  # Checks if "of" follows "value"
        array[index] == ""  # Removes "of"
        index+=1
        if lem.lemmatize(array[index]) not in itemList:  # Checks if word is NOT an item
            transReview.append("Review item.")
            transDict["item"] = f"Value of {array[index]}"

# Function for "returned" keyword
def returnedFunction(array,transDict):
    if "returned" in array and transDict["service"] is None:
        transDict["service"] = "returned"

# Function for "by" keyword
def byFunction(array, transReview,placesArray,peopleArray):
    index = array.index('by')  # Gets the array index for "by"
    arrEnd = len(array)-index  # Saves distance between index and array end

    if index > 0 and array[index - 1] == "returned":   # Checks if "returned" is preceeding
        if array[index+1] not in places_df:
            transReview.append("Review: New/Unkown place")
        placesArray.append(array[index+1])   # Stores place
    elif index > 0 and array[index - 1] == "sent":   # Checks if "sent" is preceding
        index+=1
        temp = findName(array, index)   # Searches for name
        peopleArray.append(temp)

    if arrEnd > 0:  # Prevents out of bounds index increments
        index+=1 
        # Checks for proceeding pronouns
        if index > 2 and array[index - 2] in ["her","him", "them", "us", "me", "you", "his"]:  
            temp = findName(array, index)   # Looks for names
            peopleArray.append(temp)
            if index > 2 and array[index - 3] == "to":   # Checks for "to {pronoun}" pattern  
                array[index - 2] = ""  # Removes "to"    
        elif findName(array, index) != 0:  # Checks for names following titles
            temp = findName(array, index)
            peopleArray.append(temp)

        if arrEnd > 1:  # Prevents out of bounds index increments
            if findName(array, index+1) != 0:  # Checks for names following titles
                temp = findName(array, index+1)
                peopleArray.append(temp)
            elif array[index] == "the":    # Checks if "the" follows
                temp = findName(array, index+1)  # Checks for names and/or professions
                if temp != 0:
                    peopleArray.append(temp)
            else:
                pplDict = peopleObject.copy()
                pplDict["firstName"] = array[index]
                transReview.append("Review: Check person's name.")

# Function for getting ADJECTIVES/Varients
def findAdjectives(array, idx, transDict):
    if process.extractBests(array[idx+1], itemList, scorer=tsr, score_cutoff=95):  # Accounts for 1 ADJECTIVE
        item = process.extractBests(array[idx+1], itemList, scorer=tsr, score_cutoff=95)[0][0]
        transDict["item"] = item
        varientsArray = [array[idx]]
        transDict["varients"] = varientsArray
        i = len(item.split())+1
        if idx+i < len(array) and array[idx+i][0].isdigit() == True:   # Checks for TOTAL PRICE
            transDict["totalPrice"] = array[idx+i] 
    elif idx+2 < len(array) and process.extractBests(array[idx+2], itemList, scorer=tsr, score_cutoff=95):  # Accounts for 2 ADJECTIVES
        item = process.extractBests(array[idx+2], itemList, scorer=tsr, score_cutoff=95)[0][0]
        transDict["item"] = item
        varientsArray = [array[idx], array[idx+1]]
        transDict["varients"] = varientsArray
        i = len(item.split())+2
        if idx+i < len(array) and array[idx+i][0].isdigit() == True:   # Checks for TOTAL PRICE
            transDict["totalPrice"] = array[idx+i] 

# Function for the pattern: for-SERVICE-{of}
# *********** Needed: ADD "&" check after SERVICE *********** #
def forServiceFunction(array, idx, transDict):
    transDict["Service"] = array[idx]   # Saves SERVICE

    # A helper function to get the item and/or adjectives
    def getItem():
        if process.extractBests(array[idx], itemList, scorer=tsr, score_cutoff=95):
            item = process.extractBests(array[idx], itemList, scorer=tsr, score_cutoff=95)[0][0]
            transDict["item"] = item
            i =len(item.split()) 
            if idx+i < len(array) and array[idx+i][0].isdigit() == True:   # Checks for TOTAL PRICE
                transDict["totalPrice"] = array[idx+i] 
        elif process.extractBests(array[idx+1], itemList, scorer=tsr, score_cutoff=95):  # Accounts for 1 ADJECTIVE
            item = process.extractBests(array[idx+1], itemList, scorer=tsr, score_cutoff=95)[0][0]
            transDict["item"] = item
            varientsArray = [array[idx]]
            transDict["varients"] = varientsArray
            i = len(item.split())+1
            if idx+i < len(array) and array[idx+i][0].isdigit() == True:   # Checks for TOTAL PRICE
                transDict["totalPrice"] = array[idx+i] 
        elif idx+2 < len(array) and process.extractBests(array[idx+2], itemList, scorer=tsr, score_cutoff=95):  # Accounts for 2 ADJECTIVES
            item = process.extractBests(array[idx+2], itemList, scorer=tsr, score_cutoff=95)[0][0]
            transDict["item"] = item
            varientsArray = [array[idx], array[idx+1]]
            transDict["varients"] = varientsArray
            i = len(item.split())+2
            if idx+i < len(array) and array[idx+i][0].isdigit() == True:   # Checks for TOTAL PRICE
                transDict["totalPrice"] = array[idx+i] 

    if idx+2 < len(array):    # Prevents out of bounds index increments
        idx+=1
        if array[idx] in ["of", "a", "an"]:  # Checks is SERVICE is followed by "of" or "a"
            idx+=1
            if process.extractBests(array[idx], itemList, scorer=tsr, score_cutoff=95):   # Checks for ITEM
                item = process.extractBests(array[idx], itemList, scorer=tsr, score_cutoff=95)[0][0]
                transDict["item"] = item
                i = len(item.split()) 
                if idx+i < len(array) and array[idx+i][0].isdigit() == True:   # Checks for TOTAL PRICE
                    transDict["totalPrice"] = array[idx+i]   
            elif idx+2 < len(array) and array[idx+1] == "of":    # Accounts for QUALIFER, checks for "of"
                transDict["qualifier"] == array[idx]  # Stores QUALIFER
                idx+=2
                getItem()   # Checks for ITEM and ADJECTIVES
            elif idx+1 < len(array):     # Checks ADJECTIVES preceding the ITEM
                findAdjectives(array, idx, transDict)
        elif idx+2 < len(array) and array[idx] == "the" and array[idx+1] == "above":   # Acounts for "the above ___" pattern
            idx+2
            if array[idx] == "a":   # Accounts for "the above a" pattern
                idx+=1
                if idx+2 < len(array) and array[idx+1] == "of":
                    transDict["qualifier"] == array[idx]
                    idx+=2
                    getItem()
            elif idx+1 < len(array) and array[idx+1] == "a":  # Accounts for "the above {linen} a" pattern
                idx+=2
                if idx+2 < len(array) and array[idx+1] == "of":
                    transDict["qualifier"] == array[idx]
                    idx+=2
                    getItem()
            elif array[idx].isdigit() == True:
                QQI_function(array, idx, transDict)
        elif array[idx].isdigit() == True:
            QQI_function(array, idx, transDict)
        elif process.extractBests(array[idx], itemList, scorer=tsr, score_cutoff=95):   # Checks for ITEM
                item = process.extractBests(array[idx], itemList, scorer=tsr, score_cutoff=95)[0][0]
                transDict["item"] = item
                i = len(item.split()) 
                if idx+i < len(array) and array[idx+i][0].isdigit() == True:   # Checks for TOTAL PRICE
                    transDict["totalPrice"] = array[idx+i]   

# Function for "for" keyword
def forFunction(array, transDict, transReview, peopleArray):
    index = array.index('for')  # Gets the array index for "for"

    if index+2 < len(array):
        if array[index + 1] == "the": # Checks if "the" follows
            index+=1
            if array[index] in itemList:
                transDict["item"] = array[index]  # Stores Item
                priceFinder(index+1,array, transDict)  #checks for totalCost
            elif array[index] in ["boy", "girl", "man", "woman"]:  # checks for people
                if priceFinder(index+1,array, transDict) == 0: #checks for cost
                    index+=1
                    name = findName(array, index)  # Checks for name if no price found  
                    if name != 0:   # If name found checks for price, accounts for length of name
                        peopleArray.append(name) # stores person
                        x = 8 - list(name.values()).count("")  # gets name count
                        priceFinder(index+x, array, transDict)  # checks for following price
                    # Stores unkown person and checks if price follows
                    elif index+1 < len(array) and array[index+1][0].isdigit() == True:  
                        unknown = peopleObject.copy()
                        unknown["firstname"] = "FNU"  # Stores first name
                        unknown["lastname"] = "LNU"  # Stores stores 
                        peopleArray.append(unknown)
                        transReview.append("Review people names.")
                        priceFinder(index+2,array, transDict)
        elif array[index+1] in servicesList or lem.lemmatize(array[index+1])[-3:]== "ing":
            index+=1
            forServiceFunction(array, index, transDict)
    elif index+1 < len(array):
        index+=1
        person = findName(array, index)
        if person == 0:
            forServiceFunction(array, index, transDict)
        else:
            peopleArray.append(person)

# Function for PERSON - "for" pattern
def peopleForFunction (array, transDict, transReview):
    index = array.index('for')  # Gets the array index for "for"
    array[index] = ""   # Removes "for"

    if index+1 == len(array): # Checks if next element is end of array
        transDict["item"] = array[index+1]  # Stores Item
        transReview.append("Review Item")
    elif index+2 < len(array) :
        index+=1
        if array[index] == "a":  # Checks if following word is "a"
            index+=1
            # Checks for ITEM
            if process.extractBests(array[index], itemList, scorer=tsr, score_cutoff=95):
                item = process.extractBests(array[index], itemList, scorer=tsr, score_cutoff=95)[0][0]
                transDict["item"] = item
                i = len(item.split()) 
                if index+i < len(array) and array[index+i][0].isdigit() == True:   # Checks for TOTAL PRICE
                    transDict["totalPrice"] = array[index+i]                    
            elif lem.lemmatize(array[index]) in qualifierList:  # Checks for Qualifier
                QAITTP_function(array, index, transDict) # Checks for QUALIFIER-{ADJECTIVE}*-ITEM-TOTALPRICE
            elif lem.lemmatize(array[index]) in servicesList:
                transDict["service"] = array[index] 
                if index+i < len(array) and array[index+i][0].isdigit() == True:   # Checks for TOTAL PRICE
                    transDict["totalPrice"] = array[index+i] 
            else:
                transDict["service"] = array[index] 
                transReview.append("Review: Confirm SERVICE.")
                if index+i < len(array) and array[index+i][0].isdigit() == True:   # Checks for TOTAL PRICE
                    transDict["totalPrice"] = array[index+i] 
        if array[index] == "interest" and array[index+1] == "on":  # checks if "interest" follows
            array[index+1] == ""     # Removes "on"
            transDict["item"] = "interest"  # Stores ITEM
        if array[index][0].isdigit() == True:
            transDict["quanity"] = array[index]
            if index+2 < len(array) and lem.lemmatize(array[index+1]) in qualifierList:
                index+1
                QQI_function(array, index, transDict)



# Function for getting the total/unit cost and converting it to pound-shilling-pence
# ********* Not completed ********* #
def getCostFunction(array,index, transDict):
    if index < len(array) and array[index][0].isdigit() == True:    # Prevents out of bounds index increment
        price = nltk.word_tokenize(array[index])
        if len(price) > 1 and price[1] == ".." and price[1] == "..":
            pass
    if index+2 <= len(array) and index+1 == "per" and index+2 == "order":
        transDict["unitPrice"] = array[index]  # Saves number as unit price

# ******************* VARIABLES USED ******************* #
# entryError[] = List to store entry errors 
# transArray[] = Array of tokenizd transactions from Chip's function
# otherItems[] = List of items associated with a single transaction
# peopleArray[] = List of people mentioned in a transaction
# placesArray[] = List of places mentioned in a transaction
# varientsArray = List of item's adjectives
# transError[] = List to store entry errors
# transReview = List of data to review in a transaction
# ****************************************************** #

# Function that parses the transactions from the entry column (transArr = array/list of transactions)
def transParse(transArr):    # sourcery skip: hoist-statement-from-loop
    
 # Initializes error array for entry
    entryError = []

    i = 0
    # Converts all array elememts to lowercase
    while i < len(transArr):
        transArr[i] = [element.lower() for element in transArr[i]]
        i+=1

    # Checks the firt word of first tranaction to get entry's transaction type.
    if transArr[0][0] == "to":
        transactionType = "debit"
    elif transArr[0][0] == "by":
        transactionType = "credt"
    else:
        entryError.append("Error: No transaction type.")
    
    # Iterating through array/list of transactions
    for transaction in transArr:
        # Initializes lists for transaction values and errors
        otherItems, peopleArray, placesArray, varientsArray, transReview = [],[],[],[],[] 
        transDict = transactionObject.copy() # Initializies dictionary for transaction
    
        # Checks if first character of first string is a digit or letter
        if transaction[0][0].isdigit() == True:
            intFirstParse(transaction, transDict, otherItems, peopleArray, placesArray, varientsArray, transReview)
        elif transaction[0][0].isalpha() == True:
            # Checks if first word in array is "to" or "by"
            if transaction[0] == "to" | transaction[0] == "by":
                # Removes "to" or "by" 
                transaction[0].pop(0)
                # Checks again if first character of first string is a digit or letter
                if transaction[0][0].isdigit() == True:
                    intFirstParse(transaction,transDict,otherItems,peopleArray,placesArray,varientsArray,transReview)
                else:
                    alphaFirstParse(transaction,transDict,otherItems,peopleArray,placesArray,varientsArray,transReview)
        else:
            entryError.append("Error: Entry does not begin with a letter or number")
              
    