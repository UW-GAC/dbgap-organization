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

    def test_no_exception_on_nonexistent_file_with_must_exist_equals_False(self):
        """does it return None with a nonexistent file and must_exist = False?"""
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

        files = [other_file, file_to_match]
        self.assertIsNone(organize_dbgap._get_file_match(files, file_to_match, 'data_dict', must_exist=False))

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
        """Make some subdirectories that repereset different dbgap consent group downloads,
        plus a phs accession, version, participant set, and consent codes"""
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
        """test that _get_special_file_set works for subject files"""
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
        """test that _get_special_file_set works for sample files"""
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
        """test that _get_special_file_set works for pedigree files"""
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
        """test that _get_special_file_set raises an exceptoin if no data dictionary is found"""
        self._make_file_set('phenotype')
        self._make_file_set('pedigree')
        # remove both of the matching data dictionaries
        os.remove(self.dd1.full_path)
        os.remove(self.dd2.full_path)
        dbgap_files = organize_dbgap.get_file_list(self.tempdir)
        with self.assertRaises(Exception):
            organize_dbgap._get_special_file_set(dbgap_files, pattern='Pedigree')

    #def test_exception_without_matching_var_report(self):
    #    """test that _get_special_file_set raises an exceptoin if no var_report is found"""
    #    self._make_file_set('phenotype')
    #    self._make_file_set('pedigree')
    #    # remove both of the matching data dictionaries
    #    os.remove(self.var_report1.full_path)
    #    os.remove(self.var_report2.full_path)
    #    dbgap_files = organize_dbgap.get_file_list(self.tempdir)
    #    with self.assertRaises(Exception):
    #        organize_dbgap._get_special_file_set(dbgap_files, pattern='Pedigree')

    def test_exception_if_special_files_are_different(self):
        self._make_file_set('phenotype')
        self._make_file_set('subject')
        dbgap_files = organize_dbgap.get_file_list(self.tempdir)
        # change one of the files to have different text
        _touch(self.data_file1.full_path, text=fake.text())
        with self.assertRaises(ValueError):
            organize_dbgap._get_special_file_set(dbgap_files, pattern='Subject')

    def test_returns_none_if_pattern_does_not_exist(self):
        self._make_file_set('phenotype')
        dbgap_files = organize_dbgap.get_file_list(self.tempdir)
        self.assertIsNone(organize_dbgap._get_special_file_set(dbgap_files, pattern='Subject'))


class GetPhenotypeFileSetsTestCase(DbgapDirectoryStructureTestCase):
    """Tests for _get_phenotype_file_set function"""

    def test_working_with_one_phenotype_file_set(self):
        """_get_phenotype_file_set works as expected with one phenotype file set"""
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
        """_get_phenotype_file_set works as expected with two phenotype file sets"""
        self._make_file_set('phenotype')
        pheno_file1 = self.data_file1
        self._make_file_set('phenotype')
        pheno_file2 = self.data_file1
        
        dbgap_files = organize_dbgap.get_file_list(self.tempdir)
        file_sets = organize_dbgap._get_phenotype_file_sets(dbgap_files)
        self.assertIsInstance(file_sets, list)
        self.assertEqual(len(file_sets), 2)

    def test_exception_raised_if_different_number_of_phenotype_files(self):
        """test that there are the same number of phenotype data_files in each.
        meant to catch the case where consent group 1 has (file1, file2) and
        consent group 2 only has (file1)."""
        self._make_file_set('phenotype')
        self._make_file_set('phenotype')
        # remove one of the consent groups' phenotype files
        os.remove(self.data_file2.full_path)
        dbgap_files = organize_dbgap.get_file_list(self.tempdir)
        with self.assertRaises(ValueError):
            organize_dbgap._get_phenotype_file_sets(dbgap_files)


