#!/usr/bin/env python3.4

import os
import sys
import re # regular expressions
from argparse import ArgumentParser
import subprocess # for system commands - in this case, only diff
from pprint import pprint

#root_directory = "/projects/topmed/dataprep/studyspecific/phase1/ramachandran_fhs/dbgap/"
#os.chdir(os.path.join(root_directory, "organized"))

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
    
    def __init__(self, file_path):
        
        self.full_path = file_path
        self.basename = os.path.basename(file_path)
        
        self.file_type = None
        self.match = None
        self.symlinked = None
    
    def __str__(self):
        return self.full_path
    
    
    def set_file_type(self, re_dict=dbgap_re_dict):
        for key, value in re_dict.items():
            match = re.match(value, self.basename)
            if match is not None:
                self.file_type = key
                self.match = match

    
def get_file_list(directory):
    
    file_list = []
    for root, dirs, files in os.walk(directory):
        for name in files:
            full_path = os.path.join(root, name)
            
            dbgap_file = DbgapFile(full_path)
            dbgap_file.set_file_type()
            
            file_list.append(dbgap_file)
    
    return file_list
    

def check_directory_structure():
    """This function will check structure of linked directories:
    ie all var_reports and data_dictionaries exist for a given phenotype file:"""
    pass


def _check_diffs(dbgap_file_subset):
    
    filename_a = dbgap_file_subset[0].full_path
    
    for i in range(1, len(dbgap_file_subset)):
        filename_b = dbgap_file_subset[i].full_path
        cmd = 'diff {file1} {file2}'.format(file1=filename_a, file2=filename_b)
        out = subprocess.check_output(cmd, shell=True)
        if len(out) > 0:
            raise ValueError('files are expect to be the same but are different: {file_a}, {file_b}'.format(file_a=filename_a, file_b=filename_b))


   
def _get_var_report_match(dbgap_files, dbgap_file_to_match, check_diffs=True):
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
    os.symlink(os.path.relpath(dbgap_file.full_path), dbgap_file.basename)

def _make_symlink_set(file_set):
    
    # link the actual data
    for f in file_set['data_files']:
        _make_symlink(f)
    # link the var_report
    _make_symlink(file_set['var_report'])
    # link the data dictionary
    _make_symlink(file_set['data_dict'])


def _make_symlinks(subject_file_set, pedigree_file_set, sample_file_set, phenotype_file_sets):
    
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
    
    os.chdir("..")

if __name__ == '__main__':
    parser = ArgumentParser()
    
    parser.add_argument("directory")
    
    args = parser.parse_args()
        
    dbgap_files = get_file_list(args.directory)
    
    # find the special file sets
    subject_file_set = _get_special_file_set(dbgap_files, pattern="Subject")
    pedigree_file_set = _get_special_file_set(dbgap_files, pattern="Pedigree")
    sample_file_set = _get_special_file_set(dbgap_files, pattern="Sample")
        
    phenotype_file_sets = _get_phenotype_file_sets(dbgap_files)

    _make_symlinks(subject_file_set, pedigree_file_set, sample_file_set, phenotype_file_sets)
    
    
    
"""    
Subjects
    Subject data dictionary
    Subject "phenotypes"
    subject var_report
Phenotypes
    for each "combined dataset", there will be:
        1 text file per consent group
        1 data dictionary - assume same or check
        1 var report?
"""