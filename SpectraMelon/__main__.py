# SpectraMelon : Audio Spetrum Processor
# Version | Date : 0.1.0-beta | 7 Oct 2023
# Author : NousernameSG

import os
import progressbar
import pandas as pd
import matplotlib.pyplot as plt

#Importing Other Program Scripts
from InputChecker import InputChecker as ic
import MiscFunctions as mf
import FindingFolders as ff


#Setting up progress bar settings
widgets=[progressbar.Percentage(), ' ', progressbar.GranularBar(), ' ', progressbar.ETA(), ]


########## Storage Arrays/Variables ##########
LowerBound_Frequency = 100
UpperBound_Frequency = 1000
FrequencyRange_Segment = 100 # The range of Frequencies for each segment (e.g. 100 ~ 199 Hz -> 100 Hz Range), this must be a multiple of LBF and UBF
NumberOfSegments = (UpperBound_Frequency - LowerBound_Frequency)/FrequencyRange_Segment
DataFiles = []


########## Main Program Functions ##########
#Function to Analyze the files and store the output (Peak Frequency & Q-Factor)
def analyze_Files():
    global LowerBound_Frequency, UpperBound_Frequency, FrequencyRange_Segment, NumberOfSegments, DataFiles, AnalyzedData, widgets

    AnalyzedData = pd.DataFrame()

    print(f"\nExtracting data from files:\n")
    with progressbar.ProgressBar(max_value=len(DataFiles), widgets=widgets) as bar:
        #Recurring for all the data files in the list
        for i in range(0, len(DataFiles)):
            #Updating Progress Bar
            bar.update(i)

            #Reading Files
            Current_File, file_name = mf.Input_File_Reader(DataFiles[i])
            if 'Amplitude Ratio' in Current_File.columns:
                AmplitudeData = pd.DataFrame(Current_File, columns=['Frequency (Hz)','Amplitude Ratio'])
            else:
                AmplitudeData = pd.DataFrame(Current_File, columns=['Frequency (Hz)','Absolute Amplitude (a.u.)'])

            # Drop Rows with Frequnecy below and above a certain frequncy in Hz
            # 3rd below this is to set the starting row to the correct index as Q-Factor is sensitive to the index
            AmplitudeData.drop(AmplitudeData[AmplitudeData['Frequency (Hz)'] < LowerBound_Frequency].index, inplace=True)
            AmplitudeData.drop(AmplitudeData[AmplitudeData['Frequency (Hz)'] >= UpperBound_Frequency].index, inplace=True)
            AmplitudeData = AmplitudeData.reset_index(drop=True)


            # Extracting the data for the different segments
            PeakFrequencies = pd.DataFrame(columns=["Frequency Range", "Peak Frequency"])
            for j in range(0, int(NumberOfSegments)):
                RestrictedAmpData = AmplitudeData.copy()
                RestrictedAmpData.drop(RestrictedAmpData[RestrictedAmpData['Frequency (Hz)'] < (LowerBound_Frequency + j*FrequencyRange_Segment)].index, inplace=True)
                RestrictedAmpData.drop(RestrictedAmpData[RestrictedAmpData['Frequency (Hz)'] >= (LowerBound_Frequency + (j+1)*FrequencyRange_Segment)].index, inplace=True)
                RestrictedAmpData = RestrictedAmpData.reset_index(drop=True)


                # Extracting Max Frequncy & Amplitude Data
                MaximumAmplitude = RestrictedAmpData.iloc[RestrictedAmpData.iloc[:,1].idxmax()]
                MaximumFrequency = MaximumAmplitude.iloc[0,]
                TempDataFrame = pd.DataFrame({"Frequency Range": [(str(LowerBound_Frequency + j*FrequencyRange_Segment) + ' ~ ' + str(LowerBound_Frequency + (j+1)*FrequencyRange_Segment))], "Peak Frequency": [MaximumFrequency]})
                PeakFrequencies = pd.concat([PeakFrequencies, TempDataFrame], ignore_index=True)

            del TempDataFrame

            # Extracts Q-Factor of each point (Comparing with the Non-Restricted interval to find Q-Factor),
            # and exports all of the data into dataframes for further analysis or saving

            # DataFrame to be used to store the 10 sets of Data for each file, data right below here only have to be input once, thus it is defined here
            IntermediateDataFrame = pd.DataFrame({'Queue':[i],
                                                'Path':[file_name]})

            for j in range(0, PeakFrequencies.shape[0]):
                MaximumAmplitude = AmplitudeData[AmplitudeData["Frequency (Hz)"] == PeakFrequencies.iloc[j,1]]
                MaximumFrequency = MaximumAmplitude.iloc[0,0]
                MaximumAmplitude_Index = int(AmplitudeData[AmplitudeData.iloc[:,0]==MaximumAmplitude.iloc[0,0]].index[0])

                # Setting Up Q-Factor Calculation Variables
                HalfMaximumAmplitude = MaximumAmplitude.iloc[0,1]/2
                LowerBoundIntercept_Index = None     # Lower Bound Intercept Index - to find the equation of the line used in calculating the frequency at intercept
                UpperBoundIntercept_Index = None     # Upper Bound Intecept Index
                LowerBoundIntercept_Frequency = 0    # Frequency at LBI - Set to zero for auto bounding if there is a situation where there isn't an actual intercept
                UpperBoundIntercept_Frequency = 0    # Frequncy at UBI - Set to zero for exception handle to work

                # Finding Frequency of Lower Bound Intercept
                # Starts from the Index of the Peak Freq down to reach the closest Intercept
                for k in range(MaximumAmplitude_Index,0,-1):
                    LowerV = AmplitudeData.iloc[k-1,1]
                    UpperV = AmplitudeData.iloc[k,1]
                    # When the Condition that one value is below and the other is above the
                    # half magnitude line, the LBI Variable is set to be used in further calculations
                    if LowerV <= HalfMaximumAmplitude and UpperV >= HalfMaximumAmplitude:
                        LowerBoundIntercept_Index = k
                        x1 = AmplitudeData.iloc[LowerBoundIntercept_Index-1,0]
                        x2 = AmplitudeData.iloc[LowerBoundIntercept_Index,0]
                        y1 = AmplitudeData.iloc[LowerBoundIntercept_Index-1,1]
                        y2 = AmplitudeData.iloc[LowerBoundIntercept_Index,1]

                        Gradient = (y2-y1)/(x2-x1)
                        Constant = y2-Gradient*x2

                        LowerBoundIntercept_Frequency = (HalfMaximumAmplitude-Constant)/Gradient   # Calculating the Intercept Frequency of the Lower Bound
                        del x1, x2, y1, y2, Gradient, Constant, LowerV, UpperV
                        break

                # Finding Frequency of Upper Bound Intercept
                #Stars from the Index of the Peak Frequncy Up to reach the closest intercept
                for k in range(MaximumAmplitude_Index,AmplitudeData.shape[0]-1):
                    LowerV = AmplitudeData.iloc[k,1]
                    UpperV = AmplitudeData.iloc[k+1,1]
                    # When the Condition that one value is below and the other is above the
                    # half magnitude line, the UBI Variable is set to be used in further calculations
                    if LowerV >= HalfMaximumAmplitude and UpperV <= HalfMaximumAmplitude:
                        UpperBoundIntercept_Index = k
                        x1 = AmplitudeData.iloc[UpperBoundIntercept_Index,0]
                        x2 = AmplitudeData.iloc[UpperBoundIntercept_Index+1,0]
                        y1 = AmplitudeData.iloc[UpperBoundIntercept_Index,1]
                        y2 = AmplitudeData.iloc[UpperBoundIntercept_Index+1,1]

                        Gradient = (y2-y1)/(x2-x1)
                        Constant = y2-Gradient*x2

                        UpperBoundIntercept_Frequency = (HalfMaximumAmplitude-Constant)/Gradient   # Calculating the Intercept Frequency of the Lower Bound
                        del x1, x2, y1, y2, Gradient, Constant, LowerV, UpperV
                        break

                # Calculating Q-Factor
                if LowerBoundIntercept_Frequency == 0 and UpperBoundIntercept_Frequency == 0:
                    qFactor = None                          # Exception Handle for the case where there doesn't exist an intercept, extremely unlikely but it's nice to have
                elif LowerBoundIntercept_Frequency == 0:
                    qFactor = MaximumFrequency/UpperBoundIntercept_Frequency
                else:
                    qFactor = MaximumFrequency/(UpperBoundIntercept_Frequency-LowerBoundIntercept_Frequency)   # The bracketed term is the Delta f used for Q-Factor calculations

                # Adding File Path and calculations into a DataFrames for Storage
                if 'Amplitude Ratio' in Current_File.columns:
                    TempStore_Anz = pd.DataFrame({('Peak Frequency ' + str((PeakFrequencies.iloc[j,0]))):[MaximumFrequency],
                                                ('Amplitude Ratio ' + str((PeakFrequencies.iloc[j,0]))):[MaximumAmplitude.iloc[0,1]],
                                                ('Q-Factor ' + str((PeakFrequencies.iloc[j,0]))):[qFactor]})
                else:
                    TempStore_Anz = pd.DataFrame({('Peak Frequency ' + str((PeakFrequencies.iloc[j,0]))):[MaximumFrequency],
                                                ('Absolute Amplitude (a.u.) ' + str((PeakFrequencies.iloc[j,0]))):[MaximumAmplitude.iloc[0,1]],
                                                ('Q-Factor ' + str((PeakFrequencies.iloc[j,0]))):[qFactor]})

                # Saves data in a DataFrame, but further processing is needed for AnalyzedData (Saved as IntermediateDataFrame) due to the axis used
                IntermediateDataFrame = pd.concat([IntermediateDataFrame, TempStore_Anz], axis=1)


            # Putting Data of the file in queue into the final DataFrame
            AnalyzedData = pd.concat([AnalyzedData, IntermediateDataFrame])
            AnalyzedData.reset_index()
            del IntermediateDataFrame, TempStore_Anz


    # Saving all of the Analyzed Data as an Excel File
    AnalyzedData.to_excel(os.path.join(ff.get_download_folder(), "Output Data.xlsx"), sheet_name='Spectrum Data', index=False)
    AnalyzedData = pd.DataFrame(columns=AnalyzedData.columns)

