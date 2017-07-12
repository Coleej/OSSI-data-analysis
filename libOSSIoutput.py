import numpy as np
import pandas as pd
import datetime as dt
import os
import re


def format_raw(f_num, data_dir='.'):
    '''Processes a directory of raw output files'''

    # hardcoded values
    # pre-allocate the dictionary which will be returned
    formatted_data = dict()
    f_pre = 'WLOG_'
    f_suf = '.CSV'

    # regex for time stamp
    re_str = '^Y17,M(\d{2}),D(\d{2}),H(\d{2}),M(\d{2}),S(\d{2}),+\r?$'
    regexp = re.compile(re_str)

    # get directory info
    os.chdir(data_dir)

    # open and format the file
    f_name = "{}{:03d}{}".format(f_pre, f_num, f_suf)

    # Check file for readability
    fd = open(f_name, 'r', newline='\n')
    if fd.readable() == True:

        # Split file by line and iterate over blocks of text
        # where each is a burst of data
        for line in fd:

            # Extrac time stamp and creat pd.Series for each burst
            tstmp = regexp.match(line)
            if tstmp:

                # Construct DatetimeIndex
                mo, day, hr, minute, sec = tstmp.groups()
                burst_str = dt.datetime(2017, int(mo), int(day),
                                        int(hr), int(minute), int(sec))
                idx = pd.date_range(burst_str, periods=12000, freq='0.1S')

                # Extract and format data lines
                line_num = 1
                burst_data = []
                while line_num <= 1000:
                    data_line = fd.readline()
                    data = data_line.split(',')
                    data = [int(ent) for ent in data[:12]]
                    burst_data.append(data[:])
                    line_num += 1

                # reshape data in to time series
                burst_data = np.asarray(burst_data)
                burst_1d = np.reshape(burst_data, -1)

                # create pd.Series with DatetimeIndex
                burst_ts = pd.Series(burst_1d, index=idx)

                # save each burst time series to the dict to be returned
                time_str = str(idx[0])
                formatted_data[time_str] = burst_ts

    fd.close()

    return formatted_data


def simple_Hs(formatted_data):
    ''' Simple function to compute Hs with 4*std of demeaned water level '''

    # create series of Hs representative for each burst
    waves = pd.Series()

    # compute signficant wave height
    data = {tstmp: data * (1000/4096)
            for tstmp, data in formatted_data.items()}
    Hs = [obs - obs.mean() for obs in data.values()]
    Hs = [4 * obs.std() for obs in data.values()]

    # Save to the pd.Series and reorder the timestamps
    tstmp = [pd.to_datetime(key) for key in data.keys()]
    waves = pd.Series(Hs, index=tstmp)
    waves = waves.sort_index()

    return waves
