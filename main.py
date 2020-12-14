import time, warnings, os, csv
import normalize_density, normalize_prices
from pint import UnitRegistry
import pandas as pd 
import numpy as np

warnings.filterwarnings('ignore')
ureg = UnitRegistry()

test_mode = False # skips selections to quickly fire through recipes
perform_updates = True # updates prices and densities

def choose_week():
	global test_mode #                                        TEST CHECK

	week_folder = os.listdir('master_recipes')
	
	count = 0
	numbered_weeks = []
	
	for week in week_folder:
		numbered_week = '[' + str(count) + ']' + ' ' + week
		numbered_weeks.append(numbered_week)
		count += 1
		
	print (*numbered_weeks, sep = '\n')
	print ('input number week')
	
	week_selection = week_folder[0] #                         TEST CHECK

	while test_mode == False: #                               TEST CHECK
		try:
			week_selection = week_folder[int(input('>'))]
			break
		except (IndexError, ValueError) as e:
			print (e, '\n')
	
	chosen_week_path = 'master_recipes/' + week_selection
	week_name = chosen_week_path.split('/')[1]
	return chosen_week_path, week_name

def choose_all_or_one(metadata_dict):
	global test_mode #                                        TEST CHECK

	print ('press [a] to normalize all recipes')
	print ('press [o] to normalize one recipe')

	all_or_one_selection = 'a' #                              TEST CHECK

	while test_mode == False: #                               TEST CHECK
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

	# fills in the [pint_raw] column
	# simpler to just get a pint object and then decide where
	# it goes than fill in [volume] and [mass] in one mega function

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

def try_volume(df): # fill in the [volume] column
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

def try_mass(df): # fill in the [mass] column
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

	# this needs to be redone with the same DataFrame.loc method used
	# in apply_weird_unit()

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

	# this needs to be redone with the same DataFrame.loc method used
	# in apply_weird_unit()

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

	# fills in mass or volume for units not given in pint recognizeable
	# units like head of cauliflower or can of beans.
	# this function is called by check_weird_unit()

	weird_frame = pd.read_csv('weird_units.csv')

	ingredient = df['ingredient']
	unit = df['raw_unit']
	number = df['number']

	if pd.isnull(number) or pd.isnull(unit) or pd.isnull(ingredient):
		return df

	x = weird_frame.loc[
		(weird_frame['ingredient'] == ingredient) &
		(weird_frame['s_unit'] == unit)
	]

	if len(x) > 1:
		print ('multiple matches for', ingredient, 'found')
		print ("that's not supposed to happen, going with")
		print ('the first one')
		print (x)

	if len(x) > 0 :

		matched_mass = x.iloc[0]['mass']
		matched_volume = x.iloc[0]['volume']

		if pd.notnull(matched_mass):
			recipe_mass = number * ureg(matched_mass)
			df['pint_mass'] = recipe_mass

		if pd.notnull(matched_volume):
			recipe_volume = number * ureg(matched_volume)
			df['pint_volume'] = recipe_volume
		

		return df

def check_weird_unit(df):
	weird_frame = pd.read_csv('weird_units.csv')

	unconverted = df[df['pint_raw'].isnull()]

	x = unconverted.apply(apply_weird_unit, axis = 1)
	
	df.fillna(x, inplace = True)

def convert_to_metric(df):

	# this function reassigns the entire row because iterrows()
	# creates a copy of the row and it was easier to do this
	# than assign each conversion by index. 

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

def round_everything(df):

	# these units will eventually be copied into the final frame
	# so they need to be a little more human-readable.
	# volume omitted because it's handled differently
	# by make_printable()

	mass_list = []
	number_list = []

	for index, row in df.iterrows():
		round_mass = round(row['pint_mass'], 1)
		round_number = round(row['number'], 1)

		mass_list.append(round_mass)
		number_list.append(round_number)

	df['pint_mass'] = mass_list
	df['number'] = number_list

def set_recipe_to_servings(df, recipe_dict):
	global test_mode #                                        TEST CHECK
	servings = recipe_dict['servings']
	name = recipe_dict['name']

	print (name, '\nHow many servings?')

	if test_mode == True: #                                   TEST CHECK
		desired_servings = 40
		recipe_dict['desired_servings'] = desired_servings

	while test_mode == False: #                               TEST CHECK
		try:
			desired_servings = float(input('>'))
			recipe_dict['desired_servings'] = desired_servings
			break
		except:
			print ('invalid input')

	multiple = desired_servings * (1 / float(servings))
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

