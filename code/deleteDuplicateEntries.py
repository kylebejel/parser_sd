import pandas as pd
import numpy as np

data = pd.read_excel("C_1760_001_FINAL_.xlsx", header=1)

print(data.shape)
print(data.to_string())
for idx in range(0, data.shape[0]-1):
  print(str(idx) + ' ' + str(data['[EntryID]'][idx+1])[:-1] + ' ' + str(data['[EntryID]'][idx]))
  if str(data['[EntryID]'][idx+1])[:-1] == str(data['[EntryID]'][idx]):#'a' in data['[EntryID]'][idx+1] or 'A' in data['[EntryID]'][idx+1]:
    print("found one")
    data = data.drop(idx)
data = data.reset_index(drop=True)
print(data.shape)
print(data.to_string())