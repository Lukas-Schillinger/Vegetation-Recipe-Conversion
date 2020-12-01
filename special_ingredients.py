import time
from pint import UnitRegistry
import pandas as pd 

ureg = UnitRegistry()

row0 = ['cauliflower', 3, 'head']
row1 = ['water', 30, 'ml']

def check_pint_comptatible(row):
	try:
		number_unit = row[1] * ureg(row[2])
		return number_unit, True
	except AttributeError:
		number_unit = str(str(row[1]) + ' ' + str(row[2]))
		return number_unit, False

def check_special_unit(row, p_comp):
	if p_comp == True:
		pass
	if p_comp == False:
		pass

def round(row, p_comp):
	if p_comp == True:
		pass
	if p_comp == False:
		pass

def check_teaspoon(row, p_comp):
	if p_comp == True:
		pass
	if p_comp == False:
		pass

def check_null(row):
	pass

'''
------------------------------
is it pint compatible?
	attach tag 
------------------------------
if unit is pint compatible
	convert to pint object
	
	if its in volume:
	

		----------------------------
		if magnitude <= 60 AND > 15:
			convert to tbsp
			return

		if magnitude <= 15:
			convert to tsp
			return

		else:
			keep it in ml
			return
		----------------------------

	if its in mass:

		convert to grams
		return

if unit is NOT pint compatible

	if unit is NULL:
		return NULL

	if unit in special units
		do this

	else:
		shitty workaround
-----------------------------

| Ingredient | Number | Volume | Mass |

'''



print (check_pint_comptatible(row0))
print (check_pint_comptatible(row1))

time.sleep(9999)