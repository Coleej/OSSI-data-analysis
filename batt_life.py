#!/usr/bin/env python
import sys

if len(sys.argv[:]) != 4:
    print('Usage: \n')
    print('batt_life "burst time (min)" "burst duration (min)" "6v|12v|18v"\n')
    sys.exit()

# calculate drain power
Bt = float(sys.argv[1]) # burst time in minutes
Bi = float(sys.argv[2]) # burst interval in minutes

batt_type = sys.argv[3] # battery type (6V 12 cell, 18V 12 cell, 21V 28 cell)
print(batt_type)
if batt_type.lower() == '6v':
    Fs = 54.0 # power used in sampling (mW)
    Sl = 3.0 # power used when sleeping (mW)
elif batt_type.lower() == '18v':
    Fs = 45.2 # power used in sampling (mW)
    Sl = 3.5 # power used when sleeping (mW)
    Bc = 100200 # typical energy in 12 C batteries (mWhrs)
elif batt_type.lower() == '21v':
    Fs = 46.2 # power used in sampling (mW)
    Sl = 3.5 # power used when sleeping (mW)
    Bc = 233800 # typical energy in 18 C batteries (mWhrs)
else:
    print('Pass battery type as 3rd argument: 16v, 18v, 21v')
    sys.exit()

Dp = Sl + Fs * (Bt/Bi) # power drain (mW)


# estimate battery life
Bl = Bc / Dp # batter life in hours
days, hours = divmod(Bl, 24)
print('Battery life is {} days and {} hours'.format(days, hours))
