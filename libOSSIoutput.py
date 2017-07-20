import numpy as np
import pandas as pd
import datetime as dt
# import wafo.objects as wo
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


def compute_eta(formatted_data):
    '''Returns the detrended water level and the depth over the
        burst.

        inputs are:
            formatted_data = returned dictionary from format_raw()

        output:
            eta = dictionary of pd.Series of free surface oscillations about
                  still water level in meters. Dictionary is keyed with the
                  time stamps of the burst initiations

        returns: eta
    '''

    # detrend and convert counts to meters (1000 mm = 4096 cts)
    data = {tstmp: data / 4096 for tstmp, data in formatted_data.items()}
    eta = {tstmp: out - out.mean() for tstmp, out in data.items()}

    return eta


def make_wf_mat(wl, fs=10, Tb=1200):
    ''' Convert pandas series to mat for use in wafo
        fs is the sampling frequency (Hz) and Tb is the burst duration (s)
    '''

    wf_mat = dict()

    # construct time vector for burst
    time = np.linspace(0, Tb - (1 / fs), fs * Tb)

    # loop to construct wf_mat
    for tstmp, obs in wl.items():

        # make mat
        mat = np.asarray([time, obs.values])
        mat = mat.transpose()

        # save to dict
        wf_mat[tstmp] = mat

    return wf_mat


def compute_depth(formatted_data, zb=0.02):
    ''' Simple function to compute the average depth (m) over a burst. This
        is done by taking the mean of the data and adding the distance of the
        instrument above the surface.

        input:
            formatted_data = A dictionary of pandas' series that are refenced
            with the timestamp of the burst intiation and are in the count
            units. This is the output of the format_raw function

            zb = hight of staff tip from surface in meters

        output:
            h = SWL over the duration of a burst
        '''

    # Convert data from counts to meters
    data = {tstmp: data / 4096 for tstmp, data in formatted_data.items()}

    # The water depth will be the mean of the free surface elevation over the
    # burst plus the staff's distance from the ground
    h_dum = [obs.mean() + zb for obs in data.values()]

    # Save to the pd.Series and reorder the timestamps
    tstmp_data = [pd.to_datetime(key) for key in data.keys()]

    h = pd.Series(h_dum, index=tstmp_data)
    h = h.sort_index()

    return h


def compute_Hm0(eta):
    ''' Computes Hm0 by 4 * std of the surface elevation oscillations

        imput: dictionary of free surface elevation series keyed with time
               stamps. Output of compute_eta

        output: pd.Series of Hm0 wave heights (m)
    '''

    # compute zero-moment wave height
    Hm0_dum = [4 * data.std() for data in eta.values()]
    tstmp_eta = [pd.to_datetime(key) for key in eta.keys()]

    Hm0 = pd.Series(Hm0_dum, index=tstmp_eta)
    Hm0 = Hm0.sort_index()

    return Hm0


def compute_spectral(eta_mat, hmin=0.04):
    ''' This function takes a wafo wave data matrix (returned by make_wf_mat)
        and computes the spectral parameters of each burst which satisfies a
        minimum depth requirement

        input:
            eta_mat = dictionary of wafo wave mats with the burst time stamp as
                      keys
            hmin = minimum depth (m) to compute the spectral params

        output:
    '''
