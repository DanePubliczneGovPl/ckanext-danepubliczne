# coding=utf-8
from abc import ABCMeta, abstractmethod
from collections import defaultdict
import ckan.plugins as p
from ckan.common import _
from ckan.logic import ValidationError


class BaseValidator(object):
    __metaclass__ = ABCMeta
    extensions_list = None

    @abstractmethod
    def validate(self, fp):
        pass


class BaseSheetValidator(BaseValidator):
    __metaclass__ = ABCMeta

    def format_cell(self, sheet_count, sheet_name, address):
        if sheet_count > 1:
            return "'{}'.{}".format(sheet_name, address)
        return address

    @abstractmethod
    def get_book(self, fp):
        pass

    @abstractmethod
    def merged_sheet_list(self, book):
        pass

    def validate(self, fp):
        book = self.get_book(fp)
        error_dict = defaultdict(list)
        self._check_merged_cells(book, error_dict)
        if error_dict:
            raise ValidationError(error_dict)

    def _check_merged_cells(self, book, error_dict):
        merged_cells = self.merged_sheet_list(book)
        if merged_cells:
            error_dict['upload'].append(
                _("Merged cells are disallowed. Fix following cells: {}.".format(", ".join(merged_cells))))


class XLSValidator(BaseSheetValidator):
    """Validator to detect merged cells in xls files

     It assumes work with data from trusted sources.
     No protection against malicious files
    (see https://docs.python.org/2/library/xml.html#xml-vulnerabilities )"""
    extensions_list = ['.xls']

    def _get_address(self, rlo, rhi, clo, chi):
        from xlrd import cellname
        return "{}:{}".format(cellname(rlo, clo), cellname(rhi - 1, chi - 1))

    def get_book(self, fp):
        from xlrd import open_workbook
        return open_workbook(file_contents=fp.read(),
                             formatting_info=True)

    def merged_sheet_list(self, book):
        sheet_count = len(book.sheets())
        merged_cells = []
        for sheet in book.sheets():
            for crange in sheet.merged_cells:
                address = self._get_address(*crange)
                merged_cells.append(self.format_cell(sheet_count, sheet.name, address))
        return merged_cells


class XLSXValidator(BaseSheetValidator):
    """Validator to detect merged cells in xlsx files"""
    extensions_list = ['.xlsx']

    def get_book(self, fp):
        from openpyxl import load_workbook
        return load_workbook(fp)

    def merged_sheet_list(self, book):
        sheet_count = len(book.worksheets)
        merged_cells = []
        for sheet in book.worksheets:
            for address in sheet.merged_cells:
                merged_cells.append(self.format_cell(sheet_count, sheet.title, address))
        return merged_cells


class DataValidatorPlugin(p.SingletonPlugin):
    validators = [XLSValidator(), XLSXValidator()]

    p.implements(p.IResourceController, inherit=True)

    def before_update(self, context, current, resource):
        if not resource['upload']:
            return
        for validator in self.validators:
            if any(resource['upload'].filename.lower().endswith(ext)
                   for ext in validator.extensions_list):

                validator.validate(resource['upload'].file)
                resource['upload'].file.seek(0)