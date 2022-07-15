from operator import index
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
qualifier_df = pd.DataFrame(db["QUALIFIER"].find())
people_df = pd.DataFrame(db["people"].find())
item_df = pd.DataFrame(db["ITEMS"].find())
places_df = pd.DataFrame(db["places"].find())

# Creating lists
qualifierList = qualifier_df['word'].to_numpy()  # Creates an array of current Qualifiers
itemList = item_df['name'].to_numpy()  # Creates an array of current Items
professionList = people_df['Profession'].to_numpy() # Creates an array of current profofessions
relationsList = ["mother", "father", "son", "sons", "daughter", "daughters", "slave", "boy", "girl", "wench", "lady", "negro"]
keywordList = ["of", "by", "for", "the", "from", "to", "by"]
prefixList = ["Mr", "Mr.", "Mrs", "Mrs.", "Ms", "Ms.", "Miss", "Miss."]
suffixList = ["jr", "sr.", "esquire"]
possessiveList = ["your", "his", "her", "my", "their", "our"]
servicesList = ["making", "mending", "postage", "waggonage", "freight"]

# Initializing dictionaries
peopleObject ={"prefix": "", "firstName": "", "lastName": "", "suffix": "", "profession": "", "loacation": "", 
                    "reference": "", "relations": ""}
transactionObject ={"quantity": "", "qualifier": "", "adjectives": "", "item": "", "unitPrice": "", 
                        "totalPrice": "", "service": "", "includedItems": ""}
moneyObject = {"pounds": "", "shilling": "", "pence": ""}

# Functon for parsing entries begining with an integer
def intFirstParse(array, transDict):
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
def alphaFirstParse(array, transDict):
        # Checks if the 2nd word is in the qualifier list 
        if lem.lemmatize(array[1]) in qualifierList:
            transDict["qualifier"] = lem.lemmatize(array[1])
        elif process.extractBests(lem.lemmatize(array[1]), itemList, scorer=tsr, score_cutoff=95):
            item = process.extractBests(lem.lemmatize(array[1]), itemList, scorer=tsr, score_cutoff=95)[0][0]
            transDict["item"] = item
            i = len(item.split()) 

# Functon to find name and following professions, starting with first name
def findName(array, idx):
    arrEnd = len(array)-idx  # Saves distance between index and array end
    newPplDict = peopleObject.copy()   # Initializes new people dictionary
    i = 0  # variable used to prevent out of bounds index increments

    # Helper function to search for profession
    def professionFinder(n):  # n = need distance from end of array
        if newPplDict["profession"] != "":
            return
        if arrEnd > n and process.extractBests(array[idx], professionList, scorer=tsr, score_cutoff=95):
            match = process.extractBests(array[idx], professionList, scorer=tsr, score_cutoff=95)
            newPplDict["profession"] = match[0][0]
                
    professionFinder(0)
    # If profession is found, increments "i" by length of profession name
    if newPplDict["profession"] != "":  
        i = len(newPplDict["profession"].split()) 

    # Checks for prefixes
    if array[idx] in prefixList and arrEnd > i:
        newPplDict["prefix"] = array[idx]
        idx+=1

    # Checks if first name is in database
    if array[idx] in people_df["firstName"]:
        newPplDict["firstName"] = array[idx]
        #Checks for last name
        newPplDict["lastName"] = array[idx+1] if arrEnd>i and array[idx+1] in people_df["lastName"] else "LNU"
        # Checks for suffix 
        if arrEnd > i+1 and array[idx+2] in suffixList:  
            newPplDict["suffix"] = array[idx+2]
            professionFinder(2)
        else:
            professionFinder(1)
    elif array[idx] in people_df["lastName"]:  # Checks if name is a last name
        newPplDict["firstName"] = "FNU"
        newPplDict["lastName"] = array[idx]
        # Checks for suffix 
        if arrEnd > i and array[idx+1] in suffixList:  
            newPplDict["suffix"] = array[idx+1]
            professionFinder(1)
        else:
            professionFinder(0)
    elif newPplDict["prefix"] == "":
        return 0  # Returns zero if no names found
    return newPplDict

# Function to look for first name or prefix if last name is found
def lastNameFound(array,idx):
    newPplDict = peopleObject.copy()   # Initializes new people dictionary
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
            transDict["totalPrice"] = array[index+1]
    else:
        return 0

