import pandas as pd
import xlwt
from pathlib import Path
import numpy as np

def preprocess(arr):
    pass

def parse_transaction():
    pass

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
    
    # run preprocessing
    entry_mat = preprocess(df)

    # make repeated idxs dict
    repeated_idxs = {}
    for x in range(0,len(entry_mat)):
        l = len(entry_mat[x])
        if l > 1:
            repeated_idxs[x] = l
    
    parsed_transactions = parse_transaction(entry_mat)

    # make lists for each column
    transcriber_time = df['Transcriber/Time']
    file_name = df['[File Name]']
    reel = df['Reel']
    owner = df['Owner']
    store = df['Store']
    year = df['Year']
    folio_page = df['Folio Page']
    entry_id = df['[EntryID]']
    prefix = df['Prefix']
    account_firstname = df['Account First Name']
    account_lastname = df['Account Last Name']
    suffix = df['Suffix']
    profession = df['Profession']
    location = df['Location']
    reference = df['Reference']
    drcr = df['Dr/Cr']

    # TEMPORARY YEAR CHANGE THIS
    temp_year = df['Temp Year']

    month = df['_Month']
    day = df['Day']

    # skip entry bc parse_entry()

    # CHANGE THIS TO EXTRACT INFO
    people = df['PEOPLE']
    places = df['PLACES']

    folio_reference = df['[Folio Reference]']

    # CHANGE THIS TO EXTRACT INFO
    entry_type = df['ENTRY TYPE']
    ledger = df['LEDGER']

    quantity = df['Quantity']
    commodity = df['Commodity']
    SL = df['SL']
    SS = df['SS']
    SD = df['SD']
    colony = df['Colony']
    CL = df['CL']
    CS = df['CS']
    CD = df['CD']
    archmat = df['[ArchMat]']
    genmat = df['[GenMat]']
    final = df['Final']

    # FIX EXTRA NOTES
    extra_notes = df['EXTRA NOTES']
    error_flag = df['flag']

    ret_list = []
    ret_size = 0
    counter = 0

    for transaction in parsed_transactions:
        temp_row = [38] * None
        # assignments
        temp_row[0]=transcriber_time[counter]
        temp_row[1]=file_name[counter]
        temp_row[2]=reel[counter]
        temp_row[3]=owner[counter]
        temp_row[4]=store[counter]
        temp_row[5]=year[counter]
        temp_row[6]=folio_page[counter]
        temp_row[7]=entry_id[counter]
        temp_row[8]=prefix[counter]
        temp_row[9]=account_firstname[counter]
        temp_row[10]=account_lastname[counter]
        temp_row[11]=suffix[counter]
        temp_row[12]=profession[counter]
        temp_row[13]=location[counter]
        temp_row[14]=reference[counter]
        temp_row[15]=drcr[counter]
        # TEMPORARY YEAR CHANGE THIS
        # temp_year = df['Temp Year']
        temp_row[16] = temp_year[counter]
        temp_row[17] = month[counter]
        temp_row[18] = day[counter]
        temp_row[22] = folio_reference[counter]
        temp_row[25] = quantity[counter]
        temp_row[26] = commodity[counter]
        temp_row[27] = SL[counter]
        temp_row[28] = SS[counter]
        temp_row[29] = SD[counter]
        temp_row[30] = colony[counter]
        temp_row[31] = CL[counter]
        temp_row[32] = CS[counter]
        temp_row[33] = CD[counter]
        temp_row[34] = archmat[counter]
        temp_row[35] = genmat[counter]
        temp_row[36] = final[counter]
        # FIX EXTRA NOTES
        temp_row[37] = extra_notes[counter]
        temp_row[38] = error_flag[counter]

        if counter in repeated_idxs.keys:
            for x in range(0,repeated_idxs[counter]):
                # people, places, ledger, entry type, flag?
                temp_row[19] = transaction['entry']
                temp_row[20] = transaction['people']
                temp_row[21] = transaction['places']
                temp_row[23] = transaction['entry_type']
                temp_row[24] = transaction['ledger']
                # append
                ret_list.append(temp_row)

        else:
            temp_row[19] = transaction['entry']
            temp_row[20] = transaction['people']
            temp_row[21] = transaction['places']
            temp_row[23] = transaction['entry_type']
            temp_row[24] = transaction['ledger']
            # append
            ret_list.append(temp_row)
        # increment
        counter+=1

    for entry in entry_mat:
        temp_list = [None] * 38
        # initial assignment
        temp_list[0]=transcriber_time[counter]
        temp_list[1]=file_name[counter]
        temp_list[2]=reel[counter]
        temp_list[3]=owner[counter]
        temp_list[4]=store[counter]
        temp_list[5]=year[counter]
        temp_list[6]=folio_page[counter]
        temp_list[7]=entry_id[counter]
        temp_list[8]=prefix[counter]
        temp_list[9]=account_firstname[counter]
        temp_list[10]=account_lastname[counter]
        temp_list[11]=suffix[counter]
        temp_list[12]=profession[counter]
        temp_list[13]=location[counter]
        temp_list[14]=reference[counter]
        temp_list[15]=drcr[counter]

        # TEMPORARY YEAR CHANGE THIS
        # temp_year = df['Temp Year']
        temp_list[16] = temp_year[counter]

        temp_list[17] = month[counter]
        temp_list[18] = day[counter]

        temp_list[22] = folio_reference[counter]

        temp_list[25] = quantity[counter]
        temp_list[26] = commodity[counter]
        temp_list[27] = SL[counter]
        temp_list[28] = SS[counter]
        temp_list[29] = SD[counter]
        temp_list[30] = colony[counter]
        temp_list[31] = CL[counter]
        temp_list[32] = CS[counter]
        temp_list[33] = CD[counter]
        temp_list[34] = archmat[counter]
        temp_list[35] = genmat[counter]
        temp_list[36] = final[counter]

        # FIX EXTRA NOTES
        temp_list[37] = extra_notes[counter]
        temp_list[38] = error_flag[counter]

        for transaction in entry:
            # assignment for changing entries
            # finish making of row and append to ret list

            # 19 20 21 23 24

            output = parse_transaction(transaction)

            temp_list[19] = entry
            temp_list[20] = people
            temp_list[21] = places
            temp_list[23] = entry_type
            temp_list[24] = ledger

            ret_list.append(temp_list)
            ret_size+=1
        counter+=1
        
    final_df = pd.DataFrame(ret_list, columns = ['Column_A','Column_B','Column_C'])


    # --------------------------------------------------------------------

def main():
    cwd = Path.cwd()
    above = cwd.parent / 'util/data/original'
    # print(f'dir is : {above}')

    for file in above.iterdir():
        df = pd.read_excel(file)
        new_df = parse(df)
        # print(new_df.head)

if __name__ == '__main__':
    main()