class CheckSymlinkTestCase(TempdirTestCase):
    """tests for _check_symlink"""

    def test_true_if_working_symlink(self):
        os.chdir(self.tempdir)
        filename = fake.file_name()
        _touch(os.path.join(self.tempdir, filename))
        symlink_name = fake.file_name()
        os.symlink(filename, symlink_name)
        self.assertTrue(organize_dbgap._check_symlink(symlink_name))

    def test_false_if_broken_symlink(self):
        os.chdir(self.tempdir)
        filename = fake.file_name()
        _touch(os.path.join(self.tempdir, filename))
        symlink_name = fake.file_name()
        os.symlink(filename, symlink_name)
        # remove the original file so the symlink breaks
        os.remove(filename)
        self.assertFalse(organize_dbgap._check_symlink(symlink_name))

    def test_exception_if_symlink_path_doesnt_exist(self):
        filename = fake.file_name()
        with self.assertRaises(FileNotFoundError):
            organize_dbgap._check_symlink(filename)

class MakeSymlinkTestCase(TempdirTestCase):
    """Tests for _make_symlink"""

    def setUp(self):
        """all tests here need a subdirectory and a file, so make those"""
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
        """test that symlinks are properly created"""
        os.chdir(os.path.join(self.tempdir, self.subdir))
        organize_dbgap._make_symlink(self.dbgap_file)
        self.assertTrue(os.path.exists(self.basename))

    def test_exception_if_path_does_not_exist(self):
        """Test that _make_symlink raises an exception if the requested file is not found"""
        os.remove(self.dbgap_file.full_path)
        with self.assertRaises(FileNotFoundError):
            organize_dbgap._make_symlink(self.dbgap_file)


class MakeSymlinkSetTestCase(DbgapDirectoryStructureTestCase):
    """Tests for _make_symlink_set function"""
    def test_working(self):
        """test that _make_symlink_set makes the symlinks for all parts of the file_set"""
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
    """Tests for _make_symlinks function"""

    def test_working(self):
        """test that it works for a standard set of dbgap files, two consent groups"""
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
        organize_dbgap._make_symlinks(subdir, subject_set, pedigree_set, sample_set, pheno_set)
        # test that directories and files were created properly
        os.chdir(subdir)
        self.assertTrue(os.path.exists(os.path.join(subdir, "Phenotypes")))
        self.assertTrue(os.path.exists(os.path.join(subdir, "Subject")))
        # make sure files are in the right place
        # we only need to check one of the data files, because _make_symlink_set was already tested
        self.assertTrue(os.path.exists('Subject/'+subject_set['data_files'][0].basename))
        self.assertTrue(os.path.exists('Subject/'+sample_set['data_files'][0].basename))
        self.assertTrue(os.path.exists('Subject/'+pedigree_set['data_files'][0].basename))
        self.assertTrue(os.path.exists('Phenotypes/'+pheno_set[0]['data_files'][0].basename))
        self.assertTrue(os.path.exists('Phenotypes/'+pheno_set[1]['data_files'][0].basename))