# Experimental: Function to change Amplitude Column to Amplitude Ratio (Amplitude of Peak Freq = 1, the rests are ratios of the peak)
def AmplitudeNormalizer():
    global LowerBound_Frequency, UpperBound_Frequency, DataFiles, widgets

    with progressbar.ProgressBar(max_value=len(DataFiles), widgets=widgets) as bar:

        print(f"\nNormalizing Data:\n")

        #Normalizing Data
        for i in range(0, len(DataFiles)):
            #Updating Progress Bar
            bar.update(i)

            Current_File, file_name = mf.Input_File_Reader(DataFiles[i])
            AmplitudeData = pd.DataFrame(Current_File, columns=['Frequency (Hz)','Absolute Amplitude (a.u.)'])

            # Drop Rows with Frequnecy below and above a certain frequncy in Hz
            AmplitudeData.drop(AmplitudeData[AmplitudeData['Frequency (Hz)'] < LowerBound_Frequency].index, inplace=True)
            AmplitudeData.drop(AmplitudeData[AmplitudeData['Frequency (Hz)'] >= UpperBound_Frequency].index, inplace=True)
            AmplitudeData = AmplitudeData.reset_index(drop=True)

            # Extracting Amplitude of Peak Frequency
            MaximumAmplitude = AmplitudeData.iloc[AmplitudeData.iloc[:,1].astype(float).idxmax()]
            MaximumAmplitude = MaximumAmplitude.iloc[1,]
            AmpRatio = pd.DataFrame([], columns=['Amplitude Ratio'])

            # Calculating Amplitude Percentages
            AmpRatio['Amplitude Ratio'] = AmplitudeData['Absolute Amplitude (a.u.)']
            AmpRatio = AmpRatio.div(MaximumAmplitude, axis=1)

            # Merging Calculated Data and Saving DataFrame as Excel Output
            AmpRatioData = pd.concat([AmplitudeData, AmpRatio],axis=1)
            AmpRatioData.to_csv(file_name + " (Mod).csv", index = False)
            AmpRatioData = pd.DataFrame(columns=AmpRatioData.columns)
            DataFiles.pop(i)
            DataFiles.insert(i, file_name + " (Mod).csv")

