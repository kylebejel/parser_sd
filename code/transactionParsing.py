from os import unlink
from re import I
from tkinter import Y
import pandas as pd
import numpy as np
import pymongo
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import nltk
from sympy import O

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

# Creating Lists From Database Data
# Gets List Of Prefixes
pf = np.array(people_df["prefix"])
pf = pf[pf!=""]
prefixList = np.unique(pf)
# Gets List Of  First Names
fn = np.array(people_df["firstName"])
fn = fn[fn!=""]
firstNameList = np.unique(fn)
# Gets List Of Last Names
ln = np.array(people_df["lastName"])
ln = ln[ln!=""]
lastNameList = np.unique(ln)
# Gets List of Suffixes
sx = np.array(people_df["suffix"])
sx = sx[sx!=""]
suffixList = np.unique(sx)
# Gets List of Professions
pf = np.array(people_df["profession"])
pf = pf[pf!=""]
professionList = np.unique(pf)
# Gets List of Places
placesList = np.array(places_df["location"])
# Gets List of Place Aliases
placeAliasList = places_df[places_df.alias != '']
placeAliasList = placeAliasList.drop(['_id', "descriptor"], axis=1)
placeAliasList
# Gets List of Items
it = np.array(places_df["items"])
it = it[it!=""]
itemList = np.unique(it)   # *** ADD "premium of insurance" and "goods" to item list

varientList = []

# Creating lists
qualifierList = ["bottle","cask","pair","yard","foot", "feet","firkin", "bale", "dozen","piece"]   
relationsList = ["mother","father","son","daughter","brother","sister","slave","boy","girl", 
                "wench","lady","negro","negroes","uncle", "aunt"]
personsList = ["man","men","woman","women","boy","girl"]
keywordList = ["of", "by", "for", "the", "from", "to", "by"]
possessiveList = ["your", "his", "her", "my", "their", "our"]
servicesList = ["making", "mending", "postage", "waggonage", "freight","inspection","pasturage","ferriage","Craft hire"]
itemQualList = ["bottle", "cask", "suit"]  # List of ITEMS that are also QUALIFIERS

# Initializing dictionaries
peopleObject ={"prefix": "", "firstName": "", "lastName": "", "suffix": "", "profession": "", "account":"", "location": "", 
                    "reference": "", "relations": ""}
transactionObject ={"quantity": "", "qualifier": "", "adjectives": "", "item": "", "unitCost": "", 
                        "totalCost": "", "service": "", "includedItems": ""}
moneyObject = {"pounds": "", "shilling": "", "pence": ""}

# =========================================== #
#             General Functions               #
# =========================================== #

# Parses entries begining withan integer
def intFirstParse(array,transDict,otherItems,peopleArray,placesArray,varientsArray,transReview):
    idx = 0
    QQI_Pattern(array, idx, transDict, transReview, placesArray, peopleArray, varientsArray, otherItems)    
        
# Parses entries begining with a letter
def alphaFirstParse(array,transDict,otherItems,peopleArray,placesArray,varientsArray,transReview):
    # sourcery skip: merge-duplicate-blocks, merge-nested-ifs, remove-redundant-if
    idx = 0
    if array[0] in ["the", "a"]:  # Removes preceding "the"/"a"
        array.pop(0)

    # Checks what word/phrase/symbol the transaction begins with
    if fuzz.ratio(lem.lemmatize(array[idx]), "charge") >= 90:  
        beginsCharge(array, transDict, transReview)
    elif fuzz.ratio(array[idx], "allowance ") >= 87:
        beginsAllowance(array, transDict, transReview) 
    elif array[idx] == "cash":
        beginsCash(array, idx, transDict,transReview, peopleArray, placesArray, otherItems)
    elif array[idx] == "total":
        beginsTotal(array, transDict, transReview) 
    elif array[idx] == "account":
        beginsAccount(array,transDict,transReview, peopleArray, placesArray)
    elif array[idx] in ["subtotal" "sum"]:
        beginsSubtotalSum(array) 
    elif array[idx] in ["at","&","and"]:
        idx+=1
        if len(array)>idx and getPlace(array,idx,placesArray) != 0:
            idx = getPlace(array,idx+1,placesArray)+1
            if len(array)>idx and array[idx][0].isdigit() == True:
                getCost(array,idx,transDict,transReview, placesArray, peopleArray)
        else:
            temp = [x for x in array if x[0].isdigit()]
            if temp != [] and array.index(temp[0])<4 :
                n = array.index(temp[0])
                pName = ' '.join(array[idx:n+1])
                placesArray.append(pName)
                transReview.append("Review: Confirm PLACE.")
            else:
                placesArray.append(array[idx+1])
                transReview.append("Review: Confirm PLACE.")
    elif len(array)>idx+1 and fuzz.ratio(lem.lemmatize(array[idx+1]), "furniture") >= 90:
        transDict["item"] = f"{array[idx]} Furniture"
        idx+=2
        beginsItem(array,idx,transDict,transReview, peopleArray, placesArray, otherItems, item)
    elif array[idx] in ["sundries", "sundry", "sundrys"]:
        pass
    elif fuzz.ratio(lem.lemmatize(array[idx]), "balance") >= 90 or fuzz.ratio(array[idx], "balance") >= 90:
        beginsBalance(array,transDict)
    elif array[idx] == "contra" and fuzz.ratio(array[idx+1], "balance") :
        beginsContraBalance(array,transDict,transReview, peopleArray, placesArray)
    elif fuzz.ratio(lem.lemmatize(array[idx]), "sterling") >= 90 or fuzz.ratio(lem.lemmatize(array[idx]), "currency") >= 90:
        beginsSterlingCurrency(array,transDict,transReview, peopleArray, placesArray)
    elif fuzz.ratio(lem.lemmatize(array[idx]), "expense") >= 90 or fuzz.ratio(array[idx], "expence") >= 90:
        array[idx] = ""
        idx+=1
        beginsExpense(array,idx,transDict,transReview, peopleArray, placesArray)
    elif len(array)>idx+1 and (fuzz.ratio(lem.lemmatize(array[idx+1]), "expense") >= 90 or fuzz.ratio(array[idx+1], "expence") >= 90):
        array[idx+1] = ""
        transDict["account"] = f"{array[idx]} Expenses"
        idx+=2
        beginsPerson(array,idx,transDict,transReview, peopleArray, placesArray, otherItems)
    elif len(array)>idx+1 and array[idx+1] == "store":
        placesArray.append(f"{array[idx]} Store")
        idx+=2
        beginsPlace(array, idx, transDict,transReview, peopleArray, placesArray)
    elif len(array)>idx+2 and array[idx]!= "account" and array[idx+1] == "of":
        transDict["service"] = array[idx]  # Stores service
        transReview.append("Review: Confirm SERVICE.")
        idx+=1
        if array[idx] in ["a", "an"]:
            idx+=1
            serviceA_Pattern(array, idx, transDict, peopleArray, transReview, placesArray)
        elif array[idx] == "of":
            idx+=1
            serviceOf_Pattern(array, idx, transDict, peopleArray, transReview, placesArray)
    elif len(array)>idx+2 and (process.extractBests(lem.lemmatize(array[idx]), servicesList, scorer=tsr, score_cutoff=95)==True or lem.lemmatize(array[idx])[-3:]== "ing"):
        transDict["Service"] = array[idx]   # Stores SERVICE
        idx+=1
        if array[idx] in ["a", "an"]:
            idx+=1
            serviceA_Pattern(array, idx, transDict, peopleArray, transReview, placesArray)
        elif array[idx] == "of":
            idx+=1
            serviceOf_Pattern(array, idx, transDict, peopleArray, transReview, placesArray)
    elif findName(array, 0) != 0:
        name = findName(array, idx)
        peopleArray.append(name[0])
        idx = name[1]
        beginsPerson(array,idx,transDict,transReview, peopleArray, placesArray, otherItems)
    elif process.extractBests(array[idx], itemList, scorer=tsr, score_cutoff=80):
        item = process.extractBests(array[idx], itemList, scorer=tsr, score_cutoff=80)[0][0]
        transDict["item"] = item
        i = len(item.split())
        idx = idx+i
        beginsItem(array,idx,transDict,transReview, peopleArray, placesArray, otherItems, item)
    elif getPlace(array,idx,placesArray) != 0:
        idx = getPlace(array,idx,placesArray)
        beginsPlace(array, idx, transDict,transReview, peopleArray, placesArray)
    elif any(word in '& and with' for word in array) == False and (array[-1][0].isdigit()==True or array[-1] in ["order"]):
        reverseParse(array,idx,transDict,transReview)
    else:
         # ******* Run all keyword functions ******* #
        
        transReview.append("Error: Transaction in unrecognizeable pattern.")

# Determines if number is a total/unit cost then convets it to to pound-shilling-pence (If not a COST returns 0, else returns 1)
def getCost(array,idx,transDict,transReview, placesArray, peopleArray):  # sourcery skip: low-code-quality
    
    money = moneyObject.copy()  # Creates new money dictionary
    flag = None  # Flag for UNIT COST

    # Checks for index range and if element is a digit
    if idx > len(array) or array[idx][0].isdigit()==False:  
        return 0

    # Checks if "at"/"is" precedes the COST
    if len(array)>idx+1 and array[idx] in ["at","is"]:  
        if len(array)>idx+2 and array[idx] == "at" and array[idx+2] == "percent":
            array[idx] == ""   # Removes "at"
            transDict["quantity"] = array[idx+1]
            transDict["qualifier"] = "Percent"
            idx+=3
            if len(array)>idx and fuzz.ratio(array[idx], "exchange")>90:
                idx+=1
        elif idx>0 and array[idx] == "at" and fuzz.ratio(array[idx-1], "valued")>90: # Checks id "valued" precedes "at"
            array[idx] == ""   # Removes "at"
            array[idx-1] == ""   # Removes "valued"
            idx+=1
            getCost(array,idx,transDict,transReview, placesArray, peopleArray)
            idx+=1
            if len(array)>idx and array[idx] in ["currency","currencies","sterling","sterlings"]:
                idx+=1
                getCost(array,idx,transDict,transReview, placesArray, peopleArray)
        else:
            idx+=1 
            flag = True  # Flag to store COST as UNIT COST
    
    # Acounts for "valued at" phrase
    if len(array)>idx+1 and fuzz.ratio(array[idx], "valued")>90 and array[idx+1] == "at":
        array[idx] == ""   # Removes "valued"
        array[idx+1] == ""   # Removes "at"
        idx+=2
        getCost(array,idx,transDict,transReview, placesArray, peopleArray)
        idx+=1
        if len(array)>idx and array[idx] in ["currency","currencies","sterling","sterlings"]:
            idx+=1
            getCost(array,idx,transDict,transReview, placesArray, peopleArray)
        return
    
    # Acounts for if "cost" precedes price
    if lem.lemmatize(array[idx], "cost")>90:
        idx+=1

    # Makes sure that value is a price
    if len(array)>idx+1 and process.extractBests(array[idx+1], itemList, scorer=tsr, score_cutoff=80) or lem.lemmatize(array[idx+1]) in qualifierList:
        QQI_Pattern(array, idx, transDict, transReview, placesArray, peopleArray)
        return 0

    # Accounts for "valued at" phrase
    if len(array)>idx+2 and array[idx] == "valued" and array[idx+1] == "at":
        idx+2

    # Checks for "currency-at-QUANTITY-QUALIFIER" pattern
    if len(array)>idx+4 and array[idx+1] in ["currency","sterling"] and array[idx+2] =="at" and array[idx+3][0].isdigit()==True and array[idx+4] == "percent":
        transDict["quantity"] = array[idx+3]
        transDict["qualifier"] = "percent"
        return 0

    cost = nltk.word_tokenize(array[idx])   # Tokenizes the string
    if len(cost) == 1 and "/" in cost[0]:   # Checks for "2/1" COST pattern
        cost = cost[0].split("/")
        money["pounds"] = "0"
        money["shillings"] = cost[0]
        money["pence"] = "0" if cost[1] == ":" else cost[1]
    elif len(cost) == 1 and cost[0].isalnum() == True and cost[0][-1] in ["d","D"]:     # Checks for "6d" COST pattern
        p = cost[0].replace(cost[0][-1],"")  # Removes the "d"
        money["pounds"] = "0"
        money["shillings"] = "0"
        money["pence"] = p
    elif len(cost) > 4 and cost[1] == ".." and cost[3] == "..":  # Checks for "83..6..2" pattern
        money["pounds"] = cost[0]
        money["shillings"] = cost[2]
        money["pence"] = cost[4]
    elif len(cost) > 4 and "..." in cost:  # Checks for decmial numbers 
        for i, element in enumerate(cost):
            if element == "..." and  i+1 < len(cost):
                x=cost[i+1]
                print(cost[i+1])
                cost[i+1] = f"0.{x}"
        money["pounds"] = cost[0]
        money["shillings"] = cost[2]
        money["pence"] = cost[4]
    elif len(cost) == 1 and cost[0].isdigit()==True:
        money["pounds"] = "0"
        money["shillings"] = "0"
        money["pence"] = cost[0]

    if money["pence"] == "":
        return 0  # Returns 0 if COST not found
    if idx+2 < len(array) and array[idx+1] == "per" and array[idx+2] == "order":  # Checks if "per order" follows COST
        print(array[idx+1])
        transDict["unitCost"] = money  # Saves COST as UNIT_COST
        array[idx+1] == ""   # Removes "per" keyword
        if len(array) > 0 and array[idx-1] == "at":
            array[idx-1] == ""   # Removes "at" keyword
    elif flag == True:
        transDict["unitCost"] = money  # Saves COST as UNIT_COST
        idx+=1
        getCost(array,idx,transDict,transReview, placesArray, peopleArray)  # Checks if TOTAL_COST follows UNIT_COST
    else:
        transDict["totalCost"] = money  # Saves COST as TOTAL_COST
        idx+1
        if len(array)>idx+2 and array[idx] == "at" and array[idx+2] == "percent":
            array[idx] == ""   # Removes "at"
            transDict["quantity"] = array[idx+1]
            transDict["qualifier"] = "Percent"
            return
    return 1  # Returns 1 if COST found

