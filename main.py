#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Project: SASA 
Description: Sleep Apnea Saturation Analysis
Author: Christopher Scott Ward, christopher.ward@bcm.edu
Created: 2025
License: MIT-X
"""

__version__ = "0.1.0"

# %% import libraries
import pandas as pd
import numpy as np
import os
import logging


# %% define functions
def build_timestamp(row):
    """
    builds a datetime timestamp from components
    year, month, day, hour, minute, second available
    as seperate columns in a row

    intended for pd .apply method
    """
    ts = pd.Timestamp(
        year = row['year'],
        month = row['month'],
        day = row['day'],
        hour = row['hour'],
        minute = row['minute'],
        second = row['second']
    )
    return ts


def night_time_check(ts, night_start=None, night_stop=None):
    """
    check if a timestamp 'ts' is between 
    night_start and night_stop timestamps
    """
    if not night_start:
        night_start = pd.Timestamp(
            hour = 21,
            minute = 0
        ).time()
   
    if not night_stop:
        night_stop = pd.Timestamp(
            hour=7,
            minute=0
        ).time()

    ts_time = ts.time()
  

    if night_start < night_stop:
        return night_start <= ts_time <= night_stop
    else:
        return ts_time >= night_start or ts_time <= night_stop

    
def identify_bin(value,bin_list):
    bin_list.sort(reverse=True)
    for i in bin_list:
        if value >= i:
            return i

# %% define classes


# %% define main ## TODO !!! currently script, need to reframe as function
def main():
    # %%
    # get input files
    input_file_path = "./sample data/pooled/"
    # get settings file
    settings_file_path = "./sample settings.xlsx"
    # get output path
    output_file_path = "./sample output/"

    # prepare logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    log_formatter = logging.Formatter("%(asctime)s | %(threadName)s | %(levelname)-5.5s |  %(message)s")
    file_handler = logging.FileHandler(os.path.join(output_file_path,'log.log'))
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)

    logger.info('log started')



    # %% collect data from file paths
    settings = pd.read_excel(settings_file_path,sheet_name = "settings").set_index('parameter')['value'].to_dict()
    file_time_fix = pd.read_excel(settings_file_path,sheet_name = "file time fix")

    # %% list of files in input_file_path
    file_list = [os.path.join(input_file_path,f) for f in os.listdir(input_file_path) if f.endswith(".csv")]

    file_dict = {}
    for f in file_list:
        subject_id = os.path.splitext(os.path.basename(f))[0].split("_")[0]
        if subject_id in file_dict:
            file_dict[subject_id].append(f)
        else:
            file_dict[subject_id] = [f]

    

    # %% populate night duration bins
    output_dict = {}
    output_dict['night_duration_bins'] = {}
    for i in range(
        settings['minimum night duration (hours)'],
        settings['complete night duration (hours)'],
        settings['night duration bin size (hours)']
    ):
        output_dict['night_duration_bins'][i] = {}
        logging.info(f'adding {i} hour night duration bin')
    if settings['complete night duration (hours)'] not in output_dict['night_duration_bins']:
        output_dict['night_duration_bins'][settings['complete night duration (hours)']] = {}
        logging.info(f'adding complete night duration bin ({settings["complete night duration (hours)"]} hrs)')
    if 0 not in output_dict['night_duration_bins']:
        output_dict['night_duration_bins'][0] = {}
        logging.info('adding 0 hr duration bin (insufficient data bin)')
    # %% loop through file list 
    
    for subject_id,subject_file_list in file_dict.items():
        subject_df_list = []
        for f in subject_file_list:
            df = pd.read_csv(f)
            # prepare timestamp column
            df['ts'] = df.apply(build_timestamp, axis=1)
            sample_interval = df['ts'].iloc[1] - df['ts'].iloc[0]
            
            # fix timestamps if manual fix needed
            if os.path.basename(f) in list(file_time_fix['filename']):
                last_row = df.iloc[-1]
                ending_ts = pd.Timestamp(
                    year = last_row['year'],
                    month = last_row['month'],
                    day = last_row['day'],
                    hour = file_time_fix[file_time_fix['filename']==os.path.basename(f)]['end hour'].iloc[0],
                    minute = file_time_fix[file_time_fix['filename']==os.path.basename(f)]['end minute'].iloc[0]
                )
                df['ts'] = pd.date_range(
                    end = ending_ts,
                    freq = sample_interval,
                    periods = df.shape[0]
                )
                logger.info(f'fixing timestamps in file: {f}, new start:{df['ts'].iloc[0]}, new end: {df['ts'].iloc[-1]}')
                
            subject_df_list.append(
                df
            )
        logger.info(f'{subject_id}: {len(subject_file_list)} piece(s). sampling interval {sample_interval.seconds} sec')
        subject_df = pd.concat(subject_df_list)

        # % process file
        # identify and placehold gaps and NA's
        subject_df['NA_filter'] = subject_df['spo2']==500
        subject_df['interval'] = subject_df['ts'].diff().dt.total_seconds()
        
        # create fixed o2 column 
        subject_df['fixed_spo2'] = subject_df['spo2']
        subject_df['fixed_pulse'] = subject_df['pulse']
        subject_df.replace({'fixed_pulse':{500:np.nan},'fixed_spo2':{500:np.nan}},inplace=True)
        subject_df.bfill(inplace=True)

        # create instantaneous o2 diff collumn
        subject_df['diff_spo2'] = subject_df['fixed_spo2'].diff()

        # % filter to "night" hours
        subject_df['night'] = subject_df['ts'].apply(
            night_time_check,
            night_start=settings['night_start_time (24hr HH:MM)'],
            night_stop=settings['night_stop_time (24hr HH:MM)']
        )

        night_df = subject_df[subject_df['night']].copy()
        night_recording_start = night_df['ts'].iloc[0]
        night_recording_stop = night_df['ts'].iloc[-1]

        # % determine which overnight bin to use
        duration = night_recording_stop - night_recording_start
        duration_hours = int(
            (duration.seconds + settings['night duration round up within (minutes)']*60)/60/60
        )
        duration_bin = identify_bin(duration_hours,list(output_dict['night_duration_bins'].keys()))

        # % score desat events
        night_df['desat'] = night_df['fixed_spo2']<settings['desat threshold']
        night_df['sub desat'] = night_df['fixed_spo2']<settings['desat subthreshold']
        night_df['spike desat'] = night_df['diff_spo2']<=settings['desat spike']

        # % apply rolling filters (min duration and sustained duration)        
        min_duration = pd.Timedelta(seconds=settings['minimum desat interval (sec)'])
        night_df['min_dur_desat'] = night_df.rolling(window=min_duration, on='ts')['desat'].min()
        night_df['min_dur_sub_desat'] = night_df.rolling(window=min_duration, on='ts')['sub desat'].min()
        night_df['min_dur_desat_bout_start'] = night_df['min_dur_desat'].astype(int).diff()

        sustained_duration = pd.Timedelta(seconds=settings['sustained desat interval (sec)'])
        night_df['sustained_dur_desat'] = night_df.rolling(window=sustained_duration, on='ts')['desat'].min()
        night_df['sustained_dur_sub_desat'] = night_df.rolling(window=sustained_duration, on='ts')['sub desat'].min()
        night_df['sustained_dur_desat_bout_start'] = night_df['sustained_dur_desat'].astype(int).diff()

        # %
        output_dict['night_duration_bins'][duration_bin][subject_id] = {
            'night start' : night_recording_start,
            'night stop' : night_recording_stop,
            'recording files' : len(subject_df_list),
            'duration recording' : f'{int(duration.seconds/3600)} hrs, {int((duration.seconds%3600)/60)} min, {int(duration.seconds%60)} sec',
            'duration artifact' : night_df[night_df['NA_filter']==True]['interval'].sum(),
            'maximum recording gap' : night_df['interval'].max(),
            'any duration desat' : night_df[night_df['desat']==True]['interval'].sum(),
            'min duration desat' : night_df[night_df['min_dur_desat']==True]['interval'].sum(),
            'count min duration desat' : night_df[night_df['min_dur_desat_bout_start']==1]['ts'].count(),
            'avg min duration desat' : night_df[night_df['min_dur_desat']==True]['interval'].sum() / night_df[night_df['min_dur_desat_bout_start']==1]['ts'].count(),
            'perc time min duration desat' : night_df[night_df['min_dur_desat']==True]['interval'].sum() / duration.seconds * 100,
            'sustained duration desat' : night_df[night_df['sustained_dur_desat']==True]['interval'].sum(),
            'count sustained duration desat' : night_df[night_df['sustained_dur_desat_bout_start']==1]['ts'].count(),
            'avg sustained duration desat' : night_df[night_df['sustained_dur_desat']==True]['interval'].sum() / night_df[night_df['sustained_dur_desat_bout_start']==1]['ts'].count(),
            'perc time sustained duration desat' : night_df[night_df['sustained_dur_desat']==True]['interval'].sum() / duration.seconds * 100,
            'any duration sub desat' : night_df[night_df['sub desat']==True]['interval'].sum(),
            'min duration sub desat' : night_df[night_df['min_dur_sub_desat']==True]['interval'].sum(),
            'sustained duration sub desat' : night_df[night_df['sustained_dur_sub_desat']==True]['interval'].sum(),
            'count spike desat' : night_df[night_df['spike desat']==True]['ts'].count()
        }
        logger.info(f'summary created for {subject_id}')


    # %% create output file
    writer = pd.ExcelWriter(
        os.path.join(output_file_path, "Aggregate" + ".xlsx"), engine="xlsxwriter"
    )
    for key, value in output_dict['night_duration_bins'].items():
        pd.DataFrame(value).transpose().to_excel(writer, f'{key} hour night session')
    writer.close()
    logger.info("Aggregate Output Saved")



# %% run main
if __name__ == "__main__":
    main()