def little_units(number):

	# this function uses a dictionary and records an 'original' and 
	# a 'processed_ml' so that if something is tweaked it can be 
	# quickly thrown into a df and checked

	proc_dict = {
		'original'     : number,
		'processed_ml' : 0 * ureg.ml,     # empty numbers given pint
		'ml'           : 0 * ureg.ml,     # conversions so .magnitude
		'cup'          : 0 * ureg.cup,    # can be checked later
		'little'       : 0 * ureg.tbsp
	}

	if number.magnitude > 60:

		# using fewer lines makes the program run faster, 
		# thats why everything is so jammed together here
		
		ml = ((number.magnitude // 1000) * 1000) * (ureg.ml)
		ml = ml.to(ureg.l)
		ml_rem = (number.magnitude % 1000)
		proc_dict['ml'] = ml
		
		cup = ((((ml_rem * ureg.ml).to(ureg.cup)).magnitude // .25) \
				 / 4) * ureg.cup
		cup_rem = (((ml_rem * ureg.ml).to(ureg.cup)).magnitude % .25)
		proc_dict['cup'] = cup
		
		little = ((cup_rem * ureg.cup).to(ureg.tbsp))
		
		if little.magnitude < 1:
			little = little.to(ureg.tsp)
		else:
			pass
		
		proc_dict['little'] = round(little, 1)

		proc_dict['processed_ml'] = round((ml + cup + little), 1)
	
	
	if number.magnitude <= 60:
		little = number.to(ureg.tbsp)
		proc_dict['little'] = round(little, 1)

		proc_dict['processed_ml'] = round(little, 1)

	if number.magnitude < 30:
		little = number.to(ureg.tsp)
		proc_dict['little'] = round(little, 1)

		proc_dict['processed_ml'] = round(little, 1)
			
	pretty_list = []
	for value in proc_dict.values():
		if value.magnitude == 0:
			pass
		else:
			pretty_list.append(str(value))
			
	del pretty_list[0:2]
	
	pretty_string = ' '.join([str(elem) for elem in pretty_list])

	return pretty_string

def make_printable(df):
	
	# If its an empty row
	if pd.isnull(df['ingredient']):
		df['pretty'] = np.nan
		
	# if its an ingredient unit that couldn't be converted to pint
	if pd.isnull(df['pint_raw']) and pd.notnull(df['raw_unit']):
		df['pretty'] = str(df['number']) + ' ' + str(df['raw_unit'])
		
	# if there's a mass
	if pd.notnull(df['pint_mass']):
		df['pretty'] = df['pint_mass']
			
	# if there's a volume but no mass
	if pd.notnull(df['pint_volume']) and pd.isnull(df['pint_mass']):
		x = little_units(df['pint_volume'])
		df['pretty'] = x
			
	return df

def get_printable(df):
	x = df.apply(make_printable, axis = 1)
	x = x.rename(columns = {'pretty' : 'number', \
							'number' : 'old_number'})

	return x[['ingredient', 'number', 'notes']]

def write_to_csv(df, recipe_dict):
	pretty_recipe = get_printable(df)

	desired_servings = recipe_dict['desired_servings']

	save_location = (
					'normalized_recipes/' + \
					recipe_dict['week_name'] + \
					'/' + \
					recipe_dict['name'] + \
					' (normalized)' + \
					'.csv' \
				)

	with open(save_location, mode = 'w') as recipe_loc:
		recipe_writer = csv.writer(recipe_loc, lineterminator = '\n')

		recipe_writer.writerow([recipe_dict['name']])
		recipe_writer.writerow([desired_servings, \
										recipe_dict['notes']])

	pretty_recipe.to_csv(save_location, index = False, mode = 'a')

def write_working_csv(df, recipe_dict, write_working = False):

	# Gives me access to the full dataframe to create test sets

	save_location = ('working_recipes/' + \
					recipe_dict['name'] + '(working).csv')

	df.to_csv(save_location, index = False)



def main():

	global perform_updates
	global test_mode #                                        TEST CHECK

	if perform_updates == True:
		normalize_density.update_densities()
		normalize_prices.main()

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

		write_working_csv(df, metadata_dict[recipe], write_working = True)

		round_everything(df)

		print (df)

		write_to_csv(df, metadata_dict[recipe])

	print (missing_den)

	

if __name__ == '__main__':
	main()
	time.sleep(9999)