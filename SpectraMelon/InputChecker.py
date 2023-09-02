# Script to check the vadility of the input by user

import os

def Path_Checker(input_path):
    while True:
        try:
            out = os.path.exists(input_path)
            break
        except:
            return out

def Extension_Checker(input_path):
    while True:
        file_name, file_extension = os.path.splitext(input_path)
        del file_name
        if file_extension != ".xlsx" and file_extension != ".xls" and file_extension != ".csv":
            del file_extension
            return False
        else:
            del file_extension
            return True

def Duplicate_Path_Checker(input_path, input_array):
    if input_path in input_array:
        return True
    else:
        return False

def int_Checker(testValue):
    while True:
        try:
            int(testValue)
            break
        except ValueError:
            Ack = input("Non-Integer Input detected \nPress Enter to Continue")
            del Ack
            return False
