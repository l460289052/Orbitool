
# DOCS

**⚠️Please view [our new docs in Notion](https://orbitool.notion.site/02229a2f509d4383bd38b5d2aeb0595b)⚠️**.

We are gradually moving the documentation to Notion.


# UI

Underlined character is a shortcut with Alt. Like 'Alt + A', 'Alt + B', etc.

Arrow keys is useful in peak fit tab. Up and down keys could change y axis, and left and right keys could change x axis.


## I. Tabs

**⚠️Please view [our new docs in Notion](https://orbitool.notion.site/02229a2f509d4383bd38b5d2aeb0595b)⚠️**.

## II. Dockers

Docker could be dragged out or be stacked.

<img src="img\dockers-draged-out.png" alt="dockers-draged-out" style="zoom: 50%;" /> <img src="img\dockers-stack.png" alt="dockers-stack" style="zoom: 50%;" /> 

### 1.Formula

There are only one formula calculator now. I will explain in detail below how it works and how to use it.

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

**⚠️Please view [our new docs in Notion](https://orbitool.notion.site/02229a2f509d4383bd38b5d2aeb0595b)⚠️**.

# Maintain

## Maintainer

The program is developed and maintained by students of Shanghai Jiao Tong University. Runlong acts as a chemical advisor during program development.

+ Developer: Yihao Li<liyihao321@sjtu.edu.cn, liyihc@outlook.com>
+ Chemical advisor: Runlong Cai<>

## Contributors

+ State Environmental Protection Key Laboratory of Formation and Prevention of Urban Air Pollution Complex, Shanghai Academy of Environmental Sciences, Shanghai, 200233, China
+ Univ. Lyon, Université Claude Bernard Lyon 1, CNRS, IRCELYON, F-69626, Villeurbanne, France.
+ Institute for Atmospheric and Earth System Research / Physics, Faculty of Science, University of Helsinki, Helsinki, 00140, Finland.

## Bugs report & function require

If you meet any bugs, please let me know. You can send me the 'log.txt' file which is under the same directory with 'Orbitool.exe'.

mail to: "Matthieu Riva"\<<matthieu.riva@ircelyon.univ-lyon1.fr>\>;  "Cheng Huang"\<<huangc@saes.sh.cn>\>

## Update logs

**⚠️Please view [our update logs in Notion](https://orbitool.notion.site/a73b2dbb579e4427a64d2bc742eec8e8)⚠️**.
