import time, warnings, os, csv, platform, textwrap
import normalize_density, normalize_prices
from pint import UnitRegistry
from pathlib import Path
import pandas as pd
import numpy as np


# lets me edit on linux
win_system = False
if platform.system() != 'Linux':
	win_system = True
	import normalize_and_print


warnings.filterwarnings('ignore')
ureg = UnitRegistry()

test_mode = False # skips selections to quickly fire through recipes
perform_updates = True # updates prices and densities


def find_working_folder():
	possible_paths = []
	possible_paths.append(Path(__file__).parent.absolute())

	drop_path = (f'{str(Path.home())}\\Dropbox')
	if os.path.isdir(drop_path): possible_paths.append(drop_path)

	for i in range(len(possible_paths)): print (f'[{i}] {possible_paths[i]}')

	print ('select path')
	selection = possible_paths[1] #                                   TEST CHECK
	while test_mode == False:
		selection = input('>>>')
		try:
			if int(selection) in range(len(possible_paths)):
				selection = possible_paths[int(selection)]
				break
			else:
				print ('invalid input, out of range')
		except ValueError:
			print ('invalid input, please input an integer')

	return selection

def choose_week(dir):

	# choose which week's recipes to normalize
	# skipped if test_mode is True

	if not os.path.isdir(f'{dir}\master_recipes'):
		os.mkdir(f'{dir}\master_recipes')

	week_folder = os.listdir(f'{dir}\master_recipes')

	for i in range(len(week_folder)): print (f'[{i}] {week_folder[i]}')

	print ('input number week')
	week_selection = week_folder[0] #                                 TEST CHECK
	while test_mode == False: #                                       TEST CHECK
		try:
			week_selection = week_folder[int(input('>>>'))]
			break
		except (IndexError, ValueError) as e:
			print (e, '\n')

	chosen_week_path = f'{dir}\master_recipes\{week_selection}'
	week_name = week_selection
	return chosen_week_path, week_name

def choose_all_or_one(metadata_dict):

	# choose to normalize all the recipes or just one
	# skipped if test_mode is True

	print ('press [a] to normalize all recipes')
	print ('press [o] to normalize one recipe')

	all_or_one_selection = 'a' #                                      TEST CHECK

	while test_mode == False: #                                       TEST CHECK
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
		return_dict = metadata_dict

	if all_or_one_selection == 'o':
		recipes = []
		for recipe in metadata_dict:
			recipes.append(recipe)

		for i in range(len(recipes)): print (f'[{i}] {recipes[i]}')
		while True:
			try:
				recipe_selection = recipes[int(input('>'))]
				break
			except (IndexError, ValueError) as e:
				print (e)

		# I need to create a new dictionary object for a single
		# selection because recipes in the dict are accessed
		# later on by their key. metadata_dict[recipe_selection]
		# doesn't include the key so a new dictionary needs
		# to be passed to get_metadata_dicts()

		recipe_selection_dict = {
			recipe_selection :
				metadata_dict[recipe_selection]
		}

		return_dict = recipe_selection_dict

	return return_dict

def get_metadata_dicts(dir):

	# collects information about the recipe not included in the
	# datatable like name, what week it's from, servings etc.

	chosen_week_path, week_name = choose_week(dir)
	recipe_file_names = os.listdir(chosen_week_path)

	recipe_paths = []
	for recipe in recipe_file_names:
		path = f'{chosen_week_path}\\{recipe}'
		recipe_paths.append(path)

	# I'm using a dict here to pass information instead of directly
	# assigning in case more information needs to be passed on
	# later like cooking instructions etc.

	# Pandas can't really handle csv data outside of a dataframe or
	# series so this information is parsed separately

	metadata_dict = {}
	for path in recipe_paths:
		if path.endswith('.csv'):
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
						'norm_filepath'	   : f'{dir}\\normalized_recipes\\{week_name}\\{name} (normalized).csv',
						'servings'         : servings,
						'notes'            : notes,
						'desired_servings' : None
					}
				}
			metadata_dict.update(metadata_entry)
		else:
			print (f"cannot open {path}")


	metadata_dict = choose_all_or_one(metadata_dict)

	# unused at the moment
	metadata_week = {'week' : week_name}

	return metadata_dict, metadata_week

