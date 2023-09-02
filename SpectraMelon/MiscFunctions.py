# List of Miscellaneous Functions that Supports the main Functionalities of the Program

# Function to Delete path from pending analysis array
def Element_Remover(removeValue, targetArray):
    while True:
        try:
            targetArray.pop(int(removeValue))
            break
        except IndexError:
            Ack = input("Specified Entry Does not Exist in the Array \nPress Enter to Continue")
            return False
