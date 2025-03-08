Forked from https://github.com/jtk-utile/jt_census

03/07 change log:

jt_lehd_ef
- Changed the year range for LEHD data pulls to include 2022
- Changed the output gpkg names to include the year of the LEHD data pulled
- Changed some of the print statements: # of workers to/from municipality was previous printing # of blocks that workers were commuting to/from, # states where workers commuting from
- Added new .csv export which sorts workers by the state they are commuting to/from
- Removed direction input from fetch_od and return both "to" and "from" directions
- Added functions get_state (opposite of get_fips) and get_muni_all (gets geometry for all munis in a state)
- Created output folder

ef_lehd
- Added new functions for LEHD data visualization (dot density map and bar chart)

Known bugs:
- Block groups do not necessarily fall within municipality lines. 
    - fetch_od currently clips block groups by municipality lines, which includes block groups that are barely within the municipality.
    - This overcounts the number of commutes to / from the municipality, and does not have the same effect on both directions.
    - For Chelsea, this results in a nonequal # of workers that live and work in Chelsea, depending on whether one is using the to or the from file. This is not an issue for dot density maps but is more apparent on bar charts.
    - Ideally, instead of clipping, blocks are split by municipality lines and jobs are assigned proportionately by area to each municipality.
- Municipality lines do not perfectly follow state lines, so sometimes dots from outside of the state get counted.
- When removing the areas of open spaces and open waters, entire block groups may get removed, so jobs that are actually located in a park/open water do not appear on the bar chart (minor issue, on the order of ~2 jobs / 17,000 for Chelsea).

Work-in-progress:
- Script Random points in polygon step
