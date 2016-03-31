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

def get_file_type(basename, re_dict=dbgap_re_dict):
    for key, value in re_dict.items():
        match = re.match(value, basename)
        if match is not None:
            file_type = key
            break

    return {'file_type': key,
            'match': match,
            'symlinked': False}
    
def get_file_type_dict(directory):
    
    file_dict = {}
    for root, dirs, files in os.walk(directory):
        for name in files:
            # os.symlink!
            # os.relpath!
            results = get_file_type(name)
            
            
            full_path = os.path.join(root, name)
            relative_path = os.path.relpath(full_path)
            file_dict[full_path] = results
            
    return file_dict


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


def make_symlinks(directory):
    file_dict = get_file_type_dict(directory)
    
    # loop over special files and link one of each, plus var_report and data_dictionary
    subject_files = [f for f in file_dict.keys() if file_dict[f]['file_type'] == 'special' and 'Subject' in f]
    pedigree_files = [f for f in file_dict.keys() if file_dict[f]['file_type'] == 'special' and 'Pedigree' in f]
    sample_files = [f for f in file_dict.keys() if file_dict[f]['file_type'] == 'special' and 'Sample' in f]
    
    print('subject:\t', subject_files[0])
    print('matching var report:\t', get_var_report_match(file_dict, subject_files[0]))
    print('matching data dict:\t', get_data_dict_match(file_dict, subject_files[0]))
    # loop over phenotype files and link all from each consent group, plus one var_report and one data_dictionary
    
if __name__ == '__main__':
    parser = ArgumentParser()
    
    parser.add_argument("directory")
    
    args = parser.parse_args()
    
    make_symlinks(args.directory)
    
    #file_types = get_file_type_dict(args.directory)
    #for key, value in file_types.items():
    #    if value['match'] is not None:
    #        print(value['file_type'], '\t', value['match'].groupdict(), "\t", key)
    #    else:
    #        print('None', '\t', os.path.basename(key))

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