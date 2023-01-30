# iotop Parser
Parse the output from the excellent iotop (https://github.com/Tomas-M/iotop) tool and produce graphs showing the per-process I/O

## Usage
* Install iotop either from your distribution's package manager or from building from source
* Launch iotop with the below arguments

```
# iotop -o --batch -t -k -P -q > /tmp/ioresults.txt
```

This will record the I/O usage of active processes once a second and print the results to `/tmp/ioresults.txt` (obviously use whatever path you wish)

* Parse the results with the parser script from this repo

```
$ python ./iotop_parser.py /tmp/ioresults.txr
```

The script will produce graphs in the `./output` directory. Each process seen performing I/O during the iotop run will have its own graph

## Interpreting the Graphs
The resulting graphs will have two Y axis:

* The left axis shows how much data the process is reading/writing in KB/s
* The right axis shows the amount of time (%) the process is delayed waiting for IO to complete or waiting for page fault I/O (swapping data in)