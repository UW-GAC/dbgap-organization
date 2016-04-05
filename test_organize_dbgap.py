#! /usr/bin/env python3.4
import unittest
import os
import re
import tempfile
import shutil
import subprocess

from faker import Factory

import organize_dbgap
# classes
from organize_dbgap import DbgapFile
# constants
from organize_dbgap import dbgap_re_dict

fake = Factory.create()

def _touch(filename):
    subprocess.check_call('touch {file}'.format(file=filename), shell=True)

class TestDbgapFile(unittest.TestCase):
    
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_str(self):
        filename = os.path.join(self.tempdir, 'testfile.xml')
        _touch(filename)
        dbgap_file = DbgapFile(filename)
        self.assertIsInstance(dbgap_file.__str__(), str)

    def test_get_file_type_phenotype(self):
        filename = os.path.join(self.tempdir, 'phs000284.v1.pht001903.v1.p1.c1.CFS_CARe_ECG.NPU.txt')
        _touch(filename)
        dbgap_file = DbgapFile(filename)
        self.assertEqual(dbgap_file.file_type, 'phenotype')
        self.assertEqual(dbgap_file.match.groupdict()['dbgap_id'], 'phs000284.v1.pht001903.v1')
        
    def test_get_file_type_data_dict(self):
        filename = os.path.join(self.tempdir, 'phs000284.v1.pht001903.v1.CFS_CARe_ECG.data_dict_2011_02_07.xml')
        _touch(filename)
        dbgap_file = DbgapFile(filename)
        self.assertEqual(dbgap_file.file_type, 'data_dict')
        self.assertEqual(dbgap_file.match.groupdict()['dbgap_id'], 'phs000284.v1.pht001903.v1')
    
    def test_get_file_type_var_report(self):
        filename = os.path.join(self.tempdir, 'phs000284.v1.pht001903.v1.p1.CFS_CARe_ECG.var_report_2011_02_07.xml')
        _touch(filename)
        dbgap_file = DbgapFile(filename)
        self.assertEqual(dbgap_file.file_type, 'var_report')
        self.assertEqual(dbgap_file.match.groupdict()['dbgap_id'], 'phs000284.v1.pht001903.v1')
    
    def test_get_file_type_other(self):
        filename = os.path.join(self.tempdir, 'phs000284.v1.pht001903.v1.p1.CFS_CARe_ECG.var_report_2011_02_07.xml.gz')
        _touch(filename)
        dbgap_file = DbgapFile(filename)
        self.assertIsNone(dbgap_file.file_type)
        self.assertIsNone(dbgap_file.match)

    def test_exception_file_not_found(self):
        filename = os.path.join(self.tempdir, 'phs000284.v1.pht001903.v1.p1.CFS_CARe_ECG.var_report_2011_02_07.xml.gz')
        with self.assertRaises(FileNotFoundError):
            dbgap_file = DbgapFile(filename)

    def test_with_different_regex_phenotype(self):
        filename = os.path.join(self.tempdir, 'phenotype.txt')
        _touch(filename)
        dbgap_file = DbgapFile(filename)
        re_dict = {'phenotype': '^phenotype.txt$',
                   'data_dict': '^data_dict.txt$',
                   'var_report': '^var_report.txt$',
                   'special': '^special.txt$',}
        dbgap_file._set_file_type(re_dict=re_dict)
        self.assertEqual(dbgap_file.file_type, 'phenotype')


    def test_with_different_regex_data_dict(self):
        filename = os.path.join(self.tempdir, 'data_dict.txt')
        _touch(filename)
        dbgap_file = DbgapFile(filename)
        re_dict = {'phenotype': '^phenotype.txt$',
                   'data_dict': '^data_dict.txt$',
                   'var_report': '^var_report.txt$',
                   'special': '^special.txt$',}
        dbgap_file._set_file_type(re_dict=re_dict)
        self.assertEqual(dbgap_file.file_type, 'data_dict')


    def test_with_different_regex_var_report(self):
        filename = os.path.join(self.tempdir, 'var_report.txt')
        _touch(filename)
        dbgap_file = DbgapFile(filename)
        re_dict = {'phenotype': '^phenotype.txt$',
                   'data_dict': '^data_dict.txt$',
                   'var_report': '^var_report.txt$',
                   'special': '^special.txt$',}
        dbgap_file._set_file_type(re_dict=re_dict)
        self.assertEqual(dbgap_file.file_type, 'var_report')

    def test_with_different_regex_special(self):
        filename = os.path.join(self.tempdir, 'special.txt')
        _touch(filename)
        dbgap_file = DbgapFile(filename)
        re_dict = {'phenotype': '^phenotype.txt$',
                   'data_dict': '^data_dict.txt$',
                   'var_report': '^var_report.txt$',
                   'special': '^special.txt$',}
        dbgap_file._set_file_type(re_dict=re_dict)
        self.assertEqual(dbgap_file.file_type, 'special')


class GetFileListTestCase(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_returns_list_of_dbgap_files(self):
        # make two different types of files in the directory
        file1 = os.path.join(self.tempdir, 'file1.txt')
        _touch(file1)
        file2 = os.path.join(self.tempdir, 'file2.txt')
        _touch(file2)
        res = organize_dbgap.get_file_list(self.tempdir)
        self.assertIsInstance(res, list)
        for x in res:
            self.assertIsInstance(x, DbgapFile)

class CheckDiffsTestCase(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_working_when_no_diff(self):
        text = fake.text()
        file1 = os.path.join(self.tempdir, 'file1.txt')
        file2 = os.path.join(self.tempdir, 'file2.txt')
        with open(file1, 'w') as f:
            f.write(text)
        with open(file2, 'w') as f:
            f.write(text)
        # dbgap file subset
        dbgap_files = organize_dbgap.get_file_list(self.tempdir)
        # if the function is not working, this will crash
        organize_dbgap._check_diffs(dbgap_files)

if __name__ == '__main__':
    unittest.main()