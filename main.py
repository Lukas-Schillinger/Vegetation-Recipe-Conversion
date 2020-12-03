import time, csv, os, normalize_density
from pint import UnitRegistry
import pandas as pd
import numpy as np

#Sets up more convenient unit conversion
ureg = UnitRegistry()

def choose_week():
	week_folder = os.listdir('master_recipes')
	
	#Display weeks in a user-friendly format
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
			if all_or_one_selection == 'a' or all_or_one_selection == 'o':
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

		'''
		I need to create a new dictionary object for a sinlge
		selection because recipes in the dict are accessed
		later on by their key. metadata_dict[recipe_selection]
		doesn't yield include the key so a new dictionary needs
		to be passed to get_metadata_dicts()
		'''
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
	'''
	I'm using a dict here to pass information instead of directly
	assigning in case more information needs to be passed on 
	later like cooking instructions etc. 

	Pandas can't really handle csv data outside of a dataframe or
	series so this information is parsed separately 
	'''
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
					'name'      : name,
					'week_name' : week_name,
					'filepath'  : path,
					'servings'  : servings,
					'notes'     : notes
				}
			}    
		metadata_dict.update(metadata_entry)
	
	metadata_dict = choose_all_or_one(metadata_dict)

	return metadata_dict

def try_metric(recipe):
	'''
	Hopefully there'll never be a situation where key
	order changes
	'''
	numberunit_dict = {
		'number_unit' : recipe.apply(conversion_machine, axis = 1),
		'ingredient'  : recipe['ingredient'],
		'notes'       : recipe['notes']
	}
	
	numberunit_recipe = pd.concat(numberunit_dict, axis = 1)
	return (numberunit_recipe)   

'''
writing these out as independent functions may not have been completely
necessary but it makes conversion_machine a little less disgusting

These actually don't even really work
'''
########################################################################

def redefine_to_compatible(cell, message = None):
	print (message)
	return input('>')

def does_it_exist(cell):
	if cell == '':
		message = ("something that was supposed to be here was not")
		cell = redefine_to_compatible(cell, message)
		does_it_exist(cell)
	else:
		return cell

def is_it_a_string(cell):
	try:
		cell = str(cell)
		return cell
	except:
		message = ('could not convert %s to a string' % cell)
		cell = redefine_to_compatible(cell, message)
		is_it_a_string(cell)

def is_it_a_float(cell):
	try:
		cell = float(cell)
		return cell
	except:
		message = ('could not convert %s to a float' % cell)
		cell = redefine_to_compatible(cell, message)
		is_it_a_float(cell)

########################################################################

def conversion_machine(row):
	number = row['number']
	unit = row['unit']

	number = does_it_exist(number)
	unit = does_it_exist(unit)

	number = is_it_a_float(number)
	unit = is_it_a_string(unit)

	'''
	Mandatory fix of tablespoon abbreviation, could be
	improved by checking from a dictionart of abbreviation
	mistakes
	'''
	if unit == 'tbs':
		unit = 'tbsp'

	if unit == 'tsp':
		numberunit = number * ureg(unit)
		'''
		If number <= 3 keep it in tsp
		If number > 3 convert it to tbsp
		If tbsp conversion is greater than
		3 convert it to grams
		'''
		if number <= 3:
			pass
		else:
			numberunit = numberunit.to(ureg.tbsp)
			if numberunit.magnitude > 3:
				numberunit = numberunit.to(ureg.ml)
			else:
				pass
	else:
		try:
			'''
			This block executes if the unit is in
			the pint library
			'''
			numberunit = number * ureg(unit)

		except AttributeError:
			'''
			Shitty string workaround. This happens if 
			the unit isn't recognized by pint.
			this is the only condition that skips
			the rounding step.

			not a good fix!
			'''
			if pd.isnull(row['ingredient']):
				return np.nan
			else:
				round_workaround = round(number, 1)
				round_workaround = str(str(round_workaround) + ' ' + str(unit))
				return round_workaround

		#If unit is a measure of volume
		if numberunit.dimensionality == ('[length] ** 3'):
			numberunit = numberunit.to(ureg.ml)

		#If unit is a measure of weight
		if numberunit.dimensionality == ('[mass]'):
			numberunit = numberunit.to(ureg.gram)

		'''
		For some reason this else block always runs, I have no idea why
		>:(
		
		else:
			print ('')
			print ('if you see this it means the unit wasn't mass or volume
			print (row['ingredient'], numberunit, numberunit.dimensionality)
			print ('')
		'''

	round_number = round(numberunit.magnitude, 1)
	final_unit = str(numberunit.units)
	numberunit = round_number * ureg(final_unit)
	return numberunit

