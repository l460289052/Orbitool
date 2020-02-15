# Oribitool Readme

[TOC]

This tool can help you process with spectrum averaging, denoising, calibrating, peak fitting and generating time series.

There are 3 parts: Toolbar, Tabs, Formula/Masslist.

If you have no idea about this. Just open 'Oribitool.exe' and follow those steps

1. add a single file -> 
2. 'Average selected file' button ->
3. double click at a spectra list item->
4. 'Continue without denoising' button->
5. double click at spectra list->
6. 'Show selected's num-th highest peak' button->
7. add several ions->
8. 'Calc calibrate info' button->
9. 'Calibrate ALL SPECTRA use info and continue' button->
10. 'default' button->
11. have fun

## Toolbar

you can export workspace and option used in this tool.

### Workspace

Workspace includes

+ Option
+ Mass List
+ Files used
+ Spectra (excepted raw data)
+ Peak list
+ Time series

#### Input&Output

It could be exported as *.OribitWork file, when you import it, all the widgets related will be set.

### Option

Option includes

+ all states of the check box, spin box, text box and radio box.
+ formula settings, like elements' minimum and maximum and charge, ppm.
+ the ions used in calibration stage

#### Input&Output

It could be exported as *.OribitOption file.

## Formula/Mass list

### Formula

this part is for formula guessing when fitting peaks in 'Spectra&Peak fit' tab using 'default' button.

#### Settings

You can change the formula's settings used in formula guessing.

+ Charge
+ ppm
+ Number of elements
+ Nitrogen rule
+ OC ratio etc

#### Calculator

You can input formula or mass. If formula was inputted, mz will be showed. Others formula(s) will be showed.

Just a hint: the result text box is editable just for copying. Oribitool won't read anything from it.

### Mass list

this part is for fitting peaks in 'Spectra&Peak fit' tab using 'mass list' button, or for calculating time series in 'Time series' tab.

#### Add

you can add an item to mass list like those:

+ input formula or mass in text box and push 'Add' button in mass list box. If you input a formula, the mz field and formula field will be filled. If a mass was inputted, only the mz field will be filled.

+ In 'Spectra&Peak fit' tab, select some peaks and push 'Add selected peak(s) to mass list', or just push 'Add all peaks to mass list'.

  If a peak have only one formula, the mz added to mass list will be its theoretical value.

#### Remove peaks

#### Input&Output

##### OribitMassList file

*.OribitMassList

##### csv file

format:

| formula/mz      |
| --------------- |
| mz1 or formula1 |
| mz2 or formula2 |
| ...             |

example:

| formula/mz |
| ---------- |
| 199.09763  |
| C6H5O8N2-  |
| C4H8O12N3- |

## Tabs

### Files

------

#### Add file

'recurrence ' check box is used when open a folder. If it's checked, I will go through every files under selected folder.

#### Average

You can determine whether use number or time to average and the time range when averaging. Whenever a file as added, the time range will be recalculated.

You can simply show file without averaging or averaging all files.

Hint: push those buttons won't do any calculation.

### Spectra

------

#### tables

+ Spectra

  all spectra will be showed here. Spectrum will be showed right if double click at a spectrum.

+ Spectrum's property

  preserved

+ Spectrum

  mz-intensity

#### Background

use modified binPMF:

  1. make a set, called `noise set`, contains all peaks in [x.5~x.8]

  2. delete peaks bigger than $mean+3*std$ of the `noise set`

  3. use $quantile value+3*std$  of `noise set` as LOD line

     ps: I tested out that when quantile = 0.7, quantile value is close to mean

  4. delete peaks below LOD in original spectrum to get denoised spectrum

Denoised spectrum will be showed as green while original spectrum will be showed as blue. You can choose to remove peaks below LOD, or all peaks minus LOD, or don't do denoise.

![spectrum1](\img\spectrum1.png)

##### Export noise

as csv file with header = "mz intensity", contains all peaks in `noise set` after step 2.

#### Calculation

If push 'Denoising for every spectrum' or 'Continue without denoising', calculation will begin to do averaging and denoising.

#### Export spectrum

as csv file with header = "mz intensity"

#### Figure

If 'Scroll according to plot' check box is checked, the spectrum table will scroll to the left mz of the figure.

### Pre peak fitting

------

all spectra are showed in left table. Select how much peak used in peak fitting and show.

#### Remove unique peak

Push your left mouse button and scroll, a red line will appear like below figure. When you release button, all peak crossed will be removed. If you delete caches, may take seconds initializing.

![peakfit1](\img\peakfit1.png)

#### Cancel remove

canceled peak's color often is different with color before removing

### Calibration

-----

#### Tables

+ Ions

  There are ions used for mass calibration, added by typing ions to text box. Multi ions could be add by split by comma as "HNO3NO3-,C6H3O2NNO3-,C6H5O3NNO3-"

+ Information

  ions' formula and files' ppm will be showed

#### Calibrate step

1. Add ions
2. click 'Calc calibrate info' to get calibration information
3. click 'Calibrate ALL SPECTRA use info and continue'  to finish calibration and begin calculation

#### Show single file's information

by pushing "Show selected file's info", you will get a figure show a file's calibration curve.

![filecalibrationinfo](\img\filecalibrationinfo.png)

### Spectra&Peak fit

---

If you want to see a spectrum's peaks, select a spectrum and push 'default'. This tool will calculate formulas for each peaks and show them in peak list table.

This figure will automatically show 5 highest peaks' formula whose peak point is in window. If one of the 5 highest peak have no formula, formula will belong to the sixth one, etc.

![spectrum2](img\spectrum2.png)

If you want to refit a peak, could double click a peak in peak list. You can change 'peak num' and push 'Re-fit' button. If you click 'Save' button, the change will be added to peak list, and the peaks' formulas won't be changed unless you refit the spectrum again. You can change formula in 'Peak fit' box by double clicking that cell.

![peakfit2](img\peakfit2.png)

ps: you can change 2 things in this groupbox: peak num and formulas

### Time series

you can add time series by following methods:

+ mz with ppm
+ formula with ppm
+ mz range
+ selected peaks in 'Spectra&Peak fit' tab's peak list with ppm
+ (selected) peaks in mass list with ppm

Time series will be showed right. If you want to check a specific time series, double it in the table, or export all time series.

### Bugs

If you meet any bugs, please let me know. You can send me the 'error.txt' file which is under the same directory with 'Oribitool.exe'.

## log
**2020.02.15  version 1.0.1**

Bug fix

+ ppm when show single file's calibration information
+ wrong elements showed in formula. eg. Na when negative and S when positive
  rewrite formula interface logic
+ "'NoneType' object has no attribute 'addPeaks'" when add peak to mass list without initialize in 'Spectra&Peak fit'
  

Appended

+ It's possible to show multi files' spectra without averaging
+ Mass list: Export to or import from csv file

Change

+ show multi ions in a time when show time series

**2020.02.12 version 1.0.0**

  have functions:

+ Option( include formula) input/output
+ Mass list input/output
+ Formula guess and calculate
+ background
  + calculate
  + recalculate
  + quantile
+ peak fit
+ mass calibratiom
+ time series