def create_normalized_directory(week_name, dir):
	if os.path.isdir(f'{dir}\\normalized_recipes\\{week_name}'):
		pass
	else:
		os.makedirs(f'{dir}\\normalized_recipes\\{week_name}')

def try_pint(df):

	# fills in the [pint_raw] column

	# simpler to just get a pint object and then decide where
	# it goes than fill in [volume] and [mass] in one mega function

	pint_list = []
	for index, row in df.iterrows():
		unit = row['raw_unit']
		number = row['number']
		pint_raw = np.nan

		try:
			pint_raw = number * ureg(unit)
		except AttributeError:
			pass

		pint_list.append(pint_raw)

	df['pint_raw'] = pint_list

def try_volume(df): # fill in the [volume] column
	volume_list = []
	for index, row in df.iterrows():
		pint_volume = np.nan

		if pd.notnull(row['pint_raw']):
			if row['pint_raw'].dimensionality == '[length] ** 3':
				pint_volume = row['pint_raw']

		volume_list.append(pint_volume)

	df['pint_volume'] = volume_list

def try_mass(df): # fill in the [mass] column
	mass_list = []
	for index, row in df.iterrows():
		pint_mass = np.nan

		if pd.notnull(row['pint_raw']):
			if row['pint_raw'].dimensionality == '[mass]':
				pint_mass = row['pint_raw']

		mass_list.append(pint_mass)

	df['pint_mass'] = mass_list

def volume_to_mass(df):

	# takes the volume, finds if there's a density entry for that
	# ingredient, and fills in a mass

	density_frame = pd.read_csv('normalized_densities.csv')

	mass_list = []
	for index, row in df.iterrows():
		pint_mass = row['pint_mass']
		if pd.notnull(row['pint_volume']) and pd.isnull(row['pint_mass']):
			matches = density_frame.loc[density_frame['ingredient'] == row['ingredient']]

			# temporary: eventually this should be able to handle multiple
			# density matches

			if len(matches) > 0:
				match = matches.iloc[0]
				density = ureg(match['density'])
				pint_mass = row['pint_volume'] * density

		mass_list.append(pint_mass)

	df['pint_mass'] = mass_list

def mass_to_volume(df):

	# does the opposite of the volume_to_mass() function

	density_frame = pd.read_csv('normalized_densities.csv')

	volume_list = []
	for index, row in df.iterrows():
		pint_volume = row['pint_volume']
		if pd.notnull(row['pint_mass']) and pd.isnull(row['pint_volume']):
			matches = density_frame.loc[density_frame['ingredient'] == row['ingredient']]

			# temporary: eventually this should be able to handle multiple
			# density matches

			if len(matches) > 0:
				match = matches.iloc[0]
				density = ureg(match['density'])
				pint_volume = (1 / density) * row['pint_mass']

		volume_list.append(pint_volume)

	df['pint_volume'] = volume_list

def apply_weird_unit(df):

	# fills in mass or volume for ingredients not given in pint
	# recognizeable units like head of cauliflower or can of beans.

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

	# searches recipe dataframe for ingredients in weird_units.csv

	weird_frame = pd.read_csv('weird_units.csv')

	unconverted = df[df['pint_raw'].isnull()]

	x = unconverted.apply(apply_weird_unit, axis = 1)

	df.fillna(x, inplace = True)

