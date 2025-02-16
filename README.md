# SASA
Sleep Apnea and Saturation Analysis

## description
sasa : (verb)
1. to know a fact
2. to know how to do something
 - Belter Creole from The Expanse

This tool is indented to improve analysis of sleep related desaturation events as monitored by pulse oximetry.

## recommendations for usage
1. collect file recordings into a common folder
  - filenames should conform to the following structures
  - [subject_id].csv : normal recording
  - [subject_id]_a.csv : fragmented recording, first fragment is marked with a, second with b, and so on. seperate the fragment marker from the subject id with an underscore
  - [subject_id]_time_off_[hhmm].csv : recording that requires timestamp correction. the hhmm should reflect the verified stop time of the recording which will be used back-calculate and correct the timestamp entries. Note - current implementation does not use the filename for this; instead an entry should be made in the settings xlsx file's "file time fix" tab for the filename and correct ending hour and minute (24 hour format)
2. review and update settings file as needed
3. point the tool to the folder containing the recordings, the settings file, and the desired output folder  

## assumptions for usage
- recordings include the following columns: year, month, day, hour, minute, second, pulse, spo2
- values in hour column use 24hr clock
- anomolous/artifact/NA values are marked as 500 in pulse and spo2 columns

## development milestones
 - [x] ingest source files
   - [x] Data - 4 second sampling freq, pulse ox O2 data (csv file)
   - [x] Data - manual correction of inaccurate timestamps - need manual offset
 - [ ] Parameters for tuning
   - [x] < 90 is desat
   - [x] minimum desat interval is 10 sec (3, 4 second samples) -- implemented as actual time based comparison
   - [x] sustained desat interval is 30 sec (8, 4 second samples) -- implemented as actual time based comparison
   - [x] a complete night = 10 hours
   - [x] incomplete (6, 4 hours)
   - [ ] (per subject report and aggregate report clustered by hour)
   - [x] study time is 9pm, 7am
 - [ ] score outcome measures
   - [x] # of desat events
   - [ ] duration of desat events
     - [x] cummulative
     - [ ] median
     - [x] mean
   - [x] # of desat events
   - [ ] # of desat events with a high amplitude
   - [ ] # of desat events where starting point was close to threshold vs dropping far below threshold
   - [x] # artifact intervals - make sure to filter artifact (marked as 500) - replace with next valid (backfill)
   - [x] % time desat
 - [ ] produce output report (per subject and aggregate)
 - [ ] create easy interface

## license
MIT-X
