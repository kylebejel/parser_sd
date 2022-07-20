import pandas as pd
import numpy as np

data = pd.read_excel("C_1760_003_FINAL_.xlsx", header=1)

for idx in range(0, data.shape[0]-1):
  if str(data['[EntryID]'][idx+1])[:-1] == str(data['[EntryID]'][idx]):#'a' in data['[EntryID]'][idx+1] or 'A' in data['[EntryID]'][idx+1]:
    data = data.drop(idx)
data = data.reset_index(drop=True)