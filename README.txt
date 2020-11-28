package dependencies:
	pint - this does the unit conversions
	pandas
	numpy

don't be suspicious that the normalized recipe folders are already
populated, they're rewritten every time the program is run. 

normalize_density updates normalized_densities.csv from master_densities.csv
every time the program is run

ignore the numpy warning that units aren't conserved when downgrading
from a dataframe to a series; numpy was added too late in the project 
for me to see the warning and it's too big a problem to fix right now

