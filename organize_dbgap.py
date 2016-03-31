#!/usr/bin/env python3.4

import os
import sys
import re # regular expressions
from argparse import ArgumentParser
import subprocess # for system commands - in this case, only diff
from pprint import pprint


# regular expression matchers for various kinds of dbgap files
dbgap_re_dict = {'data_dict': r'^(?P<dbgap_id>phs\d{6}\.v\d+?\.pht\d{6}\.v\d+?)\.(?P<base>.+?)\.data_dict(?P<extra>\w{0,}?)\.xml$',
           'phenotype': r'^(?P<dbgap_id>phs\d{6}\.v\d+?\.pht\d{6}\.v\d+?)\.p(\d+?)\.c(\d+?)\.(?P<base>.+?)\.(?P<consent_code>.+?)\.txt$',
           'var_report': r'^(?P<dbgap_id>phs\d{6}\.v\d+?\.pht\d{6}\.v\d+?)\.p(\d+?)\.(?P<base>.+?)\.var_report(\w{0,}?)\.xml$',
           'special': r'^(?P<dbgap_id>phs\d{6}\.v\d+?\.pht\d{6}\.v\d+?)\.p(\d+?)\.(.+?)\.MULTI.txt$'
           }

# some notes:
# the var_reports and data dictionaries pertain to a single participant set number; they are the same across consent groups
# we only need to link 1 var_report and 1 data_dict for each phenotype dataset.

class DbgapFile(object):
    """Class to hold information about files downloaded from dbgap.
    """
    def __init__(self, file_path):
        """Constructor function for DbgapFile instances.
        
        Arguments:
        
        file_path: full path to a file downloaded from dbgap
        """
        self.full_path = file_path
        self.basename = os.path.basename(file_path)
        
        # these will be set in sorting
        self.file_type = None # possibilities are 'phenotype', 'var_report', 'data_dict'
        self.match = None # will store the regular expression re.match object


    def __str__(self):
        """string method for DbgapFile objects"""
        return self.full_path
    
    
    def set_file_type(self, re_dict=dbgap_re_dict):
        """Function to set the file_type of a DbgapFile object, based on regular expression patterns"""
        
        for key, value in re_dict.items():
            match = re.match(value, self.basename)
            if match is not None:
                self.file_type = key
                self.match = match

    
def get_file_list(directory):
    """Returns a list of DbgapFile objects, one for each file in the downloaded directory tree.
    The DbgapFile objects will already have been classified with their file_type attribute set.
    """
    file_list = []
    for root, dirs, files in os.walk(directory):
        for name in files:
            full_path = os.path.join(root, name)
            
            dbgap_file = DbgapFile(full_path)
            dbgap_file.set_file_type()
            
            file_list.append(dbgap_file)
    
    return file_list
    

def _check_diffs(dbgap_file_subset):
    """Run a unix diff on a set of files to make sure that they are all the same.
    
    If they are not the same, a ValueError is raised."""
    filename_a = dbgap_file_subset[0].full_path
    
    for i in range(1, len(dbgap_file_subset)):
        filename_b = dbgap_file_subset[i].full_path
        cmd = 'diff {file1} {file2}'.format(file1=filename_a, file2=filename_b)
        out = subprocess.check_output(cmd, shell=True)
        if len(out) > 0:
            raise ValueError('files are expect to be the same but are different: {file_a}, {file_b}'.format(file_a=filename_a, file_b=filename_b))