class UncompressTestCase(TempdirTestCase):
    """Tests for uncompress function"""

    def test_working_with_gzipped_txt_file_in_different_directory(self):
        """Test that uncompress properly unzips a .txt.gz file"""
        # make a file and compress it
        filename = os.path.join(self.tempdir, fake.file_name(extension="txt"))
        _touch(filename)
        cmd = 'gzip {file}'.format(file=filename)
        subprocess.check_call(cmd, shell=True)
        os.chdir(self.original_directory)
        organize_dbgap.uncompress(self.tempdir)
        self.assertTrue(os.path.exists(os.path.join(self.tempdir, filename)))
        self.assertFalse(os.path.exists(os.path.join(self.tempdir, filename + ".gz")))

    def test_non_txt_gzipped_file_still_compressed(self):
        """Test that uncompress does not unzip a non-.txt.gz file"""
        filename = os.path.join(self.tempdir, fake.file_name(extension="png"))
        _touch(filename)
        cmd = 'gzip {file}'.format(file=filename)
        subprocess.check_call(cmd, shell=True)
        organize_dbgap.uncompress(self.tempdir)
        self.assertTrue(os.path.exists(filename + ".gz"))
        self.assertFalse(os.path.exists(filename))

    def test_working_with_tar_gz_in_different_directory(self):
        """Test that uncompress properly untars a .tar.gz file from a different directory"""
        os.chdir(self.tempdir)
        file1 = fake.file_name(extension="txt")
        _touch(file1)
        file2 = fake.file_name(extension="txt")
        _touch(file2)
        # tar them
        tarfile = fake.file_name(extension='tar.gz')
        cmd = 'tar -czf {tarfile} {file1} {file2}'.format(tarfile=tarfile, file1=file1, file2=file2)
        subprocess.check_call(cmd, shell=True)
        # remove original files
        os.remove(file1)
        os.remove(file2)
        os.chdir(self.original_directory)
        organize_dbgap.uncompress(self.tempdir)
        self.assertTrue(os.path.exists(os.path.join(self.tempdir, file1)))
        self.assertTrue(os.path.exists(os.path.join(self.tempdir, file2)))
        self.assertFalse(os.path.exists(os.path.join(self.tempdir, tarfile)))

    def test_working_with_tar_gz_in_subfolder_from_different_directory(self):
        """test that uncompress properly untars a tar.gz file in a subdirectory"""
        os.chdir(self.tempdir)
        # make a subdirectory - the tar file and original files will be in the subdirectory
        subdir = fake.word()
        os.mkdir(os.path.join(self.tempdir, subdir))
        os.chdir(subdir)
        file1 = fake.file_name(extension="txt")
        _touch(file1)
        file2 = fake.file_name(extension="txt")
        _touch(file2)
        # tar them
        tarfile = fake.file_name(extension='tar.gz')
        cmd = 'tar -czf {tarfile} {file1} {file2}'.format(tarfile=tarfile, file1=file1, file2=file2)
        subprocess.check_call(cmd, shell=True)
        # remove original files
        os.remove(file1)
        os.remove(file2)
        os.chdir(self.original_directory)
        organize_dbgap.uncompress(self.tempdir)
        # make sure that the files are in the proper subdirectory after uncompress
        self.assertTrue(os.path.exists(os.path.join(self.tempdir, subdir, file1)))
        self.assertTrue(os.path.exists(os.path.join(self.tempdir, subdir, file2)))
        self.assertFalse(os.path.exists(os.path.join(self.tempdir, subdir, tarfile)))

    def test_recursive(self):
        """test that uncompress works recursively, ie it untars a tar file that has
        a .txt.gz file inside, and then that the .txt.gz file is unzipped"""
        os.chdir(self.tempdir)
        file1 = fake.file_name(extension="txt")
        _touch(file1)
        file2 = fake.file_name(extension='txt')
        _touch(file2)
        # zip one of them
        cmd = 'gzip {file}'.format(file=file1)
        subprocess.check_call(cmd, shell=True)
        # inside a tar file
        tarfile = fake.file_name(extension='tar.gz')
        cmd = 'tar -czf {tarfile} {file1} {file2}'.format(tarfile=tarfile, file1=file1+'.gz', file2=file2)
        subprocess.check_call(cmd, shell=True)
        # remove original file
        os.remove(file1 + ".gz")
        os.remove(file2)
        os.chdir(self.original_directory)
        # uncompress
        organize_dbgap.uncompress(self.tempdir)
        self.assertTrue(os.path.exists(os.path.join(self.tempdir, file1)))
        self.assertTrue(os.path.exists(os.path.join(self.tempdir, file2)))
        self.assertFalse(os.path.exists(os.path.join(self.tempdir, tarfile)))


