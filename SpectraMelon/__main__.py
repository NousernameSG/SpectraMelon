# SpectraMelon : Audio Spectrum Analyzer
# Version | Date : 0.1.0-alpha | 20 Sept 2023
# Author : NousernameSG

import os
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go

#Importing Other Program Scripts
from InputChecker import InputChecker as ic
import MiscFunctions as mf
import FindingFolders as ff


########## Storage Arrays/Variables ##########
LowerBound_Freq = 100
UpperBound_Freq = 1000
Freq_SegmentRange = 100 # The range of Frequencies for each segment (e.g. 100 ~ 199 Hz -> 100 Hz Range), this must be a multiple of LBF and UBF
NumberOfSegments = (UpperBound_Freq - LowerBound_Freq)/Freq_SegmentRange
dFiles = []
AnalyzedData = pd.DataFrame([])

# Specific Arrays for TablePlotter
To_Be_Plotted_Data = pd.DataFrame([])


########## Main Program Functions ##########
#Function to Analyze the files and store the output (Peak Frequency & Q-Factor)
def analyze_Files():
    global LowerBound_Freq, UpperBound_Freq, Freq_SegmentRange, NumberOfSegments, dFiles, AnalyzedData, To_Be_Plotted_Data


    #Recurring for all the data files in the list
    for i in range(0, len(dFiles)):
        Current_File, file_name = mf.Input_File_Reader(dFiles[i])
        TempStore_Anz = pd.DataFrame({'Queue':[i],
                                      'Path':[file_name]})
        if 'Amplitude Ratio' in Current_File.columns:
            AmpData = pd.DataFrame(Current_File, columns=['Frequency (Hz)','Amplitude Ratio'])
        else:
            AmpData = pd.DataFrame(Current_File, columns=['Frequency (Hz)','Absolute Amplitude (a.u.)'])

        # Drop Rows with Frequnecy below and above a certain frequncy in Hz
        # 3rd below this is to set the starting row to the correct index as Q-Factor is sensitive to the index
        AmpData.drop(AmpData[AmpData['Frequency (Hz)'] < LowerBound_Freq].index, inplace=True)
        AmpData.drop(AmpData[AmpData['Frequency (Hz)'] >= UpperBound_Freq].index, inplace=True)
        AmpData = AmpData.reset_index(drop=True)

        # Extracting the data for the different segments
        MaxFreqPoints = pd.DataFrame(columns=["Frequency Range", "Peak Frequency"])
        for j in range(0, int(NumberOfSegments)):
            RestrictedAmpData = AmpData.copy()
            RestrictedAmpData.drop(RestrictedAmpData[RestrictedAmpData['Frequency (Hz)'] < (LowerBound_Freq + j*Freq_SegmentRange)].index, inplace=True)
            RestrictedAmpData.drop(RestrictedAmpData[RestrictedAmpData['Frequency (Hz)'] >= (LowerBound_Freq + (j+1)*Freq_SegmentRange)].index, inplace=True)
            RestrictedAmpData = RestrictedAmpData.reset_index(drop=True)


            # Extracting Max Frequncy & Amplitude Data
            MaxAmp = RestrictedAmpData.iloc[RestrictedAmpData.iloc[:,1].idxmax()]
            MaxFreq = MaxAmp.iloc[0,]
            TempDataFrame = pd.DataFrame({"Frequency Range": [(str(LowerBound_Freq + j*Freq_SegmentRange) + ' ~ ' + str(LowerBound_Freq + (j+1)*Freq_SegmentRange))], "Peak Frequency": [MaxFreq]})
            MaxFreqPoints = pd.concat([MaxFreqPoints, TempDataFrame], ignore_index=True)

        del TempDataFrame

        for j in range(0, MaxFreqPoints.shape[0]):
            MaxAmp = AmpData[AmpData["Frequency (Hz)"] == MaxFreqPoints.iloc[j,1]]
            MaxFreq = MaxAmp.iloc[0,0]
            MaxAmpIdx = int(AmpData[AmpData.iloc[:,0]==MaxAmp.iloc[0,0]].index[0])

        # Setting Up Q-Factor Calculation Variables
        Half_MxAmp = MaxAmp.iloc[1,]/2
        LBI_Idx = None     # Lower Bound Intercept Index - to find the equation of the line used in calculating the frequency at intercept
        UBI_Idx = None     # Upper Bound Intecept Index
        LBI_Freq = 0    # Frequency at LBI - Set to zero for auto bounding if there is a situation where there isn't an actual intercept
        UBI_Freq = 0    # Frequncy at UBI - Set to zero for exception handle to work

        # Finding Frequency of Lower Bound Intercept
        # Starts from the Index of the Peak Freq down to reach the closest Intercept
        for j in range(MaxAmpIdx,0,-1):
            LowerV = AmpData.iloc[j-1,1]
            UpperV = AmpData.iloc[j,1]
            # When the Condition that one value is below and the other is above the
            # half magnitude line, the LBI Variable is set to be used in further calculations
            if LowerV <= Half_MxAmp and UpperV >= Half_MxAmp:
                LBI_Idx = j
                x1 = AmpData.iloc[LBI_Idx-1,0]
                x2 = AmpData.iloc[LBI_Idx,0]
                y1 = AmpData.iloc[LBI_Idx-1,1]
                y2 = AmpData.iloc[LBI_Idx,1]

                Gradient = (y2-y1)/(x2-x1)
                Constant = y2-Gradient*x2

                LBI_Freq = (Half_MxAmp-Constant)/Gradient   # Calculating the Intercept Frequency of the Lower Bound
                del x1, x2, y1, y2, Gradient, Constant, LowerV, UpperV
                break

        # Finding Frequency of Upper Bound Intercept
        #Stars from the Index of the Peak Frequncy Up to reach the closest intercept
        for j in range(MaxAmpIdx,AmpData.shape[0]-1):
            LowerV = AmpData.iloc[j,1]
            UpperV = AmpData.iloc[j+1,1]
            # When the Condition that one value is below and the other is above the
            # half magnitude line, the UBI Variable is set to be used in further calculations
            if LowerV >= Half_MxAmp and UpperV <= Half_MxAmp:
                UBI_Idx = j
                x1 = AmpData.iloc[UBI_Idx,0]
                x2 = AmpData.iloc[UBI_Idx+1,0]
                y1 = AmpData.iloc[UBI_Idx,1]
                y2 = AmpData.iloc[UBI_Idx+1,1]

                Gradient = (y2-y1)/(x2-x1)
                Constant = y2-Gradient*x2

                UBI_Freq = (Half_MxAmp-Constant)/Gradient   # Calculating the Intercept Frequency of the Lower Bound
                del x1, x2, y1, y2, Gradient, Constant, LowerV, UpperV
                break

        # Calculating Q-Factor
        if LBI_Freq == 0 and UBI_Freq == 0:
            qFactor = None                          # Exception Handle for the case where there doesn't exist an intercept, extremely unlikely but it's nice to have
        elif LBI_Freq == 0:
            qFactor = MaxFreq/UBI_Freq
        else:
            qFactor = MaxFreq/(UBI_Freq-LBI_Freq)   # The bracketed term is the Delta f used for Q-Factor calculations

        # Labelling Test Number
        test_number = None
        if 'Test 1' in file_name:
            test_number = 1
        elif 'Test 2' in file_name:
            test_number = 2
        elif 'Test 3' in file_name:
            test_number = 3
        elif 'Avg' in file_name:
            test_number = 'Avg'
        else:
            test_number = None

        # Adding File Path and calculations into a DataFrames for Storage
        if 'Amplitude Ratio' in Current_File.columns:
            TempStore_Anz = pd.DataFrame({'Test Number':[test_number],
                                          'Peak Frequency':[MaxFreq],
                                          'Amplitude Ratio':[MaxAmp.iloc[1,]],
                                          'Q-Factor':[qFactor]})
            TempStore_Plot = pd.DataFrame({'Test':[test_number],
                                           'Peak Freq':[round(MaxFreq,3)],
                                           'Amp Ratio':[round(MaxAmp.iloc[1,],3)],
                                           'Q-Factor':[round(qFactor,3)]})
        else:
            TempStore_Anz = pd.DataFrame({'Test Number':[test_number],
                                          'Peak Frequency':[MaxFreq],
                                          'Absolute Amplitude (a.u.)':[MaxAmp.iloc[1,]],
                                          'Q-Factor':[qFactor]})
            TempStore_Plot = pd.DataFrame({'Test':[test_number],
                                           'Peak Freq':[round(MaxFreq,3)],
                                           'Amplitude':[round(MaxAmp.iloc[1,],3)],
                                           'Q-Factor':[round(qFactor,3)]})

        AnalyzedData = pd.concat([AnalyzedData, TempStore_Anz], ignore_index=True)
        To_Be_Plotted_Data = pd.concat([To_Be_Plotted_Data, TempStore_Plot], ignore_index=True)
        del TempStore_Anz, TempStore_Plot


        ##### Preparing Data to be Plotted by Data Plotters #####

        #Function Variables
        SavePath = ''
        WatermelonLetter = ''   # Accepted Inputs (A, B, Amb)
        TestRepetitions = 0
        AvgFileExists = False

        # Adding Data into Array for Table Plotter
        SelectedPath = os.path.dirname(file_name)
        # Checking if path with Specific Watermelon letter is in SavePath
        if 'A Test' in SelectedPath and os.path.dirname(SelectedPath) in SavePath:
            pass
        elif 'A Test' in SelectedPath and not os.path.dirname(SelectedPath) in SavePath:
            SavePath = os.path.dirname(SelectedPath)
            WatermelonLetter = 'A'
            for j in range(0, len(dFiles)):
                if os.path.join(os.path.dirname(SelectedPath), 'A Test') in dFiles[j]:
                    TestRepetitions += 1
                    PlotRep = 1
            for j in range(0, len(dFiles)):
                if os.path.join(os.path.dirname(SelectedPath), 'A Test Avg') in dFiles[j]:
                    AvgFileExists = True
        elif 'B Test' in SelectedPath and os.path.dirname(SelectedPath) in SavePath:
            pass
        elif 'B Test' in SelectedPath and not os.path.dirname(SelectedPath) in SavePath:
            SavePath = os.path.dirname(SelectedPath)
            WatermelonLetter = 'B'
            for j in range(0, len(dFiles)):
                if os.path.join(os.path.dirname(SelectedPath), 'B Test') in dFiles[j]:
                    TestRepetitions += 1
                    PlotRep = 1
            for j in range(0, len(dFiles)):
                if os.path.join(os.path.dirname(SelectedPath), 'B Test Avg') in dFiles[j]:
                    AvgFileExists = True
        elif 'Amb Test' in SelectedPath and os.path.dirname(SelectedPath) in SavePath:
            pass
        elif 'Amb Test' in SelectedPath and not os.path.dirname(SelectedPath) in SavePath:
            SavePath = os.path.dirname(SelectedPath)
            WatermelonLetter = 'Amb'    # Special Code for Ambient Tests
            for j in range(0, len(dFiles)):
                if os.path.join(os.path.dirname(SelectedPath), 'Amb Test') in dFiles[j]:
                    TestRepetitions += 1
                    PlotRep = 1
            for j in range(0, len(dFiles)):
                if os.path.join(os.path.dirname(SelectedPath), 'Amb Test Avg') in dFiles[j]:
                    AvgFileExists = True

        # IMPORTANT: Avg File (If it Exists) should be the last file, this chuck is referrin to the code above
        # Calculating Values after tests for that expeiment has been ran
        # Counter to Find out how many iterations depending on number of input tests
        # Input Filter to ensure that the Variable isn't reset while on the same test set

        if AvgFileExists == True:
            if PlotRep == TestRepetitions-1:
                # Calculating Mean and adding it to the To be Plotted Dataframe
                MeanData = To_Be_Plotted_Data.mean(axis=0, skipna=True, numeric_only=True)
                MeanData = MeanData.to_frame().transpose()
                MeanData.at[0,'Test']='Mean'

                # Calculating SD and adding it to the To be Plotted Dataframe
                SDData = To_Be_Plotted_Data.std(skipna=True, numeric_only=True)
                SDData = SDData.to_frame().transpose()
                SDData.at[0,'Test']='SD'
                To_Be_Plotted_Data = pd.concat([To_Be_Plotted_Data, MeanData.round(3), SDData.round(3)], ignore_index=True)
                MeanData = SDData = None
                PlotRep += 1
            elif PlotRep == TestRepetitions:    # REMINDER: Avg File Must Be at the last Entry
                # Plotting Data and Flushing Variables
                TablePlotter(To_Be_Plotted_Data,SavePath,WatermelonLetter)
                To_Be_Plotted_Data = pd.DataFrame(columns=To_Be_Plotted_Data.columns)
                SavePath = ''
                WatermelonLetter = ''
                AvgFileExists = False
                PlotRep = 1
                TestRepetitions = 0
            elif PlotRep < TestRepetitions-1:
                PlotRep += 1
            else:
                Ack = input('Failure - Issue at Plotter variable Calculations')
                del Ack
        else:
            if PlotRep == TestRepetitions:
                # Calculating Mean and adding it to the To be Plotted Dataframe
                MeanData = To_Be_Plotted_Data.mean(axis=0, skipna=True)
                MeanData = MeanData.to_frame().transpose()
                MeanData.at[0,'Test']='Mean'

                # Calculating SD and adding it to the To be Plotted Dataframe
                SDData = To_Be_Plotted_Data.std()
                SDData = SDData.to_frame().transpose()
                SDData.at[0,'Test']='SD'
                To_Be_Plotted_Data = pd.concat([To_Be_Plotted_Data, MeanData.round(3), SDData.round(3)], ignore_index=True)
                MeanData = SDData = None

                # Plotting Data and Flushing Variables
                TablePlotter(To_Be_Plotted_Data,SavePath,WatermelonLetter)
                To_Be_Plotted_Data = pd.DataFrame(columns=To_Be_Plotted_Data.columns)
                SavePath = WatermelonLetter = ''
                PlotRep = 1
                TestRepetitions = 0
            elif PlotRep < TestRepetitions:
                PlotRep += 1
            else:
                Ack = input('Failure - Issue at Plotter variable Calculations')
                del Ack


    # Saving all of the Analyzed Data as an Excel File
    AnalyzedData.to_excel(os.path.join(ff.get_download_folder(), "Output Data.xlsx"), sheet_name='Spectrum Data', index=False)
    AnalyzedData = pd.DataFrame(columns=AnalyzedData.columns)