# Function for QUANTITY-QUALIFIER-ITEM pattern
def QQI_function(array, idx, transDict):
    transDict["quantity"] = array[idx]  # Stores number as QUANTITY
    arrEnd = len(array)-idx  # Saves distance between index and array end
    idx+=1

    if lem.lemmatize(array[idx]) in qualifierList:  # Checks for QUALIFIER
        transDict["qualifier"] = array[idx]
        # Checks for item
        if arrEnd > 3 and process.extractBests(lem.lemmatize(array[idx+1]), itemList, scorer=tsr, score_cutoff=95):
            item = process.extractBests(lem.lemmatize(array[idx+1]), itemList, scorer=tsr, score_cutoff=95)[0][0]
            transDict["item"] = item
            i = len(item.split()) 
            if arrEnd > 4 and array[index+i][0].isdigit()==True:
                transDict["totalCost"] = array[index]
    elif process.extractBests(lem.lemmatize(array[idx]), itemList, scorer=tsr, score_cutoff=95):
        item = process.extractBests(lem.lemmatize(array[idx]), itemList, scorer=tsr, score_cutoff=95)[0][0]
        transDict["item"] = item
        i = len(item.split()) 
        if arrEnd > 4 and array[index+i][0].isdigit()==True:
            transDict["totalCost"] = array[index]

# QUALIFIER-{ADJECTIVE}* -ITEM-TOTAL PRICE pattern
def QAITTP_function(array, idx, transDict, varientsArray):
    transDict["qualifier"] = array[idx]  # Stores qualifier
    arrEnd = len(array)-idx  # Saves distance between index and array end

    # Checks for ITEM
    if arrEnd > 0 and process.extractBests(lem.lemmatize(array[idx+1]), itemList, scorer=tsr, score_cutoff=95):
        item = process.extractBests(lem.lemmatize(array[idx+1]), itemList, scorer=tsr, score_cutoff=95)[0][0]
        transDict["item"] = item
        i = len(item.split())+1
        if arrEnd > 1 and array[idx+i][0].isdigit() == True:
            transDict["totalCost"] = array[idx+i]
    # Checks for 1 adjective then item
    elif arrEnd > 1 and process.extractBests(lem.lemmatize(array[idx+2]), itemList, scorer=tsr, score_cutoff=95):
        item = process.extractBests(lem.lemmatize(array[idx+2]), itemList, scorer=tsr, score_cutoff=95)[0][0]
        transDict["item"] = item
        i = len(item.split())+1  
        transDict["varient"] = array[idx+1]
        if arrEnd > 2 and array[idx+i][0].isdigit() == True:
            transDict["totalCost"] = array[idx+i]
    # Checks for 2 adjectives then item
    elif arrEnd > 2 and process.extractBests(lem.lemmatize(array[idx+3]), itemList, scorer=tsr, score_cutoff=95):
        item = process.extractBests(lem.lemmatize(array[idx+3]), itemList, scorer=tsr, score_cutoff=95)[0][0]
        transDict["item"] = item
        i = len(item.split())+1  
        varientsArray.append(array[idx+1])  
        varientsArray.append(array[idx+2])   
        transDict["varient"] = varientsArray
        if arrEnd > 3 and array[idx+i][0].isdigit() == True:
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
def perFunction(array, transReview, peopleArray, placesArray):  
    index = array.index('per')  # Gets the array index of "per"
    arrEnd = len(array)-index  # Saves distance between index and array end

    if arrEnd > 1:  # Prevents out of bounds index increments
        index+=1
        if array[index] == "the":   # Checks if next word is "the"
            array[index] = ""
            index+=1
            if arrEnd > 2 and array[index] in professionList:   # Checks if next word is pwersom or a profession
                pplDict = findName(array, index)
                if pplDict !=0:
                    peopleArray.append(pplDict)
            else:           # Saves next word as a place
                placesArray.append(array[index])
                transReview.append("Review places")
            """ elif array[index] == "order":    # Checks if next word is "order"
            if index > 1 and array[index-2][0].isdigit() == True:    # Checks if preceding element is a digit
                transactionDict["unitPrice"] = array[index-2]  # Saves number as unit price"""
        elif array[index] in relationsList or array[index] in prefixList:	 # Checks if word is in relationList or prefixList
            index+=1
            pplDict = findName(array, index)
        elif array[index+1] in relationsList:    # accounts for if possessives precede the relation
            index+=2
            pplDict = findName(array, index)
        else:
            pplDict = findName(array, index)
            
    if pplDict != 0:   # Checks if person was found
        peopleArray.appand(pplDict)   # Stores name