class CreateFinalDirectoryTestCase(TempdirTestCase):
    """Tests for create_final_directory function"""

    def setUp(self):
        """All tests here need a phs_string and a version_string, so make them here"""
        super(CreateFinalDirectoryTestCase, self).setUp()
        self.phs = 'phs{phs:06d}'.format(phs=fake.pyint())
        self.version = 'v{v}'.format(v=fake.pyint())

    def test_working(self):
        """test that create_final_directory_structure works with expected input"""
        organize_dbgap.create_final_directory(self.phs, self.version, self.tempdir)
        self.assertTrue(os.path.exists(os.path.join(self.tempdir, self.phs)))
        self.assertTrue(os.path.exists(os.path.join(self.tempdir, self.phs, self.version)))

    def test_working_if_phs_exists_but_version_does_not(self):
        """test that create_final_directory_structure works with expected input, and if
        the phs directory already exists"""
        os.mkdir(os.path.join(self.tempdir, self.phs))
        organize_dbgap.create_final_directory(self.phs, self.version, self.tempdir)
        self.assertTrue(os.path.exists(os.path.join(self.tempdir, self.phs, self.version)))

    def test_exception_raised_if_phs_and_version_exist(self):
        """Test that create_final_directory structure raises an exception if the version
        of this stuy already has a directory"""
        os.mkdir(os.path.join(self.tempdir, self.phs))
        os.mkdir(os.path.join(self.tempdir, self.phs, self.version))
        with self.assertRaises(FileExistsError):
            organize_dbgap.create_final_directory(self.phs, self.version, self.tempdir)

    def test_exception_if_directory_doesnt_exist(self):
        """Test that create_final_directory raises an exception if the specified out_path doesn't exist"""
        nonexistent_directory = 'foo'
        with self.assertRaisesRegex(FileNotFoundError, r"{outdir}'$".format(outdir=nonexistent_directory)):
            organize_dbgap.create_final_directory(self.phs, self.version, nonexistent_directory)

class CopyFilesTestCase(TempdirTestCase):
    """Tests of copy_files function"""

    def test_working(self):
        """test that copy_files works as expected"""
        os.chdir(self.tempdir)
        subdir1 = fake.word()
        os.mkdir(subdir1)
        filename = fake.file_name()
        _touch(os.path.join(subdir1, filename))
        # second subdirectory to copy to, but don't create it; the copy_files function should
        subdir2 = fake.word()
        organize_dbgap.copy_files(subdir1, subdir2)
        self.assertTrue(os.path.exists(os.path.join(subdir2, filename)))


    def test_fails_if_to_path_already_exists(self):
        """test that copy_files fails if the destination path already exists"""
        os.chdir(self.tempdir)
        subdir1 = fake.word()
        os.mkdir(subdir1)
        filename = fake.file_name()
        _touch(os.path.join(subdir1, filename))
        # second subdirectory to copy to, but don't create it; the copy_files function should
        subdir2 = fake.word()
        os.mkdir(subdir2)
        with self.assertRaises(Exception):
            organize_dbgap.copy_files(subdir1, subdir2)


class OrganizeTestCase(DbgapDirectoryStructureTestCase):
    """Tests for organize function"""

    def setUp(self):
        """these tests need a second temporary directory for the organized files"""
        # call superclass setUp function
        super(OrganizeTestCase, self).setUp()
        # create a second tempdir for the organization
        self.organized_dir = tempfile.mkdtemp()

    def tearDown(self):
        super(OrganizeTestCase, self).tearDown()
        # also remove the temp organized directory
        shutil.rmtree(self.organized_dir)

    def test_working(self):
        """test that organize makes the proper subdirectories when linking;
        we already test all the other functions that are called by organize,
        so those are not explicitly tested here."""
        self._make_file_set('phenotype')
        pheno_file_check = self.data_file1
        self._make_file_set('subject')
        subject_file_check = self.data_file1
        self._make_file_set('sample')
        sample_file_check = self.data_file1
        self._make_file_set('pedigree')
        pedigree_file_check = self.data_file1
        # move all the files to the raw directory, because it's required by the organize function
        organize_dbgap.organize(self.tempdir, self.organized_dir, link=True)
        self.assertTrue(os.path.exists(os.path.join(self.organized_dir, "Subject")))
        self.assertNotEqual(os.listdir(os.path.join(self.organized_dir, "Subject")), 0)
        self.assertTrue(os.path.exists(os.path.join(self.organized_dir, "Phenotypes")))
        self.assertNotEqual(os.listdir(os.path.join(self.organized_dir, "Phenotypes")), 0)