def convert_from_volume_to_mass(recipe_row):
	densities_list = pd.read_csv('normalized_densities.csv')

	for index, density_row in densities_list.iterrows():

		if density_row['ingredient'] == recipe_row['ingredient']:
			if recipe_row['number_unit'].units == 'milliliter':

				recipe_number_unit = recipe_row['number_unit']
				density = float(density_row['density'].split(' ')[0])
				recipe_number = round((recipe_number_unit.magnitude * density), 1)
				recipe_number_unit = recipe_number * ureg.gram
				recipe_row['number_unit'] = recipe_number_unit

	return recipe_row['number_unit']

def try_mass(numberunit_dataframe):

	number_unit = numberunit_dataframe.apply(convert_from_volume_to_mass, axis = 1)

	weighed_dict = {
		'number_unit' : number_unit,
		'ingredient'  : numberunit_dataframe['ingredient'],
		'notes'       : numberunit_dataframe['notes']
	}
	
	weighed_recipe = pd.concat(weighed_dict, axis = 1)
	return (weighed_recipe) 

def find_missing_densities(DataFrame):
	local_missing_densities = []
	for index, row in DataFrame.iterrows():

		if isinstance(row['number_unit'], str) or pd.isnull(row['number_unit']):
			#Catching the ingredients using shitty workaround
			pass
		else:
			'''
			This won't catch units too small to have been recorded
			but they were probably in units too small to have mattered
			'''
			if row['number_unit'].units == 'milliliter':
				#idk  there were nan units getting through
				if row['ingredient'] == 'nan':
					pass
				else:
					local_missing_densities.append(row['ingredient'])
			else:
				pass
	return local_missing_densities

def  write_to_csv(dataframe, recipe_dict, desired_servings):
	save_location = 'normalized_recipes/' + recipe_dict['week_name'] + '/' + recipe_dict['name'] + ' (normalized)' + '.csv'

	with open(save_location, mode = 'w') as recipe_location:
		recipe_writer = csv.writer(recipe_location, lineterminator = '\n')

		recipe_writer.writerow([recipe_dict['name']])
		recipe_writer.writerow([desired_servings, recipe_dict['notes']])

	'''
	mode = 'a' writes in 'append' to avoid writing over the metadata
	above
	'''
	dataframe.to_csv(save_location, index = False, mode = 'a')


def main():

	'''
	Updates densities before running; densities are calculated 
	from master_densities.csv by normalize_densities.py and stored
	in normalized_densities. main.py uses these densities with try_mass()
	'''
	normalize_density.update_densities()

	metadata_dict = get_metadata_dicts()

	#Stores the missing densities collected by find_missing_densities()
	missing_densities = []

	#Runs through every recipe going to be used in a given week
	for recipe in metadata_dict:
		'''
		Not necessary to give these separate variables but it makes
		things easier to read
		'''
		recipe_filepath = metadata_dict[recipe]['filepath']
		recipe_servings = float(metadata_dict[recipe]['servings'])
		recipe_notes = metadata_dict[recipe]['notes']

		desired_servings = float(input(metadata_dict[recipe]['name'] + ': How many servings?\n >'))

		recipe_dataframe = pd.read_csv(recipe_filepath, header = 2)

		#Set Servings to 1 and then to the desired number of servings
		multiple = desired_servings * (1 / recipe_servings)
		recipe_dataframe['number'] = recipe_dataframe['number'] * multiple

		'''
		try_metric will convert to metric where possible, conserving units
		if the conversion is too small to be useful

		try_mass will convert to mass where units are in ml and the density
		has been recorded
		'''
		numberunit_dataframe = try_metric(recipe_dataframe)
		mass_frame = try_mass(numberunit_dataframe)

		'''
		missing densities will only return ingredients that stopped
		at ml, not units that stopped at tbsp or tsp.

		The little units don't need to be converted to density
		'''
		local_missing_densities = find_missing_densities(mass_frame)
		missing_densities.extend(local_missing_densities)

		write_to_csv(mass_frame, metadata_dict[recipe], desired_servings)

		print ('%s normalized and saved to:' % (metadata_dict[recipe]['name']))
		print ([metadata_dict[recipe]['filepath']], '\n')

	print ('\nThe following ingredients could have been converted')
	print ('to mass but no density has been recorded for them')
	print ('in master_densities.py\n')

	print (set(missing_densities))

	print ('Finished!')

if __name__ == '__main__':
	main()
	time.sleep(9999)