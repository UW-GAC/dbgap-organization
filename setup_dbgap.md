# General info
The dbGaP project directory for topmed is /projects/topmed/dbGaP-9334/.
All decryption needs to be done in this directory.
Afterward, the decrypted phenotype files will be moved out of this directory and into a different directory under /projects/topmed/downloaded_data/dbGaP/<phs>/<version>/raw.
Symlinks will be generated in /projects/topmed/downloaded_data/dbGaP/<phs>/<version>/organized for easier loading into the database.

The organize_dbgap.py script aims to do all of this with one line.

# One-time setup steps:

## Make yourself a working directory:
mkdir /projects/topmed/dbgap_workspaces/\<username\>

## Run vdb-config. You will feel like you've been transported back to 1990 and are using MS-DOS.

/projects/resources/software/apps/sratoolkit/vdb-config -i


1. import repository key (press 4). It is located here:
/projects/topmed/dbgap_workspaces/prj_9334.ngc
You will have to navigate with the anti-gui.
To select a directory, use the arrows and then enter to choose.
To get to the files tab, press tab.
Tab again to "ok" and hit enter to save.
It took me too long to figure this out.

2. say "yes" to "do you want to change the location?"
Navigate to choose:

/projects/topmed/dbgap_workspaces/\<username\>

3. Save your changes (press 6)

4. Exit (press 7)


# Steps for setting up a project for import

## download set up

cd /projects/topmed/dbgap_workspaces/\<username\>

mkdir downloads/phsXXXXXX.vXX

For example, framingham v27 is phs000007.v27 and Cleveland Family Study v1 is phs000284.v1 It is important that the phs and version numbers are correct, as that's how the python script knows where to put the final decrypted, uncompressed, symlinked data.

## download the data

Instructions to do this still need to be added.

## run the python script
organize_dbgap.py downloads/phsXXXXXX.vXX

This script can be run from any directory. It will:

* decrypt dbgap files

* create the final directory for the files, e.g. /projects/topmed/downloaded_data/dbGaP/phs000007/v27/

* copy dbgap files to, e.g. /projects/topmed/downloaded_data/dbGaP/phs000007/v27/raw

* uncompress raw files

* sort dbgap files into types: phenotype, data dictionary, var report, or special (subject/sample/pedigree)

* match up each phenotype or special file with its corresponding var_report and data_dict file

* organize raw files using symlinks in the "organized" subdirectory, e.g., /projects/topmed/downloaded_data/dbGaP/phs000007/v27/organized

* print out any files that were not sortable because they didn't match the expected filename conventions. These should be inspected to make sure nothing was missed.