class ParseInputDirectoryReleasedTestCase(unittest.TestCase):
    """Tests for parse_input_directory with released data. Note that it is impossible
    to test all non-matches for the regex, so only a few specific cases are tested"""

    def test_working(self):
        """test that a directory with the expected structure is appropriately parsed"""
        phs_string = 'phs{phs:06d}'.format(phs=fake.pyint())
        version_string = 'v{v}'.format(v=fake.pyint())
        input_directory = '.'.join([phs_string, version_string])
        result = organize_dbgap.parse_input_directory(input_directory)
        self.assertIsInstance(result, dict)
        self.assertEqual(result['phs'], phs_string)
        self.assertEqual(result['v'], version_string)

    def test_working_with_abs_path(self):
        """test that parse_input_directory works with an absolute path instead of
        a relative path"""
        phs_string = 'phs{phs:06d}'.format(phs=fake.pyint())
        version_string = 'v{v}'.format(v=fake.pyint())
        input_directory = os.path.abspath('.'.join([phs_string, version_string]))
        result = organize_dbgap.parse_input_directory(input_directory)
        self.assertIsInstance(result, dict)
        self.assertEqual(result['phs'], phs_string)
        self.assertEqual(result['v'], version_string)

    def test_working_with_trailing_slash(self):
        """test that parse_input_directory works if the input directory has a trailing slash"""
        phs_string = 'phs{phs:06d}'.format(phs=fake.pyint())
        version_string = 'v{v}'.format(v=fake.pyint())
        input_directory = '.'.join([phs_string, version_string]) + "/"
        result = organize_dbgap.parse_input_directory(input_directory)
        self.assertIsInstance(result, dict)
        self.assertEqual(result['phs'], phs_string)
        self.assertEqual(result['v'], version_string)

    def test_exception_if_wrong_format_phs(self):
        """test that an exception is raised if the directory has the wrong phs format"""
        phs_string = 'phs{phs:05d}'.format(phs=fake.pyint())
        version_string = 'v{v}'.format(v=fake.pyint())
        input_directory = '.'.join([phs_string, version_string])
        with self.assertRaises(ValueError):
            organize_dbgap.parse_input_directory(input_directory)

    def test_exception_if_missing_version(self):
        """test that an exception is raised if the directory is missing the version"""
        phs_string = 'phs{phs:05d}'.format(phs=fake.pyint())
        with self.assertRaises(ValueError):
            organize_dbgap.parse_input_directory(phs_string)

    def test_exception_wrong_join(self):
        """test that an exception is raised if the phs and version are separated by the wrong character"""
        phs_string = 'phs{phs:05d}'.format(phs=fake.pyint())
        version_string = 'v{v}'.format(v=fake.pyint())
        input_directory = '-'.join([phs_string, version_string])
        with self.assertRaises(ValueError):
            organize_dbgap.parse_input_directory(phs_string)

class ParseInputDirectoryPrereleaseTestCase(unittest.TestCase):
    """Tests for parse_input_directory with pre-accessioned data Note that it is impossible
    to test all non-matches for the regex so only a few specific cases are tested."""
    
    def test_working(self):
        date = '20160208'
        input_directory = ''.join(['ProcessedPheno', date])
        result = organize_dbgap.parse_input_directory(input_directory, prerelease=True)
        self.assertIsInstance(result, dict)
        self.assertEqual(result['date'], date)

    def test_working_with_trailing_slash(self):
        date = '20160208'
        input_directory = ''.join(['ProcessedPheno', date, '/'])
        result = organize_dbgap.parse_input_directory(input_directory, prerelease=True)
        self.assertIsInstance(result, dict)
        self.assertEqual(result['date'], date)

    def test_fails_with_invalid_regex(self):
        prefix = fake.word()
        date = '20160208'
        input_directory = ''.join([prefix, date])
        with self.assertRaises(ValueError):
            organize_dbgap.parse_input_directory(input_directory, prerelease=True)

    def test_fails_with_valid_regex_but_invalid_date(self):
        prefix = 'ProcessedPheno'
        date = '20169999'
        input_directory = ''.join([prefix, date])
        with self.assertRaises(ValueError):
            organize_dbgap.parse_input_directory(input_directory, prerelease=True)

    def test_fails_with_valid_regex_but_valid_date_that_is_not_zero_padded(self):
        prefix = 'ProcessedPheno'
        date = '2016101'
        input_directory = ''.join([prefix, date])
        with self.assertRaises(ValueError):
            organize_dbgap.parse_input_directory(input_directory, prerelease=True)
    
if __name__ == '__main__':
    unittest.main()