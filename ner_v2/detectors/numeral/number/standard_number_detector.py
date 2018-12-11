# coding=utf-8
import pandas as pd
import os
import re

from ner_v2.detectors.numeral.constant import NUMBER_DATA_FILE_NUMBER, NUMBER_DATA_FILE_NUMERALS, \
    NUMBER_DATA_FILE_VALUE, NUMBER_DATA_FILE_TYPE, NUMBER_TYPE_UNIT, NUMBER_DATA_CONSTANT_FILE, NUMBER_DETECT_VALUE, \
    NUMBER_DETECT_UNIT
from ner_v2.detectors.numeral.utils import get_number_from_numerals


class BaseNumberDetector(object):
    def __init__(self, entity_name, data_directory_path):
        """
        Base Regex class which will be imported by language date class by giving their data folder path
        This will create standard regex and their parser to detect date for given language.
        Args:
            data_directory_path (str): path of data folder for given language
        """
        self.text = ''
        self.tagged_text = ''
        self.processed_text = ''
        self.date = []
        self.original_date_text = []
        self.entity_name = entity_name
        self.tag = '__' + entity_name + '__'

        self.numbers_word = {}
        self.language_scale_map = {}

        # Method to initialise value in regex
        self.init_regex_and_parser(data_directory_path)

        self.regex_numeric_patterns = re.compile(r'\s(([\d,]+[.]?[\d]*)\s?(' + str(self.language_scale_map.keys())
                                                 + r'?))\s')

        # Variable to define default order in which detector will work
        self.detector_preferences = [
                                     self._detect_number_from_digit]

    def detect_number(self, text):
        self.text = text
        self.processed_text = text
        self.tagged_text = text

        number_list, original_list = None, None
        for detector in self.detector_preferences:
            number_list, original_list = detector(number_list, original_list)
            self._update_processed_text(original_list)
        return number_list, original_list

    @staticmethod
    def _get_numerals_list(numerals_text):
        """
        Split numerals
        Args:
            numerals_text (str): numerals text
        Returns:
            (list) : list containing numeral after split
        """
        numerals_list = numerals_text.split("|")
        return [num.lower().strip() for num in numerals_list if num.strip()]

    def init_regex_and_parser(self, data_directory_path):
        """
        Initialise numbers word from from data file
        Args:
            data_directory_path (str): path of data folder for given language
        Returns:
            None
        """
        data_df = pd.read_csv(os.path.join(data_directory_path, NUMBER_DATA_CONSTANT_FILE), encoding='utf-8')
        for index, row in data_df.iterrows():
            number = row[NUMBER_DATA_FILE_NUMBER]
            numerals = row[NUMBER_DATA_FILE_NUMERALS]
            value = row[NUMBER_DATA_FILE_VALUE]
            if float(value).is_integer():
                value = int(row[NUMBER_DATA_FILE_VALUE])
            number_type = row[NUMBER_DATA_FILE_TYPE]

            numerals_list = self._get_numerals_list(numerals)
            if number_type == NUMBER_TYPE_UNIT:
                self.numbers_word[number] = (1, value)
                self.numbers_word[str(value)] = (1, value)
                for numeral in numerals_list:
                    self.numbers_word[numeral] = (1, value)
            else:
                self.numbers_word[number] = (value, 0)
                self.numbers_word[str(value)] = (value, 0)
                for numeral in numerals_list:
                    self.numbers_word[numeral] = (value, 0)
                    self.language_scale_map[numeral] = value

    def _detect_number_from_numerals(self, number_list, original_list):
        """
        Detect number from numeral text
        Args:
            number_list (list): list containing detected numeric text
            original_list (list): list containing original numeral text
        Returns:
            number_list (list): list containing updated detected numeric text
            original_list (list): list containing updated original numeral text
        """
        number_list = number_list or []
        original_list = original_list or []

        numeral_text_list = re.split(r'[\-\:]', self.processed_text)
        for numeral_text in numeral_text_list:
            number_data = get_number_from_numerals(numeral_text, self.numbers_word)
            for number, original_text in zip(number_data[0], number_data[1]):
                number_list.extend({
                    NUMBER_DETECT_VALUE: number,
                    NUMBER_DETECT_UNIT: None
                })
                original_list.append(original_text)
        return number_list, original_list

    def _detect_number_from_digit(self, number_list, original_list):
        """
        Detect number from numeric text
        Args:
            number_list (list): list containing detected numeric text
            original_list (list): list containing original numeral text
        Returns:
            number_list (list): list containing updated detected numeric text
            original_list (list): list containing updated original numeral text
        """
        number_list = number_list or []
        original_list = original_list or []

        patterns = self.regex_numeric_patterns.findall(self.processed_text)
        for pattern in patterns:
            original = pattern[0]
            number = pattern[1].replace(",", "")
            scale = pattern[2]
            scale = self.language_scale_map[scale] if scale else 1
            number = float(number) * scale
            number = int(number) if number.is_integer() else number

            number_list.append({
                NUMBER_DETECT_VALUE: number,
                NUMBER_DETECT_UNIT: None
            })
            original_list.append(original)

        return number_list, original_list

    def _update_processed_text(self, original_number_list):
        """
        Replaces detected date with tag generated from entity_name used to initialize the object with

        A final string with all dates replaced will be stored in object's tagged_text attribute
        A string with all dates removed will be stored in object's processed_text attribute

        Args:
            original_number_list (list): list of substrings of original text to be replaced with tag
                                       created from entity_name
        """
        for detected_text in original_number_list:
            self.tagged_text = self.tagged_text.replace(detected_text, self.tag)
            self.processed_text = self.processed_text.replace(detected_text, '')


class NumberDetector(BaseNumberDetector):
    def __init__(self, entity_name, data_directory_path):
        super(NumberDetector, self).__init__(entity_name=entity_name, data_directory_path=data_directory_path)