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
    """Creates a file of a given filename.

    Positional arguments:
    filename: the filename to create

    Keyword arguments
    text: text to write to the file
    """
    with open(filename, 'w') as f:
        f.write(text)


def _get_test_dbgap_filename(file_type, **kwargs):
    """Construct and return a test dbgap file name with the correct pattern for a given file_type

    Positional arguments
    file_type: dbgap file type to create, one of phenotype, var_report, data_dict, subject, sample, or pedigree

    Keyword arguemnts:
    **kwargs: normal **kwargs syntax in python, but can be used to construct similar filenames.
              Not all arguments are used for all types.
        phs: study accession
        phs_v: study version
        pht: dataset accession
        pht_v: dataset version
        base: basename (ie dataset name before dbgap appends accession numbers)
        ps: participant set
        consent_group: numeric indicator of consent group
        consent_code: consent code ie HMB-NPU

    """
    phs = kwargs.get('phs', fake.pyint())
    phs_v = kwargs.get('phs_v', fake.pyint())
    pht = kwargs.get('pht', fake.pyint())
    pht_v = kwargs.get('pht_v', fake.pyint())
    base = kwargs.get('base', fake.word())

    beginning = 'phs{phs:06d}.v{phs_v}.pht{pht:06d}.v{pht_v}'.format(phs=phs, phs_v=phs_v, pht=pht, pht_v=pht_v)

    if file_type == 'phenotype':
        ps = kwargs.get('ps', fake.pyint())
        consent_group = kwargs.get('consent', fake.pyint())
        consent_code = kwargs.get('consent_code', fake.word())
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
        """DbgapFile objects have correct file_type for test phenotype files"""
        filename = _get_test_dbgap_filename('phenotype')
        dbgap_file = DbgapFile(filename, check_exists=False)
        self.assertEqual(dbgap_file.file_type, 'phenotype')

    def test_var_report(self):
        """DbgapFile objects have correct file_type for test var_report files"""
        filename = _get_test_dbgap_filename('var_report')
        dbgap_file = DbgapFile(filename, check_exists=False)
        self.assertEqual(dbgap_file.file_type, 'var_report')

    def test_data_dict(self):
        """DbgapFile objects have correct file_type for test data_dict files"""
        filename = _get_test_dbgap_filename('data_dict')
        dbgap_file = DbgapFile(filename, check_exists=False)
        self.assertEqual(dbgap_file.file_type, 'data_dict')

    def test_subject(self):
        """DbgapFile objects have correct file_type for test subject files"""
        filename = _get_test_dbgap_filename('subject')
        dbgap_file = DbgapFile(filename, check_exists=False)
        self.assertEqual(dbgap_file.file_type, 'special')

    def test_pedigree(self):
        """DbgapFile objects have correct file_type for test pedigree files"""
        filename = _get_test_dbgap_filename('pedigree')
        dbgap_file = DbgapFile(filename, check_exists=False)
        self.assertEqual(dbgap_file.file_type, 'special')

    def test_sample(self):
        """DbgapFile objects have correct file_type for test sample files"""
        filename = _get_test_dbgap_filename('sample')
        dbgap_file = DbgapFile(filename, check_exists=False)
        self.assertEqual(dbgap_file.file_type, 'special')


class TempdirTestCase(unittest.TestCase):
    """Superclass to hold setUp and tearDown methods for TestCases that need temporary directories"""
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        # get original directory in case we chdir in a test function
        self.original_directory = os.getcwd()

    def tearDown(self):
        shutil.rmtree(self.tempdir)
        # change back to original directory
        os.chdir(self.original_directory)


