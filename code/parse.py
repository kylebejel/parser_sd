# code for the function that parses everything
def parse():
    #Load spreadsheet into pd dataframe
    #delete rows that need to be deleted from spreadsheet
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