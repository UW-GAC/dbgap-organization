#!/usr/bin/env python3.4

import os
import sys
import shutil # file system utilities
import re # regular expressions
from argparse import ArgumentParser
import subprocess # for system commands - in this case, only diff
from pprint import pprint
import errno

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
    def __init__(self, file_path, check_exists=True):
        """Constructor function for DbgapFile instances.
        
        Arguments:
        
        file_path: full path to a file downloaded from dbgap
        """
        self.full_path = os.path.abspath(file_path)
        
        if check_exists and not os.path.exists(self.full_path):
            raise FileNotFoundError(self.full_path + " does not exist")

        self.basename = os.path.basename(file_path)
        
        # these will be set in the set_file_type class method
        self.file_type = None # will store the file type
        self.match = None # will store the regular expression re.match object

        # auto-set the file type
        self._set_file_type() # possibilities are 'phenotype', 'var_report', 'data_dict'
        
    def __str__(self):
        """string method for DbgapFile objects"""
        return self.full_path
    
    
    def _set_file_type(self, re_dict=dbgap_re_dict):
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
            
            file_list.append(dbgap_file)
    
    return file_list
    

def _check_diffs(dbgap_file_subset):
    """Run a unix diff on a set of files to make sure that they are all the same.
    
    If they are not the same, a ValueError is raised."""
    filename_a = dbgap_file_subset[0].full_path
    
    for i in range(1, len(dbgap_file_subset)):
        filename_b = dbgap_file_subset[i].full_path
        cmd = 'diff {file1} {file2}'.format(file1=filename_a, file2=filename_b)
        try:
            out = subprocess.check_output(cmd, shell=True)
        except subprocess.CalledProcessError:
            raise ValueError('files are expect to be the same but are different: {file_a}, {file_b}'.format(file_a=filename_a, file_b=filename_b))


def _get_file_match(dbgap_files, dbgap_file_to_match, match_type, check_diffs=True):
    """For a given DbgapFile, find the matcing var_report DbgapFile.
    
    Arguments:
    
    dbgap_files: list of DbgapFile objects returned from get_file_list
    dbgap_file_to_match: single DbgapFile object for which to find the matching file
    match_type: type of file to match (typically data_dict or var_report)
    
    Optional arguments:
    check_diffs: if True, check that all matching var_report files are the same.
    
    Files are matched based on file_type (to match match_type) and the
    dgap_id capture group from the regular expressions used to classify files.
    dbgap_id is the prefix of each file (ie phs??????.v?.pht??????.v?).
    
    Returns:
    
    the DbgapFile object that has the same dbgap_id as the dbgap_file_to_match and correct file_type.
    """
    dbgap_id_to_match = dbgap_file_to_match.match.groupdict()['dbgap_id']

    matches = []
    for f in dbgap_files:
        if f.file_type == match_type:
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
    var_report = _get_file_match(dbgap_files, special_files[0], 'var_report')
    data_dict = _get_file_match(dbgap_files, special_files[0], 'data_dict')
    
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
        var_report = _get_file_match(dbgap_files, matching_files[0], 'var_report')
        data_dict = _get_file_match(dbgap_files, matching_files[0], 'data_dict')
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
    path = os.path.relpath(dbgap_file.full_path)
    if not os.path.exists(path):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), path)
    os.symlink(path, dbgap_file.basename)


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
        os.makedirs("Subject")
    os.chdir("Subject")

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
        
    os.chdir("../..")


def decrypt(directory, decrypt_path='/projects/resources/software/apps/sratoolkit/vdb-decrypt'):
    """Decrypt dbgap files
    
    Arguments:
    
    directory: directory to decrypt
    
    Keyword arguments:
    
    decrypt_path: path to sratoolkit's vdb-decrypt binary
    """
    # get original directory
    original_directory = os.getcwd()
    # need to be in the dbgap workspace directory to actually do the decryption
    os.chdir(directory)
    # system call to the decrypt binary
    subprocess.check_call('{vdb} .'.format(vdb=decrypt_path), shell=True)
    os.chdir(original_directory)


