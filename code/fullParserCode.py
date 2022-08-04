import re
from os import unlink
from re import I
from tkinter import Y
import nltk
import numpy as np
import pandas as pd
import pymongo
from fuzzywuzzy import fuzz, process
from regex import P, R
from sympy import O



# Function to connect to database
def get_database():  
    # Creates a connection to MongoDB
    client = pymongo.MongoClient("mongodb://root:Lsfr5n3J0Jib@ec2-52-203-105-125.compute-1.amazonaws.com:27017/shoppingStories?authSource=admin&readPreference=primary&ssl=false")

    # Returns the database collection we'll be using
    return client["shoppingStories"]
 

#create function that separates 1 entry column into multiple entries to pass to next function
def seperate(text):
  #will always return an array
  textArray = re.split("   ( |\})|\n", text)
  while None in textArray:
    textArray.remove(None)
  return textArray

#creat function to preprocess ALREADY SEPEARTED ENTRIES with nlkt
def editTokens(text):
  #create variable tokens which is tokenized string
  tknzr = nltk.tokenize.TweetTokenizer(match_phone_numbers=False)
  tokens = tknzr.tokenize(text)
  print(tokens)
  #begin process of removing words that are replacements
  replaceWordIndex = []
  removenumbersIndex = []
  for idx, word in enumerate(tokens): #this basically means that 'current' index is accesed by variable idx inside loop
    if word == '[':
      if tokens[idx + 2] == ']' and (tokens[idx - 1][0] == tokens[idx + 1][0] or tokens[idx - 1] in ["ditto", "Ditto"]):
        replaceWordIndex.append(idx) #replace words based on matching first letter
      elif tokens[idx+1].isdigit() == True and tokens[idx+3] != "..":  # Accounts for prices in brackets
        removenumbersIndex.append(idx)
  for num in removenumbersIndex:#pop the numbers
    tokens.pop(num+1)
    for count in range(len(replaceWordIndex)): #adjust index accordingly
      if(replaceWordIndex[count] > num):
        replaceWordIndex[count] = replaceWordIndex[count]-1
    for count in range(len(removenumbersIndex)): #adjust index accordingly
      if(removenumbersIndex[count] > num):
        removenumbersIndex[count] = removenumbersIndex[count]-1
  for num in replaceWordIndex: #pop replaced word and brakets
    tokens.pop(num+2)
    tokens.pop(num)
    tokens.pop(num-1)
    for count in range(len(replaceWordIndex)): #adjust index accordingly
      if(replaceWordIndex[count] > num):
        replaceWordIndex[count] = replaceWordIndex[count]-3
  #replace where more than 1 word between []
  replaceWordIndex = []
  removenumbersIndex = []
  for idx, word in enumerate(tokens):
    if (word == "["):
      for count in range(idx+1, len(tokens)):
        if (tokens[count] == "["):
          break
        elif (tokens[count] == "]"):
          if (tokens[idx-1][0] == tokens[idx+1][0] or tokens[idx-1] in ["ditto","Ditto"]):
            replaceWordIndex.append(idx)
          break
      break
  for num in replaceWordIndex:
    tokens.pop(num-1)
    for count in range(len(replaceWordIndex)): #adjust index accordingly
      if(replaceWordIndex[count] > num):
        replaceWordIndex[count] = replaceWordIndex[count]-3
  #now remove all contents between parentheses
  for idx, word in enumerate(tokens):
    if (word == '(' and tokens[idx+2] == ')'):
      tokens.pop(idx+1)
  #remove all non-alphanumerica characters between arrows '<' and '>'
  for idx, word in enumerate(tokens):
    if (word == '<' and tokens[idx+2] == '>' and not(tokens[idx+1].isalnum())):
      tokens.pop(idx+1)
 
  fractions = {'¼': "0.25", "⅓": "0.33", '½': "0.5", '⅕': "0.2", '⅙': "0.167", '⅐': "0.143", '⅛':" 0.125", '⅑': "0.111", 
    '⅒': "0.1", '⅔': "0.667", '⅖': "0.4", '¾': "0.75", '⅗': "0.6", '⅜': "0.375", '⅘': "0.8", '⅚': "0.833", '⅞': "0.875" }
  
  for idx, word in enumerate(tokens):
    if word in fractions:
      tokens[idx] = fractions[word]
    
    # Removes periods
    if tokens[idx] == ".":
      tokens[idx] = ""


  # Removes periods and stitches prices back together
  for idx, word in enumerate(tokens):
    # Removes possessive 's
    if len(tokens[idx]) > 1 and tokens[idx][-1] == "s" and tokens[idx][-2] == "'":
      tokens[idx] = tokens[idx].replace("'","")
     
     # 0 .. 0 .. 0
     # 0  1 2  3 4
    # Stitches Prices
    if tokens[idx] == "..":
      if len(tokens)>idx+2 and tokens[idx+1][0].isdigit()==True and tokens[idx+2] == "..":
        tokens[idx] = tokens[idx]+tokens[idx+1]+tokens[idx+2]
        tokens[idx+1] = ""
        tokens[idx+2] = ""
        if idx>0 and tokens[idx-1][0].isdigit()==True:
          tokens[idx] = tokens[idx-1]+tokens[idx]
          tokens[idx-1] = ""
        if len(tokens)>idx+3 and tokens[idx+3][0].isdigit()==True:
          tokens[idx] = tokens[idx]+tokens[idx+3]
          tokens[idx+3] = ""

  #remove all character removals '^','[',']','<','>', '{', '}', '(', ')',  '&ct', 'etcetera', 'Etcetera', '£'
  removals = ['^','[',']','<','>', '{', '}', '(', ')', '&ct', 'etcetera', 'Etcetera', '£','?']  # add all characters to be removed to this list
  for count, character in itertools.product(range(len(tokens)), removals):
    while character in tokens[count]:
      tokens[count] = tokens[count].replace(character,"")
        
  #remove "" tokens
  while ("" in tokens):
    tokens.remove('')

  #gluing preceding tokens and fractions together
  numberRE = re.compile("[0-9]+")
  decimalRE = re.compile("\.[0-9]+")
  for idx, word in enumerate(tokens):
    if (numberRE.match(tokens[idx])
        and idx + 1 < len(tokens)) and (decimalRE.match(tokens[idx + 1])):
      tokens[idx] = tokens[idx] + tokens[idx+1]
      tokens.pop(idx+1)

  #gluing 'per' and 'cent' together
  for idx, word in enumerate(tokens):
    if (word in ['per', 'Per'] and idx + 1 < len(tokens)) and tokens[idx + 1] in ["cent", "Cent"]:
      tokens[idx] = 'percent'
      tokens.pop(idx+1)

  saveIdx =[]
  #changing 'w' and 'wt' 'ws' to pounds
  for idx, word in enumerate(tokens):
    if tokens[idx] in ["w","wt","W", "WT", "Wt", 'ws', 'Ws', 'wS', 'WS']:
      tokens[idx] = "pound"
    # Accounts for "w" attached to numbers (Ex: "10w" becomes "10 pound") 
    if len(tokens[idx])>1 and tokens[idx][0].isdigit() == True and (tokens[idx][-1] in ["w","W"] or tokens[idx][-2] in ["w","W"] ):
        tokens[idx] = tokens[idx].replace(tokens[idx][-1],"")
        saveIdx.append(idx)
        if tokens[idx][-1] in ["w","W"]: tokens[idx] = tokens[idx].replace(tokens[idx][-1],"")
        
  for i in saveIdx:
    tokens.insert(i+1, 'pound')

  # two pound in a row
  poundSpellings = ['pound', 'pounds', 'Pound', 'Pounds']
  for idx, word in enumerate(tokens):
    for spelling in poundSpellings:
      if word == spelling:
        for spelling2 in poundSpellings:
          while (idx+1 < len(tokens)):
            if tokens[idx+1] == spelling2:
              tokens.pop(idx+1)
            break

  # 1 M thousand and 1M Thousand --> 1000
  print(tokens)
  for idx, word in enumerate(tokens):
    numMre = re.compile('\d+(M|m)')# any number of digits followed by a single 'M' or 'm'
    if word.isnumeric():
      while (idx+2 < len(tokens)):
        if tokens[idx+1] == 'M' or tokens[idx+1] == 'm':
          if tokens[idx+2] == 'thousand' or tokens[idx+2] == 'Thousand':
            tokens[idx] = tokens[idx]+'000'
            tokens.pop(idx+2)
            tokens.pop(idx+1)
        break
    elif re.match(numMre, word):
      while (idx+1 < len(tokens)):
        if tokens[idx+1] == 'thousand' or tokens[idx+1] == 'Thousand':
          tokens[idx] = tokens[idx].rstrip(tokens[idx][-1])
          tokens[idx] = tokens[idx] + '000'
          tokens.pop(idx+1)
        break
  return tokens


