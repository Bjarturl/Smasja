# S.M.Á.S.J.Á (Sjá Myndræna Ástandssögu Skála og Jaðarkera í Álframleiðslu)
A GUI analysis tool made with PyQt5 for the ISAL aluminum plant in Straumsvík.
This was a summer job and at the end of summer the tool was introduced to staff along with 
instructions on how to set it up on their own machines.
The project was initially meant to be reducing a 250mb Excel model that took an hour to update manually with new data.
I figured the best thing to do was make a GUI that did all the background database work for you.
This code version is stripped of all sensitive data such as table/column names, details about the model purpose etc.
The data is various stats about pots and potrooms that's updated daily. The data ranges back many years but only the past 5 years were necessary for this model.
## Functionality
The tool functionalities include:
* Fetching data from an Oracle database and presenting them on graphs.
  * The available plots are scatter and line.
  * Plots can be combined on a single graph.
  * Plots can start from the right or left side.
  * Color can be customized.
* Filtering data by potroom, year or pot number.
* Analysis mode which is a shortcut to display the data that was the purpose of the original model.
* A sortable table of the data points presented.
* A few shortcuts that were requested by the model designer.
* Saving the graphs to local directory.
* Undo functionality.
* Updating the data automatically
* And more!