def organize(directory, link=False, nfiles=None):
    """Organize dbgap files by type and make symlinks
    
    Positional arguments
    directory: directory to organize; should be the dbgap_raw directory
    
    Keyword arguments
    link: boolean indicator whether to make symlinks or not
    nfiles: integer argument to limit number of symlinks created (for testing purposes)
    """
    os.chdir(directory)
    
    dbgap_files = get_file_list("raw")
    
    # find the special file sets
    subject_file_set = _get_special_file_set(dbgap_files, pattern="Subject")
    pedigree_file_set = _get_special_file_set(dbgap_files, pattern="Pedigree")
    sample_file_set = _get_special_file_set(dbgap_files, pattern="Sample")
    
    # find the phenotype file sets
    phenotype_file_sets = _get_phenotype_file_sets(dbgap_files)
    
    # if requested, generate the symlinks in the 'organized' subdirectory
    if link:
        _make_symlinks(subject_file_set, pedigree_file_set, sample_file_set, phenotype_file_sets, nfiles=nfiles)
    
    # report files without matches
    unsorted_files = [f for f in dbgap_files if f.file_type is None]
    
    if len(unsorted_files) > 0:
        print("unsorted files:")
        for f in unsorted_files:
            print(f.basename)

def parse_input_directory(directory):
    """Parse dbgap study accession and version out of input directory string
    
    Positional arguments
    directory: directory to operate on. Can be a full path or a relative path.
               The last subdirectory of the path is inspected for the dbgap study
               accession and version - should look like e.g., phs000007.v1
    
    Return
    dictionary with keys 'phs' (maps to e.g., 'phs000007') and 'v' (maps to e.g., 'v27')
    """
    if directory.endswith("/"):
        directory = directory[:-1]
    basename = os.path.basename(directory)
    print(basename)
    regex = re.compile(r'(?P<phs>phs\d{6})\.(?P<v>v\d+)$')
    match = regex.match(basename)
    if match is not None:
        return(match.groupdict())
    else:
        raise ValueError('{basename} does not match expected string phs??????.v*'.format(basename=basename))


def create_final_directory(phs, version, default_path="/projects/topmed/downloaded_data/dbGaP/test/"):
    """Creates final output directory for files
    
    Positional arguments:
    phs: phs string like phs000007
    version: version string like v27
    
    Keyword arguments
    default_path: base path indicating where to create the output directory, ie it will be:
                  basepath/phs/version
    
    Returns:
    full path to directory that was just created
    """
    # check that it does not already exist
    phs_directory = os.path.join(default_path, phs)
    if not os.path.exists(phs_directory):
        os.mkdir(phs_directory)
    version_directory = os.path.join(phs_directory, version)
    if os.path.exists(version_directory):
        msg = '{d} already exists!'.format(d=version_directory)
        raise FileExistsError(msg)
    else:
        os.mkdir(version_directory)
        
    return version_directory
    

def copy_files(from_path, to_path):
    
    print("from: ", from_path)
    print("to:   ", to_path)
    shutil.copytree(from_path, to_path)

def uncompress(directory):
    """Uncompress a directory by walking the directory tree. Currently not guaranteed
    to be recursive, i.e. does not uncompress a file that was previously in a tar archive.
    """
    rerun = False
    # may need to be called recursively
    # walk through the directory and find anything that needs to be uncompressed
    for root, dirs, files in os.walk(directory):
        for name in files:
            # tar file
            if name.endswith(".tar.gz"):
                abspath = os.path.join(root, name)
                cmd = 'tar -xvzf {file} -C {directory}'.format(file=abspath, directory=root)
                subprocess.check_call(cmd, shell=True)
                # we don't want to save the tar archive
                os.remove(abspath)
                rerun = True
            if name.endswith(".txt.gz"):
                abspath = os.path.join(root, name)
                cmd = 'gunzip {file}'.format(file=abspath)
                subprocess.check_call(cmd, shell=True)
    
    if rerun:
        # recursion!
        uncompress(directory)

if __name__ == '__main__':
    """Main function:
    * decrypt dbgap files in download directory
    * copy files to their final location
    * uncompress files (probably needs to be a recursive function)
    * parse command line arguments
    * get DbgapFile list
    * find the file sets to symlink
    * create symlinks
    
    Tasks bulleted with * are already being done; those bulleted with - still need to be written.
    """
    parser = ArgumentParser()
    
    parser.add_argument("directory")
    
    args = parser.parse_args()
    
    directory = os.path.abspath(args.directory)
    
    phs_dict = parse_input_directory(directory)
    
    output_directory = create_final_directory(phs_dict['phs'], phs_dict['v'])
    
    # do the decryption
    decrypt(directory)
    
    # copy files to the final "raw" directory
    copy_files(directory, os.path.join(output_directory, "raw"))
    
    #output_directory = "/projects/topmed/downloaded_data/dbGaP/test/phs000007/v27"
    uncompress(output_directory)
    
    # organize files into symlinks
    organize(output_directory, link=True)
