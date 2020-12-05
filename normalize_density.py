import time, csv
import pandas as pd
from pint import UnitRegistry

ureg = UnitRegistry()

def combine_volume(row):
	number = row['volume number']
	unit = row['volume unit']

	if unit == 'tbs':
		unit = 'tbsp'

	numberunit = number * ureg(unit)
	numberunit = numberunit.to(ureg.ml)
	return numberunit

def combine_mass(row):
	number = row['mass number']
	unit = row['mass unit']

	numberunit = number * ureg(unit)
	numberunit = numberunit.to(ureg.gram)
	return numberunit

def update_densities():
	master_densities = 'master_densities.csv'

	names = ['ingredient', 'volume number', 'volume unit', 'mass number', 'mass unit']
	md_dataframe = pd.read_csv(master_densities, names = names)

	normalized_dict = {
		'ingredient'      : md_dataframe['ingredient'],
		'combined_volume' : md_dataframe.apply(combine_volume, axis = 1),
		'combined_mass'   : md_dataframe.apply(combine_mass, axis = 1)
		}

	normalized_frame = pd.concat(normalized_dict, axis = 1)
	normalized_frame['density'] = normalized_frame['combined_mass'] / normalized_frame['combined_volume']

	normalized_frame.to_csv('normalized_densities.csv', index = False)
	print ('Densities updated from %s\n' % master_densities)