# Determines if word is a kn known PLACE name (If not found returns 0, else returns index of next word )
def getPlace(array,idx,placesArray):
    # Serches for place
    if process.extractBests(array[idx], placesList, scorer=fuzz.token_set_ratio, score_cutoff=80):
        place = process.extractBests(array[idx], placesList, scorer=fuzz.token_set_ratio, score_cutoff=80)[0][0]
        placesArray.append(place)
        i = len(place.split())
        idx = idx+i
        return idx
    # Searches for place alias and maps it to the real/full name
    elif process.extractBests(array[idx], placeAliasList["alias"], scorer=fuzz.token_set_ratio, score_cutoff=80):
        pl = process.extractBests(array[idx], placeAliasList["alias"], scorer=fuzz.token_set_ratio, score_cutoff=80)[0][0]
        n = placeAliasList.index[placeAliasList['alias']==pl].tolist()
        realName = placeAliasList['location'].loc[n[0]]
        placesArray.append(realName)
        i = len(realName.split())
        idx = idx+i
        return idx
    return 0

# Finds names & professions, and preceding/following prefixes/suffixes
# (Returns 0 if no names found, else returns [peopleObject, idx], where idx = index of next word)
def findName(array, idx):
    newPplDict = peopleObject.copy()   # Initializes new people dictionary

    # Helper function to search for profession
    def professionFinder():  # n = need distance from end of array
        if process.extractBests(array[idx], professionList, scorer=tsr, score_cutoff=95):
            match = process.extractBests(array[idx], professionList, scorer=tsr, score_cutoff=95)
            newPplDict["profession"] = match[0][0]
            idx = idx + len(newPplDict["profession"].split())   # If profession is found, increments "i" by length of profession name
            
    # Checks for preceeding professions     
    professionFinder()

    # Checks for prefixes
    if idx < len(array) and array[idx] in prefixList:
        newPplDict["prefix"] = array[idx]
        idx+=1

    # Checks if first name is in database
    while idx < len(array):
        # Checks if first name is in database
        if process.extractBests(array[idx], firstNameList, scorer=tsr, score_cutoff=90):
            fName = process.extractBests(array[idx], firstNameList, scorer=tsr, score_cutoff=90)
            newPplDict["firstName"] = fName[0][0]
            idx = idx + len(fName[0][0].split())
            if process.extractBests(array[idx], lastNameList, scorer=tsr, score_cutoff=90):   #Checks for last name
                newPplDict["lastName"] = array[idx]  
                idx+=1
                if array[idx] in suffixList:  # Checks for suffixes 
                    newPplDict["suffix"] = array[idx]
                    idx+=1
                    professionFinder() # Checks for following professions
            else: 
                newPplDict["lastName"] = "LNU"
            # Checks for suffixes following first name
            if array[idx] in suffixList:  
                newPplDict["suffix"] = array[idx]
                idx+=1
                professionFinder()   # Checks for following professions
        elif process.extractBests(array[idx], lastNameList, scorer=tsr, score_cutoff=90):  # Checks if name is a last name
            lName = process.extractBests(array[idx], lastNameList, scorer=tsr, score_cutoff=90)
            newPplDict["firstName"] = "FNU"
            newPplDict["lastName"] = lName[0][0]
            idx = idx + len(lName[0][0].split())
            if array[idx] in suffixList:  # Checks for suffix 
                newPplDict["suffix"] = array[idx]
                idx+=1
                professionFinder()  # Checks for following professions
        # Checks is any person found
        if newPplDict == peopleObject:
            return 0  # Returns zero if no names found
        else:
            return [newPplDict, idx]

# Looks for a first name/prefix if a last name is found
def reverseFindName(array,idx,peopleArray):
    newPplDict = peopleObject.copy()   # Initializes new people dictionary
    while idx > 0: 
        if  process.extractBests(array[idx], professionList, scorer=tsr, score_cutoff=86):  # Checks for professions folloing names
            job = process.extractBests(array[idx], professionList, scorer=tsr, score_cutoff=86)[0][0]
            newPplDict["profession"] = job
            idx = idx - len(job.split())
        
        if array[idx] == "the":  # Accounts for "the" preceding professions
            idx = idx-1

        if array[idx] in suffixList:    # Checks for suffix
            newPplDict["suffix"] = array[idx]
            idx = idx-1

        if process.extractBests(array[idx], lastNameList, scorer=tsr, score_cutoff=88):  # Checks for last name
            LName = process.extractBests(array[idx-1], lastNameList, scorer=tsr, score_cutoff=88)[0][0]
            newPplDict["lastName"] = array[idx]  # Stores last name
            idx = idx - len(LName.split())

        if process.extractBests(array[idx], firstNameList, scorer=tsr, score_cutoff=88):  # Checks for first Name
            fName = process.extractBests(array[idx], firstNameList, scorer=tsr, score_cutoff=88)[0][0]
            newPplDict["firstName"] = fName
            idx = idx - len(fName.split())

        if array[idx] in prefixList:   # Checks if prefix precedes first name
            newPplDict["prefix"] = array[idx]
            idx = idx-1

        if  process.extractBests(array[idx], professionList, scorer=tsr, score_cutoff=86):  # Checks for preceding profession
            job = process.extractBests(array[idx], professionList, scorer=tsr, score_cutoff=86)[0][0]
            newPplDict["profession"] = job
            idx = idx - len(job.split())

        if newPplDict != peopleObject:
            peopleArray.append(newPplDict)
            return 1
        else:
            return 0
  
# Removes associated keywords
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

# Reverse parses transactions
def reverseParse(array,transDict,transReview, varientsArray, placesArray, peopleArray):
    idx = len(array)-1

    # Helper Function to account for ADJECTIVES
    def getAdjs():
        transDict["qualifier"] = array[idx]
        idx = idx-1
        if idx>0 and array[idx][0].isdigit() == True and array[idx].isalnum() == False: # Checks for QUANTITY
            transDict["quantity"] = array[idx]
            if idx>0 and array[0] == "of":  # Checks if "of" precedes/Accounts for SERVICE-of pattern
                idx = idx-1
                # Checks for SERVICES
                if idx>0 and (process.extractBests(lem.lemmatize(array[idx]), servicesList, scorer=tsr, score_cutoff=95)==True or lem.lemmatize(array[idx])[-3:]== "ing"):  
                    transDict["service"] = array[idx]
                else:
                    transDict["service"] = array[idx]
                    transReview.append("REVIEW: Confirm Service")

    # Helper Function to account for SERVICES
    def servicesHelper():
        if idx>0 and process.extractBests(lem.lemmatize(array[idx]),servicesList,scorer=tsr,score_cutoff=90) or lem.lemmatize(array[idx])[-3:]=="ing": 
            transDict["service"] = array[idx]
        elif idx > 1 and array[idx] == "of" and process.extractBests(lem.lemmatize(array[idx-1]),servicesList,scorer=tsr,score_cutoff=90) or lem.lemmatize(array[idx-1])[-3:]=="ing":
            transDict["service"] = array[idx-1]

    # Checks if last element is a COST
    if len(array)>3 and array[idx] == "order" and array[idx-1] == "per" and array[idx-2][0].isdigit()==True:
        idx = idx-3
    if getCost(array,idx,transDict,transReview, placesArray, peopleArray) == 0: # Checks for COST and returns if not found 
        return
    idx = idx-1

    # Checks if "at" precedes COST
    if 0<idx and array[idx] == "at":
        idx = idx-1

    if 0<idx and array[idx] in qualifierList:   # Accounts for ITEMS that are also QUALIFIERS
        transDict["item"] = array[idx]
        idx = idx-1
        if 0<idx and array[0] in ["a", "an"]:  # Checks if "a" or "an" precedes QUALIFIER
            transDict["quantity"] = "1"    # Saves QUANTITY as 1
            idx = idx-1
            servicesHelper()  # Checks for SERVICES
        elif 0<idx and array[idx][0].isdigit()==True:  # Checks if a digit precedes QUALIFIER
            transDict["quantity"] = array[idx]   # Saves QUANTITY
            idx = idx-1
            servicesHelper()  # Checks for SERVICES
    elif 0<idx and (process.extractBests(lem.lemmatize(array[idx]), servicesList, scorer=tsr, score_cutoff=95)==True or lem.lemmatize(array[idx])[-3:]== "ing"):  
        transDict["service"] = array[idx]
        idx = idx-1
        if 0<idx and lem.lemmatize(array[idx]) in qualifierList:  # Checks for QUALIFIER
                transDict["qualifier"] = array[idx]
                idx = idx-1
                if 0<idx and array[idx][0].isdigit()==True:  # Checks if a digit precedes QUALIFIER
                    transDict["quantity"] = array[idx]   # Saves QUANTITY
    elif 0<idx and process.extractBests(array[idx], itemList, scorer=tsr, score_cutoff=90):  # Checks for ITEM
        item = process.extractBests(lem.lemmatize(array[idx]), itemList, scorer=tsr, score_cutoff=90)
        transDict["item"] = item[0][0]
        i = len(item[0][0].split())
        idx = idx-i

        if 0<idx and array[0] == "of":  # Checks if "of" precedes/Accounts for QUALIFIER-of pattern
            idx = idx-1
            if 0<idx and lem.lemmatize(array[idx]) in qualifierList:  # Checks for QUALIFIER
                transDict["qualifier"] = array[idx]
                idx = idx-1
                if 0<idx and array[0] in ["a", "an"]:  # Checks if "a" or "an" precedes QUALIFIER
                    transDict["quantity"] = "1"    # Saves QUANTITY as 1
                    idx = idx-1
                    servicesHelper()  # Checks for SERVICES
                elif 0<idx and array[idx][0].isdigit()==True:  # Checks if a digit precedes QUALIFIER
                    transDict["quantity"] = array[idx]   # Saves QUANTITY
                    idx = idx-1
                    servicesHelper()  # Checks for SERVICES
        elif 0<idx and lem.lemmatize(array[idx]) in qualifierList:  # Checks for QUALIFIER
            transDict["qualifier"] = array[idx]
            idx = idx-1
            if 0<idx and array[idx][0].isdigit()==True and array[idx].isalnum()==False: # Checks for QUANTITY
                transDict["quantity"] = array[idx]
                if 0<idx and array[0] == "of":  # Checks if "of" precedes/Accounts for SERVICE-of pattern
                    idx = idx-1
                    # Checks for SERVICES
                    if 0<idx and (process.extractBests(lem.lemmatize(array[idx]), servicesList, scorer=tsr, score_cutoff=95)==True or lem.lemmatize(array[idx])[-3:]== "ing"):  
                        transDict["service"] = array[idx]
                    else:
                        transDict["service"] = array[idx]
                        transReview.append("REVIEW: Confirm Service")
        elif 0<idx-1 and lem.lemmatize(array[idx-1]) in qualifierList:  # Accounts for 1 ADJECTIVE
            idx = idx-1
            varientsArray.append(array[idx])
            transReview.append("Review: Confirm ADJECTIVE.")
            getAdjs()
        elif 0<idx-2 and lem.lemmatize(array[idx-2]) in qualifierList:  # Accounts for 2 ADJECTIVEs
            idx = idx-2
            varientsArray.append(array[idx])
            varientsArray.append(array[idx-1])
            transReview.append("Review: Confirm ADJECTIVES.")
            getAdjs()