def _get_var_report_match(dbgap_files, dbgap_file_to_match, check_diffs=True):
    """For a given DbgapFile, find the matcing var_report DbgapFile.
    
    Arguments:
    
    dbgap_files: list of DbgapFile objects returned from get_file_list
    dbgap_file_to_match: single DbgapFile object for which to find the matching var_report file
    
    Optional arguments:
    check_diffs: if True, check that all matching var_report files are the same.
    
    Files are matched based on file_type (to identify var_reports) and the
    dgap_id capture group from the regular expressions used to classify files.
    dbgap_id is the prefix of each file (ie phs??????.v?.pht??????.v?).
    
    Returns:
    
    the DbgapFile var_report object that has the same dbgap_id as the dbgap_file_to_match.
    """
    dbgap_id_to_match = dbgap_file_to_match.match.groupdict()['dbgap_id']

    matches = []
    for f in dbgap_files:
        if f.file_type == 'var_report':
            if f.match.groupdict()['dbgap_id'] == dbgap_id_to_match:
                matches.append(f)

    # need to diff the files here to make sure they are the same
    if check_diffs:
        _check_diffs(matches)
        
    # return the first
    return matches[0]


def _get_data_dict_match(dbgap_files, dbgap_file_to_match, check_diffs=True):
    """For a given DbgapFile, find the matcing data_dict DbgapFile.
    
    Arguments:
    
    dbgap_files: list of DbgapFile objects returned from get_file_list
    dbgap_file_to_match: single DbgapFile object for which to find the matching var_report file
    
    Optional arguments:
    check_diffs: if True, check that all matching data_dict files are the same.
    
    Files are matched based on file_type (to identify data_dict) and the
    dgap_id capture group from the regular expressions used to classify files.
    dbgap_id is the prefix of each file (ie phs??????.v?.pht??????.v?).
    
    Returns:
    
    the DbgapFile var_report object that has the same dbgap_id as the dbgap_file_to_match.
    """
    dbgap_id_to_match = dbgap_file_to_match.match.groupdict()['dbgap_id']

    matches = []
    for f in dbgap_files:
        if f.file_type == 'data_dict':
            if f.match.groupdict()['dbgap_id'] == dbgap_id_to_match:
                matches.append(f)

    # need to diff the files here to make sure they are the same
    if check_diffs:
        _check_diffs(matches)
    
    # return the first
    return matches[0]


def _get_special_file_set(dbgap_files, pattern='Subject'):
    """Returns the file_set for "special" files: ie, the Subject, Sample, and Pedigree files
    
    Arguments:
    
    dbgap_files: list of DbgapFile objects returned from get_file_list
    
    Optional arguments:
    
    pattern: the pattern in the file name to identify which file to find (ie, 'Subject' to find the subject files)
    
    Returns:
    file_set: a dictionary with keys
                'data_files' (list DbgapFiles of length 1, since all special files are the same across consent groups)
                'var_report' (one corresponding var_report DbgapFile for this file)
                'data_dict' (one corresponding data_dict DbgapFile for this file)

    Since all var_report and data_dict files are the same for a given set of phenotype files
    across consent groups, this function only returns one data_dict and one var_report for
    each phenotype file set.
    """
    special_files = [f for f in dbgap_files if f.file_type == 'special' and pattern in f.basename]
    
    # make sure they are all the same
    
    # get the var_report and data_dictionary to go with the subject file
    var_report = _get_var_report_match(dbgap_files, special_files[0])
    data_dict = _get_data_dict_match(dbgap_files, special_files[0])
    
    # return the whole set
    file_set = {'data_files': [special_files[0]],
                'var_report': var_report,
                'data_dict': data_dict}
    return file_set


