#!/usr/bin/env python3.4

import os
import sys
import re # regular expressions

root_directory = "/projects/topmed/downloaded_data/dbGaP/test/phs000284/"
os.chdir(os.path.join(root_directory, "organized"))

# regular expression matchers for various kinds of dbgap files
dbgap_re_dict = {'data_dict': r'^phs(?P<phs>\d{6})\.v(?P<phs_v>\d+?)\.pht(?P<pht>\d{6})\.v(?P<pht_v>\d+?)\.(?P<base>.+?)\.data_dict(?P<extra>\w+?)\.xml$',
           'phenotype': r'^phs(\d{6})\.v(\d+?)\.pht(\d{6})\.v(\d+?)\.p(\d+?)\.c(\d+?)\.(.+?)\.(.+?)\.txt$',
           'var_report': r'^phs(\d{6})\.v(\d+?)\.pht(\d{6})\.v(\d+?)\.(.+?)\.var_report(\w+?)\.xml$',
           'special': r'^phs(\d{6})\.v(\d+?)\.pht(\d{6})\.v(\d+?)\.p(\d+?)\.(.+?)\.MULTI.txt$'
           }

def sort_file(basename, re_dict=dbgap_re_dict):
    for key, value in re_dict.items():
        match = re.match(value, basename)
        if match:
            return key
    
    return None
    
def main():
    
    patterns_to_link = (".xml", ".txt")
    
    for root, dirs, files in os.walk(root_directory):
        for name in files:
            # os.symlink!
            # os.relpath!
            file_type = sort_file(name)
            print(file_type, name)
if __name__ == '__main__':
    main()


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