# Runs the keyword functions
def searchAllKeywords(array, transDict, transReview, peopleArray, placesArray):

    if "per" in array:  # Checks for "per" keyword
        per_Keyword(array, transReview, peopleArray, placesArray)
    if "charge" in array:  # Checks for "charge" keyword
        charge_Keyword(array, transDict, transReview)
    if "returned" in array or "returnd" in array or "omitted" in array:   # Checks for "returned" and "omitted" keywords
        returnedOmitted_Keywords(array,transDict)
    if process.extractBests("expense", array, scorer=tsr, score_cutoff=90):   # Checks for "expense" keyword
        expense_Keyword(array, peopleArray, transReview, transDict)
    if process.extractBests("expence", array, scorer=tsr, score_cutoff=90):    # Checks for "expence" (misspelled) keyword
        expense_Keyword(array, peopleArray, transReview, transDict)
    if process.extractBests("account", array, scorer=tsr, score_cutoff=90):  # Checks for "account" keyword
        account_Keyword(array, transReview, peopleArray, transDict)
    if process.extractBests("received", array, scorer=tsr, score_cutoff=90):   # Checks for "received" keyword
        received_Keyword (array,placesArray,transReview,peopleArray)
    if "value" in array:   # Checks for "value" keyword
        value_Keyword(array, transReview,transDict)
    if "by" in array:    # Checks for "by" keyword
        by_Keyword(array, transReview,placesArray,peopleArray)
    if "for" in array:    # Checks for "for" keyword
        idx = None
        for_Keyword(array, idx, transDict, transReview, peopleArray)
    if process.extractBests("ballance", array, scorer=tsr, score_cutoff=87):   # Checks for "balance" keyword
        balance_Keyword(array, transDict)
    for i in range(len(array) - 1):  # Checks for "on the" key phrase
        value = array[i:i+2]
        if value == ["on", "the"]:
            idx1 = i
            idx2 = i+1
            onThe_Keywords(array,idx1, idx2, placesArray, transReview)
            break
    for i in range(len(array) - 1):  # Checks for "in the" key phrase
        value = array[i:i+2]
        if value == ["in", "the"]:
            idx1 = i
            idx2 = i+1
            onThe_Keywords(array,idx1, idx2, placesArray, transReview)
            break

# Assists in obtaining possible ADJECTIVES/Varients
def findAdjectives(array, idx, transDict):
    if idx+1 < len(array) and process.extractBests(array[idx+1], itemList, scorer=tsr, score_cutoff=87):  # Accounts for 1 ADJECTIVE
        item = process.extractBests(array[idx+1], itemList, scorer=tsr, score_cutoff=87)
        transDict["item"] = item[0][0]
        varientsArray = [array[idx]]
        transDict["varients"] = varientsArray
        i = len(item.split())+1
        idx = idx+i
        getCost(array,idx, transDict)
        return 1
    elif idx+2 < len(array) and process.extractBests(array[idx+2], itemList, scorer=tsr, score_cutoff=87):  # Accounts for 2 ADJECTIVES
        item = process.extractBests(array[idx+2], itemList, scorer=tsr, score_cutoff=87)
        transDict["item"] = item[0][0]
        varientsArray = [array[idx], array[idx+1]]
        transDict["varients"] = varientsArray
        i = len(item.split())+2
        idx = idx+i
        getCost(array,idx, transDict)
        return 1
    elif idx+3 < len(array) and process.extractBests(array[idx+3], itemList, scorer=tsr, score_cutoff=87):  # Accounts for 3 ADJECTIVES
        item = process.extractBests(array[idx+3], itemList, scorer=tsr, score_cutoff=87)
        transDict["item"] = item[0][0]
        varientsArray = [array[idx], array[idx+3]]
        transDict["varients"] = varientsArray
        i = len(item.split())+3
        idx = idx+i
        getCost(array,idx, transDict)
        return 1
    else:
        return 0

# =========================================== #
#             Pattern Functions               #
# =========================================== #

# Handles the "QUANTITY-QUALIFIER-ITEM" pattern
def QQI_Pattern(array, idx, transDict, transReview, placesArray, peopleArray):
    if idx+1 >= len(array):
        return

    # Helper function for retreiving ITEMS
    def getItemFunction():
        item = process.extractBests(lem.lemmatize(array[idx]), itemList, scorer=tsr, score_cutoff=95)
        transDict["item"] = item[0][0]
        i = len(item[0][0].split())
        idx = idx + i
        getCost(array,idx,transDict)

    if array[idx][0].isdigit():
        transDict["quantity"] = array[idx]  # Stores number as QUANTITY
    elif array[idx] in ["a","an"]:
        transDict["quantity"] = "1"

    idx+=1
    
    # Removes "nett" that precedes ITEM
    if "nett" in array and "off" not in array:
        index = array.index("nett")
        array.pop(index)
        
    if lem.lemmatize(array[idx]) in itemQualList:   # Checks for items that are also qualifiers
         # Checks for QUALIFIER-of-ITEM pattern 
        if idx+2 < len(array) and array[idx+1] == "of" and process.extractBests(lem.lemmatize(array[idx+2]), itemList, scorer=tsr, score_cutoff=95):
            transDict["qualifier"] = array[idx]
            idx+=2
            getItemFunction()
         # Checks if following word is an ITEM
        elif idx+1 < len(array) and process.extractBests(lem.lemmatize(array[idx+1]), itemList, scorer=tsr, score_cutoff=95):
            idx+1
            getItemFunction()
        else:
            if idx+2 < len(array):
                findAdjectives(array, idx, transDict)  # Checks for ADJECTIVES
            else:
                transDict["item"] = array[idx]   # Saves word as an ITEM if no ADJECTIVES found
                idx+1
                getCost(array,idx,transDict)
    elif idx+1 < len(array) and lem.lemmatize(array[idx]) in qualifierList:  # Checks for QUALIFIER
        transDict["qualifier"] = array[idx]  # Saves qualifier
        idx+=1
        # Checks for QUALIFIER-of-ITEM pattern 
        if idx >= len(array) and lem.lemmatize(array[idx-1]) == "pound":
            transDict["item"] = "Tobacco"
        elif idx+1 < len(array) and array[idx] == "of" and process.extractBests(lem.lemmatize(array[idx+1]), itemList, scorer=tsr, score_cutoff=95):
            idx+=1
            getItemFunction()
        elif process.extractBests(lem.lemmatize(array[idx]), servicesList, scorer=tsr, score_cutoff=95)==True or lem.lemmatize(array[idx])[-3:]== "ing":    # Checks for known services
            transDict["service"] = array[idx]
            if idx+2 < len(array) and array[idx+1] == "of":  # Checks if "of" follows SERVICE
                idx+2
                serviceOf_Pattern(array, idx, transDict)
        elif array[idx] not in servicesList and idx+1 < len(array) and array[idx+1] == "of":  # Accounts for unknown services
            transDict["service"] = array[idx]
            transReview.append("Review: Confirm SERVICE.")
            if idx+2 < len(array) and array[idx+1] == "of":
                idx+2
                serviceOf_Pattern(array, idx, transDict)
        elif idx+1 < len(array) and array[idx] == "at":
            idx+=1
            if getPlace(array,idx,placesArray)!= 0:
                idx = idx + getPlace(array,idx,placesArray)
            elif idx+1 < len(array) and process.extractBests(lem.lemmatize(array[idx+1]), servicesList, scorer=tsr, score_cutoff=95)==True or lem.lemmatize(array[idx+1])[-3:]== "ing":
                transDict["service"] = array[idx+1]
                placesArray.append(array[idx])
                transReview.append("Review: Confirm PLACE.")
                idx+=2
                serviceA_Pattern(array, idx, transDict, peopleArray, transReview, placesArray)
        elif process.extractBests(lem.lemmatize(array[idx]), itemList, scorer=tsr, score_cutoff=95):   # Checks for ITEM
            getItemFunction()
        else:     # Checks ADJECTIVES preceding the ITEM
            findAdjectives(array, idx, transDict)
    elif process.extractBests(array[idx], itemList, scorer=tsr, score_cutoff=95):  # Checks for ITEM if no QUALIFIER found
        getItemFunction()
    elif getCost(array,idx-1,transDict) != 0:  # Checks if QUANTITY is really a COST
        transDict["quantity"] = ""
    elif findAdjectives(array, idx, transDict) == 0:    # Checks ADJECTIVES preceding the ITEM
        if len(array)>idx+1:
            transDict["item"] = f"{array[idx]} {array[idx+1]}"
        else:
            transDict["item"] = f"{array[idx]}"
        if transDict["quantity"] == "1":
            transDict["quantity"] = ""
        transReview.append("Review: Confirm ITEM.")
        
# Handles the "QUALIFIER-{ADJECTIVE}* -ITEM-TOTAL_COST" pattern
def QAITTP_Pattern(array, idx, transDict, transReview):
    
    # Helper function for retreiving ITEMS
    def getItemFunction():
        item = process.extractBests(lem.lemmatize(array[idx]), itemList, scorer=tsr, score_cutoff=95)
        transDict["item"] = item[0][0]
        i = len(item[0][0].split())
        idx = idx + i
        getCost(array,idx,transDict)
    
    if lem.lemmatize(array[idx]) in itemQualList:   # Checks for items that are also qualifiers
         # Checks for QUALIFIER-of-ITEM pattern 
        if idx+2 < len(array) and array[idx+1] == "of" and process.extractBests(lem.lemmatize(array[idx+2]), itemList, scorer=tsr, score_cutoff=95):
            transDict["qualifier"] = array[idx]
            idx+=2
            getItemFunction()
         # Checks if following word is an ITEM
        elif idx+1 < len(array) and process.extractBests(lem.lemmatize(array[idx+1]), itemList, scorer=tsr, score_cutoff=95):
            idx+1
            getItemFunction()
        else:
            if idx+2 < len(array):
                findAdjectives(array, idx, transDict)  # Checks for ADJECTIVES
            else:
                transDict["item"] = array[idx]   # Saves word as an ITEM if no ADJECTIVES found
                idx+1
                getCost(array,idx,transDict)
    elif idx+1 < len(array): # Stores for QUALIFIER
        transDict["qualifier"] = array[idx]  # Saves qualifier
        idx+=1
        # Checks for QUALIFIER-of-ITEM pattern 
        if idx+1 < len(array) and array[idx] == "of" and process.extractBests(lem.lemmatize(array[idx+1]), itemList, scorer=tsr, score_cutoff=95):
            idx+=1
            getItemFunction()
        # Checks for SERVICES
        elif process.extractBests(lem.lemmatize(array[idx]), servicesList, scorer=tsr, score_cutoff=90)==True or lem.lemmatize(array[idx])[-3:]== "ing":    
            transDict["service"] = array[idx]
            if idx+1 < len(array) and array[idx+1] == "of":  # Checks if "of" follows SERVICE
                idx+1
                serviceOf_Pattern(array, idx, transDict)
        elif array[idx] not in servicesList and idx+1 < len(array) and array[idx+1] == "of":  # Accounts for unknown services
            transDict["service"] = array[idx]
            transReview.append("Review: Confirm SERVICE")
            if idx+1 < len(array) and array[idx+1] == "of":
                idx+1
                serviceOf_Pattern(array, idx, transDict)
        elif process.extractBests(lem.lemmatize(array[idx]), itemList, scorer=tsr, score_cutoff=95):   # Checks for ITEM
            getItemFunction()
        else:     # Checks ADJECTIVES preceding the ITEM
            findAdjectives(array, idx, transDict)

