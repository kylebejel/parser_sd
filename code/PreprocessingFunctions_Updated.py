import itertools
import nltk
nltk.download('punkt')
import re

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
  tknzr = nltk.tokenize.TweetTokenizer()
  tokens = tknzr.tokenize(text)

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
 
  # Removes periods and stitches prices back together
  for idx, word in enumerate(tokens):
    # Removes periods
    if tokens[idx] == ".":
      tokens[idx] = ""

    # Removes possessive 's
    if len(tokens[idx]) > 1 and tokens[idx][-1] == "s" and tokens[idx][-2] == "'":
      tokens[idx] = tokens[idx].replace("'","")

    # Stitches Prices
    if tokens[idx] == "..":
      if idx > 0 and idx+3 < len(tokens) and tokens[idx+2] == ".." and tokens[idx-1].isdigit()==True:
        tokens[idx-1] = tokens[idx-1]+tokens[idx]+tokens[idx+1]+tokens[idx+2]+tokens[idx+3]
        tokens[idx:idx+4] = ""
      elif idx > 1 and idx+3 < len(tokens) and tokens[idx+2] == ".." and tokens[idx-2].isdigit()==True:
        tokens[idx-2] = tokens[idx-2]+tokens[idx]+tokens[idx+1]+tokens[idx+2]+tokens[idx+3]
        tokens[idx:idx+4] = ""

  #remove all character removals '^','[',']','<','>', '{', '}', '(', ')',  '&ct', 'etcetera', 'Etcetera', '£'
  removals = ['^','[',']','<','>', '{', '}', '(', ')', '&ct', 'etcetera', 'Etcetera', '£']  # add all characters to be removed to this list
  for count, character in itertools.product(range(len(tokens)), removals):
    while character in tokens[count]:
      tokens[count] = tokens[count].replace(character,"")
        
  #remove "" tokens
  while ("" in tokens):
    tokens.remove('')

  #fraction handling
  fractions = ["¼", "½", "¾", "⅓", "⅔", "⅕", "⅖", "⅗", "⅘", "⅙", "⅚", "⅛", "⅜", "⅝", "⅞"]
  fracReplace = ["0.25", "0.5", "0.75", "0.333", "0.667", "0.2", "0.4", "0.6", "0.8", "0.167", "0.833", "0.125", "0.375", "0.625", "0.875"]
  for count in range(len(tokens)):
    for fraction in fractions:
      tokens[count] = tokens[count].replace(fraction, fracReplace[fractions.index(fraction)])

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

  #changing 'w' and 'wt' to pounds
  for idx, word in enumerate(tokens):
    if tokens[idx] in ["w","wt","W", "WT", "Wt"]:
      tokens[idx] = "pound"
    # Accounts for "w" attached to numbers (Ex: "10w" becomes "10 pound") 
    if tokens[idx][0].isdigit() == True and (tokens[idx][-1] in ["w","W"] or tokens[idx][-2] in ["w","W"] ):
        tokens[idx] = tokens[idx].replace(tokens[idx][-1],"")
        if tokens[idx][-1] in ["w","W"]: tokens[idx] = tokens[idx].replace(tokens[idx][-1],"")
        tokens.insert(idx+1, 'pound')
      

  return tokens


def preprocess(string):#function that is acctually called
  breakup = seperate(string)
  preprocessed = []
  for count in range(0, len(breakup)):
    preprocessed.append(editTokens(breakup[count]))
  while [] in preprocessed:
    preprocessed.remove([])
  return preprocessed
