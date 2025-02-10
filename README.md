# SASA
Sleep Apnea and Saturation Analysis

## description
sasa : (verb)
1. to know a fact
2. to know how to do something
 - Belter Creole from The Expanse

This tool is indented to improve analysis of sleep related desaturation events as monitored by pulse oximetry.

## development milestones
 - [ ] ingest source files
   - [ ] Data - 4 second sampling freq, pulse ox O2 data (csv file)
   - [ ] Data - manual correction of inaccurate timestamps - need maual offset
 - [ ] Parameters for tuning
   - [ ] < 90 is desat
   - [ ] minimum desat interval is 10 sec (3, 4 second samples)
   - [ ] sustained desat interval is 30 sec (8, 4 second samples)
   - [ ] a complete night = 10 hours
   - [ ] incomplete (6, 4 hours)
   - [ ] (per subject report and aggregate report clustered by hour)
   - [ ] study time is 9pm, 7am
 - [ ] score outcome measures
   - [ ] # of desat events
   - [ ] duration of desat events, cummulative, median, mean
   - [ ] # of desat events with a high amplitude
   - [ ] # of desat events where starting point was close to threshold vs dropping far below threshold
   - [ ] # artifact intervals - make sure to filter artifact (marked as 500) - replace with next valid (backfill)
   - [ ] % time desat
 - [ ] produce output report (per subject and aggregate)
 - [ ] create easy interface

## license
MIT-X