# Handles the "SERVICE-of" pattern
def serviceOf_Pattern(array, idx, transDict, peopleArray, transReview, placesArray):# sourcery skip: low-code-quality

    # Function for repeat code
    def rentFunction():
        temp = getPlace(array,idx,placesArray)
        if temp != 0:
            idx = idx+temp
            getCost(array,idx,transDict)
        elif [x for x in array[idx:] if x[0].isdigit()]:  # Checks if digit follows near
            num = [x for x in array[idx:] if x[0].isdigit()]  
            if array.index(num[0])<4 :
                n = array.index(num[0])
                pName = ' '.join(array[idx:n+1])
                placesArray.append(pName)   # Assumes unknown PLACE
                transReview.append("Review: Confirm PLACE.")
                idx = n+1
                getCost(array,idx,transDict)
        else:
            pName = ' '.join(array[idx:])
            placesArray.append(pName)   # Assumes unknown PLACE
            transReview.append("Review: Confirm PLACE.")
            getCost(array,idx,transDict)

    if idx>=2 and lem.lemmatize(array[idx-2]) == "rent" and array[idx] not in possessiveList: # Checks if service is "rent"
        rentFunction()
    elif idx+1 < len(array) and array[idx] in possessiveList:  # checks for relations
        idx+=1
        # Checks for relation
        if process.extractBests(lem.lemmatize(array[idx]), relationsList, scorer=tsr, score_cutoff=95):
            relation = lem.lemmatize(array[idx])
            temp = None
            idx+=1
            # Checks for names
            if idx < len(array) and findName(array, idx, transDict) !=0:  
                temp = findName(array, idx, transDict)
                temp[0]["relations"] = relation
                peopleArray.append(temp[0])
                i = len(temp[0].split())
                idx += i
            # Saves unkown person if no name found
            if temp is None:
                person = peopleObject.copy()
                person["relations"] = relation
                person["firstName"] = "FNU"
                person["lastName"] = "LNU"
                peopleArray.append(person)
            # Checks for Item
            if idx < len(array) and process.extractBests(lem.lemmatize(array[idx]), itemList, scorer=tsr, score_cutoff=95):
                item = process.extractBests(lem.lemmatize(array[idx]), itemList, scorer=tsr, score_cutoff=95)
                transDict["item"] = item[0][0]
                i = len(item[0][0].split())
                idx += i
            else: # Saves unknown ITEM
                transDict["item"] = array[idx]
                transReview.append("Review: Confirm ITEM.")
                idx+=1
            getCost(array,idx,transDict)
    elif idx+1 < len(array) and array[idx] in ["a", "an"]:  # Checks for SERVICE-of-a pattern
        idx+=1
        if lem.lemmatize(array[idx-3]) == "rent":  # Checks if service is "rent"
            rentFunction()
        elif array[idx][0].isdigit() == True: # Checks if next value is a digit
            QQI_Pattern(array, idx, transDict, transReview,placesArray)  # Checks for QUANTITY-QUALIFIER-ITEM pattern
        elif process.extractBests(array[idx], itemList, scorer=tsr, score_cutoff=90):  # Checks if known ITEM
            item = process.extractBests(array[idx], itemList, scorer=tsr, score_cutoff=90)
            transDict["quantity"] = "1"
            transDict["item"] = item[0][0]
            i = len(item[0][0].split())
            idx += i
            getCost(array,idx,transDict)
        else:
            transDict["item"] = array[idx] # Assumes word is unknown ITEM
            transReview.append("Review: Confirm ITEM.")
    elif array[idx][0].isdigit() == True: # Checks if next value is a digit
        QQI_Pattern(array, idx, transDict, transReview,placesArray)  # Checks for QUANTITY-QUALIFIER-ITEM pattern
    else:
        findName(array, idx, transDict)

# Handles the "SERVICE-{a, an}" pattern
# *********** Needed: ADD "&" check after SERVICE *********** #
def serviceA_Pattern(array, idx, transDict, peopleArray, transReview, placesArray):
    # A helper function to get the item and/or adjectives
    def getItem():
        if process.extractBests(array[idx], itemList, scorer=tsr, score_cutoff=95):   # Gets Item
            item = process.extractBests(array[idx], itemList, scorer=tsr, score_cutoff=95)
            transDict["item"] = item[0][0]
            transDict["quantity"] = "1"
            i =len(item.split()) 
            idx = idx+i
            getCost(array,idx, transDict)
        elif process.extractBests(array[idx+1], itemList, scorer=tsr, score_cutoff=95):  # Accounts for 1 ADJECTIVE
            item = process.extractBests(array[idx+1], itemList, scorer=tsr, score_cutoff=95)
            transDict["item"] = item[0][0]
            transDict["quantity"] = "1"
            varientsArray = [array[idx]]
            transDict["varients"] = varientsArray
            i = len(item.split())+1
            idx = idx+i
            getCost(array,idx, transDict)
        elif idx+2 < len(array) and process.extractBests(array[idx+2], itemList, scorer=tsr, score_cutoff=95):  # Accounts for 2 ADJECTIVES
            item = process.extractBests(array[idx+2], itemList, scorer=tsr, score_cutoff=95)
            transDict["item"] = item[0][0]
            transDict["quantity"] = "1"
            varientsArray = [array[idx], array[idx+1]]
            transDict["varients"] = varientsArray
            i = len(item.split())+2
            idx = idx+i
            getCost(array,idx, transDict)
        
    while idx < len(array):    # Prevents out of bounds index increments
        if array[idx] in ["a", "an"]:  # Checks is SERVICE is followed by "of" or "a"
            idx+=1
            if process.extractBests(array[idx], itemList, scorer=tsr, score_cutoff=95):   # Checks for ITEM
                item = process.extractBests(array[idx], itemList, scorer=tsr, score_cutoff=95)[0][0]
                transDict["item"] = item
                transDict["quantity"] = "1"
                i = len(item.split()) 
                idx = idx+i
                getCost(array,idx, transDict)
            elif idx+2 < len(array) and array[idx+1] == "of":    # Accounts for QUALIFER, checks for "of"
                transDict["qualifier"] == array[idx]  # Stores QUALIFER
                transDict["quantity"] = "1"
                idx+=2
                getItem()   # Checks for ITEM and ADJECTIVES
            elif idx>1 and array[idx-2] == "rent":
                temp = getPlace(array,idx,placesArray)
                if temp != 0:
                    idx = idx+temp
                    getCost(array,idx,transDict)
                elif [x for x in array[idx:] if x[0].isdigit()]:  # Checks if digit follows near
                    num = [x for x in array[idx:] if x[0].isdigit()]  
                    if array.index(num[0])<4 :
                        n = array.index(num[0])
                        pName = ' '.join(array[idx:n+1])
                        placesArray.append(pName)   # Assumes unknown PLACE
                        transReview.append("Review: Confirm PLACE.")
                        idx = n+1
                        getCost(array,idx,transDict)
                else:
                    pName = ' '.join(array[idx:])
                    placesArray.append(pName)   # Assumes unknown PLACE
                    transReview.append("Review: Confirm PLACE.")
            elif idx+1 < len(array):     # Checks ADJECTIVES preceding the ITEM
                transDict["quantity"] = "1"
                findAdjectives(array, idx, transDict)
        elif array[idx] == "of":
            idx+=1
            serviceOf_Pattern(array, idx, transDict, peopleArray, transReview, placesArray)
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
            QQI_Pattern(array, idx, transDict, transReview,placesArray)  # Checks for QUANTITY-QUALIFIER-ITEM pattern
        elif process.extractBests(array[idx], itemList, scorer=tsr, score_cutoff=86):   # Checks for ITEM
                item = process.extractBests(array[idx], itemList, scorer=tsr, score_cutoff=86)[0][0]
                transDict["item"] = item
                i = len(item.split()) 
                idx = idx+i
                getCost(array,idx, transDict)
        elif findName(array, idx) != 0:
            temp = findName(array, idx)
            peopleArray.append(temp[0])
            idx = idx+temp[1]
            if process.extractBests(array[idx], itemList, scorer=tsr, score_cutoff=86):
                item = process.extractBests(array[idx], itemList, scorer=tsr, score_cutoff=86)[0][0]
                transDict["item"] = item
            elif len(array)>idx+2 and array[idx]=="to":
                idx+=1
                if getPlace(array,idx,placesArray) == 0:
                    placesArray.append(array[idx])   # Assumes unknown PLACE
                    transReview.append("Review: Confirm PLACE.")
        break

# Handles the "PERSON-for" pattern
def peopleFor_Pattern(array, transDict, transReview, placesArray):
    idx = array.index('for')  # Gets the array index for "for"
    array[idx] = ""   # Removes "for"

    # Helper function for retreiving ITEMS
    def getItemFunction():
        item = process.extractBests(lem.lemmatize(array[idx]), itemList, scorer=tsr, score_cutoff=95)
        transDict["item"] = item[0][0]
        i = len(item[0][0].split())
        idx = idx + i
        getCost(array,idx, transDict)

    if idx+1 == len(array): # Checks if next element is end of array
        transDict["item"] = array[idx+1]  # Stores Item
        transReview.append("Review Item")
    elif idx+2 < len(array) :
        idx+=1
        if array[idx] == "a":  # Checks if following word is "a"
            idx+=1
            # Checks for ITEM
            if process.extractBests(array[idx], itemList, scorer=tsr, score_cutoff=95):
                item = process.extractBests(array[idx], itemList, scorer=tsr, score_cutoff=95)[0][0]
                transDict["item"] = item
                i = len(item.split()) 
                idx = idx+i 
                getCost(array,idx, transDict)                
            elif lem.lemmatize(array[idx]) in qualifierList:  # Checks for Qualifier
                QAITTP_Pattern(array, idx, transDict) # Checks for QUALIFIER-{ADJECTIVE}*-ITEM-TOTAL_COST
            elif lem.lemmatize(array[idx]) in servicesList:
                transDict["service"] = array[idx] 
                idx = idx+1 
                getCost(array,idx, transDict)
            else:
                transDict["service"] = array[idx] 
                transReview.append("Review: Confirm SERVICE.")
                idx = idx+1 
                getCost(array,idx, transDict)
        if array[idx] == "interest" and array[idx+1] == "on":  # checks if "interest" follows
            array[idx+1] == ""     # Removes "on"
            transDict["item"] = "interest"  # Stores ITEM
        if array[idx][0].isdigit() == True:
            transDict["quanity"] = array[idx]
            if idx+2 < len(array) and lem.lemmatize(array[idx+1]) in qualifierList:
                idx+1
                QQI_Pattern(array, idx, transDict, transReview,placesArray)

# =========================================== #
#             "Begins" Functions              #
# =========================================== #

# Handles transactions begining with "Charge"/"Charges"
def beginsCharge(array, transDict, transReview, peopleArray, placesArray): # sourcery skip: low-code-quality
    idx = 0
    if idx+2 < len(array) and array[idx+1] == "on" and fuzz.ratio(lem.lemmatize(array[idx+2]), "Merchandise") >= 87:
        idx+2
        if idx == len(array)-1:
            transDict["item"] = "Charges on Merchandise"
        elif idx+1 < len(array) and array[idx+1][0].isdigit():   # Checks if next value is a digit
            idx+=1
            temp = getCost(array,idx, transDict)  # Checks for COST
            if temp == 0:
                QQI_Pattern(array, idx, transDict)   # checks for QUANTITY-QUALIFIER-ITEM pattern
        elif idx+2 < len(array) and array[idx+1] == "for":  # checks if "for" is next word
            idx+=1
            for_Keyword(array, idx, transDict, transReview, peopleArray)
    elif idx+1 < len(array) and array[idx+1][0].isdigit():   # Checks if next value is a digit
        idx+=1
        getCost(array,idx, transDict)  # Checks for COST      
    elif idx+1 < len(array) and findName(array, idx+1, transDict) !=0:
        temp = findName(array, idx, transDict)
        peopleArray.append(temp[0])
        idx+=temp[1]
        # Checks for SERVICES following names
        if idx < len(array) and (process.extractBests(lem.lemmatize(array[idx]), servicesList, scorer=tsr, score_cutoff=95)==True or lem.lemmatize(array[idx])[-3:]== "ing"):
            transDict["service"] = array[idx]
            idx+1
            if array[idx] in ["a", "an"]:
                idx+=1
                serviceA_Pattern(array, idx, transDict, peopleArray, transReview, placesArray)
            elif array[idx] == "of":
                idx+=1
                serviceOf_Pattern(array, idx, transDict, peopleArray, transReview, placesArray)
            elif array[idx] in ["&", "and"]:
                pass  # ******** ADD "&"/"and" function ******** #

# Handles transactions begining with "allowance"
def beginsAllowance(array, transDict, transReview, placesArray):
    idx = 0
    if array[idx]=="an":
        idx+=1

    if idx+1 < len(array) and array[idx]=="on":
        idx+=1
        if array[idx][0].isdigit() == True:
            QQI_Pattern(array, idx, transDict, transReview, placesArray)
        elif process.extractBests(array[idx], itemList, scorer=tsr, score_cutoff=87):
            item = process.extractBests(array[idx], itemList, scorer=tsr, score_cutoff=87)[0][0]
            transDict["item"] = item
            i = len(item.split())+1
            idx+=i
            getCost(array,idx, transDict)
        else:
            findAdjectives(array, idx, transDict)

