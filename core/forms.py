from django.core.exceptions import ValidationError
import os
from django import forms
import xlrd
from phonenumber_field.phonenumber import to_python
from structlog import get_logger

IMPORT_FILE_TYPES = ['.xls', '.xlsx']

class UploadSMSExcelForm(forms.Form):
    file = forms.FileField()

    def is_valid(self, request):
        valid = super(UploadSMSExcelForm, self).is_valid()
        if not valid:
            return valid, False

        # validate the excel file
        try:
            excel_file = self.cleaned_data['file']
            extension = os.path.splitext(excel_file.name)[1]
            if not (extension in IMPORT_FILE_TYPES):
                data = False, ("extension", extension)
                return data
            status, recipient = self.get_name_and_nums_from_excel(file_contents=excel_file.read())

        except ValidationError as e:
            # self.add_error('file', e)
            return False, e

        return status, recipient

    def get_name_and_nums_from_excel(self, path=None, file_contents=None):
        logger = get_logger(__name__).bind(
            action="validate excel file",
        )
        """
        takes an excel file and validates the data
        the excel files should have 2 columns
               1. full names ( optional)
               2. phone number ( compulsory and should be valid, starting with +2547 or 2547)
        """
        if file_contents:
            book = xlrd.open_workbook(file_contents=file_contents)
        else:
            book = xlrd.open_workbook(path)

        names_and_numbers = {}

        for sheet_no in range(1):

            sheet = book.sheet_by_index(sheet_no)
            rows = sheet.nrows

            if sheet.ncols > 2:
                logger.info('failing of excel file')
                data = False, "should be 2 columns"
                return data

            first_column = 0
            second_column = 1
            errors = []
            for i in range(rows):
                values = sheet.row_values(i, first_column, second_column + 1)

                # names is the first column
                names = str(values[0])
                try:
                    phone_number = str(int(values[1]))
                except:
                    phone_number = str(values[1])

                # # check if row is empty line
                if names == '' and phone_number == '':
                    continue

                # phone number should be an int
                if not isinstance(phone_number, str):
                    data = False, "phone number should be in the format(s) above in row {0} column {1}".format(i, second_column)
                    return data
                number = phone_number
                if phone_number.startswith('254'):
                    phone_number = phone_number.replace('254', '+254', 1)
                if phone_number.startswith('7'):
                    phone_number = '+254' + phone_number
                if phone_number.startswith('0'):
                    phone_number = '+254' + phone_number[-9:]
                if not phone_number.startswith('+'):
                    phone_number = '+' + phone_number

                validate = to_python(phone_number).is_valid()
                # validate phone number has a good format
                if not validate:
                    errors.append({"phone_number": number, "row": i+1,
                                   "column": "two" if second_column == 1 else second_column})

                names_and_numbers[names] = phone_number

            if names_and_numbers == {}:
                data = False, "Empty file not allowed"
                return data
            if errors:
                data = False, errors
                return data
            return True, names_and_numbers