def convert_to_metric(df):

	# converts pint_mass and pint_volume to g and ml so other
	# functions don't need to constantly redo this

	volume_list = []
	mass_list = []

	for index, row in df.iterrows():
		ml_volume = np.nan
		g_mass = np.nan

		if pd.notnull(row['pint_volume']):
			ml_volume = (row['pint_volume']).to(ureg.ml)
		if pd.notnull(row['pint_mass']):
			g_mass = (row['pint_mass']).to(ureg.g)

		volume_list.append(ml_volume)
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

	# multiplies all the ingredients by (1 / original_servings) then
	# multiplies by desired_servings

	servings = recipe_dict['servings']
	name = recipe_dict['name']

	print (name, '\nHow many servings?')

	if test_mode == True: #                                           TEST CHECK
		desired_servings = 40
		recipe_dict['desired_servings'] = desired_servings

	while test_mode == False: #                                       TEST CHECK
		try:
			desired_servings = float(input('>'))
			recipe_dict['desired_servings'] = desired_servings
			break
		except:
			print ('invalid input')

	multiple = desired_servings * (1 / float(servings))
	df['number'] = df['number'].astype(float) * multiple

def get_recipe_df(filepath):

	# creates dataframes from the passed filepaths with the columns
	# to be filled in later

	# separates the instructions from the recipe numbers by looking
	# for the word 'instructions'
	# will break if the ingredient 'instructions' is used
	with open(filepath) as o_recipe:
		read_recipe = csv.reader(o_recipe)
		list_recipe = list(read_recipe)
		end_of_numbers = len(list_recipe) - 3
		for line in list_recipe:
			if 'Instructions' in line:
				end_of_numbers = (list_recipe.index(line)-3)

	df = pd.read_csv(filepath, header=2, nrows=(end_of_numbers))
	df = df.rename(columns = {'unit' : 'raw_unit'})

	df['pint_raw'] = np.nan
	df['pint_volume'] = np.nan
	df['pint_mass'] = np.nan

	return df

def fix_units(df):
	df['raw_unit'] = df['raw_unit'].replace('tbs', 'tbsp')

def find_missing_densities(df, missing_densities):

	# mass is prioritized for now. We don't need volume
	# unless it's needed for a price calculation

	x = df.loc[
			(pd.isnull(df['pint_mass'])) &
			(pd.notnull(df['pint_volume']))
		]

	x = x['ingredient'].drop_duplicates()
	x_list = x.tolist()

	for ingredient in x_list:
		if ingredient in missing_densities:
			pass
		else:
			missing_densities.append(ingredient)

def find_missing_prices(df, missing_prices):
	x = df.loc[
			(pd.isnull(df['price'])) &
			(pd.notnull(df['ingredient']))
		]

	x = x['ingredient'].drop_duplicates()
	x_list = x.tolist()

	for ingredient in x_list:
		if ingredient in missing_prices:
			pass
		else:
			missing_prices.append(ingredient)

def little_units(number):
	# called by make_printable() if the ideal number to print is in volume

	# takes something like '2378 ml' and converts it into a more user
	# friendly format like 'X liters, X cups, X tablespoons'

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
	# creates a number + unit combined string to make the recipe easier to read

	# If its an empty row
	if pd.isnull(df['ingredient']):
		df['pretty'] = np.nan

	# if its an ingredient unit that couldn't be converted to pint
	if pd.isnull(df['pint_raw']) and pd.notnull(df['raw_unit']):
		df['pretty'] = f"{df['number']} {df['raw_unit']}"

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

def write_to_csv(df, recipe_dict, dir):
	pretty_recipe = get_printable(df)

	desired_servings = recipe_dict['desired_servings']
	save_location = recipe_dict['norm_filepath']

	# write the title, servings, notes, and numbers
	with open(save_location, mode = 'w') as recipe_loc:
		recipe_writer = csv.writer(recipe_loc, lineterminator = '\n')

		recipe_writer.writerow([recipe_dict['name']])
		recipe_writer.writerow([desired_servings, \
										recipe_dict['notes']])

	pretty_recipe.to_csv(save_location, index = False, mode = 'a')