class TestDbgapFile(TempdirTestCase):
    """TestCase class for DbgapFile class"""

    def test_str(self):
        """test that str method returns a string"""
        filename = os.path.join(self.tempdir, 'testfile.xml')
        _touch(filename)
        dbgap_file = DbgapFile(filename)
        self.assertIsInstance(dbgap_file.__str__(), str)

    def test_get_file_type_phenotype(self):
        """DbgapFile._set_file_type works correctly for phenotoype files"""
        filename = os.path.join(self.tempdir, 'phs000284.v1.pht001903.v1.p1.c1.CFS_CARe_ECG.NPU.txt')
        _touch(filename)
        dbgap_file = DbgapFile(filename)
        self.assertEqual(dbgap_file.file_type, 'phenotype')
        self.assertEqual(dbgap_file.match.groupdict()['dbgap_id'], 'phs000284.v1.pht001903.v1')
        
    def test_get_file_type_data_dict(self):
        """DbgapFile._set_file_type works correctly for data_dict files"""
        filename = os.path.join(self.tempdir, 'phs000284.v1.pht001903.v1.CFS_CARe_ECG.data_dict_2011_02_07.xml')
        _touch(filename)
        dbgap_file = DbgapFile(filename)
        self.assertEqual(dbgap_file.file_type, 'data_dict')
        self.assertEqual(dbgap_file.match.groupdict()['dbgap_id'], 'phs000284.v1.pht001903.v1')
    
    def test_get_file_type_var_report(self):
        """DbgapFile._set_file_type works correctly for var_report files"""
        filename = os.path.join(self.tempdir, 'phs000284.v1.pht001903.v1.p1.CFS_CARe_ECG.var_report_2011_02_07.xml')
        _touch(filename)
        dbgap_file = DbgapFile(filename)
        self.assertEqual(dbgap_file.file_type, 'var_report')
        self.assertEqual(dbgap_file.match.groupdict()['dbgap_id'], 'phs000284.v1.pht001903.v1')
    
    def test_get_file_type_other(self):
        """DbgapFile._set_file_type works correctly for files that don't match a regex"""
        filename = os.path.join(self.tempdir, 'phs000284.v1.pht001903.v1.p1.CFS_CARe_ECG.var_report_2011_02_07.xml.gz')
        _touch(filename)
        dbgap_file = DbgapFile(filename)
        self.assertIsNone(dbgap_file.file_type)
        self.assertIsNone(dbgap_file.match)

    def test_exception_file_not_found(self):
        """is an exception raised when the file is not found?"""
        filename = os.path.join(self.tempdir, 'phs000284.v1.pht001903.v1.p1.CFS_CARe_ECG.var_report_2011_02_07.xml.gz')
        with self.assertRaises(FileNotFoundError):
            dbgap_file = DbgapFile(filename)

    def test_works_with_nonexistent_file_and_check_exists_false(self):
        """is an exception not raised when the file is not found but check_exists=False?"""
        filename = os.path.join(self.tempdir, 'phs000284.v1.pht001903.v1.p1.CFS_CARe_ECG.var_report_2011_02_07.xml.gz')
        # this should not crash
        dbgap_file = DbgapFile(filename, check_exists=False)

    def test_with_different_regex_phenotype(self):
        """test that DbgapFile._set_file_type works with a different regex pattern dictionary for phentoype files"""
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
        """test that DbgapFile._set_file_type works with a different regex pattern dictionary for data dict files"""
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
        """test that DbgapFile._set_file_type works with a different regex pattern dictionary for var_report files"""
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
        """test that DbgapFile._set_file_type works with a different regex pattern dictionary for special files"""
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
    """class to hold tests for _get_file_list function"""

    def test_returns_list_of_dbgap_files(self):
        """is a list of DbagpFile objects returned?"""
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
    """class to hold tests for _check_diffs function"""

    def test_working_when_no_diff(self):
        """does _check_diffs work when the files are not different?"""
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
        """Does _check_diffs raise a ValueError exception if the files are different?"""
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
    """Class to hold tests for _get_file_match function"""

    def test_working_data_dict(self):
        """does it properly match data dictionaries?"""
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
        """does it properly match var_reports?"""
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

    def test_raise_exception_if_no_match_with_different_file_type(self):
        """does it return None if there are no matches?"""
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
        with self.assertRaises(IndexError):
            organize_dbgap._get_file_match(files, file_to_match, 'var_report', check_diffs=False)

    def test_working_with_multiple_matches_returns_one(self):
        """does it return only one file if multiple matches are found?"""
        # make two directories, one for each consent group
        dir1 = os.path.join(self.tempdir, 'dir1')
        dir2 = os.path.join(self.tempdir, 'dir2')

        phs = 7
        pht = 1

        # make a set of matching dd files
        base_dd_filename = _get_test_dbgap_filename('data_dict', phs=phs, phs_v=1, pht=pht, pht_v=1)
        filename_dd1 = os.path.join(dir1, base_dd_filename)
        dd1 = DbgapFile(filename_dd1, check_exists=False)
        filename_dd2 = os.path.join(dir2, base_dd_filename)
        dd2 = DbgapFile(filename_dd2, check_exists=False)

        # make the file to match
        filename_to_match = _get_test_dbgap_filename('phenotype', phs=phs, phs_v=1, pht=pht, pht_v=1)
        phenotype = DbgapFile(filename_to_match, check_exists=False)

        files = [dd1, phenotype, dd2]
        self.assertEqual(organize_dbgap._get_file_match(files, phenotype, 'data_dict', check_diffs=False), dd1)

    def test_working_with_check_diffs_no_diff(self):
        """does it work with check_diffs and no differences?"""
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
        """does it raise an exception with check_diffs and different matching files?"""
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