# Handles transactions begining with "total"
def beginsTotal(array, transDict, transReview):
    # Skips transactions that consist of only "total"
    if len(array) == 1 and array[0] == "total":
        return
    # Skips transactions that consist of only "total tobacco"
    if len(array) == 2 and process.extractBests(array[1], "tobacco", scorer=tsr, score_cutoff=90):
        return
    # Skips transactions that start with "total carried"
    if len(array)>1 and array[1] == "carried":
        return

    if len(array) == 2 and array[1] in ["sterling", "currency"]:
        transDict["item"] = "Total"
    elif len(array)>2 and process.extractBests(array[1], "tobacco", scorer=tsr, score_cutoff=90) and array[2][0].isdigit == True:
        transDict["quantity"] = array[2]
        idx = 3
        if len(array)>3 and array[idx] in ["at","is"]:
            transDict["qualifer"] = "pound"
            getCost(array, idx, transDict)
        elif len(array)>4 and array[idx+1] in ["at","is"]:
            transDict["qualifer"] = array[3]
            idx = 4
            getCost(array, idx, transDict)
    elif len(array) < 6 and ("account" in array or "accounts" in array):
        transDict["item"] = "Total"

# Handles transactions begining with "subtotal" or "sum"
def beginsSubtotalSum(array):
    # Skips transactions that begin with "sum being" or "sum from"
    if array[0] == "sum" and array[1] in ["being", "from"]:
        if array[1]=="from":
            array[1]==""
        return
    # Skips transactions that consist of only "subtotal"
    if len(array) == 1 and array[0] == "subtotal":
        return
    # Skips transactions that consist of only "subtotal tobacco"
    if len(array) == 2 and array[0] == "subtotal" and process.extractBests(array[1], "tobacco", scorer=tsr, score_cutoff=90):
        return

# Handles transactions begining with "ballance"/ "balance"
def beginsBalance(array,transDict):
    array[0] == ""   # Removes "balance", as it is a keyword
    if array[1] == "carried":    
        transDict["item"] = "Total"
    elif array[1] == "due":   # Handles transactions begining with "balance due"
        if array[3] == "contra" or array[2] == "contra":
            transDict["item"] = "Contra Balance"
        elif array[2] == "carried":
            transDict["item"] = "Total"
        else:
            transDict["item"] = "Balance Due"
    elif array[1] == "from" and array[2] == "liber" :   # Handles transactions begining with "balance from liber"
        array[1] == ""  # Removes "from", as it is a keyword
        transDict["item"] = "Balance from"
    elif array[1] == "to" and array[2] == "liber" :   # Handles transactions begining with "balance to liber"
        array[1] == ""  # Removes "to"
        transDict["item"] = "Balance to"
    elif "contra" in array:
        idx = array.index("contra")
        if len(array)>idx-1 and array[idx-1] in ["per","charged"]:
            transDict["item"] = "Contra Balance"

# Handles transactions begining with "expense"/"expence"
def beginsExpense(array,idx,transDict,transReview, peopleArray, placesArray):
   # Helper function to excute repeated code
    def helper(idx):
        if len(array)>idx and array[idx] == "for" :
            for_Keyword(array, idx, transDict, transReview, peopleArray,placesArray)
        elif len(array)>idx and array[idx][0].isdigit() == True:
            QQI_Pattern(array, idx, transDict, transReview)
        elif len(array)>idx and array[idx] == "a":
            QQI_Pattern(array, idx, transDict, transReview)
        elif len(array)>idx+1 and array[idx]=="its" and fuzz.token_set_ratio(array[idx+1],"value")>90:
            idx+=2
            getCost(array,idx,transDict,transReview, placesArray, peopleArray)
        elif len(array)>idx+1 and array[idx] == "of":
            idx+=1
            if process.extractBests(array[idx], itemList, scorer=tsr, score_cutoff=85):
                item = process.extractBests(array[idx], itemList, scorer=tsr, score_cutoff=85)[0][0]
                transDict["item"] = item
                i = len(item.split())
                idx = idx+i
                getCost(array,idx,transDict,transReview, placesArray, peopleArray)
            elif process.extractBests(lem.lemmatize(array[idx]), servicesList, scorer=tsr, score_cutoff=95)==True or lem.lemmatize(array[idx])[-3:]== "ing":
                idx+=1
                if len(array)>idx+1 and array[idx] in ["a","an","the"]:
                    transDict["service"] = f"{array[idx-1]} {array[idx]} {array[idx+1]}"
                    idx+=2
                    getCost(array,idx,transDict,transReview, placesArray, peopleArray)
                else:    
                    transDict["service"] = f"{array[idx-1]}"
                    getCost(array,idx,transDict,transReview, placesArray, peopleArray)
            elif array[idx] in ["a","an"]:
                serviceA_Pattern(array, idx, transDict, peopleArray, transReview, placesArray)

    if len(array)>idx+1 and array[idx] == "for":
        array[idx] = ""  # Removes "for"
        idx+=1  
        temp = findName(array, idx)

        if temp != 0:
            peopleArray.append(temp[0])
            idx = idx+temp[1]
            helper(idx)
        elif len(array)>idx+2 and array[idx+1] in ["for","its","a","of"] :
            accountName = peopleObject.copy()
            accountName["account"] = f"{array[idx]} Expenses"
            peopleArray.append(accountName)
            idx+=1
            helper(idx)
        elif len(array)>idx+3 and array[idx+2] ["for","its","a"] :
            accountName = peopleObject.copy()
            accountName["account"] = f"{array[idx]} {array[idx+1]} Expenses"
            peopleArray.append(accountName)
            idx+=2
            helper(idx)
    else:
        helper(idx)
    
# Handles transactions begining with "account"
def beginsAccount(array,transDict,transReview, peopleArray, placesArray):
    array[0] == ""  # Removes "account", as it'a also a keyword
    idx = 1
   # Helper function to excute repeated code
    def helper(idx):
        if len(array)>idx and array[idx] == "for" :
            array[idx] = ""  # Removes "for"
            for_Keyword(array, idx, transDict, transReview, peopleArray,placesArray)
        elif array[idx][0].isdigit() == True:
            if getCost(array,idx,transDict) == 0:
                QQI_Pattern(array, idx, transDict, transReview)
        

    if len(array)>idx+1 and array[idx] == "of":
        idx+=1  
        temp = findName(array, idx)
        if len(array)>idx+2 and temp == 0 and array[idx+1] == "for" :
            accountName = peopleObject.copy()
            accountName["account"] = f"{array[2]} Expenses"
            peopleArray.append(accountName)
            array[idx+1] = ""  # Removes "for"
            idx+=1
            helper(idx)
        elif len(array)>idx+1 and fuzz.ratio(lem.lemmatize(array[idx+1]), "furniture") >= 90:
            transDict["item"] = f"{array[idx]} Furniture"
            idx+=2
            helper(idx)
        elif len(array)>idx+3 and temp == 0 and array[idx+2] == "for" :
            accountName = peopleObject.copy()
            accountName["account"] = f"{array[2]} {array[3]}"
            peopleArray.append(accountName)
            idx+=2
            helper(idx)
        elif temp != 0:
            peopleArray.append(temp[0])
            idx = temp[1]+1
            helper(idx)

# Handles transactions begining with a "sterling"/"currency"
def beginsSterlingCurrency(array,transDict,transReview, peopleArray, placesArray):
    # Saves the initial currency
    if fuzz.ratio(array[idx], "currency") > 88:
        initial = "currency"
    elif fuzz.ratio(array[idx], "sterling") > 88:
        initial = "sterling"

    def checkForAt():   # Helper function for repeated code
        if len(array)>idx+1 and array[idx] == "at" and array[idx+1][0].isdigit==True:
            array[idx] == ""   # Removes "at"
            transDict["quantity"] = array[idx+1]
            idx+=2
            if len(array)>idx and array[idx]=="percent":
                transDict["qualifier"] = "Percent"
            else:
                transDict["qualifier"] = "Percent"
                transReview.append("Review: Confirm QUANTITY and QUALIFIER.")
 
    idx=1# Sets index
    if len(array)> idx and array[idx] == "for":   # Checks for "for"
        idx+=1

    while idx < len(array):
        if array[idx] == "the":  # Acounts for if "the" follows
            idx+=1
            if len(array)>idx+1 and array[idx] == "contra":  # Acounts for if "the contra" follows
                idx+=1
        
        if array[idx][0].isdigit()==True:
            num = array[idx]
            idx+=1
            # Checks is "tobacco" is in the array
            if process.extractBests("tobacco", array[idx:], scorer=fuzz.token_set_ratio, score_cutoff=85):
                QQI_Pattern(array, idx-1, transDict, transReview)
            elif len(array)>idx+2 and array[idx+1]=="per" and array[idx+2]=="contra":
                array[idx+1]= ""  # Removes "per"
                transDict["item"] = f"{array[idx]} to {initial} per Contra"
                transDict["totalCost"] = num
                idx+=3
                checkForAt()
            elif fuzz.ratio(array[idx], "currency") > 88  or fuzz.ratio(array[idx], "sterling") > 88:
                transDict["item"] = f"{array[idx]} to {initial}"
                transDict["totalCost"] = num
                idx+=1
                checkForAt()
        
# Handles transactions begining with a "Contra Balance"
def beginsContraBalance(array,transDict,transReview, peopleArray, placesArray):
    transDict["item"] = "Contra Balance"
    #Checks if "to" is in the transaction
    if "to" in array[2:]:
        idx = array.index("to")
        array[idx] = ""   # removes "to"
        idx+=1
        if len(array)>idx:
            temp = findName(array, idx)
            if temp == 0 and getPlace(array,idx,placesArray) == 0:
                unknown = peopleObject.copy()
                unknown["firstName"] = "FNU"
                unknown["lastName"] = "LNU"
                peopleArray.append(unknown)
                transReview.append("Review: Unknown person found.")
            elif temp != 0:
                peopleArray.append(temp[0])

# Handles transactions begining with a PLACE
def beginsPlace(array, idx, transDict,transReview, peopleArray, placesArray): # sourcery skip: low-code-quality

    if len(array)>idx+2 and array[idx] == "cash" and array[idx+1] == "paid":
        idx+=2
        if len(array)>idx+1 and array[idx] == "by":
            array[idx] = ""   # Removes "by"
            idx+=1
        temp = findName(array, idx) 
        if temp != 0:
            peopleArray.append(temp[0])
    elif process.extractBests(lem.lemmatize(array[idx]), servicesList, scorer=tsr, score_cutoff=88)==True or lem.lemmatize(array[idx])[-3:]== "ing":
        idx+=1
        serviceA_Pattern(array, idx, transDict, peopleArray, transReview, placesArray)
    elif len(array)>idx+3 and array[idx] in possessiveList and array[idx+2] == "of":
        idx+=3
        if process.extractBests(lem.lemmatize(array[idx]), servicesList, scorer=tsr, score_cutoff=88)==True or lem.lemmatize(array[idx])[-3:]== "ing":
            transDict["service"] = array[idx]  # Stores service
            idx+=1
            serviceA_Pattern(array, idx, transDict, peopleArray, transReview, placesArray)
        elif len(array)>idx+1 and array[idx] in ["a","an"]:
            serviceA_Pattern(array, idx, transDict, peopleArray, transReview, placesArray)
        elif len(array)>idx+2 and array[idx+1] in ["of","a","an"]:
            transDict["service"] = array[idx]  # Stores unknown service
            transReview.append("Review: Confirm SERVICE.")
            idx+=1
            serviceA_Pattern(array, idx, transDict, peopleArray, transReview, placesArray)
    elif len(array)>idx+3 and array[idx] == "for":
        if process.extractBests(lem.lemmatize(array[idx]), servicesList, scorer=tsr, score_cutoff=88)==True or lem.lemmatize(array[idx])[-3:]== "ing":
            idx+=1
            serviceA_Pattern(array, idx, transDict, peopleArray, transReview, placesArray)
    elif array[idx][0].isdigit() == True:
        temp = getCost(array,idx,transDict)
        if temp == 0:
            QQI_Pattern(array, idx, transDict, transReview)

