dot11s_simulation
=================

These files must be inside a folder named 'dot11s_simulation' inside the folder named 'ns-3.xx' of the ns3 simulator folder <br>
*This was tested with ns3 v3.17* <br>

The file 'special-wscript' must overwrite the wscript file of the folder 'ns-3.xx',<br>
```
cp special-wscript ../wscript
```
it will make the waf builder search these folders

###Folders

- results - this folder contains the results files of the simulations
- scripts - this folder contains the scripts that run the simulations and organize the results
- src - this folder contains the ns3 source code in C

###Python dependencies

*these are used to calculate statistics*
- numpy
- scikits.bootstrap