# Experimental: Function to change Amplitude Column to Amplitude Ratio (Amplitude of Peak Freq = 1, the rests are ratios of the peak)
def AmplitudeNormalizer():
    global LowerBound_Freq, UpperBound_Freq, dFiles
    for i in range(0, len(dFiles)):
        Current_File, file_name = mf.Input_File_Reader(dFiles[i])
        AmpData = pd.DataFrame(Current_File, columns=['Frequency (Hz)','Absolute Amplitude (a.u.)'])

        # Drop Rows with Frequnecy below and above a certain frequncy in Hz
        AmpData.drop(AmpData[AmpData['Frequency (Hz)'] < LowerBound_Freq].index, inplace=True)
        AmpData.drop(AmpData[AmpData['Frequency (Hz)'] >= UpperBound_Freq].index, inplace=True)
        AmpData = AmpData.reset_index(drop=True)

        # Extracting Amplitude of Peak Frequency
        MaxAmp = AmpData.iloc[AmpData.iloc[:,1].idxmax()]
        MaxAmp = MaxAmp.iloc[1,]
        AmpRatio = pd.DataFrame([], columns=['Amplitude Ratio'])

        # Calculating Amplitude Percentages
        AmpRatio['Amplitude Ratio'] = AmpData['Absolute Amplitude (a.u.)']
        AmpRatio = AmpRatio.div(MaxAmp, axis=1)

        # Merging Calculated Data and Saving DataFrame as Excel Output
        AmpRatioData = pd.concat([AmpData, AmpRatio],axis=1)
        AmpRatioData.to_csv(file_name + " (Mod).csv", index = False)
        AmpRatioData = pd.DataFrame(columns=AmpRatioData.columns)
        dFiles.pop(i)
        dFiles.insert(i, file_name + " (Mod).csv")

