#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Project: SASA
Description: Sleep Apnea Saturation Analysis
Author: Christopher Scott Ward, christopher.ward@bcm.edu
Created: 2025
License: MIT-X
"""

__version__ = "0.1.1"

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
        year=row["year"],
        month=row["month"],
        day=row["day"],
        hour=row["hour"],
        minute=row["minute"],
        second=row["second"],
    )
    return ts


def night_time_check(ts, night_start=None, night_stop=None):
    """
    check if a timestamp 'ts' is between
    night_start and night_stop timestamps
    """
    if not night_start:
        night_start = pd.Timestamp(hour=21, minute=0).time()

    if not night_stop:
        night_stop = pd.Timestamp(hour=7, minute=0).time()

    ts_time = ts.time()

    if night_start < night_stop:
        return night_start <= ts_time <= night_stop
    else:
        return ts_time >= night_start or ts_time <= night_stop


def identify_bin(value, bin_list):
    bin_list.sort(reverse=True)
    for i in bin_list:
        if value >= i:
            return i


def bout_assembler(start_bouts, stop_bouts):
    bouts = []
    if start_bouts.shape[0] == 0 or stop_bouts.shape[0] == 0:
        return bouts
    elif start_bouts.iat[0] > stop_bouts.iat[0]:
        # animal started night_df desatted...drop first bout for revised count, mean, and median calcs
        for i in range(min(start_bouts.shape[0], stop_bouts.shape[0] - 1)):
            bouts.append(
                {
                    "start": start_bouts.iat[i],
                    "stop": stop_bouts.iat[i + 1],
                    "duration": (stop_bouts.iat[i + 1] - start_bouts.iat[i]).seconds,
                }
            )
    else:
        for i in range(min(start_bouts.shape[0], stop_bouts.shape[0])):
            bouts.append(
                {
                    "start": start_bouts.iat[i],
                    "stop": stop_bouts.iat[i],
                    "duration": (stop_bouts.iat[i] - start_bouts.iat[i]).seconds,
                }
            )
    return bouts


def flag_subdesat_starts(bouts, night_df):
    for i in range(len(bouts)):
        try:
            bouts[i]["started subdesat"] = int(
                night_df[night_df["ts"] < bouts[i]["start"]][
                    "sustained_dur_sub_desat"
                ].iloc[-1]
            )
        except Exception as e:
            print(e)
            bouts[i]["started subdesat"] = "unk"
        # print(bouts)
    return bouts


def prepare_output_dict(
    night_recording_start,
    night_recording_stop,
    subject_df_list,
    duration,
    night_df,
    desat_bouts,
    subdesat_bouts,
    sustained_desat_bouts,
    sustained_subdesat_bouts,
):
    output_dict = {
        "night start": night_recording_start,
        "night stop": night_recording_stop,
        "recording files": len(subject_df_list),
        "duration recording": f"{int(duration.seconds/3600)} hrs, {int((duration.seconds%3600)/60)} min, {int(duration.seconds%60)} sec",
        "duration artifact": night_df[night_df["NA_filter"] == True]["interval"].sum(),
        "maximum recording gap": night_df["interval"].max(),
        "any duration desat": night_df[night_df["desat"] == True]["interval"].sum(),
        "min duration desat": night_df[night_df["min_dur_desat"] == True][
            "interval"
        ].sum(),
        "count min duration desat": night_df[night_df["min_dur_desat_bout_start"] == 1][
            "ts"
        ].count(),
        "avg min duration desat": night_df[night_df["min_dur_desat"] == True][
            "interval"
        ].sum()
        / night_df[night_df["min_dur_desat_bout_start"] == 1]["ts"].count(),
        "perc time min duration desat": night_df[night_df["min_dur_desat"] == True][
            "interval"
        ].sum()
        / duration.seconds
        * 100,
        "sustained duration desat": night_df[night_df["sustained_dur_desat"] == True][
            "interval"
        ].sum(),
        "count sustained duration desat": night_df[
            night_df["sustained_dur_desat_bout_start"] == 1
        ]["ts"].count(),
        "avg sustained duration desat": night_df[
            night_df["sustained_dur_desat"] == True
        ]["interval"].sum()
        / night_df[night_df["sustained_dur_desat_bout_start"] == 1]["ts"].count(),
        "perc time sustained duration desat": night_df[
            night_df["sustained_dur_desat"] == True
        ]["interval"].sum()
        / duration.seconds
        * 100,
        "any duration sub desat": night_df[night_df["sub desat"] == True][
            "interval"
        ].sum(),
        "min duration sub desat": night_df[night_df["min_dur_sub_desat"] == True][
            "interval"
        ].sum(),
        "sustained duration sub desat": night_df[
            night_df["sustained_dur_sub_desat"] == True
        ]["interval"].sum(),
        "count spike desat": night_df[night_df["spike desat"] == True]["ts"].count(),
        "bounded desat count": len(desat_bouts),
        "bounded desat from subdesat count": len(
            [i["started subdesat"] for i in desat_bouts if i == 1]
        ),
        "bounded desat duration": np.sum([i["duration"] for i in desat_bouts]),
        "bounded desat mean duration": np.mean([i["duration"] for i in desat_bouts]),
        "bounded desat median duration": np.median(
            [i["duration"] for i in desat_bouts]
        ),
        "bounded subdesat count": len(subdesat_bouts),
        "bounded subdesat duration": np.sum([i["duration"] for i in subdesat_bouts]),
        "bounded subdesat mean duration": np.mean(
            [i["duration"] for i in subdesat_bouts]
        ),
        "bounded subdesat median duration": np.mean(
            [i["duration"] for i in subdesat_bouts]
        ),
        "bounded sustained desat count": len(sustained_desat_bouts),
        "bounded sustained desat from subdesat count": len(
            [i["started subesat"] for i in sustained_desat_bouts if i == 1]
        ),
        "bounded sustained desat duration": np.sum(
            [i["duration"] for i in sustained_desat_bouts]
        ),
        "bounded sustained desat mean duration": np.mean(
            [i["duration"] for i in sustained_desat_bouts]
        ),
        "bounded sustained desat median duration": np.median(
            [i["duration"] for i in sustained_desat_bouts]
        ),
        "bounded sustained subdesat count": len(sustained_subdesat_bouts),
        "bounded sustained subdesat duration": np.sum(
            [i["duration"] for i in sustained_subdesat_bouts]
        ),
        "bounded sustained subdesat mean duration": np.mean(
            [i["duration"] for i in sustained_subdesat_bouts]
        ),
        "bounded sustained subdesat median duration": np.mean(
            [i["duration"] for i in sustained_subdesat_bouts]
        ),
    }
    return output_dict


# %% define classes


# %% define main ## TODO !!! currently script, need to reframe as function
def main():
    # %%
    # get input files
    input_file_path = "./sample data/pooled/"
    # input_file_path = "./sample data/test_cases/"
    # get settings file
    settings_file_path = "./sample settings.xlsx"
    # get output path
    output_file_path = "./sample output/"
    # output_file_path = "./test output/"

    # prepare logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    log_formatter = logging.Formatter(
        "%(asctime)s | %(threadName)s | %(levelname)-5.5s |  %(message)s"
    )
    file_handler = logging.FileHandler(os.path.join(output_file_path, "log.log"))
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)

    logger.info("log started")

    # %% collect data from file paths
    settings = (
        pd.read_excel(settings_file_path, sheet_name="settings")
        .set_index("parameter")["value"]
        .to_dict()
    )
    file_time_fix = pd.read_excel(settings_file_path, sheet_name="file time fix")

    # %% list of files in input_file_path
    file_list = [
        os.path.join(input_file_path, f)
        for f in os.listdir(input_file_path)
        if f.endswith(".csv")
    ]
    logger.info(f"input files found: {file_list}")

    file_dict = {}
    for f in file_list:
        subject_id = os.path.splitext(os.path.basename(f))[0].split("_")[0]
        if subject_id in file_dict:
            file_dict[subject_id].append(f)
        else:
            file_dict[subject_id] = [f]

    # %% populate night duration bins
    output_dict = {}
    output_dict["night_duration_bins"] = {}
    for i in range(
        settings["minimum night duration (hours)"],
        settings["complete night duration (hours)"],
        settings["night duration bin size (hours)"],
    ):
        output_dict["night_duration_bins"][i] = {}
        logging.info(f"adding {i} hour night duration bin")
    if (
        settings["complete night duration (hours)"]
        not in output_dict["night_duration_bins"]
    ):
        output_dict["night_duration_bins"][
            settings["complete night duration (hours)"]
        ] = {}
        logging.info(
            f'adding complete night duration bin ({settings["complete night duration (hours)"]} hrs)'
        )
    if 0 not in output_dict["night_duration_bins"]:
        output_dict["night_duration_bins"][0] = {}
        logging.info("adding 0 hr duration bin (insufficient data bin)")
    # %% loop through file list

    for subject_id, subject_file_list in file_dict.items():
        subject_df_list = []
        output_summary = {}
        for f in subject_file_list:
            df = pd.read_csv(f)
            # prepare timestamp column
            df["ts"] = df.apply(build_timestamp, axis=1)
            sample_interval = df["ts"].iloc[1] - df["ts"].iloc[0]

            # fix timestamps if manual fix needed
            if os.path.basename(f) in list(file_time_fix["filename"]):
                last_row = df.iloc[-1]
                ending_ts = pd.Timestamp(
                    year=last_row["year"],
                    month=last_row["month"],
                    day=last_row["day"],
                    hour=file_time_fix[
                        file_time_fix["filename"] == os.path.basename(f)
                    ]["end hour"].iloc[0],
                    minute=file_time_fix[
                        file_time_fix["filename"] == os.path.basename(f)
                    ]["end minute"].iloc[0],
                )
                df["ts"] = pd.date_range(
                    end=ending_ts, freq=sample_interval, periods=df.shape[0]
                )
                logger.info(
                    f"fixing timestamps in file: {f}, new start:{df['ts'].iloc[0]}, new end: {df['ts'].iloc[-1]}"
                )

            subject_df_list.append(df)
        logger.info(
            f"{subject_id}: {len(subject_file_list)} piece(s). sampling interval {sample_interval.seconds} sec"
        )
        subject_df = pd.concat(subject_df_list)

        # % process file
        # identify and placehold gaps and NA's
        subject_df["NA_filter"] = subject_df["spo2"] == 500
        subject_df["interval"] = subject_df["ts"].diff().dt.total_seconds()

        # create fixed o2 column
        subject_df["fixed_spo2"] = subject_df["spo2"]
        subject_df["fixed_pulse"] = subject_df["pulse"]
        subject_df.replace(
            {"fixed_pulse": {500: np.nan}, "fixed_spo2": {500: np.nan}}, inplace=True
        )
        subject_df.bfill(inplace=True)

        # create instantaneous o2 diff collumn
        subject_df["diff_spo2"] = subject_df["fixed_spo2"].diff()

        # % filter to "night" hours
        subject_df["night"] = subject_df["ts"].apply(
            night_time_check,
            night_start=settings["night_start_time (24hr HH:MM)"],
            night_stop=settings["night_stop_time (24hr HH:MM)"],
        )

        night_df = subject_df[subject_df["night"]].copy()
        night_recording_start = night_df["ts"].iloc[0]
        night_recording_stop = night_df["ts"].iloc[-1]

        # % determine which overnight bin to use
        duration = night_recording_stop - night_recording_start
        duration_hours = int(
            (
                duration.seconds
                + settings["night duration round up within (minutes)"] * 60
            )
            / 60
            / 60
        )
        duration_bin = identify_bin(
            duration_hours, list(output_dict["night_duration_bins"].keys())
        )

        # % score desat events
        night_df["desat"] = night_df["fixed_spo2"] < settings["desat threshold"]
        night_df["sub desat"] = (
            night_df["fixed_spo2"] < settings["desat subthreshold"]
        ) & (night_df["fixed_spo2"] >= settings["desat threshold"])
        night_df["spike desat"] = night_df["diff_spo2"] <= settings["desat spike"]

        # % apply rolling filters (min duration and sustained duration) - apply twice, once to remove too small and second time to refill the time
        min_duration = pd.Timedelta(seconds=settings["minimum desat interval (sec)"])
        night_df["min_dur_desat_trimmed"] = night_df.rolling(
            window=min_duration, on="ts"
        )["desat"].min()
        night_df["min_dur_desat"] = night_df.rolling(window=min_duration, on="ts")[
            "min_dur_desat_trimmed"
        ].max()
        night_df["min_dur_sub_desat_trimmed"] = night_df.rolling(
            window=min_duration, on="ts"
        )["sub desat"].min()
        night_df["min_dur_sub_desat"] = night_df.rolling(window=min_duration, on="ts")[
            "min_dur_sub_desat_trimmed"
        ].max()
        night_df["min_dur_desat_bout_start"] = (
            night_df["min_dur_desat"].astype(int).diff()
        )
        night_df["min_dur_sub_desat_bout_start"] = (
            night_df["min_dur_sub_desat"].astype(int).diff()
        )

        desat_start_bouts = night_df["ts"][night_df["min_dur_desat_bout_start"] == 1]
        desat_stop_bouts = night_df["ts"][night_df["min_dur_desat_bout_start"] == -1]

        subdesat_start_bouts = night_df["ts"][
            night_df["min_dur_sub_desat_bout_start"] == 1
        ]
        subdesat_stop_bouts = night_df["ts"][
            night_df["min_dur_sub_desat_bout_start"] == -1
        ]

        sustained_duration = pd.Timedelta(
            seconds=settings["sustained desat interval (sec)"]
        )
        night_df["sustained_dur_desat_trimmed"] = night_df.rolling(
            window=sustained_duration, on="ts"
        )["desat"].min()
        night_df["sustained_dur_desat"] = night_df.rolling(
            window=sustained_duration, on="ts"
        )["sustained_dur_desat_trimmed"].max()
        night_df["sustained_dur_sub_desat_trimmed"] = night_df.rolling(
            window=sustained_duration, on="ts"
        )["sub desat"].min()
        night_df["sustained_dur_sub_desat"] = night_df.rolling(
            window=sustained_duration, on="ts"
        )["sustained_dur_sub_desat_trimmed"].max()
        night_df["sustained_dur_desat_bout_start"] = (
            night_df["sustained_dur_desat"].astype(int).diff()
        )
        night_df["sustained_dur_sub_desat_bout_start"] = (
            night_df["sustained_dur_sub_desat"].astype(int).diff()
        )

        sustained_desat_start_bouts = night_df["ts"][
            night_df["sustained_dur_desat_bout_start"] == 1
        ]
        sustained_desat_stop_bouts = night_df["ts"][
            night_df["sustained_dur_desat_bout_start"] == -1
        ]

        sustained_subdesat_start_bouts = night_df["ts"][
            night_df["sustained_dur_sub_desat_bout_start"] == 1
        ]
        sustained_subdesat_stop_bouts = night_df["ts"][
            night_df["sustained_dur_sub_desat_bout_start"] == -1
        ]

        subdesat_bouts = bout_assembler(subdesat_start_bouts, subdesat_stop_bouts)
        sustained_subdesat_bouts = bout_assembler(
            sustained_subdesat_start_bouts, sustained_subdesat_stop_bouts
        )
        desat_bouts = flag_subdesat_starts(
            bout_assembler(desat_start_bouts, desat_stop_bouts), night_df
        )
        sustained_desat_bouts = flag_subdesat_starts(
            bout_assembler(sustained_desat_start_bouts, sustained_desat_stop_bouts),
            night_df,
        )

        # %
        output_summary = prepare_output_dict(
            night_recording_start,
            night_recording_stop,
            subject_df_list,
            duration,
            night_df,
            desat_bouts,
            subdesat_bouts,
            sustained_desat_bouts,
            sustained_subdesat_bouts,
        )
        output_dict["night_duration_bins"][duration_bin][subject_id] = output_summary

        logger.info(f"summary created for {subject_id}")

        # create output of annotated night dataframe
        writer = pd.ExcelWriter(
            os.path.join(os.path.join(output_file_path, f"{subject_id}_night.xlsx")),
            engine="xlsxwriter",
        )
        night_df.to_excel(writer, sheet_name=f"{subject_id}")
        pd.DataFrame(desat_bouts).to_excel(writer, sheet_name="desat bouts")
        pd.DataFrame(sustained_desat_bouts).to_excel(
            writer, sheet_name="sustained desat bouts"
        )
        pd.DataFrame(subdesat_bouts).to_excel(writer, sheet_name="subdesat bouts")
        pd.DataFrame(sustained_subdesat_bouts).to_excel(
            writer, sheet_name="sustained subdesat bouts"
        )
        pd.DataFrame(output_summary, index=[0]).to_excel(writer, sheet_name="summary")
        writer.close()

        logger.info("annotated night time series saved")

    # %% create output file
    writer = pd.ExcelWriter(
        os.path.join(output_file_path, "Aggregate" + ".xlsx"), engine="xlsxwriter"
    )
    for key, value in output_dict["night_duration_bins"].items():
        pd.DataFrame(value).transpose().to_excel(
            writer, sheet_name=f"{key} hour night session"
        )
    writer.close()
    logger.info("Aggregate Output Saved")


# %% run main
if __name__ == "__main__":
    main()
