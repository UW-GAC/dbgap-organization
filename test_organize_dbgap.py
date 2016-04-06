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

def _touch(filename, text=""):
    with open(filename, 'w') as f:
        f.write(text)


def _get_test_dbgap_filename(file_type, **kwargs):
    phs = kwargs.get('phs', fake.pyint())
    phs_v = kwargs.get('phs_v', fake.pyint())
    pht = kwargs.get('pht', fake.pyint())
    pht_v = kwargs.get('pht_v', fake.pyint())
    base = kwargs.get('base', fake.word())

    beginning = 'phs{phs:06d}.v{phs_v}.pht{pht:06d}.v{pht_v}'.format(phs=phs, phs_v=phs_v, pht=pht, pht_v=pht_v)

    if file_type == 'phenotype':
        ps = kwargs.get('ps', fake.pyint())
        consent_group = kwargs.get('consent', fake.pyint())
        consent_code = fake.word()
        end = '.p{ps}.c{c}.{base}.{code}.txt'.format(ps=ps, c=consent_group, base=base, code=consent_code)
    elif file_type == 'var_report':
        ps = kwargs.get('ps', fake.pyint())
        end = '.p{ps}.{base}.var_report.xml'.format(base=base, ps=ps)
    elif file_type == 'data_dict':
        end = '.{base}.data_dict.xml'.format(base=base)
    elif file_type == 'subject':
        ps = kwargs.get('ps', fake.pyint())
        end = '.p{ps}.Subject.MULTI.txt'.format(ps=ps)
    elif file_type == 'sample':
        ps = kwargs.get('ps', fake.pyint())
        end = '.p{ps}.Sample.MULTI.txt'.format(ps=ps)
    elif file_type == 'pedigree':
        ps = kwargs.get('ps', fake.pyint())
        end = '.p{ps}.Pedigree.MULTI.txt'.format(ps=ps)
    else:
        raise ValueError('file_type does not match allowed types')
    return beginning + end

class GetTestDbgapFilenameTestCase(unittest.TestCase):
    """Tests for the helper function _get_test_dbgap_filename"""

    def test_phenotype(self):
        filename = _get_test_dbgap_filename('phenotype')
        dbgap_file = DbgapFile(filename, check_exists=False)
        self.assertEqual(dbgap_file.file_type, 'phenotype')

    def test_var_report(self):
        filename = _get_test_dbgap_filename('var_report')
        dbgap_file = DbgapFile(filename, check_exists=False)
        self.assertEqual(dbgap_file.file_type, 'var_report')

    def test_data_dict(self):
        filename = _get_test_dbgap_filename('data_dict')
        dbgap_file = DbgapFile(filename, check_exists=False)
        self.assertEqual(dbgap_file.file_type, 'data_dict')

    def test_subject(self):
        filename = _get_test_dbgap_filename('subject')
        dbgap_file = DbgapFile(filename, check_exists=False)
        self.assertEqual(dbgap_file.file_type, 'special')

    def test_pedigree(self):
        filename = _get_test_dbgap_filename('pedigree')
        dbgap_file = DbgapFile(filename, check_exists=False)
        self.assertEqual(dbgap_file.file_type, 'special')

    def test_sample(self):
        filename = _get_test_dbgap_filename('sample')
        dbgap_file = DbgapFile(filename, check_exists=False)
        self.assertEqual(dbgap_file.file_type, 'special')

class TempdirTestCase(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tempdir)


class TestDbgapFile(TempdirTestCase):
    
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

    def test_works_with_nonexistent_file_and_check_exists_false(self):
        filename = os.path.join(self.tempdir, 'phs000284.v1.pht001903.v1.p1.CFS_CARe_ECG.var_report_2011_02_07.xml.gz')
        # this should not crash
        dbgap_file = DbgapFile(filename, check_exists=False)

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


class GetFileListTestCase(TempdirTestCase):

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

class CheckDiffsTestCase(TempdirTestCase):

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

    def test_exception_with_diff(self):
        file1 = os.path.join(self.tempdir, 'file1.txt')
        file2 = os.path.join(self.tempdir, 'file2.txt')
        file3 = os.path.join(self.tempdir, 'file3.txt')
        text = fake.text()
        with open(file1, 'w') as f:
            f.write(text)
        with open(file2, 'w') as f:
            f.write(text)
        with open(file3, 'w') as f:
            f.write(fake.text())
        # dbgap file subset
        dbgap_files = organize_dbgap.get_file_list(self.tempdir)
        with self.assertRaises(ValueError):
            organize_dbgap._check_diffs(dbgap_files)