# Function to Calculate the Averaged Data (Mean of Each Row of Entry - They must have the same number of Inputs)
# Note: This will calculate the average of all of the Data given and output it an excel sheet
def TestAvgCalculator():
    global dFiles

    SavePath = []
    Reduced_dFiles = []
    NewOutput_dFiles = []
    WatermelonLetter = ''   # Valid Inputs (A, B, Amb)
    TestRepetitions = 0
    Freq_Axis = pd.DataFrame()
    input_data = pd.DataFrame()

    # Mini Feature to count how many repetitions are needed
    for i in range (0,len(dFiles)):
        SelectedPath = os.path.dirname(os.path.dirname(dFiles[i]))
        if os.path.join(SelectedPath, 'A Test') in dFiles[i]:
            if any(os.path.join(SelectedPath, 'A Test') in SavePath for (flag) in SavePath) == False:
                TestRepetitions += 1
                SavePath.append(os.path.join(SelectedPath, 'A Test'))
        elif os.path.join(SelectedPath, 'B Test') in dFiles[i]:
            if any(os.path.join(SelectedPath, 'B Test') in SavePath for (flag) in SavePath) == False:
                TestRepetitions += 1
                SavePath.append(os.path.join(SelectedPath, 'B Test'))
        elif os.path.join(SelectedPath, 'Amb Test') in dFiles[i]:
            if any(os.path.join(SelectedPath, 'Amb Test') in SavePath for (flag) in SavePath) == False:
                TestRepetitions += 1
                SavePath.append(os.path.join(SelectedPath, 'Amb Test'))

    # Resetting Save Path
    SavePath = []

    for i in range (0,TestRepetitions):
        SelectedPath = os.path.dirname(os.path.dirname(dFiles[0]))
        # Checking if path with Specific Watermelon letter is in SavePath
        if 'A Test' in os.path.dirname(dFiles[0]):
            WatermelonLetter = 'A'
            for j in range(0, len(dFiles)):
                if os.path.join(SelectedPath, 'A Test') in dFiles[j]:
                    Reduced_dFiles.append(dFiles[j])
            # Removing files added into Reduced_dFiles from the main dFiles list
            dFiles = [elements for elements in dFiles if os.path.join(SelectedPath, 'A Test') not in elements]
        elif 'B Test' in os.path.dirname(dFiles[0]):
            WatermelonLetter = 'B'
            for j in range(0, len(dFiles)):
                if os.path.join(SelectedPath, 'B Test') in dFiles[j]:
                    Reduced_dFiles.append(dFiles[j])
            # Removing files added into Reduced_dFiles from the main dFiles list
            dFiles = [elements for elements in dFiles if os.path.join(SelectedPath, 'B Test') not in elements]
        elif 'Amb Test' in os.path.dirname(dFiles[0]):
            WatermelonLetter = 'Amb'
            for j in range(0, len(dFiles)):
                if os.path.join(SelectedPath, 'Amb Test') in dFiles[j]:
                    Reduced_dFiles.append(dFiles[j])
            # Removing files added into Reduced_dFiles from the main dFiles list
            dFiles = [elements for elements in dFiles if os.path.join(SelectedPath, 'Amb Test') not in elements]

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
        MaxAmp = AveragedData.iloc[AveragedData.iloc[:,1].idxmax()]
        MaxAmp = MaxAmp.iloc[1,]
        AveragedData['Amplitude Ratio'] = AveragedData['Amplitude Ratio'].div(MaxAmp)

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

        # Adding Files into a new list to replace the dFiles
        Reduced_dFiles.append(AddedPath)
        NewOutput_dFiles.extend(Reduced_dFiles)
        Reduced_dFiles = []

    return NewOutput_dFiles