# Function for "balance" keyword
def balanceFunction(array, transDict):
    # Gets the array index for "balance"/"ballance"
    if 'balance' in array:
        index = array.index('balance')
    if 'ballance' in array:
        index = array.index('ballance')

    arrEnd = len(array)-index  # Saves distance between index and array end
        
    # Removes other keywords attached to "balance"   
    if index > 0 and array[index-1] == "the":
        array[index-1] = ""
        if index > 1 and array[index-2] == "for":
            array[index-2] = ""
        transDict["item"] = "balance from"
    if arrEnd > 0 and array[index+1] == "of":
        array[index+1] = ""
        transDict["item"] = "balance from"

# Function for "charge" keyword
def chargeFunction(array, transDict, transReview):
    index = array.index('charge')   # Gets the array index for "charge"
    arrEnd = len(array)-index  # Saves distance between index and array end

    if arrEnd > 1 and array[index + 1] in ["of", "on"]:
        # Checks for ITEM
        if process.extractBests(lem.lemmatize(array[index+2]), itemList, scorer=tsr, score_cutoff=95):
            item = process.extractBests(lem.lemmatize(array[index+2]), itemList, scorer=tsr, score_cutoff=95)[0][0]
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
    newPplDict = peopleObject.copy()   # Initializes new people dictionary

    # Checks words preceding "Expense"
    if index > 0:  # Prevents out of bounds index subtraction
        if array[index - 1] in people_df["lastName"]:   # Checks if a last name is preceding
            index = index-1
            pplDict = lastNameFound(array,index)   # Checks for first name
            pplDict["lastName"] = array[index]  # Stores last name
        elif array[index - 1] in people_df["firstName"]:  # Checks if a first name is preceding
            newPplDict["firstName"] = array[index-1]
            if index > 1 and array[index-2] in prefixList:   # Checks if a prefix is preceding
                newPplDict["prefix"] = array[index-2]
        elif array[index-1] not in ["the", "for"]:   # Checks if "the" or "for" are preceding
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
                newPplDict["Account"] = f"{array[index]} Expenses" # Saves Account Name
            else:
                peopleList.append(newPplDict)

        # Checks if following word is "of" and saves folloiwing word as the item
        if array[index] == "of":
            array[index] == ""  # Removes "of"
            index+=1
            transDict["item"] = array[index]
            transReview.append("Review Item")
        
        # Checks if first element of following string is a digit
        if array[index][0].isdigit() == True:
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
            pplDict["account"] = array[index-1]  # Saves account
            transReview.append("Review Acount name. ")
            peopleArray.append(pplDict)

    index+=1
    # Checks the following word
    if arrEnd >= 2 and array[index] == "of":  # Checks if "of" follows "account"
        array[index] == ""  # Removes "of"
        index+=1
        if array[index] in people_df["firstName"]: # Checks if a first name follows "of"
            findName(array, index)  # Checks for name
        elif arrEnd >= 3 and array[index] in prefixList:   # Checks if prefix follows "of"
            peopleDict["prefix"] = array[index]
            index+=1
            findName(array, index)  # Checks for name

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
        if index > 2 and array[index - 2] in ["her","him", "them", "us", "me", "you"]:  
            temp = findName(array, index)   # Looks for names
            peopleArray.append(temp)
            if index > 2 and array[index - 3] == "to":   # Checks for "to {pronoun}" pattern  
                array[index - 2] = ""  # Removes "to"    
        elif array[index] in people_df["firstName"]:
            temp = findName(array, index)    # Checks for names
            if temp["firstName"] != None:
                peopleArray.append(temp)

        if arrEnd > 1:  # Prevents out of bounds index increments
            if array[index+1] in people_df["firstName"] or array[index+1] in people_df["lastName"]:
                temp = findName(array, index)    # Checks for names following titles
                if array[index] in prefixList:   # Checks for prefixes
                    temp["prefix"] = array[index]
                if array[index] in professionList:  # Checks for professions
                    temp["profession"] = array[index]
                if temp["firstName"] != None:
                    peopleArray.append(temp)
            elif array[index] == "the":    # Checks if "the" follows "by"
                if array[index+1] not in professionList:  # Checks for "the {profession} pattern
                    transReview.append("Review: Check Profession")
                peopleDict["profession"] = array[index+1]
            else:
                peopleDict["firstName"] = array[index]
                transReview.append("Review: Check person's name.")

