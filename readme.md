
[TOC]

# Requirements

## Executable file

.Net Framework >= 4.5

## Run by python

+ install python 3.8.10
+ please view requirements.txt
+ copy those dlls to Orbitool/utils/readers
  + ThermoFisher.CommonCore.BackgroundSubtraction.dll
  + ThermoFisher.CommonCore.Data.dll
  + ThermoFisher.CommonCore.MassPrecisionEstimator.dll
  + ThermoFisher.CommonCore.RawFileReader.dll
+ python Main.py

# Try

## Download

[download link](https://orbitrap.catalyse.cnrs.fr/download-link/)

## Procedure

Open "Orbitool.exe"

This tool can help you process with spectrum averaging, denoising, calibrating, peak fitting and generating time series.

There are 3 parts: Toolbar, Tabs, Dockers.

If you have no idea about this. Just open 'Orbitool.exe' and follow those steps

1. add a single file
2. 'All file' button (Alt + A)
3. show selected raw spectrum in spectra list (Alt + A)
4. Calc noise level for selected spectrum (Alt + C)
5. denoise (Enter)
6. Finish and continue (Enter)
7. Calc calibrate info (Alt + C)
8. Calibrate and continue (Enter)
9. show selected spectrum

# Tips

+ Please save workspace to disk when processing large file for saving memory. (Click Workspace->Save as)

# UI

Underlined character is a shortcut with Alt. Like 'Alt + A', 'Alt + B', etc.

Arrow keys is useful in peak fit tab. Up and down keys could change y axis, and left and right keys could change x axis.


## I. Tabs

### 1.Files

+ Import

  Import RAW file directly or from a folder.

+ Average

  + Use time period
  + Use num period
  + Determine time range for period

> push those buttons won't do any calculation.
>
> Shortcuts: Del for remove selected files

### 2.Noise

+ Calculate

  You can add some independent point for fit separately.

+ Denoise

> The 'denoise' button will read all files and save denoise information. (The real denoise will be done after calibration because of files' difference)
>
> Shortcuts: double click 'type' column will scale to that noise.

### 3.Peak Shape

Orbitool will use some peaks to calculate the width of peak. (if use norm distribution)

> Shortcuts: use mouse plot a red line to remove peaks

### 4.Calibration

Orbitool will use provided ions calibrate files. Different files will use different infos because of different files really need to calibrate separately.

### 5.Peak Fit

+ Filter

  Orbitool will show fitted peaks in peak list docker. You can filter use peaks filter, and filters will overlay.

+ Actions

  Actions will done for all shown peaks in peak list docker.
  
+ Plot

  Position of plot will bind with the peak list. (Can unbind with checking box)

> Shortcuts: Arrow keys for plot.

### 6.Mass Defect

...

### 7.Timeseries

+ Add a timeseries by

  + mz &  tolerance(ppm)

  + a formula

  + mz range

    will use max intensity in mz range as a timeseries

+ Add many timeseries by

  + peak list
  + mass list selected peaks
  + mass list all peaks

Export Time series

| isotime | igor time | matlab time | excel time | C3H3O3- | C2HO4- | ... |
| ------- | --------- | ----------- | ---------- | ------- | ------ | --- |
| time1   | ...       | ...         | ...        | ...     | ...    | ... |
| time2   | ...       | ...         | ...        | ...     | ...    | ... |
| ...     | ...       | ...         | ...        | ...     | ...    | ... |

### 8.Concatenate time series

You can add time series by importing csv files.

To recognize csv file's format, your csv file should be like:

| time  | formula1 | formula2 | ... |
| ----- | -------- | -------- | --- |
| time1 | ...      | ...      | ... |
| time2 | ...      | ...      | ... |
| ...   | ...      | ...      | ... |

You can change some key row/column's position to fit your csv file

+ Ion row ( formula row )
+ time column
+ ion ( formula) beginning column

<img src="img\timeSeriesCatCsv.svg" alt="timeSeriesCatCsv" style="zoom:150%;" />

## II. Dockers

Docker could be dragged out or be stacked.

<img src="img\dockers-draged-out.png" alt="dockers-draged-out" style="zoom: 50%;" /> <img src="img\dockers-stack.png" alt="dockers-stack" style="zoom: 50%;" /> 

### 1.Formula

There are two formula calculator. One use DBE and the other not.

### 2.Mass List

Orbitool use mass list to fit peak or calculate timeseries.

+ Chemical group

  You can plus or minus a chemical group to a whole list

Import/Export

| mz  | formulas |
| --- | -------- |
| mz1 | formula1 |
| mz2 | formula2 |
| ... | ...      |

> If a mass list item has a formula, its mz doesn't matter.

### 3.Spectra List

### 4.Spectrum

### 5.Peak List

Double click at peaks could refit this peak. Input a mass could jump to the nearest peak.

## III. Toolbar

you can export workspace and config used in this tool.

### Workspace

Almost all data. File format is HDF5 file. When processing large files, please save it to disk first or will consume 

#### Input&Output

It could be exported as *.Orbitool file, when you import it, all the widgets related will be set.

### Option

Option includes

+ all states of the check box, spin box, text box and radio box.
+ formula settings, like elements' minimum and maximum and charge, ppm.
+ the ions used in calibration stage
+ mass list

#### Input&Output

It could be exported as *.Orbitool Workspace file. Means you can only import config from another workspace file.

# Details

## 1.Noise

### Global noise

use modified binPMF:

  1. make a set, called `noise set`, contains all peaks in [x.5~x.8]

  2. delete peaks bigger than $mean+N\_sigma*std$ of the `noise set`

  3. use $quantile value+N\_sigma*std$  of `noise set` as LOD line

     ps: I tested out that when quantile = 0.7, quantile value is close to mean

  4. delete peaks below LOD in original spectrum to get denoised spectrum

### Noise points

There are some points with larger noise, like NO3- and HN2O6-, etc. They should be calculated independently.

## 2.Peak Shape

...

## 3.Calibration

When averaging spectra between files, make sure calibration first.

Before calibration:



After calibration:



## 4.Spectra&Peak fit

### Tag

+ A peak could be assigned with a Tag
+ Available tags are
  + Noise: this peak is a noise peak
  + Done: this peak is handled
  + Fail: this peak is failed to fit, Orbitool will automatically add this tag to peak when fail to fit peak.


## 5.Mass defect

you can choose what rainbow stand for, DBE or certain element's num. And you can choose whether use size( aka area) stand for log intensity or intensity.

![mass defect](img/massdefect.png)

## 6.Time series

...



## 7.Formula

this part is for formula guessing when fitting peaks in 'Spectra&Peak fit' tab using 'default' button.

### Formula Format

#### Input

some examples to indicate what format of formula could be understand by Orbitool

+ H2O
+ HH\[2\]O
+ NO3-
+ NH4+
+ SO4-2 or SO4e-2
+ Ca+2
+ C6(H2O)6
+ na2 s2 o 3

#### Output

some examples to help you understand the format of formula of Orbitool

+ H2O
+ HH\[2\]O
+ NO3-
+ NH4+
+ SO4-2 (Won't use SO4e-2 because of Ne-3)


### Settings

You can change the formula's settings used in formula guessing.

+ base group
+ mz range
+ DBE
+ ppm
+ whether use Nitrogen rule
+ elements and isotopes to be used
+ elements' parameters

### Calculator

You can input **formula** or **mass**. 

+ If formula was inputted, the result will be its mass (with electron). 
+ if mass was inputted, the Calculator will calculate and show formula(s).

Just a hint: the result text box is editable just for copying. Orbitool won't read anything from it.

### Calculation method

each element (take electron as a special element) has 7 parameters can be changed (some elements' some parameters won't be changed):

+ MIN: minimum of the element's number
+ MAX: maximum of the element's number
+ 2*DBE: 2 times element's effect to DBE
+ H min, H max: ability to replace H
+ O min, O max: ability to replace O

 I will show you with this tool's built-in elements' parameters:

|     | min | max | 2*DBE | H min | H max | O min | O max |
| --- | --- | --- | ----- | ----- | ----- | ----- | ----- |
| e   | -1  | 1   | -1    | -0.5  | -0.5  | 0     | 0     |
| C   | 0   | 20  | 2     | -     | 2     | 0     | 3     |
| H   | 0   | 40  | -1    | -1    | -1    | 0     | 0     |
| O   | 0   | 15  | 0     | 0     | 0     | -1    | -1    |
| N   | 0   | 4   | 1     | -1    | 1     | 0     | 3     |
| S   | 0   | 3   | 0     | 0     | 0     | 0     | 4     |
| Li  | 0   | 3   | -1    | 0     | 0     | 0     | 0     |
| Na  | 0   | 3   | -1    | 0     | 0     | 0     | 0     |
| K   | 0   | 3   | -1    | 0     | 0     | 0     | 0     |
| F   | 0   | 15  | -1    | -1    | 0     | 0     | 0     |
| Cl  | 0   | 3   | -1    | -1    | 0     | 0     | 3     |
| Br  | 0   | 3   | -1    | -1    | 0     | 0     | 3     |
| I   | 0   | 3   | -1    | -1    | 0     | 0     | 3     |
| P   | 0   | 4   | 1     | -1    | 1     | 0     | 6     |
| Si  | 0   | 5   | 2     | 0     | 2     | 0     | 3     |

for element C, H min change with number

| C num | 0   | 1   | 2   | 3   | 4   | 5   | 6   | 7   | 8   | 9   | 10  | 11  | 12  |
| ----- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H min | 0   | 4   | 4   | 6   | 6   | 6   | 6   | 8   | 8   | 8   | 8   | 10  | ... |

some parameters have some initial value:

| 2*DBE | H min | H max | O min | O max |
| ----- | ----- | ----- | ----- | ----- |
| 2     | -0.5  | 2.5   | 0     | 0     |

#### example

If I have a part of formula 'C10N-', for this part: 

+ minimum of O will be $max(0_{O:min},0_{initial:Omin}+1*0_{e:Omin}+10*0_{C:Omin}+1*0_{N:Omin})=0$
+ maximum of O will be $min(15_{O:max},0_{initial:Omax}+1*0_{e:Omin}+10*3_{C:Omax}+1*3_{N:Omax})=15$

Then program will iterate O number from 0 to 15.

If O number is 11 at some time while iterating, the part becomes 'C10O11N-':

+ minimum of H will be $max(0_{H:min},-0.5_{initial:Hmin}+1*(-0.5)_{e:Hmin}+8_{\text{Hmin for C=10}}+1*(-1)_{N:Hmin})=6$
+ maximum of H will be $min(40_{H:min},2.5_{initial:Hmax}+1*(-0.5)_{e:Hmax}+10*2_{C:Hmax}+1*1_{N:Hmax})=23$

So the program will iterate H number from 6 to 23 for a specific mass guessing.

I will add some mass constrains within iteration.

for a ion 'C10H15O11N-', $DBE=\frac{2_{initial:2DBE}+1*(-1)_{e:2DBE}+10*2_{C:2DBE}+1*1_{N:2DBE}+15*(-1)_{H:2DBE}}{2}=3.5$

### Unstricted Calculator

This calculator will ignore DBE, search all formulas which is correspond with ppm restriction and elements/isotopes number constrain.

It can find formulas like 'C5HO5-' or 'C[13]3H3O[18]-'. So the result maybe very long.



# Maintain

## Maintainer
+ School of Electronic, Information and Electrical Engineering, Shanghai Jiao Tong University, Shanghai, 200240, China

## Contributors

+ State Environmental Protection Key Laboratory of Formation and Prevention of Urban Air Pollution Complex, Shanghai Academy of Environmental Sciences, Shanghai, 200233, China
+ Univ. Lyon, Université Claude Bernard Lyon 1, CNRS, IRCELYON, F-69626, Villeurbanne, France.
+ Institute for Atmospheric and Earth System Research / Physics, Faculty of Science, University of Helsinki, Helsinki, 00140, Finland.

## Bugs report & function require

If you meet any bugs, please let me know. You can send me the 'log.txt' file which is under the same directory with 'Orbitool.exe'.

mail to: "Matthieu Riva"\<<matthieu.riva@ircelyon.univ-lyon1.fr>\>;  "Cheng Huang"\<<huangc@saes.sh.cn>\>

## log

**2022.07.23 version 2.2.2**

+ reduce size to ~100MB
+ you can set DBE to a minus value ( only valid for unrestricted calculator )

**2022.03.07 version 2.2.1**

+ Drag files or folders then drop them to file list
+ improve display when calibrate
+ Bug fix
  + randomness in calc noise

**2022.02.10 version 2.1.5**

> should be 2.2.0

+ Calibration segments support
   + Add a new window for calibration details
+ Real "save as" instead of copy
+ Broken file read support
+ Change progress bar update interval
+ Bug fix
   + crash while resize plot
   + fail to export because of time format

**2022.02.03 version 2.1.4**

+ Bug fix
  + re-calculate norm peak after removing lines from peak shape tab
  + some problems about mass calculator
+ Refine
  + will report missing ions when failed to fit

**2021.11.08 version 2.1.3**

+ Bug fix
  + while mass resolution is float number

**2021.10.15 version 2.1.2**

+ Add period average
+ change read datetime method, auto determine time format

+ Bug fix
  + file rtol is omit by mistake after ver 2.0.2

**2021.09.27 version 2.1.1**

+ Add atoms type for mass defect, like

  CHO, CHON, CHONS, etc.

+ Add group step in filters

  + Step range
  + Group to add
  + Group to minus

**2021.09.22 version 2.0.16 (rename to 2.1.0)**

+ Rewrite structures with built-in module `dataclasses` instead of `pydantic`
+ Reduce fit number because of 'fail' tag

**2021.09.17 version 2.0.15**

+ Bug fix
  + Array error when save

**2021.09.16 version 2.0.14**

+ You can open 'peak float window' in 'formula result window' to determine targeted peak's formula
+ Slider will keep its position when filtering
+ Replot within peak list

+ Bug fix
  + No high-intensity noise point available will report bug
  + Plot move after moving plot

+ Code
  + Refactor: create signals using weakref

**2021.09.10 version 2.0.13**

+ Bug fix
  + Nested peaks may not pick highest peaks

**2021.09.08 version 2.0.12**

+ use group instead of positive/negative when calculate formula

**2021.09.02 version 2.0.11**

+ optimize single thread running
+ calibration
  + sort by mass after add ions
  + add background color to used ions
+ tag
  + add tag to peak
  + add background color to peak list accord to tag
  + when peak fit failed, a 'Fail' tag will be added to peak instead of crash
+ add filters
  + according to tag
  + according to intensity
  + according to isotope
  + according to contains group
  + according to mass defect


Bug fix
+ denoise: error ploy coef 
+ calibration: couldn't find peak 

**2021.08.25 version 2.0.10**

+ bind peaks and plot
+ add jump in peaks
+ support formula like C(H2O)2, SO4e-2 (equal to SO4-2), Cu+2 (equal to CuE+2, uppercase E to split from Cu), c 10 h 20

Bug fix

+ recalc noise params error

**2021.08.18 version 2.0.9**

+ use another strategy when calc calibration infomation

Bug fix
+ large ppm when calibration

**2021.08.17 version 2.0.8**

+ Accept Zero formulas as formula calculation result
+ Sort formula by ppm
+ Sort isotopes by mass
+ Change opaque to transparency

Bug fix
+ Error when delete high-intensity peaks from noise tab
+ Error when import mass list without formulas
+ Unify rtol when fit use mass list


**2021.08.11 version 2.0.7**

Bug fix
+ Res = None at peak shape tab
+ unify plot actions
+ add tool tips
+ change spin boxes' limits
+ mass defect transparent


**2021.08.08 version 2.0.6**

+ Remove microsecond when show files

Bug fix
+ Crash when save workspace

**2021.08.01 version 2.0.5**

+ Orbitool won't plot timeseries by default (too slow)

Bug fix
+ adjust timeseries
+ calculate noise
+ export timeseries

**2021.07.27 version 2.0.4**

+ Mass list export with split formula

**2021.07.26 version 2.0.3 beta**

+ Adjust mass list item by group

**2021.07.23 version 2.0.2 beta**

Bug fix
+ rtol setting in noise tab

**2021.07.20 version 2.0.1 beta**

Bug fix
+ Matplotlib crash when point too much
+ Index error when calculate calibration information
+ Index error when choosing spectrum
+ Formula noise width
+ Recalculate noise error
+ When get peak shape, remove error peaks

**2021.07.18 version 2.0.0 beta**

+ Using HDF5 as backend. Now you can use disk instead of memory store large data.
+ Change UI
+ Abortable multiprocessing
+ Redesign denoise and calibrate logic
+ Almost rewrite the program
+ Shortcuts

**2020.10.15 version 1.4.0**

Bug fix
+ When a formula contains isotope, it's difficult to set another isotope to zero.

Appended
+ Normal formula calculator could get formula with same 2 isotopes like 'C13C[13]2...'
+ Unrestricted formula calculator
  + Unrestricted calculator will treat elements and isotopes fairly. It only relays on isotopes' mass and could get formula like 'C10H[2]O[18]18-'

**2020.8.24 version 1.3.4**

Bug fix

+ number of isotope couldn't larger than non isotope element when type a formula, like "N[15]O3-". It's legal now, thanks to Runlong for finding bugs.

**2020.7.29 version 1.3.3**

Appended

+ could skip calibration

Bug fix

+ error when spectra merge peaks
+ multiple same peaks in mass list

**2020.7.24 version 1.3.2**

Bug fix

+ error when delete ions in calibration tab
+ change policy for peak failed to fit 

**2020.7.10 version 1.3.1**

Appended

+ export spectra

Bug fix

+ error occured when averaging RAW file with multiple filters

**2020.6.26 version 1.3.0**

Appended

+ concatenate time series (beta)
+ add some formula function for future
+ time series's header in table will indicate line in plot. To achieve this, change UI's style



Changed

+ substitute numba with cython



Bug fix

+ caption wrong when read workspace file
+ move colorbar's label to top in mass defect tab

**2020.6.21 version 1.2.9**

Change

+ when export mass list, use 2 columns (formula,mz) instead of 1 mixed column

Bug fix
+ some "index out of range"

**2020.5.22 version 1.2.8**

Change

+ when calculate mass defect, use nearest formula instead of treat it as a grey point for a peak with multi-formula.

Bug fix
+ when add peaks to mass list, there will be some peak not merged.
+ error when calculate mass defect using element.

**2020.5.15 version 1.2.7**

Appended
+ Export
  + fit infomation
  + mass defect
+ when export time serieses
  + export time as isotime, igor time, matlab datenum, excel datenum
  + choose with or without text "with ppm"

Bug fix
+ numba.numpy_extensions not found. numba changed its interface in new version, and new version have some errors when generate executable files, so use numba's version 0.48
+ wrong spelling
  from "Oribit" to "Orbit"

**2020.4.17 version 1.2.6**

Appended
+ Merge close peaks

Bug fix
+ area calculation

**2020.4.9 version 1.2.5**

Bug fix
+ Crash when type wrong element

**2020.3.31 version 1.2.4**

Bug fix
+ Error when merge mass list

**2020.3.31 version 1.2.3**

Bug fix
+ scan number error while averaging (maybe fix or not, I have no file to test)
+ math domain error when fit peak, and this is a reason for 'NoneType' object has no attribute 'fileTime' error. But this peak must be wrong, because this error only occurs when mz less than 0.
+ convert inputted formula with isotopes wrong.

**2020.03.31 version 1.2.2**

Bug fix
+ Division Zero Error when autoscale timeseries
+ Error when average by number

Changed
+ Rewrite average by time part

**2020.03.30 version 1.2.1**

Bug fix
+ Error when merge peaks in mass list
+ Erroe when fit use mass list
+ Error when add isotope

Maybe fixed
+ Error scan number

**2020.03.29 version 1.2.0**

Bug fix
+ Out of range when remove peak from mass list

Appended
+ Log scale and autoscale in timeseries
+ Merge mass list
+ Mass defect

Changed
+ When averaging across file, keep time interval 

**2020.03.17 version 1.1.2**

Bug fix
+ Error when use mass list fit spectrum

**2020.03.12 version 1.1.1**

Bug fix
+ Cannot show file's calibration information

**2020.03.11 version 1.1.0**

Warning

+ I rewrite formula calculation part by cython, so it mismatch with former OrbitWork/OrbitOption file

Appended

+ Rewrite formula calculation part by cython which is extremely fast than python (50 times faster without accuracy loss, the only cost is nearly 2 weeks coding). I also changed the structure, now you can add any element you want
+ Formula panel size changeable

**2020.02.29 version 1.0.3**

Warning

+ I add a polarity filter, so it mismatch with former OrbitWork file

Appended

+ polarity filter when averaging spectrum

Change

+ UI

**2020.02.27 version 1.0.2**

Warning

+ I change the structure of .OrbitWork file, so it may mismatch with former .OrbitWork file.

Appended

+ resize panels by mouse(test)
+ option for whether y axis use log scale
+ autoscale button for spectra
+ ppm column in 'Spectra&Peak fit' tab
+ isotope ratio column in 'Peak fit' group box

**2020.02.15  version 1.0.1**

Bug fix

+ ppm when show single file's calibration information
+ wrong elements shown in formula. eg. Na when negative and S when positive
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

