# larbatchdag

This contains scripts that can assist in launching jobs via dags. To get it in a LArSoft installation:

```
cd srcs
mrb g ssh://github.com/bcarls/larbatchdag/
mrb uc
```

Then you can build it as usual. 

## Creating a dag

The gen_dag.py script reads in xml files normally written for project.py and creates a dag for them that you can then launch. Once built, do this to launch:

```
gen_dag.py --xml xml_file.xml
```

This then creates the dag file. Glance over the dag file to make sure it's sensible. Once happy with it, launch the dag with this:

```
jobsub_submit_dag -G uboone file:// <full path to the dag>dag_from_xml.dag
```



