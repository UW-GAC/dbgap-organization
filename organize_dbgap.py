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

def get_file_type(basename, re_dict=dbgap_re_dict):
    for key, value in re_dict.items():
        match = re.match(value, basename)
        if match:
            return key
    
    return None
    
def get_file_type_dict(directory):
    
    file_dict = {}
    for root, dirs, files in os.walk(directory):
        for name in files:
            # os.symlink!
            # os.relpath!
            file_type = get_file_type(name)
            
            full_path = os.path.join(root, name)
            relative_path = os.path.relpath(full_path)
            file_dict[relative_path] = file_type
            
    return file_dict

def check_directory_structure():
    """This function will check structure of linked directories:
    ie all var_reports and data_dictionaries exist for a given phenotype file:"""
    pass


if __name__ == '__main__':
    parser = ArgumentParser()
    
    parser.add_argument("directory")
    
    args = parser.parse_args()
    
    file_types = get_file_type_dict(args.directory)
    for key, value in file_types.items():
        print(value, "\t", key)


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