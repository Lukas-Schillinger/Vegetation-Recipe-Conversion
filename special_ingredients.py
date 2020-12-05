import time, warnings, os, csv
from pint import UnitRegistry
import pandas as pd 
import numpy as np

warnings.filterwarnings('ignore')

ureg = UnitRegistry()

def choose_week():
	week_folder = os.listdir('master_recipes')
	
	count = 0
	numbered_weeks = []
	
	for week in week_folder:
		numbered_week = '[' + str(count) + ']' + ' ' + week
		numbered_weeks.append(numbered_week)
		count += 1
		
	print (*numbered_weeks, sep = '\n')
	print ('input number week')
	
	while True:
		try:
			week_selection = week_folder[int(input('>'))]
			break
		except (IndexError, ValueError) as e:
			print (e, '\n')
	
	chosen_week_path = 'master_recipes/' + week_selection
	week_name = chosen_week_path.split('/')[1]
	return chosen_week_path, week_name

def choose_all_or_one(metadata_dict):
	print ('press [a] to normalize all recipes')
	print ('press [o] to normalize one recipe')

	while True:
		try:
			all_or_one_selection = str(input('>'))
			selections = ('a', 'o')
			if all_or_one_selection in selections:
				break
			else:
				print ('invalid selection')
		except (IndexError, ValueError) as e:
			print (e, '\n')

	if all_or_one_selection == 'a':
		return metadata_dict

	if all_or_one_selection == 'o':
		count = 0
		listed_recipes = []
		for recipe in metadata_dict:
			print  ('[' + str(count) + ']' + ' ' + recipe)
			listed_recipes.append(recipe)
			count += 1

		print ('choose recipe to normalize')
		while True:
			try:
				recipe_selection = listed_recipes[int(input('>'))]
				break
			except (IndexError, ValueError) as e:
				print (e)

		# I need to create a new dictionary object for a sinlge
		# selection because recipes in the dict are accessed
		# later on by their key. metadata_dict[recipe_selection]
		# doesn't include the key so a new dictionary needs
		# to be passed to get_metadata_dicts()

		recipe_selection_dict = {
			recipe_selection :
				metadata_dict[recipe_selection]
		}

		return recipe_selection_dict

	else:
		print ('ERROR ERROR ERROR YOU SHOULDNT SEE THIS')

def get_metadata_dicts():
	chosen_week_path, week_name = choose_week()
	recipe_file_names = os.listdir(chosen_week_path)

	recipe_paths = []
	for recipe in recipe_file_names:
		path = chosen_week_path + '/' + recipe
		recipe_paths.append(path)

	# I'm using a dict here to pass information instead of directly
	# assigning in case more information needs to be passed on 
	# later like cooking instructions etc. 

	# Pandas can't really handle csv data outside of a dataframe or
	# series so this information is parsed separately 

	metadata_dict = {}
	for path in recipe_paths:
		with open(path) as recipe_csv:
			open_recipe = csv.reader(recipe_csv)
			rows = list(open_recipe)
			
			name = rows[0][0]
			servings = rows[1][0]
			notes = rows[1][1]
			
			metadata_entry = {
				name : {
					'name'             : name,
					'week_name'        : week_name,
					'filepath'         : path,
					'servings'         : servings,
					'notes'            : notes,
					'desired_servings' : None
				}
			}    
		metadata_dict.update(metadata_entry)
	
	metadata_dict = choose_all_or_one(metadata_dict)

	return metadata_dict


def try_pint(df):
	pint_list = []
	for i in range(len(df)):
		x = df.loc[i]
		unit = x['raw_unit']
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
			pint_mass = x['pint_mass']
			ready_for_conversion = True

		else:
			pint_mass = x['pint_mass']

		if ready_for_conversion == True:
			for i in range(len(density_frame)):
				y = density_frame.loc[i]

				if y['ingredient'] == x['ingredient']:

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
			pint_volume = x['pint_volume']
			ready_for_conversion = True

		else:
			pint_volume = x['pint_volume']

		if ready_for_conversion == True:
			for i in range(len(density_frame)):
				y = density_frame.loc[i]

				if y['ingredient'] == x['ingredient']:

					density = ureg(y['density'])
					pint_volume = (1 / density) * x['pint_mass']

		volume_list.append(pint_volume)

	df['pint_volume'] = volume_list

