# Introduction

With this app you are able to integrate data of a csv file into OpenMTC. The csv file must have a column with a timestamp and one column with some kind of device id. You are able to configure the duration of the data injection. The timing of your csv will be scaled to that duration.

# Getting started

To get an overview of the available parameters, just execute:

```
./apps/csv-injector --help
```

# Configuration

The most important paramters are:

* csv-path: Path to your csv file
* device-classifier: The id of the column with the device ids
* date-classifier: The id of the column with the timestamp
* time-format: Format of your timestamp (example:  %d/%m/%Y-%H:%M)
* duration: time to inject the data (seconds)
* repeat: repeat after full csv is injected (bool)

# Example

If you have a csv like this at "~/test.csv":

```csv
Date,ID,Temp,Hum,Battery
23/01/2018-00:50,environment_1,13.3,41,100
18/02/2018-14:01,environment_2,20.4,46,0,99
02/03/2018-23:11,environment_1,19.1,14,100
03/03/2018-00:01,environment_2,19,13,100
08/03/2018-03:01,environment_1,19.5,26,0,99
08/03/2018-10:11,environment_2,21.9,29,0,100
09/03/2018-16:21,environment_1,21.4,27,0,99
09/03/2018-16:51,environment_1,21.3,27,0,100
16/03/2018-06:36,environment_2,15.1,36,0,100
20/03/2018-09:27,environment_1,18.9,19,0,100
20/03/2018-10:27,environment_1,20.3,20,0,99
```

The app could be started like this:

```
./apps/csv-injector \
    --csv-path "~/test.csv" \
    --device-classifier "ID" \
    --date-classifier "Date" \
    --time-format "%d/%m/%Y-%H:%M" \
    --duration 300
    --repeat 0
```