# Function to Graph out the FFT Graph
def FFTPlotter(input_array):
    for i in range(0, len(input_array)):
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

# Function to Plot out Table with Data
def TablePlotter(input_data, save_path, watermelon_letter=''):
    # Plotting Image
    fig = go.Figure(data=[
            go.Table(
                header=dict(values=list(input_data.columns),align='center'),
                cells=dict(values=input_data.values.transpose(),
                        fill_color = [["white","lightgrey"]*input_data.shape[0]],
                        align='center'
                    )
                )
        ],
        layout=go.Layout(
            margin=go.layout.Margin(
                l=0, #left margin
                r=0, #right margin
                b=0, #bottom margin
                t=0, #top margin
            )
        )
    )

    fig.update_layout(
        autosize=False,
        width=400,
    )

    # Selecting Correct File Label (referencing the Watermelon Letter)
    fig.write_image(os.path.join(save_path, (watermelon_letter + " Result Table.png")),height=148, scale=6)

# Function to Select Specific Program Feature
def SelectFeature():
    global dFiles
    while True:
        mf.cls()
        print("Queue: ")
        for i in range(0,len(dFiles)):
            print(i, end="")
            print(" \t ", end="")
            print(dFiles[i])
        Fea_Options = input("\n\nOptions \n[1] Amplitude Ratio Calculator \n[2] Averaged Data Calculator \n[3] FFT Spectrum Plotter \n[4] Spectrum Analyzer \n[5] Full Suite \n[6] Back \n[7] Exit \nSelect Option: ")
        if ic.int_Checker(Fea_Options) == False:
            continue
        else:
            Fea_Options = int(Fea_Options)

        match Fea_Options:
            case 1:
                # Option 1 : Amplitude Percentage Calculator
                AmplitudeNormalizer()
                dFiles = []
                break

            case 2:
                # Option 2 : Averaged Data Calculator
                dFiles = TestAvgCalculator()
                break

            case 3:
                # Option 3 : FFT Spectrum Graph Plotter
                FFTPlotter(dFiles)
                dFiles = []
                break

            case 4:
                # Option 4 : Spectrum Analyzer
                analyze_Files()
                dFiles = []
                break

            case 5:
                # Option 5 : Full Suite (Percentage Calculator -> Averaged Data -> FFT Graph Plotter -> Analyzer)
                AmplitudeNormalizer()
                dFiles = TestAvgCalculator()
                FFTPlotter(dFiles)
                analyze_Files()
                dFiles = []
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
    print("SpectraMelon: Audio Spectrum Analyzer")
    print("Build: v0.1.0-alpha (20 Sept 2023)", end="\n\n")
    print("This Audio Spectrum Analyzer is built for the Research and Development Stage of the SRP Project")
    print("\"Investigation of Acoustic Properties of Water Melon\"", end="\n\n")
    print(' PROGRAM '.center(100, '*'), end="\n\n")
    print("Queue: ")
    for i in range(0,len(dFiles)):
        print(i, end="")
        print(" \t ", end="")
        print(dFiles[i])

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
            elif ic.Duplicate_Path_Checker(Data_File_Path, dFiles) == True:
                Ack = input("This file path already exists in the queue \nPress Enter to Continue")
                continue
            else:
                dFiles.append(Data_File_Path)

        case 2:
            # Option 2 : Removing Data Files from the list to be analyzed
            Remove_Data_File = input("\nInput the Numerical Position of file to be removed (First File is 0): ")
            if ic.int_Checker(Remove_Data_File) == False:
                continue
            if mf.Element_Remover(Remove_Data_File, dFiles) == False:
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