class GetFileMatchTestCase(TempdirTestCase):
    # some of the methods will need a temp directory

    def test_working_data_dict(self):
        phs = 7
        pht_to_match = 1
        other_pht = 2
        # make a set of matching files
        filename = _get_test_dbgap_filename('data_dict', phs=phs, phs_v=1, pht=pht_to_match, pht_v=1)
        xml_file = DbgapFile(filename, check_exists=False)
        filename = _get_test_dbgap_filename('phenotype', phs=phs, phs_v=1, pht=pht_to_match, pht_v=1)
        file_to_match = DbgapFile(filename, check_exists=False)
        # make a file that doesn't match
        filename = _get_test_dbgap_filename('data_dict', phs=phs, phs_v=1, pht_v=1)
        other_file = DbgapFile(filename, check_exists=False)

        files = [xml_file, other_file, file_to_match]
        self.assertEqual(organize_dbgap._get_file_match(files, file_to_match, 'data_dict', check_diffs=False), xml_file)

    def test_working_var_report(self):
        phs = 7
        pht_to_match = 1
        other_pht = 2
        # make a set of matching files
        filename = _get_test_dbgap_filename('data_dict', phs=phs, phs_v=1, pht=pht_to_match, pht_v=1)
        xml_file = DbgapFile(filename, check_exists=False)
        filename = _get_test_dbgap_filename('phenotype', phs=phs, phs_v=1, pht=pht_to_match, pht_v=1)
        file_to_match = DbgapFile(filename, check_exists=False)
        # make a file that doesn't match
        filename = _get_test_dbgap_filename('data_dict', phs=phs, phs_v=1, pht_v=1)
        other_file = DbgapFile(filename, check_exists=False)

        files = [xml_file, other_file, file_to_match]
        self.assertEqual(organize_dbgap._get_file_match(files, file_to_match, 'data_dict', check_diffs=False), xml_file)

    def test_returns_none_if_no_match_with_different_file_type(self):
        phs = 7
        pht_to_match = 1
        other_pht = 2
        # make a set of matching files
        filename = _get_test_dbgap_filename('data_dict', phs=phs, phs_v=1, pht=pht_to_match, pht_v=1)
        xml_file = DbgapFile(filename, check_exists=False)
        filename = _get_test_dbgap_filename('phenotype', phs=phs, phs_v=1, pht=pht_to_match, pht_v=1)
        file_to_match = DbgapFile(filename, check_exists=False)
        # make a file that doesn't match
        filename = _get_test_dbgap_filename('data_dict', phs=phs, phs_v=1, pht_v=1)
        other_file = DbgapFile(filename, check_exists=False)

        files = [xml_file, other_file, file_to_match]
        self.assertIsNone(organize_dbgap._get_file_match(files, file_to_match, 'var_report', check_diffs=False))

    def test_working_with_check_diffs_no_diff(self):
        
        # make two directories, one for each consent group
        dir1 = os.path.join(self.tempdir, 'dir1')
        dir2 = os.path.join(self.tempdir, 'dir2')
        os.mkdir(dir1)
        os.mkdir(dir2)

        phs = 7
        pht = 1
        text = fake.text()

        # make a set of matching dd files
        base_dd_filename = _get_test_dbgap_filename('data_dict', phs=phs, phs_v=1, pht=pht, pht_v=1)
        filename_dd1 = os.path.join(dir1, base_dd_filename)
        _touch(filename_dd1, text=text)
        dd1 = DbgapFile(filename_dd1)
        filename_dd2 = os.path.join(dir2, base_dd_filename)
        _touch(filename_dd2, text=text)
        dd2 = DbgapFile(filename_dd2)

        # make the file to match
        filename_to_match = _get_test_dbgap_filename('phenotype', phs=phs, phs_v=1, pht=pht, pht_v=1)
        phenotype = DbgapFile(filename_to_match, check_exists=False)

        files = [dd1, phenotype, dd2]
        self.assertEqual(organize_dbgap._get_file_match(files, phenotype, 'data_dict', check_diffs=True), dd1)

    def test_exception_with_check_diffs(self):
        
        # make two directories, one for each consent group
        dir1 = os.path.join(self.tempdir, 'dir1')
        dir2 = os.path.join(self.tempdir, 'dir2')
        os.mkdir(dir1)
        os.mkdir(dir2)

        phs = 7
        pht = 1

        # make a set of non-matching dd files whose names indicate they should match
        base_dd_filename = _get_test_dbgap_filename('data_dict', phs=phs, phs_v=1, pht=pht, pht_v=1)
        filename_dd1 = os.path.join(dir1, base_dd_filename)
        _touch(filename_dd1, text=fake.text())
        dd1 = DbgapFile(filename_dd1)
        filename_dd2 = os.path.join(dir2, base_dd_filename)
        _touch(filename_dd2, text=fake.text())
        dd2 = DbgapFile(filename_dd2)

        # make the file to match
        filename_to_match = _get_test_dbgap_filename('phenotype', phs=phs, phs_v=1, pht=pht, pht_v=1)
        phenotype = DbgapFile(filename_to_match, check_exists=False)

        files = [dd1, phenotype, dd2]
        with self.assertRaises(ValueError):
            organize_dbgap._get_file_match(files, phenotype, 'data_dict', check_diffs=True)


if __name__ == '__main__':
    unittest.main()