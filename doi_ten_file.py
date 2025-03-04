
import glob 
import os
# change name of file
os.chdir("C:/Users/ADMIN/Downloads/CarTGMT/")
for index, oldfile in enumerate (glob.glob("*.*"), start=1): 
    newfile='{}{}.jpg'.format("", index)
    os.rename(oldfile, newfile)