# Handles transactions begining with a "cash"
def beginsCash(array, idx, transDict,transReview, peopleArray, placesArray, otherItems): 
    # Sets transaction ITEM to "cash" and creates 2nd transaction object
    transDict["item"] = "Cash"
    item2 = transactionObject.copy()

    if len(array) == 1:
        transDict["item"] = "Cash"
        return
    else:
        idx = 1

    # Adds "Cash Account" to accounts
    newAccount = peopleObject.copy()
    newAccount["account"] = "Cash Account"
    peopleArray.append(newAccount)

    # Helper function for repeat code (checks if item 2 found)
    def checkItem2():
        if item2 != transactionObject:
            otherItems.append(item2)
            transDict["includedItems"] = otherItems

    # Helper function for repeat cost code 
    def checkIfDigit():
        if array[idx][0].isdigit()==True:
            getCost(array,idx,transDict)

    # Helper function for repeat code (checks for unknown/new place name)
    def placeName():
        n = array.index(temp[0])
        pName = ' '.join(array[idx:n+1])
        placesArray.append(pName)   # Assumes unknown PLACE
        transReview.append("Review: Confirm PLACE.")
        idx = array.index(temp[0])+1

    while len(array) > idx:
        if findName(array, idx) != 0:  # Checks for PERSON
            temp = findName(array, idx)
            peopleArray.append(temp[0])
            idx = idx+temp[1]
            if fuzz.ratio(lem.lemmatize(array[idx]), "expense") >= 90 or fuzz.ratio(array[idx], "expence") >= 90:
                idx+=1
                if array[idx][0].isdigit()==True:
                    QQI_Pattern(array, idx, transDict, transReview, placesArray, peopleArray)
        elif process.extractBests(lem.lemmatize(array[idx]), servicesList, scorer=tsr, score_cutoff=90)==True or lem.lemmatize(array[idx])[-3:]== "ing":
            item2["service"] = array[idx]
            idx+=1
            serviceA_Pattern(array, idx, item2, peopleArray, transReview, placesArray)
            checkItem2()
        elif array[idx] == "paid": # Checks for "paid"
            array[idx] = ""  # Removes "paid"
            idx+=1
            beginsCashPaid(array, idx, transDict,transReview, peopleArray, placesArray, otherItems)
        elif fuzz.ratio(lem.lemmatize(array[idx]), "expense") >= 90 or fuzz.ratio(array[idx], "expence") >= 90:  # Checks for "expense"/"expence"
            array[idx] = ""    # Removes "expense"/"expence"
            idx+=1
            if array[idx] in ["to","at"]:  # Checks for "to"/"at"
                array[idx] = ""    # Removes "to"/"at"
                idx+=1
                temp =  getPlace(array,idx,placesArray)  # Checks for PLACE
                if temp !=0:
                    idx += temp
                    if array[idx]=="to":
                        idx+=1
                        # Checks for SERVICE
                        if process.extractBests(lem.lemmatize(array[idx]), servicesList, scorer=tsr, score_cutoff=90)==True or lem.lemmatize(array[idx])[-3:]== "ing":
                            item2["service"] = array[idx]
                            idx+=1
                            serviceA_Pattern(array, idx, item2, peopleArray, transReview, placesArray)
                            checkItem2()
                    else:
                        getCost(array,idx,transDict)
                elif [x for x in array[idx:] if x[0].isdigit()] != []:  # If PLACE not found checks if digit follows near
                    temp = [x for x in array[idx:] if x[0].isdigit()]  
                    if array.index(temp[0])<4 :
                        placeName()
                        getCost(array,idx,transDict)
                elif [x for x in array[idx:] if x=="to"] != []:   # If PLACE not found checks if "to" follows near
                    temp = [x for x in array[idx:] if x=="to"]  
                    if array.index(temp[0])<4 :
                        placeName()
                        if process.extractBests(lem.lemmatize(array[idx]), servicesList, scorer=tsr, score_cutoff=90)==True or lem.lemmatize(array[idx])[-3:]== "ing":
                            item2["service"] = array[idx]
                            idx+=1
                            serviceA_Pattern(array, idx, item2, peopleArray, transReview, placesArray)
                            checkItem2()
                else:
                    pName = ' '.join(array[idx:])  # Assumes unknown PLACE
                    placesArray.append(pName)
                    transReview.append("Review: Confirm PLACE.")
            elif array[idx] == "of":  # Checks for "of"
                array[idx] = ""    # Removes "of"
                idx+=1
                if process.extractBests(lem.lemmatize(array[idx]), servicesList, scorer=tsr, score_cutoff=90)==True or lem.lemmatize(array[idx])[-3:]== "ing":
                    item2["service"] = array[idx]
                    idx+=1
                    serviceA_Pattern(array, idx, item2, peopleArray, transReview, placesArray)
                    checkItem2()
            elif array[idx] == "by":   # Checks for "by"
                array[idx] = ""    # Removes "by"
                idx+=1
                name = findName(array, idx)
                if name !=0:
                    peopleArray.append(name[0])
                    idx = idx+name[1]
                    if array[idx] == "at":
                        idx+=1
                        if getPlace(array,idx,placesArray) !=0:
                            idx = idx + getPlace(array,idx,placesArray)
                            if array [idx][0].isdigit()==True:
                                getCost(array,idx,transDict)
                            elif array [-1][0].isdigit()==True:
                                getCost(array,idx,transDict)
                                transReview.appaend("Review: Confirm COST. ")
        elif array[idx] == "per":   # Checks for "per"
            array[idx] = ""  # Removes "per"
            idx+=1
            temp = per_Keyword(array, transReview, peopleArray, placesArray)
            if temp !=0:
                idx = idx+temp
                getCost(array,idx,transDict)
        elif array[idx] == "for":   # Checks for "for"
            array[idx] = ""  # Removes "for"
            idx+=1
            if array[idx][0].isdigit()==True:
                QQI_Pattern(array, idx, item2, transReview, placesArray, peopleArray)
                checkItem2()
            elif array[idx] in ["a","an"]:
                serviceA_Pattern(array, idx, item2, peopleArray, transReview, placesArray)
                checkItem2()
            elif process.extractBests(lem.lemmatize(array[idx]), servicesList, scorer=tsr, score_cutoff=90)==True or lem.lemmatize(array[idx])[-3:]== "ing":
                item2["service"] = array[idx]
                idx+=1
                serviceA_Pattern(array, idx, item2, peopleArray, transReview, placesArray)
                checkItem2()
        elif fuzz.ratio(array[idx], "advanced") > 86:   # Checks for "advanced"
            idx+=1
            temp = findName(array, idx)  # Checks for name
            if temp !=0:   
                peopleArray.append(temp[0])   # Stores found name
                idx = idx+temp[1]
                if lem.lemmatize(array[idx]) in relationsList:  # Checks for relation (girl/boy/son/mother/father/etc) if name found
                    idx+=1
                    name = findName(array, idx)   # Checks of name of relation
                    if name !=0:
                        peopleArray.append(name[0])  # Stores name of found relation
                        idx = idx+name[1]
                        checkIfDigit()   # Checks for COST if name of relation IS found
                    else:
                        checkIfDigit() # Checks for COST if name of relation NOT found
                else:
                    checkIfDigit()   # Checks for COST if NO relation is found
            # checks for "your/his/her-RELATION" pattern         
            elif len(array)>idx+1 and array[idx] in possessiveList and lem.lemmatize(array[idx+1]) in relationsList:
                idx+=2
                name = findName(array, idx)   # Checks of name of relation
                if name !=0:
                    peopleArray.append(name[0])   # Stores name of found relation
                    idx = idx+name[1]
                    checkIfDigit()  # Checks for COST if name of relation IS found
                else:
                    checkIfDigit()   # Checks for COST if name of relation NOT found
        elif len(array)>idx+1 and array[idx] == "received" and array[idx+1] == "from":   # Checks for "received from "
            array[idx+1] = ""    # Removes "from"
            idx+=2
            temp = findName(array, idx)
            if temp != 0:
                peopleArray.append(temp[0]) 
                idx = idx+temp[1]
                if array[idx] == "for":
                    idx+=1
                    serviceA_Pattern(array, idx, item2, peopleArray, transReview, placesArray)
            else:
                temp =  getPlace(array,idx,placesArray)
                if temp != 0:
                    idx = idx+temp
                    if array[idx] == "for":
                        idx+=1
                        serviceA_Pattern(array, idx, item2, peopleArray, transReview, placesArray)
        elif fuzz.ratio(array[idx], "lacking") > 90:   # Checks for "lacking"
            return
        elif fuzz.ratio(array[idx], "account") > 90:   # Checks for "account"
            array[idx] = ""  # Removes "account"
            idx+=1
            getCost(array,idx,transDict)
        elif array[idx] == "of":    # Checks for "of"
            idx+=1
            temp = findName(array, idx)
            if temp != 0:
                peopleArray.append(temp[0])
                idx+=1
                getCost(array,idx,transDict)
        elif process.extractBests("club", array, scorer=tsr, score_cutoff=88):   # Checks if "club" is in the array
            item2["item"] = "Club Costs"
            idx = array.index(process.extractBests("club", array, scorer=tsr, score_cutoff=88)[0][0])+1
            if array[idx] == "at":  # Checks for "at"
                array[idx] = ""   # Removes "at"
                idx+=1
                temp = getPlace(array,idx,placesArray)
                if temp!=0:
                    idx = idx+temp
                    getCost(array,idx,transDict)
        break

    # Moves TOTAL_COST from Item2 to "Cash" item
    if transDict["totalCost"] == "" and item2["totalCost"] != "":
        transDict["totalCost"] = item2["totalCost"]
        item2["totalCost"] = ""

# Handles transactions begining with a "cash paid"
def beginsCashPaid(array, idx, transDict,transReview, peopleArray, placesArray, otherItems):
    # Sets transaction ITEM to "cash" and creates 2nd transaction object
    transDict["item"] = "Cash"
    item2 = transactionObject.copy()

    # Helper function for repeat code (checks if item 2 found)
    def checkItem2():
        if item2 != transactionObject:
            otherItems.append(item2)
            transDict["includedItems"] = otherItems
        
    while len(array) > idx:
        if findName(array, idx) != 0:  # Checks for PERSON
            temp = findName(array, idx)
            peopleArray.append(temp[0])
            idx = idx+temp[1]
            if fuzz.ratio(lem.lemmatize(array[idx]), "expense") >= 90 or fuzz.ratio(array[idx], "expence") >= 90:  # Checks if "expense"/"expence" follows
                idx+=1
                if array[idx][0].isdigit()==True:  # Checks for QUALITY-QUANTITY-ITEM pattern
                    QQI_Pattern(array, idx, item2, transReview, placesArray, peopleArray)
                    checkItem2()
                elif array[idx] == "of":
                    idx+=1
                    if process.extractBests(lem.lemmatize(array[idx]), servicesList, scorer=tsr, score_cutoff=90)==True or lem.lemmatize(array[idx])[-3:]== "ing":
                        item2["service"] = array[idx]
                        idx+=1
                        serviceA_Pattern(array, idx, item2, peopleArray, transReview, placesArray)
                        checkItem2()
            elif array[idx] == "for":
                for_Keyword(array, idx, item2, transReview, peopleArray,placesArray)
                checkItem2()
            elif array[idx] == "at":
                array[idx] = ""    # Removes "at"
                idx+=1
                if getPlace(array,idx,placesArray) == 0:
                    placesArray.append(array[idx])
                    transReview.append("Review: Confirm PLACE.")
        elif array[idx][0].isdigit() == True:
            QQI_Pattern(array, idx, item2, transReview, placesArray, peopleArray)
            checkItem2()
        # Checks for SERVICE
        elif process.extractBests(lem.lemmatize(array[idx]), servicesList, scorer=tsr, score_cutoff=90)==True or lem.lemmatize(array[idx])[-3:]== "ing":
            item2["service"] = array[idx]
            idx+=1
            serviceA_Pattern(array, idx, item2, peopleArray, transReview, placesArray)
            checkItem2()
        elif len(array)>idx+1 and array[idx+1] in ["of","a","an"]:  # Checks for unknown SERVICE
            item2["service"] = array[idx]
            transReview.append("Review: Confirm SERVICE.")
            idx+=1
            serviceA_Pattern(array, idx, item2, peopleArray, transReview, placesArray)
            checkItem2()
        elif array[idx] in possessiveList:  # Checks for "your"/"his"/"her"/etc
            idx+=2
            if array[idx][0].isdigit() == True:  # Checks for COST
                getCost(array,idx,transDict)
            elif findName(array, idx) != 0:   # Checks for PERSOM
                temp = findName(array, idx)
                peopleArray.append(temp[0])
                idx = idx+temp[1]
                getCost(array,idx,transDict)
        elif array[idx] == "for":
            for_Keyword(array, idx, item2, transReview, peopleArray,placesArray)
            checkItem2()
        break

    # Moves TOTAL_COST from Item2 to "Cash" item
    if transDict["totalCost"] == "" and item2["totalCost"] != "":
        transDict["totalCost"] = item2["totalCost"]
        item2["totalCost"] = ""

