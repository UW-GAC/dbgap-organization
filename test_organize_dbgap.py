#! /usr/bin/env python3.4
import unittest
import os
import re
import tempfile
import shutil
import subprocess

# classes
from organize_dbgap import DbgapFile
# constants
from organize_dbgap import dbgap_re_dict

class TestDbgapFile(unittest.TestCase):
    
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_str(self):
        filename = os.path.join(self.tempdir, 'testfile.xml')
        subprocess.check_call('touch {file}'.format(file=filename), shell=True)
        dbgap_file = DbgapFile(filename)
        self.assertIsInstance(dbgap_file.__str__(), str)

    def test_get_file_type_phenotype(self):
        filename = os.path.join(self.tempdir, 'phs000284.v1.pht001903.v1.p1.c1.CFS_CARe_ECG.NPU.txt')
        subprocess.check_call('touch {file}'.format(file=filename), shell=True)
        dbgap_file = DbgapFile(filename)
        dbgap_file.set_file_type()
        self.assertEqual(dbgap_file.file_type, 'phenotype')
        self.assertEqual(dbgap_file.match.groupdict()['dbgap_id'], 'phs000284.v1.pht001903.v1')
        
    def test_get_file_type_data_dict(self):
        filename = os.path.join(self.tempdir, 'phs000284.v1.pht001903.v1.CFS_CARe_ECG.data_dict_2011_02_07.xml')
        subprocess.check_call('touch {file}'.format(file=filename), shell=True)
        dbgap_file = DbgapFile(filename)
        dbgap_file.set_file_type()
        self.assertEqual(dbgap_file.file_type, 'data_dict')
        self.assertEqual(dbgap_file.match.groupdict()['dbgap_id'], 'phs000284.v1.pht001903.v1')
    
    def test_get_file_type_var_report(self):
        filename = os.path.join(self.tempdir, 'phs000284.v1.pht001903.v1.p1.CFS_CARe_ECG.var_report_2011_02_07.xml')
        subprocess.check_call('touch {file}'.format(file=filename), shell=True)
        dbgap_file = DbgapFile(filename)
        dbgap_file.set_file_type()
        self.assertEqual(dbgap_file.file_type, 'var_report')
        self.assertEqual(dbgap_file.match.groupdict()['dbgap_id'], 'phs000284.v1.pht001903.v1')
    
    def test_get_file_type_other(self):
        filename = os.path.join(self.tempdir, 'phs000284.v1.pht001903.v1.p1.CFS_CARe_ECG.var_report_2011_02_07.xml.gz')
        subprocess.check_call('touch {file}'.format(file=filename), shell=True)
        dbgap_file = DbgapFile(filename)
        dbgap_file.set_file_type()
        self.assertIsNone(dbgap_file.file_type)
        self.assertIsNone(dbgap_file.match)

    def test_exception_file_not_found(self):
        filename = os.path.join(self.tempdir, 'phs000284.v1.pht001903.v1.p1.CFS_CARe_ECG.var_report_2011_02_07.xml.gz')
        with self.assertRaises(FileNotFoundError):
            dbgap_file = DbgapFile(filename)

    def test_with_different_regex_phenotype(self):
        filename = os.path.join(self.tempdir, 'phenotype.txt')
        subprocess.check_call('touch {file}'.format(file=filename), shell=True)
        dbgap_file = DbgapFile(filename)
        re_dict = {'phenotype': '^phenotype.txt$',
                   'data_dict': '^data_dict.txt$',
                   'var_report': '^var_report.txt$',
                   'special': '^special.txt$',}
        dbgap_file.set_file_type(re_dict)
        self.assertEqual(dbgap_file.file_type, 'phenotype')


if __name__ == '__main__':
    unittest.main()