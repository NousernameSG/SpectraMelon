
LowerBound_Freq = 100
UpperBound_Freq = 1000
Freq_SegmentRange = 100 # The range of Frequencies for each segment (e.g. 100 ~ 199 Hz -> 100 Hz Range), this must be a multiple of LBF and UBF
Segments = (UpperBound_Freq - LowerBound_Freq)/Freq_SegmentRange
Segments = int(Segments)

for j in range(0, Segments):
    print(LowerBound_Freq + j*Freq_SegmentRange)
    print(LowerBound_Freq + (j+1)*Freq_SegmentRange)
    print("\n")