# Handles transactions begining with an ITEM
def beginsItem(array,idx,transDict,transReview, peopleArray, placesArray, otherItems, item):

    #Checks if ITEM only and adds quantity as "1"
    if len(array) == idx+1:
        transDict["quantity"] = "1"
        return
    
    # Removes "on hand" phrase
    if "hand" in array:
        index = array.index("hand")
        if index>0 and array(index-1)=="on":
            array.pop(index)
            array.pop(index-1)

    while len(array) > idx:
        # Checks if next word is "at"
        if array[idx] == "at":
            x = getCost(array,idx,transDict)
            if x == 0 or (transDict["unitCost"] == "" and transDict["totalCost"] == ""):
                getPlace(array,idx,placesArray)
            array[idx] = ""  # Removes "at"
        elif len(array)>idx+1 and array[idx][0].isdigit() and lem.lemmatize(array[idx+1]) in qualifierList:
            transDict["quantity"] = array[idx]
            transDict["qualifier"] = lem.lemmatize(array[idx+1])
            idx+=2
            getCost(array,idx,transDict)
        elif array[idx] == "on":
            array[idx] = ""   # Removes "on"
            idx+=1
            if len(array)>idx+3 and array[idx+1]=="at" and array[idx+2].isdigit():
                transDict["item"] = f"{item} on {array[idx]}"
                uc = 100 + int(array[idx+2])
                transDict["unitCost"] = f"{uc}"
                idx+=3
                if len(array)>idx+1 and array[idx].isalpha():
                    idx+=1
                getCost(array,idx,transDict)
            else:
                getPlace(array,idx,placesArray)
        elif array[idx][0].isdigit():
            getCost(array,idx,transDict)
        elif array[idx] == "from":
            x = getPlace(array,idx,placesArray)
            if x != 0:
                idx+=x
                if array[idx] == "to":
                    y = getPlace(array,idx,placesArray)
                    idx+=y
                getCost(array,idx,transDict)
        elif len(array)>idx+1 and fuzz.token_set_ratio(array[idx],"received ")>90 and array[idx+1] in ["per", "by"]:
            idx+=2
            if array[idx] == "the":
                idx+=1
            temp = getPlace(array,idx,placesArray)
            if temp !=0:
                if array[idx-1] == "the":
                    array[idx-2] = ""  # Removes "per"/"by"
                else:
                    array[idx-1] = ""  # Removes "per"/"by"
                idx = idx+temp
                if array[idx] == "from":
                    idx+=1
                    place = getPlace(array,idx,placesArray)
                    if place !=0:
                        array[idx-1] = ""  # Removes "from"
                        idx = idx+place
                        getCost(array,idx,transDict,transReview, placesArray, peopleArray)
                elif array[idx] == "per":
                    idx+=1
                    person = findName(array, idx)
                    if person !=0:
                        array[idx-1] = ""  # Removes "per"
                        peopleArray.append(person[0])
                        idx = idx+person[1]
                        getCost(array,idx,transDict,transReview, placesArray, peopleArray)
                    elif array[idx] == "the":
                        idx+=1
                        place = getPlace(array,idx,placesArray)
                        if place !=0:
                            array[idx-2] = ""  # Removes "per"
                            idx = idx+place
                            getCost(array,idx,transDict,transReview, placesArray, peopleArray)
            else:
                person = findName(array, idx)
                if person !=0:
                    if array[idx-1] == "the":
                        array[idx-2] = ""  # Removes "per"/"by"
                    else:
                        array[idx-1] = ""  # Removes "per"/"by"
                    peopleArray.append(person[0])
                    idx = idx+person[1]
                    getCost(array,idx,transDict,transReview, placesArray, peopleArray)

# Handles transactions begining with a PERSON name or profession
def beginsPerson(array,idx,transDict,transReview, peopleArray, placesArray, otherItems):
    if len(array) == idx+1:
        transDict["item"] = "Cash"
        return

    # Removes the word "the" from the array
    array = list(filter(("the").__ne__, array))

    if len(array)>idx+3 and array[idx] == "on" and array[idx+1] == "account" and array[idx+2] == "of":
        idx+=3
        name = findName(array, idx)
        if name != 0:
            peopleArray.append(name[0])
            idx = idx+name[1]

    while len(array) > idx:
        if array[idx].isdigit()==True:
            if len(array)>idx+1 and lem.lemmatize(array[idx+1]) in qualifierList:
                QQI_Pattern(array, idx, transDict, transReview, placesArray, peopleArray)
            else:
                getCost(array,idx,transDict)
        elif process.extractBests(lem.lemmatize(array[idx]), servicesList, scorer=tsr, score_cutoff=95)==True or lem.lemmatize(array[idx])[-3:]== "ing":
            idx+=1
            serviceA_Pattern(array, idx, transDict, peopleArray, transReview, placesArray)
        elif array[idx] == "for":
            for_Keyword(array, idx, transDict, transReview, peopleArray,placesArray)
        elif array[idx] == "off" and "nett" in array[idx:]:
            idx+=1
            if "nett" in array:
                nIndex = array.index("nett")+1
            if "net" in array:
                nIndex = array.index("net")+1
            
            if len(array)>nIndex and array[idx].isdigit()==True and array[nIndex].isdigit()==True:
                quantity = int(array[nIndex]) - int(array[idx])
                transDict["quantity"] = quantity
                idx+=1
                nIndex+=1
            
                if len(array)>nIndex and lem.lemmatize(array[nIndex]) in qualifierList:
                    transDict["qualifier"] = lem.lemmatize(array[nIndex])
                    nIndex+=1
                    if process.extractBests(array[nIndex], itemList, scorer=tsr, score_cutoff=80):
                        item = process.extractBests(array[nIndex], itemList, scorer=tsr, score_cutoff=80)[0][0]
                        transDict["item"] = item
                        i = len(item.split())
                        nIndex = nIndex+i
                        getCost(array,idx,transDict)
                elif lem.lemmatize(array[idx]) in qualifierList:
                    transDict["qualifier"] = lem.lemmatize(array[idx])
                    if process.extractBests(array[nIndex], itemList, scorer=tsr, score_cutoff=80):
                        item = process.extractBests(array[nIndex], itemList, scorer=tsr, score_cutoff=80)[0][0]
                        transDict["item"] = item
                        i = len(item.split())
                        nIndex = nIndex+i
                        getCost(array,idx,transDict)
                else:
                    transDict["item"] = "Tobacco"
                    transDict["qualifier"] = "Pound"
                    transReview.append("Review: Confirm ITEM and QUALIFIER.")
        elif len(array) > idx+1 and array[idx]=="the" and fuzz.token_set_ratio(array[idx+1], "ballance")>87:
            transDict["item"] = "Balance from"
            array[idx] = ""
            idx+=2
            if len(array) > idx and array[idx] == "of":
                idx+=1
                if array[idx] in possessiveList:
                    idx+=1
                if len(array) > idx+1 and array[idx+1]=="account":
                    array[idx+1] = "" # Removes "account"
                    newPplDict = peopleObject.copy()   # Initializes new people dictionary
                    newPplDict["account"] = f"{array[idx]} Account" # Saves Account Name
                    transReview.append("Review: ACCOUNT name.")


            





        pass
    pass       
            
# =========================================== #
#             Keyword Functions               #
# =========================================== #

# Handles the "per" keyword
def per_Keyword(array, transReview, peopleArray, placesArray):  
    if index is None:  # Checks if index id given
        index = array.index('per')  # Gets the array index of "per"

    pplDict = 0   # Initializing variable
    if index+1 < len(array):    # Prevents out of bounds index increments
        index+=1
        if len(array)>index+1 and array[index] == "the":   # Checks if next word is "the"
            index+1
            pplDict = findName(array, index)   # Looks for profession/person
            if pplDict == 0:      # If no person/profession found, saves next word as a place
                temp = getPlace(array,index,placesArray)
                if temp == 0:
                    placesArray.append(array[index])
                    transReview.append("Review places")
        elif index+1 < len(array) and lem.lemmatize(array[index]) in relationsList:	 # Checks if word is in relationList
            index+=1
            pplDict = findName(array, index)
        elif index+2 < len(array) and lem.lemmatize(array[index+1]) in relationsList:    # accounts for if possessives precede the relation
            index+=2
            pplDict = findName(array, index)
        else:
            pplDict = findName(array, index)
            
    if pplDict != 0:   # Checks if person was found
        peopleArray.appand(pplDict[0])   # Stores name
        return pplDict[1]
    else:
        return 0

# Handles the "from" keyword
def from_Keyword(array, transReview, peopleArray, placesArray):  
    index = array.index('from')  # Gets the array index of "from"

    index+=1  # Increments index
    while len(array)>index:  # Prevents out of bounds index increments 
        if array[index] == "the":   # Checks for "the"
            index+=1
            temp = getPlace(array,index,placesArray)  # Checks for PLACE
            if temp == 0:
                person = findName(array, index)   # Checks for PERSON if PLACE not found
                if person == 0:      # If no PERSON is found, saves word as a place
                    placesArray.append(array[index])
                    transReview.append("Review: Confirm PLACE name.")
        elif index+1 < len(array) and lem.lemmatize(array[index]) in relationsList:	 # Checks if word is in relationList
            index+=1
            person = findName(array, index)
        elif index+2 < len(array) and lem.lemmatize(array[index+1]) in relationsList:    # accounts for if possessives precede the relation
            index+=2
            person = findName(array, index)
        else:
            placesArray.append(array[index])  # If no known PERSON or PLACE is found, saves word as a place
            transReview.append("Review: Confirm PLACE name.")
                
        if person != 0:   # Checks if person was found
            peopleArray.appand(person[0])   # Stores name
        
        return

# Handles the "balance" keyword
def balance_Keyword(array, transDict,transReview, placesArray, peopleArray):
    # Gets the array index for "balance"/"ballance"
    keyword =  process.extractBests(lem.lemmatize("balance"), array, scorer=tsr, score_cutoff=87)
    idx = array.index(keyword)  # Gets the array index of "balance"
        
    # Removes other keywords attached to "balance"   
    if idx > 0 and array[idx-1] == "the":
        array[idx-1] = ""
        if idx > 1 and array[idx-2] == "for":
            array[idx-2] = ""
        transDict["item"] = "balance from"
    if len(array)>idx+1  and array[idx+1] == "of":
        array[idx+1] = ""
        transDict["item"] = "balance from"
    if len(array)>idx+1 and array[idx+1].isdigit():
        getCost(array,idx,transDict,transReview, placesArray, peopleArray)

# Handles the "on the" keyword pair
def onThe_Keywords(array,idx1,idx2, placesArray, transReview):
    array[idx1] = ""  # Removes "on"/"in"
    array[idx2] = ""  # Removes "the"
    
    if idx2 < len(array):
        idx2+=1
        if getPlace(array, idx2, placesArray) == 0:
            placesArray.append(array[idx2])
            transReview.append("Review: Confirm place name.")
    
# Handles the "charge on/of" keyword pattern
def charge_Keyword(array, transDict, transReview):
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

# Handles the "charged" keyword
def charged_Keyword(array):
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

# ******** FINISH this function ******** #
# EX: Ballance from Liber A including 15/:  paid an Express from Alexandria <...> the Night 
def paid_Keyword(array):
    idx = array.index('paid')
    if idx > 0:
        pass  # Look for cost
    if len(array)>idx+1 and array[idx+1] in ["a","an"]:
        pass # Look for ITEM, if not exist idx+1 is ITEM