class DbgapDirectoryStructureTestCase(TempdirTestCase):
    """superclass that auto-creates a dbgap directory structure"""

    def _make_file_set(self, file_type):
        # make a set of phenotype/var_reports/data_dicts in each
        kwargs = {'phs': self.phs,
                  'phs_v': self.phs_v,
                  'pht': fake.pyint(),
                  'pht_v': fake.pyint(),
                  'base': fake.word(),
                  'ps': self.ps,
                  'consent': 1,
                  'consent_code': self.consent_code1
                  }

        if file_type == 'subject':
            kwargs['base'] = 'Subject'
        if file_type == 'sample':
            kwargs['base'] = 'Sample'
        if file_type == 'pedigree':
            kwargs['base'] = 'Pedigree'

        # consent group 1
        # data
        filename = os.path.join(self.dir1, _get_test_dbgap_filename(file_type, **kwargs))
        _touch(filename)
        self.data_file1 = DbgapFile(filename)

        # var reports
        filename = os.path.join(self.dir1, _get_test_dbgap_filename('var_report', **kwargs))
        _touch(filename)
        self.var_report1 = DbgapFile(filename)

        # data_dicts
        filename = os.path.join(self.dir1, _get_test_dbgap_filename('data_dict', **kwargs))
        _touch(filename)
        self.dd1 = DbgapFile(filename)

        # consent group 2
        kwargs['consent'] = 2
        kwargs['consent_code'] = self.consent_code2

        # data
        filename = os.path.join(self.dir2, _get_test_dbgap_filename(file_type, **kwargs))
        _touch(filename)
        self.data_file2 = DbgapFile(filename)

        # var reports
        filename = os.path.join(self.dir2, _get_test_dbgap_filename('var_report', **kwargs))
        _touch(filename)
        self.var_report2 = DbgapFile(filename)

        # data_dicts
        filename = os.path.join(self.dir2, _get_test_dbgap_filename('data_dict', **kwargs))
        _touch(filename)
        self.dd2 = DbgapFile(filename)

    def setUp(self):
        # call superclass constructor
        super(DbgapDirectoryStructureTestCase, self).setUp()
        # now make a directory structure
        self.dir1 = os.path.join(self.tempdir, "dir1")
        os.mkdir(self.dir1)
        self.dir2 = os.path.join(self.tempdir, "dir2")
        os.mkdir(self.dir2)

        self.phs = fake.pyint()
        self.phs_v = fake.pyint()
        self.ps = fake.pyint()

        self.consent_code1 = fake.word()
        self.consent_code2 = fake.word()

    def tearDown(self):
        # call superclass constructor - should delete temp dir
        super(DbgapDirectoryStructureTestCase, self).tearDown()


