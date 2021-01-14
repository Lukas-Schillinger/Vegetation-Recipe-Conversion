import xlwings as xw 
import os, time, csv, pathlib, shutil
from openpyxl import Workbook

def make_excel_sheets(current_week):
	for recipe in (os.listdir('normalized_recipes\\' + current_week)):
		path = pathlib.Path(recipe)
		name = path.stem
		
		wb = Workbook()
		ws = wb.active

		with open((
			'normalized_recipes\\' + \
			current_week + \
			'\\' + \
			recipe), 'r') as f:

			for row in csv.reader(f):
				ws.append(row)
			wb.save('working_excel\\' + name + '.xlsx')

def fix_column_width():
	for recipe in (os.listdir('working_excel')):

		app = xw.App(visible = False)
		wb = xw.Book(('working_excel\\' + recipe))

		for ws in wb.sheets:
			ws.autofit(axis = 'columns')

		wb.save('working_excel\\' + recipe)
		app.quit()

def print_to_printer():
	for recipe in (os.listdir('working_excel')): 
		path = ('working_excel\\' + recipe)

		print ('printing %s' % recipe)
		os.startfile(path, 'print')
		print ('%s sent to printer' % recipe)

def loading_animation():
	animation = '/—\\|'
	for char in animation:
		sys.stdout.write('\r' + char)
		time.sleep(.08)
		sys.stdout.flush()

def main(current_week, print_ex = False):

	print ('creating temporary excel directory')
	try:
		os.mkdir('working_excel')
	except OSError:
		print ('directory already exists or an error occurred')
		pass

	print ('converting CSVs to excel sheets')
	make_excel_sheets(current_week)

	print ('resizing column width')
	fix_column_width()
	print ('columns widths resized')

	if print_ex == True:
		print_to_printer()
	else:
		print ('print_ex set to false')

	shutil.rmtree('working_excel')
	print ('temporay excel directory deleted')
	print ('normalize_and_print complete')