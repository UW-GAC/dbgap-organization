#! /usr/bin/env python3.4
import unittest
# classes
from organize_dbgap import DbgapFile
# constants
from organize_dbgap import dbgap_re_dict

import re

import tempfile
import shutil

def _get_test_dbgap_filename(file_type):
    pass

class TestDbgapFile(unittest.TestCase):
    
    def test_str(self):
        filename = '/projects/geneva/testfile.xml'
        dbgap_file = DbgapFile(filename)
        self.assertIsInstance(dbgap_file.__str__(), str)

    def test_get_file_type_phenotype(self):
        filename = 'directory/phs000284.v1.pht001903.v1.p1.c1.CFS_CARe_ECG.NPU.txt'
        dbgap_file = DbgapFile(filename)
        dbgap_file.set_file_type()
        self.assertEqual(dbgap_file.file_type, 'phenotype')
        self.assertEqual(dbgap_file.match.groupdict()['dbgap_id'], 'phs000284.v1.pht001903.v1')
        
    def test_get_file_type_data_dict(self):
        filename = 'directory/phs000284.v1.p1.data_dictionary.MULTI/phs000284.v1.pht001903.v1.CFS_CARe_ECG.data_dict_2011_02_07.xml'
        dbgap_file = DbgapFile(filename)
        dbgap_file.set_file_type()
        self.assertEqual(dbgap_file.file_type, 'data_dict')
        self.assertEqual(dbgap_file.match.groupdict()['dbgap_id'], 'phs000284.v1.pht001903.v1')
    
    def test_get_file_type_var_report(self):
        filename = 'directory/phs000284.v1.pht001903.v1.p1.CFS_CARe_ECG.var_report_2011_02_07.xml'
        dbgap_file = DbgapFile(filename)
        dbgap_file.set_file_type()
        self.assertEqual(dbgap_file.file_type, 'var_report')
        self.assertEqual(dbgap_file.match.groupdict()['dbgap_id'], 'phs000284.v1.pht001903.v1')
    
    def test_get_file_type_other(self):
        filename = 'directory/phs000284.v1.pht001903.v1.p1.CFS_CARe_ECG.var_report_2011_02_07.xml.gz'
        dbgap_file = DbgapFile(filename)
        dbgap_file.set_file_type()
        self.assertIsNone(dbgap_file.file_type)
        self.assertIsNone(dbgap_file.match)


if __name__ == '__main__':
    unittest.main()