def write_instructions(recipe_dict, dir):
	save_location = recipe_dict['norm_filepath']

	with open(recipe_dict['filepath']) as o_recipe:
		read_recipe = csv.reader(o_recipe)
		list_recipe = list(read_recipe)
		end_of_numbers = len(list_recipe)
		for line in list_recipe:
			if 'Instructions' in line:
				end_of_numbers = (list_recipe.index(line))

	wrapped_text = []
	for line in list_recipe[end_of_numbers:len(list_recipe)]:
		joined = ''.join(line)
		wrapped = textwrap.wrap(joined, width=100)
		wrapped_text.append(wrapped)

	with open(save_location, 'a') as o_target:
		o_target.write('\n')
		for paragraph in wrapped_text:
			if not paragraph:
				o_target.write('\n')
			if len(paragraph) < 2 and paragraph:
				o_target.write(paragraph[0] + '\n')
			else:
				for line in paragraph:
					o_target.write(line + '\n')

def get_prices(df, recipe_dict):
	price_path = 'normalized_costs.csv'
	price_frame = pd.read_csv(price_path)

	prices = []
	for index, row in df.iterrows():
		price = np.nan

		matches = price_frame.loc[price_frame['ingredient'] == row['ingredient']]
		if len(matches) > 0:
			#print (matches)

			# temporary: I'm just taking the first match here
			# everntually this needs to ask which price you want to use
			match = matches.iloc[0]

			price_mass = np.nan
			price_volume = np.nan
			price_special = np.nan

			conversions = []
			if pd.notnull(row['pint_mass']) and pd.notnull(match['cost_per_gram']):
				price_mass = (row['pint_mass']).magnitude * match['cost_per_gram']
				conversions.append(round(price_mass, 2))

			if pd.notnull(row['pint_volume']) and pd.notnull(match['cost_per_ml']):
				price_volume = (row['pint_volume']).magnitude * match['cost_per_ml']
				conversions.append(round(price_volume, 2))

			if row['raw_unit'] == match['special_unit']:
				price_special = row['number'] * match['cost_per_s_unit']
				conversions.append(round(price_special, 2))

			for i in range(len(conversions)):
				if i == (len(conversions) - 1):
					pass
				else:
					if abs(conversions[i] - conversions[i + 1]) > .1:
						print (f'error with {row["ingredient"]}')
						print (f'{row["ingredient"]}\n{conversions}')

			if conversions:
				price = conversions[0]

		prices.append(price)

	df['price'] = prices

			#print (row['ingredient'])
			#print (f'cost by mass: {price_mass}')
			#print (f'cost by volume: {price_volume}')
			#print (f'cost by special_unit: {price_special}')


def write_working_csv(df, recipe_dict):
	# Gives me access to the full dataframe to create test sets

	if test_mode == True:
		save_location = ('working_recipes/' + \
						recipe_dict['name'] + '(working).csv')
		df.to_csv(save_location, index = False)
	else:
		pass

	save_location = ('working_recipes/' + \
					recipe_dict['name'] + '(working).csv')
	df.to_csv(save_location, index = False)

def main():

	dir = find_working_folder()

	if perform_updates == True:
		normalize_density.update_densities()
		normalize_prices.main()
		print ('updates complete\n')

	metadata_dict, metadata_week = get_metadata_dicts(dir)

	create_normalized_directory(metadata_week['week'], dir)

	# empty lists to collect missing info

	missing_densities = []
	missing_prices = []

	# recipes filepaths to print
	to_print = []

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

		find_missing_densities(df, missing_densities)

		convert_to_metric(df)

		write_working_csv(df, metadata_dict[recipe])

		get_prices(df, metadata_dict[recipe])

		find_missing_prices(df, missing_prices)

		round_everything(df)

		print (df)

		write_to_csv(df, metadata_dict[recipe], dir)

		write_instructions(metadata_dict[recipe], dir)

		to_print.append(metadata_dict[recipe]['norm_filepath'])

	print (f'Missing Densities: \n{missing_densities}')
	print (f'Missing Prices: \n{missing_prices}')

	if win_system:
		normalize_and_print.main(to_print, dir, print_ex = False)


if __name__ == '__main__':
	main()