class GetSpecialFileSetTestCase(DbgapDirectoryStructureTestCase):
    
    def test_working_with_subject_pattern(self):
        self._make_file_set('phenotype')
        self._make_file_set('subject')
        dbgap_files = organize_dbgap.get_file_list(self.tempdir)
        file_set = organize_dbgap._get_special_file_set(dbgap_files, pattern='Subject')
        self.assertIsInstance(file_set, dict)
        self.assertIsInstance(file_set['var_report'], DbgapFile)
        self.assertIsInstance(file_set['var_report'], DbgapFile)
        self.assertIsInstance(file_set['data_files'], list)
        self.assertEqual(len(file_set['data_files']), 1)
        # checking files
        self.assertTrue(file_set['var_report'].full_path in [self.var_report1.full_path, self.var_report2.full_path])
        self.assertTrue(file_set['data_dict'].full_path in [self.dd1.full_path, self.dd2.full_path])
        self.assertTrue(file_set['data_files'][0].full_path in [self.data_file1.full_path, self.data_file2.full_path])

    def test_working_with_sample_pattern(self):
        self._make_file_set('phenotype')
        self._make_file_set('sample')
        dbgap_files = organize_dbgap.get_file_list(self.tempdir)
        file_set = organize_dbgap._get_special_file_set(dbgap_files, pattern='Sample')
        self.assertIsInstance(file_set, dict)
        self.assertIsInstance(file_set['var_report'], DbgapFile)
        self.assertIsInstance(file_set['var_report'], DbgapFile)
        self.assertIsInstance(file_set['data_files'], list)
        self.assertEqual(len(file_set['data_files']), 1)
        # checking files
        self.assertTrue(file_set['var_report'].full_path in [self.var_report1.full_path, self.var_report2.full_path])
        self.assertTrue(file_set['data_dict'].full_path in [self.dd1.full_path, self.dd2.full_path])
        self.assertTrue(file_set['data_files'][0].full_path in [self.data_file1.full_path, self.data_file2.full_path])

    def test_working_with_pedigree_pattern(self):
        self._make_file_set('phenotype')
        self._make_file_set('pedigree')
        dbgap_files = organize_dbgap.get_file_list(self.tempdir)
        file_set = organize_dbgap._get_special_file_set(dbgap_files, pattern='Pedigree')
        self.assertIsInstance(file_set, dict)
        self.assertIsInstance(file_set['var_report'], DbgapFile)
        self.assertIsInstance(file_set['var_report'], DbgapFile)
        self.assertIsInstance(file_set['data_files'], list)
        self.assertEqual(len(file_set['data_files']), 1)
        # checking files
        self.assertTrue(file_set['var_report'].full_path in [self.var_report1.full_path, self.var_report2.full_path])
        self.assertTrue(file_set['data_dict'].full_path in [self.dd1.full_path, self.dd2.full_path])
        self.assertTrue(file_set['data_files'][0].full_path in [self.data_file1.full_path, self.data_file2.full_path])

    def test_exception_without_matching_data_dict(self):
        self._make_file_set('phenotype')
        self._make_file_set('pedigree')
        # remove both of the matching data dictionaries
        os.remove(self.dd1.full_path)
        os.remove(self.dd2.full_path)
        dbgap_files = organize_dbgap.get_file_list(self.tempdir)
        with self.assertRaises(Exception):
            organize_dbgap._get_special_file_set(dbgap_files, pattern='Pedigree')

    def test_exception_without_matching_var_report(self):
        self._make_file_set('phenotype')
        self._make_file_set('pedigree')
        # remove both of the matching data dictionaries
        os.remove(self.var_report1.full_path)
        os.remove(self.var_report2.full_path)
        dbgap_files = organize_dbgap.get_file_list(self.tempdir)
        with self.assertRaises(Exception):
            organize_dbgap._get_special_file_set(dbgap_files, pattern='Pedigree')

class GetPhenotypeFileSetsTestCase(DbgapDirectoryStructureTestCase):

    def test_working_with_one_phenotype_file_set(self):
        self._make_file_set('phenotype')
        dbgap_files = organize_dbgap.get_file_list(self.tempdir)
        file_sets = organize_dbgap._get_phenotype_file_sets(dbgap_files)
        self.assertIsInstance(file_sets, list)
        self.assertEqual(len(file_sets), 1)
        file_set = file_sets[0]
        self.assertIsInstance(file_set['var_report'], DbgapFile)
        self.assertIsInstance(file_set['var_report'], DbgapFile)
        self.assertIsInstance(file_set['data_files'], list)
        self.assertEqual(len(file_set['data_files']), 2) # 2 consent groups
        # checking files
        self.assertTrue(file_set['var_report'].full_path in [self.var_report1.full_path, self.var_report2.full_path])
        self.assertTrue(file_set['data_dict'].full_path in [self.dd1.full_path, self.dd2.full_path])
        self.assertTrue(file_set['data_files'][0].full_path in [self.data_file1.full_path, self.data_file2.full_path])
        self.assertTrue(file_set['data_files'][1].full_path in [self.data_file1.full_path, self.data_file2.full_path])

    def test_working_with_two_phenotype_file_sets(self):
        self._make_file_set('phenotype')
        pheno_file1 = self.data_file1
        self._make_file_set('phenotype')
        pheno_file2 = self.data_file1
        
        dbgap_files = organize_dbgap.get_file_list(self.tempdir)
        file_sets = organize_dbgap._get_phenotype_file_sets(dbgap_files)
        self.assertIsInstance(file_sets, list)
        self.assertEqual(len(file_sets), 2)

