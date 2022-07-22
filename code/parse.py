# code for the function that parses everything
def parse(filepath):
    #Load spreadsheet into pd dataframe
    data = pd.read_excel("C_1760_003_FINAL_.xlsx", header=1)
    
    #delete rows that need to be deleted from spreadsheet
    for idx in range(0, data.shape[0]-1):
        if str(data['[EntryID]'][idx+1])[:-1] == str(data['[EntryID]'][idx]):
    data = data.reset_index(drop=True)

    #create new dataframe that will contain parsed info
    #put all direct transfer information from original sheet into 'parsed' sheet
    #for rows in entry column:
        #call preprocess function
        #for transaction in entry:
            #call transaction Parsing function
            #if second or later transaction:
                #create new row in dataframe at location and copy down information from previous row
            #add transaction to next line
    #export to json to load to MongoDB temp database (which will then get loaded to website)
    pass