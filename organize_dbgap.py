#!/usr/bin/env python3.4

import os
import sys
import re # regular expressions
from argparse import ArgumentParser

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

def get_var_report_match(file_dict, key):
    dbgap_id_to_match = file_dict[key]['match'].groupdict()['dbgap_id']
    for k in file_dict.keys():
        if file_dict[k]['file_type'] == 'var_report':
            if file_dict[k]['match'] is not None:
                if file_dict[k]['match'].groupdict()['dbgap_id'] == dbgap_id_to_match:
                    return k


def get_data_dict_match(file_dict, key):
    dbgap_id_to_match = file_dict[key]['match'].groupdict()['dbgap_id']
    for k in file_dict.keys():
        if file_dict[k]['file_type'] == 'data_dict':
            if file_dict[k]['match'] is not None:
                if file_dict[k]['match'].groupdict()['dbgap_id'] == dbgap_id_to_match:
                    return k


def _check_file_set_is_unique(files):
    basename_set = set([f.basename for f in files])
    if len(basename_set) != 1:
        raise ValueError(r'files have different basenames: {files}'.format(files=', '.join(basename_set)))

def _get_subject_files(dbgap_files):
    subject_files = [f for f in dbgap_files if f.file_type == 'special' and 'Subject' in f.basename]
    
    # make sure they are unique
    _check_file_set_is_unique(subject_files)
    
    # keep only the first
    return subject_files

def make_symlinks(dbgap_files):
    
    # find the subject_files
    subject_file_set = _get_subject_files(dbgap_files)
    
    
    print("\nSubject:")
    print([f.basename for f in subject_file_set])
    
    
if __name__ == '__main__':
    parser = ArgumentParser()
    
    parser.add_argument("directory")
    
    args = parser.parse_args()
    
    dbgap_files = get_file_list(args.directory)
    
    make_symlinks(dbgap_files)
    
    
    
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