class MakeSymlinkTestCase(TempdirTestCase):

    def setUp(self):
        # call superclass constructor
        super(MakeSymlinkTestCase, self).setUp()
        # make a file
        self.basename = _get_test_dbgap_filename('phenotype')
        self.full_path = os.path.join(self.tempdir, self.basename)
        _touch(self.full_path)
        self.dbgap_file = DbgapFile(self.full_path)
        # make a subdirectory
        self.subdir = fake.word()
        os.mkdir(os.path.join(self.tempdir, self.subdir))


    def test_working(self):
        os.chdir(os.path.join(self.tempdir, self.subdir))
        organize_dbgap._make_symlink(self.dbgap_file)
        self.assertTrue(os.path.exists(self.basename))

    def test_exception_if_path_does_not_exist(self):
        os.remove(self.dbgap_file.full_path)
        with self.assertRaises(FileNotFoundError):
            organize_dbgap._make_symlink(self.dbgap_file)


class MakeSymlinkSetTestCase(DbgapDirectoryStructureTestCase):

    def test_working(self):
        # generate a set of phenotype files
        self._make_file_set('subject')
        dbgap_files = organize_dbgap.get_file_list(self.tempdir)
        #print(os.getcwd())
        file_set = organize_dbgap._get_special_file_set(dbgap_files)
        subdir = os.path.join(self.tempdir, fake.word())
        os.mkdir(subdir)
        os.chdir(subdir)
        organize_dbgap._make_symlink_set(file_set)
        self.assertTrue(os.path.exists(file_set['var_report'].full_path))
        self.assertTrue(os.path.exists(file_set['data_dict'].full_path))
        for x in file_set['data_files']:
            self.assertTrue(os.path.exists(x.full_path))

class MakeSymlinksTestCase(DbgapDirectoryStructureTestCase):

    def test_working(self):
        # generate a set of all files
        self._make_file_set('phenotype')
        self._make_file_set('phenotype')
        self._make_file_set('subject')
        self._make_file_set('sample')
        self._make_file_set('pedigree')
        # get file sets
        dbgap_files = organize_dbgap.get_file_list(self.tempdir)
        subject_set = organize_dbgap._get_special_file_set(dbgap_files, pattern="Subject")
        pedigree_set = organize_dbgap._get_special_file_set(dbgap_files, pattern="Pedigree")
        sample_set = organize_dbgap._get_special_file_set(dbgap_files, pattern="Sample")
        pheno_set = organize_dbgap._get_phenotype_file_sets(dbgap_files)
        # make a subdir
        subdir = os.path.join(self.tempdir, fake.word())
        os.mkdir(subdir)
        os.chdir(subdir)
        organize_dbgap._make_symlinks(subject_set, pedigree_set, sample_set, pheno_set)
        self.assertTrue(os.path.exists("organized"))
        self.assertTrue(os.path.exists("organized/Phenotypes"))
        self.assertTrue(os.path.exists("organized/Subject"))
        # make sure files are in the right place
        # we only need to check one of the data files, because _make_symlink_set was already tested
        self.assertTrue(os.path.exists('organized/Subject/'+subject_set['data_files'][0].basename))
        self.assertTrue(os.path.exists('organized/Subject/'+sample_set['data_files'][0].basename))
        self.assertTrue(os.path.exists('organized/Subject/'+pedigree_set['data_files'][0].basename))
        self.assertTrue(os.path.exists('organized/Phenotypes/'+pheno_set[0]['data_files'][0].basename))
        self.assertTrue(os.path.exists('organized/Phenotypes/'+pheno_set[1]['data_files'][0].basename))

class UncompressTestCase(TempdirTestCase):

    def test_working_with_gzipped_txt_file(self):
        # make a file and compress it
        filename = os.path.join(self.tempdir, fake.file_name(extension="txt"))
        _touch(filename)
        cmd = 'gzip {file}'.format(file=filename)
        subprocess.check_call(cmd, shell=True)
        organize_dbgap.uncompress(self.tempdir)
        self.assertTrue(os.path.exists(filename))
        self.assertFalse(os.path.exists(filename + ".gz"))

    def test_non_txt_gzipped_file_still_compressed(self):
        filename = os.path.join(self.tempdir, fake.file_name(extension="png"))
        _touch(filename)
        cmd = 'gzip {file}'.format(file=filename)
        subprocess.check_call(cmd, shell=True)
        organize_dbgap.uncompress(self.tempdir)
        self.assertTrue(os.path.exists(filename + ".gz"))
        self.assertFalse(os.path.exists(filename))

if __name__ == '__main__':
    unittest.main()