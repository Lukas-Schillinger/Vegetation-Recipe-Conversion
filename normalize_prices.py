import pandas as pd
import numpy as np
from pint import UnitRegistry
import time

ureg = UnitRegistry()
Q_ = ureg.Quantity

def write_norm_price(row, number):
	try:
		number = number.magnitude
	except AttributeError:
		number = float(number)
		
	price = row['price'] * (1 / number)
	
	if pd.isnull(row['norm_price']):
		price = price
	else:
		x = abs(float(row['norm_price']) - price)
		if x > 0.10:
			ingredient = row['ingredient']
			print ('error:')
			print (ingredient, 'price different by volume and mass')
			print ('old price:', row['norm_price'])
			print ('new price', price)
		else:
			price = price
			
	return price

def normalize_prices(cost_frame):
	cost_frame['norm_price'] = np.nan

	volume_list = []
	mass_list = []
	s_list = []
	norm_price_list = []

	for index, row in cost_frame.iterrows():
		
		volume = row['volume']
		mass = row['mass']
		s_ = row['s_unit']
		
		if pd.notnull(volume):
			volume = Q_(volume)
			volume = volume.to(ureg.ml)
			
			price = write_norm_price(row, volume)
			
			volume = round(((volume * (1 / volume)) * ureg.ml), 1)
			volume_list.append(volume)
		else:
			volume = np.nan
			volume_list.append(volume)
		
		if pd.notnull(mass):
			mass = Q_(mass)
			mass = mass.to(ureg.g)
			
			price = write_norm_price(row, mass)
			
			mass = round(((mass * (1 / mass)) * ureg.g), 1)
			mass_list.append(mass)
		else:
			mass = np.nan
			mass_list.append(mass)
			
		if pd.notnull(s_):
			s_number, s_unit = s_.split(' ')
			s_number = round((int(s_number) * (1 / int(s_number))), 1)
			
			price = write_norm_price(row, int(s_number))
			
			s_number = str(s_number) + ' ' + str(s_unit)
			s_list.append(s_number)
		else:
			s_number = np.nan
			s_list.append(s_number)
			
		norm_price_list.append(price)

	cost_frame['pint_volume'] = volume_list
	cost_frame['pint_mass'] = mass_list
	cost_frame['s_norm'] = s_list
	cost_frame['norm_price'] = norm_price_list

	normalized_cost_frame = cost_frame[['ingredient', 
									'pint_volume', 
									'pint_mass', 
									's_norm', 
									'norm_price',
									'notes']]

	return normalized_cost_frame

def main():
	cost_frame = pd.read_csv('master_costs.csv')
	normalized_frame = normalize_prices(cost_frame)
	cost_frame.to_csv('normalized_costs.csv', index = False)

if __name__ == '__main__':
	main()