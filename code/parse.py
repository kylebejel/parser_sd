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
    file_name = df2['Transcriber/Time']
    reel = df2['Transcriber/Time']
    owner = df2['Transcriber/Time']
    store = df2['Transcriber/Time']
    year = df2['Transcriber/Time']
    folio_page = df2['Transcriber/Time']
    entry_id = df2['Transcriber/Time']
    prefix = df2['Transcriber/Time']
    account_firstname = df2['Transcriber/Time']
    account_lastname = df2['Transcriber/Time']
    suffix = df2['Transcriber/Time']
    profession = df2['Transcriber/Time']
    location = df2['Transcriber/Time']
    reference = df2['Transcriber/Time']
    drcr = df2['Transcriber/Time']
    temp_year = df2['Transcriber/Time']
    month = df2['Transcriber/Time']
    day = df2['Transcriber/Time']
    #skip entry bc parse_entry()
    people = df2['Transcriber/Time']
    places = df2['Transcriber/Time']
    folio_reference = df2['Transcriber/Time']
    transcriber_time = df2['Transcriber/Time']
    transcriber_time = df2['Transcriber/Time']
    transcriber_time = df2['Transcriber/Time']
    transcriber_time = df2['Transcriber/Time']
    transcriber_time = df2['Transcriber/Time']
    transcriber_time = df2['Transcriber/Time']
    transcriber_time = df2['Transcriber/Time']
    transcriber_time = df2['Transcriber/Time']
    transcriber_time = df2['Transcriber/Time']
    transcriber_time = df2['Transcriber/Time']
    transcriber_time = df2['Transcriber/Time']
    transcriber_time = df2['Transcriber/Time']
    transcriber_time = df2['Transcriber/Time']
    transcriber_time = df2['Transcriber/Time']
    transcriber_time = df2['Transcriber/Time']
    transcriber_time = df2['Transcriber/Time']

    ret_df['[Transcriber/Time]'] = df2['Transcriber/Time']
    ret_df['[File Name]'] = df2['[File Name]']
    ret_df['Reel'] = df2['Reel']
    ret_df['Owner'] = df2['Owner']
    ret_df['Store'] = df2['Store']
    ret_df[5] = df2[5]
    ret_df['FolioPage'] = df2['Folio Page']
    ret_df['EntryID'] = df2['[EntryID]']
    ret_df['Prefix'] = df2['Prefix']
    ret_df['AccountFirstName'] = df2['Account First Name']
    ret_df['AccountLastName'] = df2['Account Last Name']
    ret_df['Suffix'] = df2['Suffix']
    ret_df['Profession'] = df2['Profession']
    ret_df['Location'] = df2['Location']
    ret_df['Reference'] = df2['Reference']
    ret_df['DrCr'] = df2['Dr/Cr']
    ret_df[16] = df2[18]
    ret_df['Month'] = df2['_Month']
    ret_df['Day'] = df2['Day']
    # change to use parse_entry()
    ret_df['Entry'] = df2['Entry']
    ret_df['People'] = np.nan
    ret_df['Places'] = np.nan
    ret_df['FolioReference'] = df2['[Folio Reference]']
    ret_df['EntryType'] = np.nan
    ret_df['Ledger'] = np.nan
    ret_df['Quantity'] = df2['Quantity']
    ret_df['Commodity'] = df2['Commodity']
    ret_df['SL'] = df2[27]
    ret_df['SS'] = df2[28]
    ret_df['SD'] = df2[29]
    ret_df['Colony'] = df2['Colony']
    ret_df['CL'] = df2[32]
    ret_df['CS'] = df2[33]
    ret_df['CD'] = df2[34]
    ret_df['ArchMat'] = df2['[ArchMat]']
    ret_df['GenMat'] = df2['[GenMat]']
    ret_df['Final'] = df2['Final']
    ret_df['ExtraNotes'] = np.nan

    return ret_df
    # pass

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