# Function to Calculate the Averaged Data (Mean of Each Row of Entry - They must have the same number of Inputs)
# Note: This will calculate the average of all of the Data given and output it an excel sheet
def TestAvgCalculator():
    global DataFiles

    SavePath = []
    Reduced_dFiles = []
    NewOutput_dFiles = []
    WatermelonLetter = ''   # Valid Inputs (A, B, Amb)
    TestRepetitions = 0
    Freq_Axis = pd.DataFrame()
    input_data = pd.DataFrame()

    # Mini Feature to count how many repetitions are needed
    for i in range (0,len(DataFiles)):
        SelectedPath = os.path.dirname(os.path.dirname(DataFiles[i]))
        if os.path.join(SelectedPath, 'A Test') in DataFiles[i]:
            if any(os.path.join(SelectedPath, 'A Test') in SavePath for (flag) in SavePath) == False:
                TestRepetitions += 1
                SavePath.append(os.path.join(SelectedPath, 'A Test'))
        elif os.path.join(SelectedPath, 'B Test') in DataFiles[i]:
            if any(os.path.join(SelectedPath, 'B Test') in SavePath for (flag) in SavePath) == False:
                TestRepetitions += 1
                SavePath.append(os.path.join(SelectedPath, 'B Test'))
        elif os.path.join(SelectedPath, 'Amb Test') in DataFiles[i]:
            if any(os.path.join(SelectedPath, 'Amb Test') in SavePath for (flag) in SavePath) == False:
                TestRepetitions += 1
                SavePath.append(os.path.join(SelectedPath, 'Amb Test'))

    # Resetting Save Path
    SavePath = []

    print(f"\nCalculating Averaged Data Set:\n")
    with progressbar.ProgressBar(max_value=len(DataFiles), widgets=widgets) as bar:
        #Recurring for all the data files in the list
        for i in range(0, len(DataFiles)):
            #Updating Progress Bar
            bar.update(i)

        # Calculating Averaged Data sets
        for i in range (0,TestRepetitions):
            SelectedPath = os.path.dirname(os.path.dirname(DataFiles[0]))
            # Checking if path with Specific Watermelon letter is in SavePath
            if 'A Test' in os.path.dirname(DataFiles[0]):
                WatermelonLetter = 'A'
                for j in range(0, len(DataFiles)):
                    if os.path.join(SelectedPath, 'A Test') in DataFiles[j]:
                        Reduced_dFiles.append(DataFiles[j])
                # Removing files added into Reduced_dFiles from the main DataFiles list
                DataFiles = [elements for elements in DataFiles if os.path.join(SelectedPath, 'A Test') not in elements]
            elif 'B Test' in os.path.dirname(DataFiles[0]):
                WatermelonLetter = 'B'
                for j in range(0, len(DataFiles)):
                    if os.path.join(SelectedPath, 'B Test') in DataFiles[j]:
                        Reduced_dFiles.append(DataFiles[j])
                # Removing files added into Reduced_dFiles from the main DataFiles list
                DataFiles = [elements for elements in DataFiles if os.path.join(SelectedPath, 'B Test') not in elements]
            elif 'Amb Test' in os.path.dirname(DataFiles[0]):
                WatermelonLetter = 'Amb'
                for j in range(0, len(DataFiles)):
                    if os.path.join(SelectedPath, 'Amb Test') in DataFiles[j]:
                        Reduced_dFiles.append(DataFiles[j])
                # Removing files added into Reduced_dFiles from the main DataFiles list
                DataFiles = [elements for elements in DataFiles if os.path.join(SelectedPath, 'Amb Test') not in elements]

            for j in range(0, len(Reduced_dFiles)):
                file_name, file_extension = os.path.splitext(Reduced_dFiles[j])
                del file_name
                if file_extension == ".xlsx" or file_extension == ".xls":
                    Current_File = pd.read_excel(Reduced_dFiles[j], sheet_name='FFT Spectrum')
                elif file_extension == ".csv":
                    Current_File = pd.read_csv(Reduced_dFiles[j])

                # Adding Freq Axis from FIRST input File into dataframe
                if Freq_Axis.empty:
                    Freq_Axis = Current_File.iloc[:,0]

                # Adding Amplitude Data into a DataFrame to Calculate Averaged Data
                if 'Amplitude Ratio' in Current_File.columns:
                    input_data[j] = Current_File.iloc[:,2]
                else:
                    input_data[j] = Current_File.iloc[:,1]

            # Calculating Averaged Data and Saving File as Excel
            AveragedData = pd.DataFrame([], columns=['Frequency (Hz)', 'Amplitude Ratio'])
            AveragedData['Frequency (Hz)'] = Freq_Axis
            AveragedData['Amplitude Ratio'] = input_data.mean(axis=1, skipna=True)
            input_data = pd.DataFrame(columns=input_data.columns)

            # Rebasing Amplitude Ratio Back to one for the peak value
            MaximumAmplitude = AveragedData.iloc[AveragedData.iloc[:,1].idxmax()]
            MaximumAmplitude = MaximumAmplitude.iloc[1,]
            AveragedData['Amplitude Ratio'] = AveragedData['Amplitude Ratio'].div(MaximumAmplitude)

            ## Checking if it is A Test or B Test Avg
            BasePath = SelectedPath
            if WatermelonLetter == 'A':
                if not os.path.exists(os.path.join(BasePath, 'A Test Avg')):
                    os.makedirs(os.path.join(BasePath, 'A Test Avg'))
                AveragedData.to_csv(os.path.join(os.path.join(BasePath, 'A Test Avg'), "FFT Spectrum.csv"), index=False)
                AddedPath = os.path.join(os.path.join(BasePath, 'A Test Avg'), "FFT Spectrum.csv")
            elif WatermelonLetter == 'B':
                if not os.path.exists(os.path.join(BasePath, 'B Test Avg')):
                    os.makedirs(os.path.join(BasePath, 'B Test Avg'))
                AveragedData.to_csv(os.path.join(os.path.join(BasePath, 'B Test Avg'), "FFT Spectrum.csv"), index=False)
                AddedPath = os.path.join(os.path.join(BasePath, 'B Test Avg'), "FFT Spectrum.csv")
            elif WatermelonLetter == 'Amb':
                if not os.path.exists(os.path.join(BasePath, 'Amb Test Avg')):
                    os.makedirs(os.path.join(BasePath, 'Amb Test Avg'))
                AveragedData.to_csv(os.path.join(os.path.join(BasePath, 'Amb Test Avg'), "FFT Spectrum.csv"), index=False)
                AddedPath = os.path.join(os.path.join(BasePath, 'Amb Test Avg'), "FFT Spectrum.csv")
            else:
                Ack = input("Bruh - L356")
                del Ack

            # Adding Files into a new list to replace the DataFiles
            Reduced_dFiles.append(AddedPath)
            NewOutput_dFiles.extend(Reduced_dFiles)
            Reduced_dFiles = []

    return NewOutput_dFiles

