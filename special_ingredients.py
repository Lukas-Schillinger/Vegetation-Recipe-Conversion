import time, warnings, pint_pandas
from pint import UnitRegistry
import pandas as pd 
import numpy as np
import main

warnings.filterwarnings('ignore')

ureg = UnitRegistry()

'''
| Ingredient | Number | Raw Unit | Volume | Mass |
'''

lines = (
	['cumin', 30, 'ml'], 
	['onion', 20, 'tbsp'], 
	['cauliflower', 3, 'head'], 
	['peanut butter', 200, 'gram']
	)

columns = ['ingredient', 'number', 'raw unit']
df = pd.DataFrame(lines, columns = columns)
df['pint_raw'] = np.nan
df['pint_volume'] = np.nan
df['pint_mass'] = np.nan
df = df.astype({'pint_raw' : complex})


def try_pint(df):
	pint_list = []
	for i in range(len(df)):
		x = df.loc[i]
		unit = x['raw unit']
		number = x['number']
		
		try:
			pint_raw = number * ureg(unit)
		except AttributeError:
			pint_raw = np.nan
		
		pint_list.append(pint_raw)

	df['pint_raw'] = pint_list

def try_volume(df):
	volume_list = []
	for i in range(len(df)):
		x = df.loc[i]

		try:
			if x['pint_raw'].dimensionality == '[length] ** 3':
				pint_volume = (x['pint_raw'])
			else:
				pint_volume = np.nan

		except AttributeError:
			pint_volume = np.nan

		volume_list.append(pint_volume)

	df['pint_volume'] = volume_list

def try_mass(df):
	mass_list = []
	for i in range(len(df)):
		x = df.loc[i]

		try:
			if x['pint_raw'].dimensionality == '[mass]':
				pint_mass = x['pint_raw']
			else:
				pint_mass = np.nan

		except AttributeError:
			pint_mass = np.nan

		mass_list.append(pint_mass)

	df['pint_mass'] = mass_list

def volume_to_mass(df):
	density_frame = pd.read_csv('normalized_densities.csv')

	mass_list = []
	for i in range(len(df)):
		ready_for_conversion = False
		x = df.loc[i]

		if pd.isnull(x['pint_mass']) and pd.notnull(x['pint_volume']):
			print (x['ingredient'], 'does have a volume and needs a mass')
			pint_mass = x['pint_mass']
			ready_for_conversion = True
		else:
			pint_mass = x['pint_mass']

		if ready_for_conversion == True:
			for i in range(len(density_frame)):
				y = density_frame.loc[i]

				if y['ingredient'] == x['ingredient']:

					print (y['ingredient'], 'matched with', x['ingredient'])

					density = ureg(y['density'])
					pint_mass = density * x['pint_volume']

		mass_list.append(pint_mass)

	df['pint_mass'] = mass_list

def mass_to_volume(df):
	density_frame = pd.read_csv('normalized_densities.csv')

	volume_list = []
	for i in range(len(df)):
		ready_for_conversion = False
		x = df.loc[i]

		if pd.isnull(x['pint_volume']) and pd.notnull(x['pint_mass']):
			print (x['ingredient'], 'does have a mass and needs a volume')
			pint_volume = x['pint_volume']
			ready_for_conversion = True
		else:
			pint_volume = x['pint_volume']

		if ready_for_conversion == True:
			for i in range(len(density_frame)):
				y = density_frame.loc[i]

				if y['ingredient'] == x['ingredient']:

					print (y['ingredient'], 'matched with', x['ingredient'])

					density = ureg(y['density'])
					pint_volume = (1 / density) * x['pint_mass']

		volume_list.append(pint_volume)

	df['pint_volume'] = volume_list

def check_weird_unit(df):
	weird_frame = pd.read_csv('weird_units.csv')

	for i in range(len(df)):
		x = df.loc[i]
		ready_for_special = False

		if pd.isnull(x['pint_raw']):
			ready_for_special = True
		else:
			pass

	print (weird_frame)

try_pint(df)
try_volume(df)
try_mass(df)

volume_to_mass(df)
mass_to_volume(df)

check_weird_unit(df)

print (df)

time.sleep(9999)