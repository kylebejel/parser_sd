import pandas as pd
import xlwt
from pathlib import Path
import numpy as np

def preprocess(arr):
    pass

# code for the function that parses everything
def parse(df):
    ret_df = pd.DataFrame
    ret_df.columns = ['[Transcriber/Time]','[File Name]','Reel','Owner','Store','Year','FolioPage','EntryID','Prefix','AccountFirstName','AccountLastName','Suffix','Profession','Location','Reference','DrCr','Year','Month','Day','Entry','People','Places','FolioReference','EntryType','Ledger','Quantity','Commodity','SL','SS','SD','Colony','CL','CS','CD','ArchMat','GenMat','Final','ExtraNotes']
    
    new_header = df.iloc[0]
    df2 = df[1:]
    df2.columns = new_header

    # transcriber_time = df2.iloc[0][1]
    # filename = df2.iloc[1][1]

    transcriber_time = df2.iloc[0][0]
    filename = df2.iloc[0][1]
    # print(f'transcriber: {transcriber_time}\nfilename: {filename}')
    df2.at[1,'[Transcriber/Time]'] = np.nan
    df2.at[1,'[File Name]'] = np.nan
    print(f'transcriber: {transcriber_time}\nfilename: {filename}')
    df2.at[2,'[Transcriber/Time]'] = transcriber_time
    df2.at[2,'[File Name]'] = filename
    # df2.drop(labels = 1, axis = 0)
    df2 = df2.iloc[1:]
    # df2.head()
    
    entry_mat = preprocess(df2)

    transcriber_time = df2['Transcriber/Time']
    file_name = df2['[File Name]']
    reel = df2['Reel']
    owner = df2['Owner']
    store = df2['Store']
    year = df2['Year']
    folio_page = df2['Folio Page']
    entry_id = df2['[EntryID]']
    prefix = df2['Prefix']
    account_firstname = df2['Account First Name']
    account_lastname = df2['Account Last Name']
    suffix = df2['Suffix']
    profession = df2['Profession']
    location = df2['Location']
    reference = df2['Reference']
    drcr = df2['Dr/Cr']

    # TEMPORARY YEAR CHANGE THIS
    temp_year = df2['Temp Year']

    month = df2['_Month']
    day = df2['Day']

    # skip entry bc parse_entry()

    # CHANGE THIS TO EXTRACT INFO
    people = df2['PEOPLE']
    places = df2['PLACES']

    folio_reference = df2['[Folio Reference]']

    # CHANGE THIS TO EXTRACT INFO
    entry_type = df2['ENTRY TYPE']
    ledger = df2['LEDGER']

    quantity = df2['Quantity']
    commodity = df2['Commodity']
    SL = df2['SL']
    SS = df2['SS']
    SD = df2['SD']
    colony = df2['Colony']
    CL = df2['CL']
    CS = df2['CS']
    CD = df2['CD']
    archmat = df2['[ArchMat]']
    genmat = df2['[GenMat]']
    final = df2['Final']

    # FIX EXTRA NOTES
    extra_notes = df2['EXTRA NOTES']
    error_flag = df2['flag']

    ret_list = []
    ret_size = 0
    counter = 0

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
        # temp_year = df2['Temp Year']
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
            temp_list[19] = entry
            temp_list[20] = people
            temp_list[21] = places
            temp_list[23] = entry_type = df2['ENTRY TYPE']
            temp_list[24] = ledger = df2['LEDGER']

            ret_list.append(temp_list)
            ret_size+=1
        counter+=1
        
    df = pd.DataFrame(ret_list, columns = ['Column_A','Column_B','Column_C'])


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
