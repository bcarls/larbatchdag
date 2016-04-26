#! /usr/bin/env python

import sys, os, urllib, shutil
import project_utilities
from xml.dom.minidom import parse
from project_modules.projectdef import ProjectDef


# Main program.

def main(argv):

    # Parse arguments.
    xmlfile = ''

    args = argv[1:]
    while len(args) > 0:
        if args[0] == '--xml' and len(args) > 1:
            xmlfile = args[1]
            del args[0:2]

    # Make sure xmlfile was specified.

    if xmlfile == '':
        print 'No xml file specified.  Type "project.py -h" for help.'
        return 1


    # Extract all project definitions.

    projects = get_projects(xmlfile)

    # Print out the dag
    # Start by finding the project name. Each project gets its own dag file.
    for project in projects:
        project_name = project.name
        dag_file = open(project_name+".dag", "w")

        previous_outdir = ""

        for stage in project.stages:
            
            # Create directories for output, logs, and work.
            if not os.path.exists(stage.outdir):
                os.makedirs(stage.outdir)
            if not os.path.exists(stage.logdir):
                os.makedirs(stage.logdir)
            if not os.path.exists(stage.workdir):
                os.makedirs(stage.workdir)

            # Get the setup_experiment.sh script
            setupscript = os.path.join(stage.workdir,'setup_experiment.sh')
            safecopy(project_utilities.get_setup_script_path(), setupscript)


            # Begin by starting the SAM project.
            dag_file.write("<serial>\n")
            dag_file.write("jobsub -n -M --group=uboone -N 1 --expected-lifetime=600s --memory=500MB")
            dag_file.write(" -f " + setupscript)
            dag_file.write(" file://"+ os.environ['PWD']+"/srcs/larbatchdag/scripts/start-project.sh")
            dag_file.write(" --sam_project " + project_name + "_" + stage.name)
            dag_file.write(" --sam_defname " + project_name + "_" + stage.name)
            dag_file.write(" --sam_group uboone")
            dag_file.write(" --sam_station uboone")
            dag_file.write("\n")
            dag_file.write("</serial>")


            # Quickly write out the wrapper fcl thingamabob

            wrapper_fcl_name = os.path.join(stage.workdir, 'wrapper.fcl')
            wrapper_fcl = safeopen(wrapper_fcl_name)
            wrapper_fcl.write('#include "%s"\n' % os.path.basename(stage.fclname))
            wrapper_fcl.write('\n')

            # Generate overrides for sam metadata fcl parameters.
            # Only do this if our xml file appears to contain sam metadata.
            xml_has_metadata = project.file_type != '' or \
                               project.run_type != ''
            
            if xml_has_metadata:
                # Add overrides for FileCatalogMetadata.
                if project.release_tag != '':
                    wrapper_fcl.write('services.FileCatalogMetadata.applicationVersion: "%s"\n' % \
                                          project.release_tag)
                else:
                    wrapper_fcl.write('services.FileCatalogMetadata.applicationVersion: "test"\n')
                if project.file_type:
                    wrapper_fcl.write('services.FileCatalogMetadata.fileType: "%s"\n' % \
                                      project.file_type)
                if project.run_type:
                    wrapper_fcl.write('services.FileCatalogMetadata.runType: "%s"\n' % \
                                      project.run_type)
                # Add experiment-specific sam metadata.
                sam_metadata = project_utilities.get_sam_metadata(project, stage)
                if sam_metadata:
                    wrapper_fcl.write(sam_metadata)

            wrapper_fcl.close()

            # Continue with the stage
            dag_file.write("\n")
            dag_file.write("<serial>\n")
            dag_file.write("jobsub -n -M --group=uboone") 
            if stage.name == "g4": 
                dag_file.write(" -f " + previous_outdir + "/\${JOBSUBPARENTJOBID}/\${JOBSUBPARENTJOBID}_\${PROCESS}/file_location_gen.txt")
            if stage.name == "detsim": 
                dag_file.write(" -f " + previous_outdir + "/\${JOBSUBPARENTJOBID}/\${JOBSUBPARENTJOBID}_\${PROCESS}/file_location_g4.txt")
            dag_file.write(" -f " + stage.fclname)
            dag_file.write(" -f " + wrapper_fcl_name )
            dag_file.write(" -f " + setupscript)
            dag_file.write(" --resource-provides=usage_model=" + stage.resource)
            dag_file.write(" " + stage.jobsub)
            dag_file.write(" --OS=" + project.os)
            dag_file.write(" -N " + str(stage.num_jobs))
            dag_file.write(" file://" + os.environ['PWD'] + "/srcs/larbatchdag/" + stage.name + "/"+stage.name +"_punch_it.sh")
            dag_file.write(" --nfile " + str(stage.max_files_per_job))
            dag_file.write(" --group uboone -g -c wrapper.fcl --ups uboonecode")
            dag_file.write(" -r " + project.release_tag + " -b " + project.release_qual)
            dag_file.write(" --workdir " + stage.workdir)
            dag_file.write(" --outdir " + stage.outdir)
            dag_file.write(" --logdir " + stage.logdir)
            dag_file.write(" -n " + str(project.num_events))
            dag_file.write(" --njobs " + str(stage.num_jobs))
            dag_file.write(" --output " + project_name + "_\${PROCESS}_%tc_" + stage.name + ".root")
            if stage.name == "g4": 
                dag_file.write(" --source-list \${CONDOR_DIR_INPUT}/file_location_gen.txt")
            if stage.name == "detsim": 
                dag_file.write(" --source-list \${CONDOR_DIR_INPUT}/file_location_g4.txt")
            dag_file.write("\n")
            dag_file.write("</serial>\n")


            # End by stopping the SAM project

            dag_file.write("<serial>\n")
            dag_file.write("jobsub -n -M --group=uboone -N 1 --expected-lifetime=600s --memory=500MB")
            dag_file.write(" -f " + setupscript)
            dag_file.write(" file://"+ os.environ['PWD']+"/srcs/larbatchdag/scripts/stop-project.sh")
            dag_file.write(" --sam_project " + project_name + "_" + stage.name)
            dag_file.write(" --sam_station uboone")
            dag_file.write("\n")
            dag_file.write("</serial>\n")
            
            previous_outdir = stage.outdir

        dag_file.close()



