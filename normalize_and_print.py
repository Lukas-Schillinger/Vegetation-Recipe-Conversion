import xlwings as xw
import os, time, csv, pathlib, shutil
from openpyxl import Workbook

def make_excel_sheets(dir, to_print):
	for recipe in to_print:
		path = pathlib.Path(f'{dir}\{recipe}')
		name = path.stem

		wb = Workbook()
		ws = wb.active

		with open(recipe, 'r') as f:

			for row in csv.reader(f):
				ws.append(row)
			wb.save('working_excel\\' + name + '.xlsx')

def title_format(sheet):
	sheet.range('A1').api.Font.Name = 'JMH Typewriter'
	sheet.range('A1').api.Font.Size = 16
	return sheet

def add_borders(sheet, end_numbers):
	sheet.range('A4:C{}'.format(end_numbers-2)).api.Borders(9).LineStyle = 1
	sheet.range('A4:C{}'.format(end_numbers-2)).api.Borders(7).LineStyle = 1
	sheet.range('A4:C{}'.format(end_numbers-2)).api.Borders(10).LineStyle = 1
	sheet.range('A4:C{}'.format(end_numbers-2)).api.Borders(8).LineStyle = 1
	sheet.range('A4:C{}'.format(end_numbers-2)).api.Borders(12).LineStyle = 1
	sheet.range('A4:C{}'.format(end_numbers-2)).api.Borders(11).LineStyle = 1
	return sheet

def fix_column_width():
	app = xw.App(visible = False)
	for recipe in (os.listdir('working_excel')):
		print (f'making {recipe} pretty')

		app = xw.App(visible = False)
		wb = xw.Book(('working_excel\\' + recipe))
		sheet = wb.sheets[0]

		lrow = sheet.range('A' + str(sheet.cells.last_cell.row)).end('up').row
		print (lrow)


		instruction_flag = None
		for i in range(1, lrow):
			if 'Instructions' in str(sheet.range('A{}'.format(i)).value):
				instruction_flag = i

		if instruction_flag:
			sheet.range('A1:C{}'.format(instruction_flag)).columns.autofit()
			sheet.range('A{}'.format(instruction_flag)).api.Font.Bold = True
			end_numbers = instruction_flag
		else:
			sheet.autofit(axis='columns')
			end_numbers = lrow

		print (end_numbers)


		# style options
		sheet = title_format(sheet)
		sheet = add_borders(sheet, end_numbers)

		wb.save('working_excel\\' + recipe)
		wb.close()

		print (f'{recipe} is pretty now\n')

	app.quit()

def print_to_printer():
	for recipe in (os.listdir('working_excel')):
		path = ('working_excel\\' + recipe)

		print ('printing %s' % recipe)
		os.startfile(path, 'print')
		print ('%s sent to printer' % recipe)

def main(to_print, dir, print_ex = False):

	os.makedirs('working_excel', exist_ok = True)

	print ('\nconverting CSVs to excel sheets')
	make_excel_sheets(dir, to_print)
	print ('conversions complete')

	print ('\nmaking the recipes pretty\n')
	fix_column_width()
	print ('recipes are pretty now')

	print ('\nstarting printing')
	if print_ex == True:
		print_to_printer()
		time.sleep(10)
		print ('recipes sent to printer')
	else:
		print ('print_ex set to false')

	# excel processes need to close before working_excel can
	# be removed. not really sure how to do this so the fix
	# for right now is making the program wait 10 seconds
	# before trying to delete them.

	# maybe launch the print_to_printer() in a separate shell
	# and proceed only when that process is closed?

	shutil.rmtree('working_excel')
	print ('\ntemporay excel directory deleted')
	print ('normalize_and_print complete')

if __name__ == '__main__':
	main()
