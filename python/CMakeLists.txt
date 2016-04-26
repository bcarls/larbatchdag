# All of the .py files in this directory are python modules.
# We distinguish executable and non-executable .py files.
# The former are installed with execute permission.
# The latter are installed without execute permission.

# Executable python files (will also be on PYTYHONPATH).

LIST(APPEND exes gen_dag.py)

# Python modules on PYTHONPATH.

# LIST(APPEND modules project_utilities.py )

# Hidden python modules in subdirectory project_modules on PYTHONPATH.

#LIST(APPEND hidden __init__.py xmlerror.py jobsuberror.py ifdherror.py pubsinputerror.py pubsdeadenderror.py projectdef.py stagedef.py projectstatus.py stagestatus.py batchstatus.py )

# GUI modules.  These are in subdirectory projectgui on PYTHONPATH.

# LIST(APPEND guis __init__.py projectapp.py projectview.py statusview.py textwindow.py )

message(STATUS "Executable python modules ${exes}")
message(STATUS "Python modules ${modules}")
message(STATUS "Hidden python modules ${hidden}")
message(STATUS "GUI python modules ${guis}")

install(PROGRAMS ${exes} DESTINATION ${product}/${version}/python)
# install(FILES ${modules} DESTINATION ${product}/${version}/python)
# install(FILES ${hidden} DESTINATION ${product}/${version}/python/project_modules)
# install(FILES ${guis} DESTINATION ${product}/${version}/python/project_gui_modules)
install_scripts(LIST ${exes})
