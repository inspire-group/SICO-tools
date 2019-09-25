# RouteViews BGP updates processing

## Dependency

Python-wget, bgpdump (https://bitbucket.org/ripencc/bgpdump/wiki/Home)

## Download a given month of updates

```
python download.py [month] [wget_input_file] [thread_no] [logger_name]

@month: the month of updates e.g. "2018.07" "2019.01"  
@wget_input_file: the file that stores the list of to-be-downloaded updates. 
Download.py will automatically generate this file.   
@thread_no: the number of threads being used for downloading  
@logger_name: logger name
```
Example
```
python download.py "2019.07" wget_input.csv 20 logging.log
```

## Process download updates
Preprocess.py will extract as_path, community string, and large community string from an update and store the result in a CSV. Updates without any community info are threw away.

```
python preprocess.py [collector_name] [month] [thread_no] 
[out_dir] [logger_name]
```
@collector_name: the name of the collector  
@out_dir: the name of the directory where processed results are stored. 