# Recursively extract projects from an xml element.

def find_projects(element, default_first_input_list = ''):

    projects = []
    default_input = default_first_input_list

    # First check if the input element is a project.  In that case, return a 
    # list containing the project name as the single element of the list.

    if element.nodeName == 'project':
        project = ProjectDef(element, default_input)
        projects.append(project)
    else:
        # Input element is not a project.
        # Loop over subelements.
        subelements = element.getElementsByTagName('*')
        for subelement in subelements:
            subprojects = find_projects(subelement, default_input)
            projects.extend(subprojects)
            if len(projects) > 0:
                if len(projects[-1].stages) > 0:
                    default_input = os.path.join(projects[-1].stages[-1].logdir, 'files.list')
    
    # Done.

    return projects





# Extract all projects from the specified xml file.

def get_projects(xmlfile):

    # Parse xml (returns xml document).

    if xmlfile == '-':
        xml = sys.stdin
    else:
        xml = urllib.urlopen(xmlfile)
    doc = parse(xml)

    # Extract root element.

    root = doc.documentElement

    # Find project names in the root element.
    
    projects = find_projects(root)

    # Done.

    return projects




# Function for opening files for writing using either python's built-in
# file object or SafeFile for dCache/pnfs files, as appropriate.

def safeopen(destination):
    #if destination[0:6] == '/pnfs/':
    #    file = SafeFile(destination)
    #else:
    if project_utilities.safeexist(destination):
        os.remove(destination)
    file = open(destination, 'w')
    return file



# Function for copying files.  Can be safely used for copying files to dCache.

def safecopy(source, destination):
    if project_utilities.safeexist(destination):
        os.remove(destination)
    shutil.copy(source, destination)







# Invoke main program.

if __name__ == '__main__':
    sys.exit(main(sys.argv))
    '''inputlist = []
    inp = open(stage.inputlist,"r")
    for line in inp:
    columns = line.split("/")
    columns = [col.strip() for col in columns]
    inputlist.append(columns[8])
    inp.close()'''