# Handles the "expense"/"expence" keyword
def expense_Keyword(array, transReview, transDict, peopleArray, placesArray): 

    # Gets the array index for "expense"/"expence"
    if process.extractBests("expense", array, scorer=tsr, score_cutoff=90):
        word = process.extractBests("expense", array, scorer=tsr, score_cutoff=90)[0][0]
        idx = array.index(word)
    if process.extractBests("expence", array, scorer=tsr, score_cutoff=90):
        word = process.extractBests("expence", array, scorer=tsr, score_cutoff=90)[0][0]
        idx = array.index(word)
            
    # Checks words preceding "Expense"
    if idx > 0:  # Prevents out of bounds index subtraction
        index = idx-1
        if reverseFindName(array,index,transReview, peopleArray) == 0:  # Checks for PEOPLE
            newPplDict = peopleObject.copy()   # Initializes new people dictionary
            newPplDict["Account"] = f"{array[index]} Expenses" # Saves Account Name
            transReview.append("Review: ACCOUNT name.")

    # Checks the following words
    if len(array)>idx+1 and array[idx+1] in ["for","of"]:
        idx+=1
        beginsExpense(array,idx,transDict,transReview, peopleArray, placesArray)

# Function for "account" keyword
def account_Keyword(array, transDict, transReview, peopleArray, placesArray):
    idx = array.index('account')  # Gets the array index for "account"
        
    # Checks words preceding "account"
    if idx > 0:  # Prevents out of bounds index subtraction
        index = idx-1
        if idx > 0 and array[index] in ["on","in"]: # Checks if "on" precedes "account"
            array[idx-1] = ""   # Removes "on"/"in" keyword
            index = index-1
        if reverseFindName(array,index,transReview, peopleArray) == 0: # Checks for preceding names and professions
            newPplDict = peopleObject.copy()   # Initializes new people dictionary
            newPplDict["Account"] = f"{array[index]} Account" # Saves Account Name
            transReview.append("Review: ACCOUNT name.")
    
    idx+=1  
    # Checks the following word
    while len(array) > idx:
        if array[idx] == "of":  # Checks if "of" follows "account"
            array[idx] == ""  # Removes "of" keyword
            idx+=1
            if len(array)>idx+1 and fuzz.ratio(lem.lemmatize(array[idx+1]), "furniture") >= 90:
                transDict["item"] = f"{array[idx]} Furniture"
                idx+=2
                if array[idx] == "for":
                    for_Keyword(array, idx, transDict, transReview, peopleArray,placesArray)
                else:
                    getCost(array,idx,transDict)
            elif len(array)>idx+1 and (fuzz.ratio(lem.lemmatize(array[idx+1]), "expense") >= 90 or fuzz.ratio(array[idx+1], "expence") >= 90):
                transDict["item"] = f"{array[idx]} Expenses"
                idx+=2
                if array[idx] == "for":
                    for_Keyword(array, idx, transDict, transReview, peopleArray,placesArray)
                else:
                    getCost(array,idx,transDict)
            else:
                findName(array, idx, transDict) # Checks for name
                
# Handles the "received" keyword
def received_Keyword(array,placesArray,transReview,peopleArray):
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

# Handles the "value" keyword
def value_Keyword(array, transReview, transDict, placesArray, peopleArray):
    idx = array.index('value')  # Gets the array index for "value"

    # Checks if "the" is preceeding and removes it
    if idx > 0 and array[idx - 1] == "the":
        array[idx - 1] == ""

    idx+=1
    if len(array)>idx and array[idx] == "of":  # Checks if "of" follows "value"
        array[idx] == ""  # Removes "of"
        idx+=1
        if process.extractBests(array[idx], itemList, scorer=tsr, score_cutoff=80):  # Checks if word is an item
            item = process.extractBests(array[idx], itemList, scorer=tsr, score_cutoff=80)[0][0]
            i = len(item.split())
            idx = idx+i
            transDict["item"] = f"Value of {item}"
        else:
            if len(array)>idx+2 and array[idx+1] in ["&","and"] and process.extractBests(array[idx+2], itemList, scorer=tsr, score_cutoff=80)==[]:
                transDict["item"] = f"{array[idx]} & {array[idx+2]} Value"
                idx+=3
                getCost(array,idx,transDict,transReview, placesArray, peopleArray)
            else:
                transDict["item"] = f"{array[idx]} Value"
                idx+=1
                getCost(array,idx,transDict,transReview, placesArray, peopleArray)
            
# Handles the "returned" keyword
def returnedOmitted_Keywords(array,transDict):
    if "returned" in array and transDict["service"] == "":
        transDict["service"] = "returned"
    if "returnd" in array and transDict["service"] == "":
        transDict["service"] = "returned"
    if "omitted" in array and transDict["service"] == "":
        transDict["service"] = "omitted"

# Handles the "by" keyword
def by_Keyword(array, transReview,placesArray,peopleArray):
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

# Handles the "for" keyword
def for_Keyword(array, idx, transDict, transReview, peopleArray,placesArray):    # sourcery skip: low-code-quality
    
    if idx is None:   # Sets index
        idx = array.index('for')  # Gets the array index for "for"
    array[idx] = ""  # Removes "for"

    # Accounts for "for part of" phrase
    if len(array)>idx+3 and array[idx+2]=="of" and (array[idx+1] == "part" or array[idx+1] == "parts"):
        idx+=3
         
    while idx < len(array):
        idx+=1
        if array[idx] == "the": # Checks if "the" follows
            idx+=1
            if (fuzz.ratio(lem.lemmatize(array[idx]), "expense") >= 90 or fuzz.ratio(array[idx], "expence") >= 90):
                expense_Keyword(array, idx, peopleArray, transReview, transDict)
            if process.extractBests(array[idx], itemList, scorer=tsr, score_cutoff=95):  # Checks for ITEM
                item = process.extractBests(array[idx], itemList, scorer=tsr, score_cutoff=95)[0][0]
                transDict["item"] = item  # Stores Item
                i = len(item[0][0].split())  # Gets item name count
                idx += i
                getCost(array,idx, transDict)  #checks for COST
            elif array[idx] in ["boy", "girl", "man", "woman"]:  # checks for people
                idx+=1
                if getCost(array,idx, transDict) == 0: #checks for cost
                    name = findName(array, idx)  # Checks for name if no COST found  
                    if name != 0:   # If name found checks for COST, accounts for length of name
                        peopleArray.append(name[0]) # stores person
                        idx += name[1]  # Updates index with name count
                        getCost(array,idx, transDict)  # checks for following COST
                    # Stores unkown person and checks if COST follows
                    elif idx+2 < len(array) and (array[idx+1][0].isdigit() == True or array[idx+2][0].isdigit() == True):  
                        unknown = peopleObject.copy()
                        unknown["firstname"] = "FNU"  # Stores first name
                        unknown["lastname"] = "LNU"  # Stores stores 
                        peopleArray.append(unknown)
                        transReview.append("Review people names.")
                        idx+=1
                        getCost(array,idx, transDict) # checks for following COST
            elif idx+1 < len(array) and array[idx][0].isdigit() == True:  # Checks for QUANTITY-QUALIFIER-ITEM pattern
                idx+=1
                QQI_Pattern(array, idx, transDict)
            elif process.extractBests(array[idx], servicesList, scorer=tsr, score_cutoff=90) or lem.lemmatize(array[idx])[-3:]== "ing":
                transDict["Service"] = array[idx]   # Stores SERVICE
                idx+=1
                serviceA_Pattern(array, idx, transDict, peopleArray, transReview, placesArray)
            elif fuzz.token_set_ratio(array[idx], "ballance")>87:
                transDict["item"] = "Balance from"
                array[idx] = ""
           # Checks for SERVICES
        elif len(array)>idx+1 and fuzz.ratio(lem.lemmatize(array[idx+1]), "furniture") >= 90:
            transDict["item"] = f"{array[idx]} Furniture"
            idx+=2
            getCost(array,idx,transDict)
        elif process.extractBests(array[idx], servicesList, scorer=tsr, score_cutoff=90) or lem.lemmatize(array[idx])[-3:]== "ing":
            transDict["Service"] = array[idx]   # Stores SERVICE
            idx+=1
            serviceA_Pattern(array, idx, transDict, peopleArray, transReview, placesArray)
        elif idx+1 < len(array) and array[idx][0].isdigit() == True:  # Checks for QUANTITY-QUALIFIER-ITEM pattern
            idx+=1
            QQI_Pattern(array, idx, transDict)
        elif array[idx] in ["a","an"]:  # Checks for QUANTITY-QUALIFIER-ITEM pattern
            QQI_Pattern(array, idx, transDict)
        elif findName(array, idx) !=0: # Checks for PERSON
            person = findName(array, idx)
            peopleArray.append(person[0]) # Stores PERSON
            idx = idx+person[1]
        elif len(array)>idx+1 and array[idx+1] in ["a", "an", "of"] :
            transDict["Service"] = array[idx]   # Stores possible SERVICE
            transReview.append("Review: Confirm SERVICE.")
            idx+=1
            serviceA_Pattern(array, idx, transDict, peopleArray, transReview, placesArray)
        elif len(array)>idx+2 and array[idx] == "fee" and array[idx+1] == "on":
            idx+=2
            if process.extractBests(array[idx], itemList, scorer=tsr, score_cutoff=85):
                item = process.extractBests(array[idx], itemList, scorer=tsr, score_cutoff=85)[0][0]
                transDict["item"] = item
                i = len(item.split())
                idx = idx+i
                getCost(array,idx,transDict,transReview, placesArray, peopleArray)
            else:
                transDict["item"] = f"Fee On {array[idx]}"
                transReview.append("Review: Confirm ITEM.")
                idx+=1
                getCost(array,idx,transDict,transReview, placesArray, peopleArray)

        break

def and_item(array, idx, transDict,peopleArray, transReview, placesArray, otherItems, flag):

    if flag[0] == "service":
        # Service "&" Service
        if array[idx] in process.extractBests(lem.lemmatize(array[idx]), servicesList, scorer=tsr, score_cutoff=95)==True or lem.lemmatize(array[idx])[-3:]== "ing":
            if transDict["item"] == "":
                transDict["service"] = f"{flag[1]} & {array[idx]}"
                serviceA_Pattern(array, idx, transDict, peopleArray, transReview, placesArray)
        else:
            if transDict["item"] == "":
                transDict["item"] = f"{flag[1]} & {array[idx]}"

    if flag[0] == "item":
        # Item "&" Service
        newItem = transactionObject.copy()
        if array[idx] in process.extractBests(lem.lemmatize(array[idx]), servicesList, scorer=tsr, score_cutoff=95)==True or lem.lemmatize(array[idx])[-3:]== "ing":
            newItem["service"] = array[idx]
            serviceA_Pattern(array, idx, newItem, peopleArray, transReview, placesArray)
            otherItems.append(newItem)

# ************************************************** VARIABLES USED *********************************************************** #
# entryError[] = List to store entry errors              |  transArray[] = Array of tokenizd transactions from Chip's function
# varientsArray = List of item's adjectives              |  otherItems[] = List of items associated with a single transaction
# transError[] = List to store entry errors              |  peopleArray[] = List of people mentioned in a transaction
# transReview = List of data to review in a transaction  |  placesArray[] = List of places mentioned in a transaction
# ***************************************************************************************************************************** #

# Function that parses the transactions from the entry column (transArr = array/list of transactions)
def transParse(transArr):    # sourcery skip: hoist-statement-from-loop
 # Initializes error array for entry
    entryError = []
    parsedTransactionsArray = []

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

        # Checks for "vizt", deletes it and everything after it
        if "vizt" in transaction:
            x = transaction.index('vizt')  # Gets the array index for "vizt"
            if transaction[x+1] == "from":
                del transaction[x:]

        # Initializes lists for transaction values and errors
        otherItems, peopleArray, placesArray, varientsArray, transReview = [],[],[],[],[] 
        transDict = transactionObject.copy() # Initializies dictionary for transaction
    
        # Checks if first character of first string is a digit or letter
        if transaction[0][0].isdigit() == True:
            intFirstParse(transaction, transDict, otherItems, peopleArray, placesArray, varientsArray, transReview)
            parsedTransactionsArray.append(transDict)
        elif transaction[0][0].isalpha() == True or transaction[0][0]=="&":
            # Checks if first word in array is "to" or "by"
            if transaction[0] == "to" | transaction[0] == "by":
                # Removes "to" or "by" 
                transaction[0].pop(0)
                # Checks again if first character of first string is a digit or letter
                if transaction[0][0].isdigit() == True:
                    intFirstParse(transaction,transDict,otherItems,peopleArray,placesArray,varientsArray,transReview)
                    parsedTransactionsArray.append(transDict)
                else:
                    alphaFirstParse(transaction,transDict,otherItems,peopleArray,placesArray,varientsArray,transReview)
                    parsedTransactionsArray.append(transDict)
        else:
            entryError.append("Error: Entry does not begin with a letter or number")
              
    return [parsedTransactionsArray, transactionType]