# Function for the pattern: for-SERVICE-{of}
"""def forServiceFunction(array, idx, transDict):
    arrEnd = len(array)-idx  # Saves distance between index and array end

    transDict["Service"]"""

# Function for "for" keyword
def forFunction(array, transDict, transReview, peopleArray):
    index = array.index('for')  # Gets the array index for "for"
    arrEnd = len(array)-index  # Saves distance between index and array end

    if arrEnd > 1:
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
                        priceFinder(index+x)  # checks for following price
                    # Stores unkown person and checks if price follows
                    elif index+1 < len(array) and array[index+1][0].isdigit() == True:  
                        unknown = peopleDict.copy()
                        unknown["firstname"] = "FNU"  # Stores first name
                        unknown["lastname"] = "?NU"  # Stores stores 
                        peopleArray.append(unknown)
                        transReview.append("Review people names.")
                        priceFinder(index+2)
        elif array[index+1] in servicesList or lem.lemmatize(array[index+1])[-3:]== "ing":
            index+=1
            forServiceFunction(array, index, transDict)
    elif arrEnd > 0:
        index+=1
        person = findName(array, index)
        if person == 0:
            forServiceFunction(array, index, transDict)
        else:
            peopleArray.append(person)

# Function for PERSON - "for" pattern
def peopleForFunction (array, transDict, transReview):
    index = array.index('for')  # Gets the array index for "for"
    arrEnd = len(array)-index  # Saves distance between index and array end
    array[index] = "for"   # Removes "for"

    if index+1 == len(array): # Checks if next element is end of array
        transDict["item"] = array[index+1]  # Stores Item
        transReview.append("Review Item")
    elif arrEnd > 1:
        index+=1
        if array[index] == "a":  # Checks if following word is "a"
            index+=1
            # Checks for ITEM
            if process.extractBests(lem.lemmatize(array[index]), itemList, scorer=tsr, score_cutoff=95):
                item = process.extractBests(lem.lemmatize(array[index]), itemList, scorer=tsr, score_cutoff=95)[0][0]
                transDict["item"] = item
                i = len(item.split()) 
                if arrEnd > i and array[index+i][0].isdigit() == True:   # Checks for TOTAL PRICE
                    transDict["totalPrice"] = array[index+i]                    
            if lem.lemmatize(array[index]) in qualifierList:
                QAITTP_function(array, index, transDict) # Checks for QUALIFIER-{ADJECTIVE}*-ITEM-TOTALPRICE
        if array[index] == "interest" and array[index+1] == "on":  # checks if "interest" follows
            array[index+1] == ""     # Removes "on"
            transDict["item"] = "interest"  # Stores ITEM
        if array[index][0].isdigit() == True:
            transDict["quanity"] = array[index]
            if arrEnd > 2 and lem.lemmatize(array[index+1]) in qualifierList:
                index+1
                QQI_function(array, index, transDict)

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
    # Initializes dictionaries

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
        otherItems, peopleArray, placesArray, varientsArray, transError, transReview = [],[],[],[],[],[] 
        transDict = transactionObject.copy() # Initializies dictionary for transaction
        idx = 0   # Initializing the index
        

        # Checks if first character of first string is a digit or letter
        if transaction[idx][0][0].isdigit() == True:
            intFirstParse(transaction)
        elif transaction[idx][0][0].isalpha() == True:
            # Checks if first word in array is "to" or "by"
            if transaction[idx][0] == "to" | transaction[idx][0] == "by":
                # Removes "to" or "by" 
                transaction[idx].pop(0)
                # Checks again if first character of first string is a digit or letter
                if transaction[idx][0][0].isdigit() == True:
                    intFirstParse(transaction)
                else:
                    alphaFirstParse(transaction)
        else:
            entryError.append("Error: Entry does not begin with a letter or number")
              