# Function to Graph out the FFT Graph
def FFTPlotter(input_array):
    print(f"\nPlotting FFT Spectrums:\n")
    with progressbar.ProgressBar(max_value=len(input_array), widgets=widgets) as bar:

        #Plotting Graph
        for i in range(0, len(input_array)):
            #Updating Progress Bar
            bar.update(i)

            Current_File, file_name = mf.Input_File_Reader(input_array[i])

            #Labelling X-Axis
            plt.xlabel('Frequency (Hz)')

            # Checking if Amplitude Ratio Exists (If not, Raw Amp would be used)
            PercentAmpExist = 'Amplitude Ratio' in Current_File.columns
            if PercentAmpExist == True:
                plt.ylabel('Amplitude Ratio')
                plt.plot(Current_File['Frequency (Hz)'], Current_File['Amplitude Ratio'], color='black', linewidth=0.5)
            else:
                plt.ylabel('Absolute Amplitude (a.u.)')
                plt.plot(Current_File['Frequency (Hz)'], Current_File['Absolute Amplitude (a.u.)'], color='black', linewidth=0.5)

            # Saving File and clearing diagram
            plt.savefig(file_name + ' Plot.jpg', dpi=400)
            plt.clf()

# Function to Select Specific Program Feature
def SelectFeature():
    global DataFiles
    while True:
        mf.cls()
        print("Queue: ")
        for i in range(0,len(DataFiles)):
            print(i, end="")
            print(" \t ", end="")
            print(DataFiles[i])
        Fea_Options = input("\n\nOptions \n[1] Amplitude Ratio Calculator \n[2] Averaged Data Calculator \n[3] FFT Spectrum Plotter \n[4] Spectrum Analyzer \n[5] Full Suite \n[6] Back \n[7] Exit \nSelect Option: ")
        if ic.int_Checker(Fea_Options) == False:
            continue
        else:
            Fea_Options = int(Fea_Options)

        match Fea_Options:
            case 1:
                # Option 1 : Amplitude Percentage Calculator
                AmplitudeNormalizer()
                DataFiles = []
                break

            case 2:
                # Option 2 : Averaged Data Calculator
                DataFiles = TestAvgCalculator()
                break

            case 3:
                # Option 3 : FFT Spectrum Graph Plotter
                FFTPlotter(DataFiles)
                DataFiles = []
                break

            case 4:
                # Option 4 : Spectrum Analyzer
                analyze_Files()
                DataFiles = []
                break

            case 5:
                # Option 5 : Full Suite (Percentage Calculator -> Averaged Data -> FFT Graph Plotter -> Analyzer)
                AmplitudeNormalizer()
                DataFiles = TestAvgCalculator()
                FFTPlotter(DataFiles)
                analyze_Files()
                DataFiles = []
                break

            case 6:
                #Option 6 : Back to Previous Page
                break

            case 7:
                # Option 7 : Exit Program
                mf.cls()
                exit()

            case _:
                ack = input("Invalid Option")
                del ack