def _get_phenotype_file_sets(dbgap_files):
    """Returns the file_set for phenotype files: ie, .txt files that are not Subject, Sample, and Pedigree files
    
    Arguments:
    
    dbgap_files: list of DbgapFile objects returned from get_file_list
        
    Returns:
    file_set: a dictionary with keys
                'data_files' (list DbgapFiles of length n, where n is the number of consent groups)
                'var_report' (one corresponding var_report DbgapFile for this file)
                'data_dict' (one corresponding data_dict DbgapFile for this file)
                
    Since all var_report and data_dict files are the same for a given set of phenotype files
    across consent groups, this function only returns one data_dict and one var_report for
    each phenotype file set.
    
    """
    
    phenotype_files = [f for f in dbgap_files if f.file_type == 'phenotype']
    # get the set of unique dbgap_ids
    dbgap_ids = set([f.match.groupdict()['dbgap_id'] for f in phenotype_files])
    
    phenotype_file_sets = []
    for dbgap_id in dbgap_ids:
        
        matching_files = [f for f in phenotype_files if f.match.groupdict()['dbgap_id'] == dbgap_id]
        var_report = _get_var_report_match(dbgap_files, matching_files[0])
        data_dict = _get_data_dict_match(dbgap_files, matching_files[0])
        this_set = {'data_files': matching_files,
                    'var_report': var_report,
                    'data_dict': data_dict
                    }
        phenotype_file_sets.append(this_set)
    
    return phenotype_file_sets
    
    
def _make_symlink(dbgap_file):
    """Make (relative path) symlinks to a DbgapFile object's path in the current directory.
    
    Arguments:
    
    dbgap_file: a DbgapFile object whose path will be used to make a symlink
    """
    os.symlink(os.path.relpath(dbgap_file.full_path), dbgap_file.basename)


def _make_symlink_set(file_set):
    """Make symlinks for a set of DbgapFile objects, ie, all the data_files and their
    corresponding data_dict file and var_report file.
    
    Arguments:
    
    file_set: a dictionary with keys 'data_files', 'var_report', and 'data_dict'
              either the dictionary returned by _get_special_file_set or one
              element of the list returned by _getphenotype_file_sets or
              
    One symlink for each of the 'data_files' is made, plus one for the var_report and data_dict files
    """
    # link the actual data
    for f in file_set['data_files']:
        _make_symlink(f)
    # link the var_report
    _make_symlink(file_set['var_report'])
    # link the data dictionary
    _make_symlink(file_set['data_dict'])


def _make_symlinks(subject_file_set, pedigree_file_set, sample_file_set, phenotype_file_sets, nfiles=None):
    """Function to generate symlinks for a set of dbgap files.
    """
    if not os.path.exists("organized"):
        os.makedirs("organized")
    os.chdir("organized")

    # special files first
    if not os.path.exists("Subjects"):
        os.makedirs("Subjects")
    os.chdir("Subjects")

    _make_symlink_set(subject_file_set)
    _make_symlink_set(sample_file_set)
    _make_symlink_set(pedigree_file_set)
    
    os.chdir("..")

    # phenotype files
    if not os.path.exists("Phenotypes"):
        os.makedirs("Phenotypes")
    os.chdir("Phenotypes")
    
    # make phenotype file symlinks
    tmp = phenotype_file_sets[:nfiles]
    for phenotype_file_set in tmp:
        _make_symlink_set(phenotype_file_set)
        
    os.chdir("..")


if __name__ == '__main__':
    """Main function:
    - parse command line arguments
    - get DbgapFile list
    - find the file sets to symlink
    - create symlinks (if requested)
    """
    parser = ArgumentParser()
    
    parser.add_argument("directory")
    parser.add_argument("--link", "-l", default=False, action="store_true",
                        help="create symlinks for the dbgap files")
    parser.add_argument("--nfiles", "-n", dest="nfiles", type=int, default=None,
                        help="number of phenotype files to link (for testing purposes)")
    
    args = parser.parse_args()
        
    dbgap_files = get_file_list(args.directory)
    
    # find the special file sets
    subject_file_set = _get_special_file_set(dbgap_files, pattern="Subject")
    pedigree_file_set = _get_special_file_set(dbgap_files, pattern="Pedigree")
    sample_file_set = _get_special_file_set(dbgap_files, pattern="Sample")
        
    phenotype_file_sets = _get_phenotype_file_sets(dbgap_files)

    if args.link:
        _make_symlinks(subject_file_set, pedigree_file_set, sample_file_set, phenotype_file_sets, nfiles=args.nfiles)
    
