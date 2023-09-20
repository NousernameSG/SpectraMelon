# List of Miscellaneous Functions that Supports the main Functionalities of the Program

import pandas as pd
import os

# Clears cli screen
def cls():
    os.system('cls' if os.name=='nt' else 'clear')

# Function to Delete path from pending analysis array
def Element_Remover(removeValue, targetArray):
    while True:
        try:
            targetArray.pop(int(removeValue))
            break
        except IndexError:
            Ack = input("Specified Entry Does not Exist in the Array \nPress Enter to Continue")
            return False

# Reads input data file and converts it into a dataframe
def Input_File_Reader(input_file):
    file_name, file_extension = os.path.splitext(input_file)
    if file_extension == ".xlsx" or file_extension == ".xls":
        Current_File = pd.read_excel(input_file, sheet_name='FFT Spectrum')
    elif file_extension == ".csv":
        Current_File = pd.read_csv(input_file)
    del file_extension

    return Current_File, file_name