########## Inital Program Page ##########
while True:
    mf.cls()
    print(' INFORMATION '.center(100, '*'))
    print("SpectraMelon: Audio Spectrum Processor")
    print("Build: v0.1.0-beta (7 Oct 2023)", end="\n\n")
    print("This Audio Spectrum Processor is built for the Research and Development Stage of the SRP Project")
    print("\"Investigation of Acoustic Properties of Water Melon\"", end="\n\n")
    print(' PROGRAM '.center(100, '*'), end="\n\n")
    print("Queue: ")
    for i in range(0,len(DataFiles)):
        print(i, end="")
        print(" \t ", end="")
        print(DataFiles[i])

    ## Program Selection Option
    aF_Options = input("\n\nOptions \n[1] Add Path \n[2] Remove Path \n[3] Continue \n[4] Exit \nSelect Option: ")
    if ic.int_Checker(aF_Options) == False:
        continue
    else:
        aF_Options = int(aF_Options)

    match aF_Options:
        case 1:
            # Option 1 : Adding Data Files into the list to be analyzed
            Data_File_Path = input("Input the Data File Path: ")
            if ic.Path_Checker(Data_File_Path) == False:
                Ack = input("This File Path Does not exist! \nPress Enter to Continue")
                continue
            elif ic.Extension_Checker(Data_File_Path) == False:
                Ack = input("Wrong File Extension (.xlsx/.xls/.csv Files only) \nPress Enter to Continue")
                continue
            elif ic.Duplicate_Path_Checker(Data_File_Path, DataFiles) == True:
                Ack = input("This file path already exists in the queue \nPress Enter to Continue")
                continue
            else:
                DataFiles.append(Data_File_Path)

        case 2:
            # Option 2 : Removing Data Files from the list to be analyzed
            Remove_Data_File = input("\nInput the Numerical Position of file to be removed (First File is 0): ")
            if ic.int_Checker(Remove_Data_File) == False:
                continue
            if mf.Element_Remover(Remove_Data_File, DataFiles) == False:
                continue

        case 3:
            # Option 3 : Select Program Processor
            SelectFeature()
            continue

        case 4:
            # Option 4 : Exit Program
            mf.cls()
            exit()

        case _:
            ack = input("Invalid Option")
            del ack