def apply_weird_unit(df):
	weird_frame = pd.read_csv('weird_units.csv')

	ingredient = df['ingredient']
	unit = df['raw_unit']
	number = df['number']

	x = weird_frame.loc[
		(weird_frame['ingredient'] == ingredient) &
		(weird_frame['s_unit'] == unit)
	]

	if len(x) > 1:
		print ('multiple matches for', ingredient, 'found')
		print ("that's not supposed to happen, going with")
		print ('the first one')
		print (x)

	if len(x) > 0:

		matched_mass = x.iloc[0]['mass']
		matched_volume = x.iloc[0]['volume']

		recipe_mass = number * ureg(matched_mass)
		recipe_volume = number * ureg(matched_volume)

		df['pint_volume'] = recipe_volume
		df['pint_mass'] = recipe_mass

		return df

def check_weird_unit(df):
	weird_frame = pd.read_csv('weird_units.csv')

	unconverted = df[df['pint_raw'].isnull()]

	x = unconverted.apply(apply_weird_unit, axis = 1)
	
	df.fillna(x, inplace = True)

def convert_to_metric(df):
	volume_list = []
	mass_list = []

	for index, row in df.iterrows():
		if pd.notnull(row['pint_volume']):
			ml_volume = row['pint_volume'].to(ureg.ml)
			volume_list.append(ml_volume)
		else:
			ml_volume = np.nan
			volume_list.append(ml_volume)

		if pd.notnull(row['pint_mass']):
			g_mass = row['pint_mass'].to(ureg.gram)
			mass_list.append(g_mass)
		else:
			g_mass = np.nan
			mass_list.append(g_mass)

	df['pint_volume'] = volume_list	
	df['pint_mass'] = mass_list

def little_units(df):
	volume_list = []

	for index, row in df.iterrows():
		volume = row['pint_volume']

		try:

			if row['pint_volume'].magnitude <= 60:
				volume = volume.to(ureg.tbsp)

			if row['pint_volume'].magnitude <= 20:
				volume = volume.to(ureg.tsp)

		except AttributeError:
			pass

		volume_list.append(volume)

	df['pint_volume'] = volume_list

def round_everything(df):
	volume_list = []
	mass_list = []
	number_list = []

	for index, row in df.iterrows():
		round_volume = round(row['pint_volume'], 1)
		round_mass = round(row['pint_mass'], 1)
		round_number = round(row['number'], 1)

		volume_list.append(round_volume)
		mass_list.append(round_mass)
		number_list.append(round_number)

	df['pint_volume'] = volume_list
	df['pint_mass'] = mass_list
	df['number'] = number_list

def set_recipe_to_servings(df, recipe_dict):
	servings = recipe_dict['servings']
	name = recipe_dict['name']

	print (name, '\nHow many servings?')
	while True:
		try:
			desired_servings = float(input('>'))
			recipe_dict['desired_servings'] = desired_servings
			break
		except:
			print ('invalid input')

	multiple = desired_servings * (1 / int(servings))
	df['number'] = df['number'] * multiple

def get_recipe_df(filepath):
	df = pd.read_csv(filepath, header = 2)
	df = df.rename(columns = {'unit' : 'raw_unit'})

	df['pint_raw'] = np.nan
	df['pint_volume'] = np.nan
	df['pint_mass'] = np.nan

	return df

def fix_units(df):
	df['raw_unit'] = df['raw_unit'].replace('tbs', 'tbsp')

def find_missing_densities(df, missing_den):
	x = df.loc[
			(pd.isnull(df['pint_mass'])) &
			(pd.notnull(df['pint_volume']))
		]

	x = x['ingredient']

	y = pd.concat([missing_den, x]).drop_duplicates()

	return y


def main():

	metadata_dict = get_metadata_dicts()

	missing_den = pd.DataFrame()
	missing_prices = pd.DataFrame()

	for recipe in metadata_dict:

		df = get_recipe_df(metadata_dict[recipe]['filepath'])

		set_recipe_to_servings(df, metadata_dict[recipe])

		fix_units(df)

		try_pint(df)

		try_volume(df)
		try_mass(df)

		volume_to_mass(df)
		mass_to_volume(df)

		check_weird_unit(df)

		missing_den = find_missing_densities(df, missing_den)

		convert_to_metric(df)

		little_units(df)

		round_everything(df)

		print (df)

	print (missing_den)

if __name__ == '__main__':
	main()
	time.sleep(9999)