def preprocess(string):#function that is acctually called
  breakup = seperate(string)
  preprocessed = []
  for count in range(0, len(breakup)):
    preprocessed.append(editTokens(breakup[count]))
  while [] in preprocessed:
    preprocessed.remove([])
  return preprocessed




# code for the function that parses everything
def parse(df):
    
    transcriber_time = df.iloc[0][0]
    filename = df.iloc[0][1]
    # print(f'transcriber: {transcriber_time}\nfilename: {filename}')
    df.at[1,'[Transcriber/Time]'] = np.nan
    df.at[1,'[File Name]'] = np.nan
    print(f'transcriber: {transcriber_time}\nfilename: {filename}')
    df.at[2,'[Transcriber/Time]'] = transcriber_time
    df.at[2,'[File Name]'] = filename
    # df.drop(labels = 1, axis = 0)
    df = df.iloc[1:]
    # df.head()
    


    # run tm first

    # run preprocessing
    entry_mat = preprocess(df)

    # make repeated idxs dict
    repeated_idxs = {}
    for x in range(0,len(entry_mat)):
        l = len(entry_mat[x])
        if l > 1:
            repeated_idxs[x] = l
    
    parsed_transactions = parse_transaction(entry_mat)

    # returned entry obj
    entry_obj_list = []

    # make lists for each column
    transcriber_time = df['Transcriber/Time']
    file_name = df['File Name']
    reel = df['Reel']
    owner = df['Owner']
    store = df['Store']
    folio_year = df['Folio Year']
    folio_page = df['Folio Page']
    entry_id = df['EntryID']
    # marginalia = df['Marginalia']
    prefix = df['Prefix']
    account_firstname = df['Account First Name']
    account_lastname = df['Account Last Name']
    suffix = df['Suffix']
    profession = df['Profession']
    location = df['Location']
    reference = df['Reference']
    drcr = df['Dr/Cr']
    year = df['Year']
    month = df['_Month']
    day = df['Day']

    entry = df['Entry']

    # CHANGE THIS TO EXTRACT INFO
    # people = df['PEOPLE']
    # places = df['PLACES']

    folio_reference = df['Folio Reference']

    # CHANGE THIS TO EXTRACT INFO
    # entry_type = df['ENTRY TYPE']
    # ledger = df['LEDGER']

    quantity = df['Quantity']
    commodity = df['Commodity']
    SE = ['£ Sterling']
    SL = df['L Sterling']
    SS = df['s Sterling']
    SD = df['d Sterling']
    colony = df['Colony Currency']
    CE = df['£ Currency']
    CL = df['L Currency']
    CS = df['s Currency']
    CD = df['d Currency']
    archmat = df['ArchMat']
    genmat = df['GenMat']
    final = df['Final']

    counter = 0

    for transaction_counter in range(0,len(parsed_transactions)):
    # for transaction in parsed_transactions:
        # assignments
        # transaction = parsed_transactions[transaction_counter]

        # meta obj
        meta_obj = {}
        meta_obj['ledger'] = None 
        meta_obj['reel'] = reel[counter]
        meta_obj['owner'] = owner[counter]
        meta_obj['store'] = store[counter]
        meta_obj['year'] = folio_year[counter]
        meta_obj['folioPage'] = folio_page[counter]
        meta_obj['entryID'] = entry_id[counter]
        meta_obj['comments'] = final[counter]

        # meta_obj_list.append(meta_obj)

        # date obj
        date_obj = {}
        date_obj['day'] = day[counter]
        date_obj['month'] = month[counter]
        date_obj['year'] = year[counter]
        # change to an appended datetime obj
        date_obj['fullDate'] = None

        # date_obj_list.append(date_obj)

        # account holder obj
        acc_holder_obj = {}
        acc_holder_obj['prefix'] = prefix[counter]
        acc_holder_obj['accountFirstName'] = account_firstname[counter]
        acc_holder_obj['accountLastName'] = account_lastname[counter]
        acc_holder_obj['suffix'] = suffix[counter]
        acc_holder_obj['profession'] = profession[counter]
        acc_holder_obj['location'] = location[counter]
        acc_holder_obj['reference'] = reference[counter]
        # change this to an int
        temp_drcr = -1
        if drcr[counter].upper() == 'DR':
            temp_drcr = 0
        if drcr[counter].upper() == 'CR':
            temp_drcr = 1
        acc_holder_obj['debitOrCredit'] = temp_drcr

        # make two poundshillingpence objects, one for currency one for sterling
        s_psp = {}
        s_psp['pounds'] = SL[counter]
        s_psp['shillings'] = SS[counter]
        s_psp['pence'] =  SD[counter]

        c_psp = {}
        c_psp['pounds'] = CL[counter]
        c_psp['shilling'] = CS[counter]
        c_psp['pence'] = CD[counter]

        # make money obj for both psp's
        money_obj = {}
        money_obj['quantity'] = quantity[counter]
        money_obj['commodity'] = commodity[counter]
        money_obj['colony'] = colony[counter]
        money_obj['sterling'] = s_psp
        money_obj['currency'] = c_psp
        
        if counter in repeated_idxs.keys:
            for x in range(0,repeated_idxs[counter]):
                # people, places, ledger, entry type, flag?
                entry_obj = {}
                item_entry_obj = {}
                item_or_service_obj = {}

                transaction = parsed_transactions[transaction_counter]

                item_or_service_obj['quantity'] = transaction['quantity']
                item_or_service_obj['qualifier'] = transaction['qualifier']
                item_or_service_obj['variants'] = transaction['variants']
                item_or_service_obj['item'] = transaction['item']
                item_or_service_obj['category'] = transaction['category']
                item_or_service_obj['subcategory'] = None
                item_or_service_obj['unitCost'] = transaction['unitCost']
                item_or_service_obj['itemCost'] = transaction['totalCost']

                item_entry_obj['perOrder'] = None
                item_entry_obj['percentage'] = None
                item_entry_obj['itemOrServices'] = []
                item_entry_obj['itemOrServices'].append(item_or_service_obj)
                item_entry_obj['itemsMentioned'] = None

                people_obj_list = []
                places_obj_list = []

                for person in transaction['mentionedPpl']:
                    person_obj = {}
                    person_obj['name'] = person
                    people_obj_list.append(person_obj)

                for place in transaction['mentionedPlaces']:
                    place_obj = {}
                    place_obj['name'] = place
                    places_obj_list.append(place_obj)
                
                entry_obj['accountHolder'] = acc_holder_obj
                entry_obj['meta'] = meta_obj
                entry_obj['dateInfo'] = date_obj
                entry_obj['folioRefs'] = folio_reference[counter]
                entry_obj['ledgerRefs'] = None
                entry_obj['itemEntries?'] = []
                entry_obj['itemEntries?'].append(item_entry_obj)
                entry_obj['tobaccoEntry?'] = None # CHANGE THIS 
                entry_obj['regularEntry?'] = None
                entry_obj['people'] = people_obj_list
                entry_obj['places'] = places_obj_list
                entry_obj['entry'] = entry[counter]
                entry_obj['money'] = money_obj
                entry_obj['errorReview'] = transaction['errorReview']

                # append
                # ret_list.append(temp_row)
                entry_obj_list.append(entry_obj)
                transaction_counter+=1

        else:
            entry_obj = {}
            item_entry_obj = {}
            item_or_service_obj = {}

            transaction = parsed_transactions[transaction_counter]

            item_or_service_obj['quantity'] = transaction['quantity']
            item_or_service_obj['qualifier'] = transaction['qualifier']
            item_or_service_obj['variants'] = transaction['variants']
            item_or_service_obj['item'] = transaction['item']
            item_or_service_obj['category'] = transaction['category']
            item_or_service_obj['subcategory'] = None
            item_or_service_obj['unitCost'] = transaction['unitCost']
            item_or_service_obj['itemCost'] = transaction['totalCost']

            item_entry_obj['perOrder'] = None
            item_entry_obj['percentage'] = None
            item_entry_obj['itemOrServices'] = []
            item_entry_obj['itemOrServices'].append(item_or_service_obj)
            item_entry_obj['itemsMentioned'] = None

            people_obj_list = []
            places_obj_list = []

            for person in transaction['mentionedPpl']:
                person_obj = {}
                person_obj['name'] = person
                people_obj_list.append(person_obj)

            for place in transaction['mentionedPlaces']:
                place_obj = {}
                place_obj['name'] = place
                places_obj_list.append(place_obj)
                
                

            entry_obj['accountHolder'] = acc_holder_obj
            entry_obj['meta'] = meta_obj
            entry_obj['dateInfo'] = date_obj
            entry_obj['folioRefs'] = folio_reference[counter]
            entry_obj['ledgerRefs'] = None
            entry_obj['itemEntries?'] = []
            entry_obj['itemEntries?'].append(item_entry_obj)
            entry_obj['tobaccoEntry?'] = None # CHANGE THIS 
            entry_obj['regularEntry?'] = None
            entry_obj['people'] = people_obj_list
            entry_obj['places'] = places_obj_list
            entry_obj['entry'] = entry[counter]
            entry_obj['money'] = money_obj
            entry_obj['errorReview'] = transaction['errorReview']

                # append
                # ret_list.append(temp_row)
            entry_obj_list.append(entry_obj)
            transaction_counter+=1

        # increment
        counter+=1
        
    return entry_obj_list


    # --------------------------------------------------------------------

def main():
    cwd = Path.cwd()
    fp = cwd / 'C_1760_002_FINAL_.xlsx'
    # print(f'dir is : {above}')

    df = pd.read_excel(fp)
    entry_objs = parse(df)
    print(entry_objs)

if __name__ == '__main__':
    main()
