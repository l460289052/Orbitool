# -*- coding: utf-8 -*-

import os
import csv
from typing import List, Tuple, Dict
from functools import wraps

from sortedcontainers import SortedSet

from OribitoolClass import *
from OribitoolBase import *

def checkPathExt(ext):
	def f(func):
		@wraps(func)
		def decorator(path, *args):
			if len(path) > 0:
				return func(os.path.splitext(path)[0] + ext, *args)
		return decorator
	return f
def checkOpenCsv(func):
	@wraps(func)
	def decorator(path, *args, **kwargs):
		if len(path) > 0:
			with open(os.path.splitext(path)[0] + '.csv', 'w', newline='') as csvfile:
				csvwriter = csv.writer(csvfile)
				return func(csvwriter, *args, **kwargs)
	return decorator

@checkOpenCsv
def exportCsv(writer: csv.writer, *args, header: Iterable = None):
	'''
	all args should have same length
	eg. exportCsv('tmp.csv', mz ,intensity, ['mz','intensity'])
	'''
	if len(args) == 0:
		return
	length = len(args[0])
	for arg in args:
		if len(arg) != length:
			raise ValueError('all args should have same length')
	if header is not None and len(header) > 0:
		writer.writerow(header)
	for index in range(length):
		writer.writerow([arg[index] for arg in args])
	print('finish exporting')


@checkOpenCsv
def exportSpectrum(writer:csv.writer, spectrum: Spectrum, sendStatus=nullSendStatus):
	fileTime = spectrum.fileTime
	msg = 'export spectrum'
	# header
	writer.writerow(['mz', 'intensity'])
	
	mz = spectrum.mz
	intensity = spectrum.intensity
	length = len(mz)
	for index in range(length):
		if index % 100 == 0:
			sendStatus(fileTime, msg, index, length)
		writer.writerow([mz[index], intensity[index]])
	sendStatus(fileTime, msg, length, length)

@checkOpenCsv
def exportNoise(writer:csv.writer, fileTime, noise: (np.ndarray, np.ndarray), sendStatus=nullSendStatus):
	msg = "export noise"
	length = len(noise[0])

	writer.writerow(['mz','noise'])
	for index, n in enumerate(np.stack(noise, 1)):
		if index % 50 == 0:
			sendStatus(fileTime, msg, index, length)
		writer.writerow(list(n))
	sendStatus(fileTime, msg, length, length)


@checkOpenCsv
def exportPeakList(writer:csv.writer, fileTime:datetime, peaks: List[Peak], sendStatus=nullSendStatus):
	msg = 'export peak list'
	writer.writerow(['mz', 'intensity', 'area', 'formula', 'DBE', 'Delta ppm'])
	length = len(peaks)
	for index, peak in enumerate(peaks):
		if index % 50 == 0:
			sendStatus(fileTime, msg, index, length)
		row = [peak.peakPosition, peak.peakIntensity, peak.area]
		if hasattr(peak,'formulaList'):
			formulaList = peak.formulaList
			if len(formulaList) > 0:
				
				f = []
				dbe = []
				for formula in formulaList:
					f.append(str(formula))
					dbe.append(str(formula.DBE()))
				row.append('/'.join(f))
				row.append('/'.join(dbe))
				if len(formulaList)==1:
					delta = (peak.peakPosition / formulaList[0].mass() - 1) * 1e6 
					row.append(delta)
		writer.writerow(row)
	sendStatus(fileTime, msg, length, length)
	
@checkOpenCsv
def exportTimeSerieses(writer:csv.writer, timeSerieses: List[TimeSeries], sendStatus=nullSendStatus):
	msg = 'export time serieses 1/2 mapping times'
	slength = len(timeSerieses)
	if slength < 1:
		raise ValueError('No time serieses (selected)')
	time = []
	now = datetime.now()
	deltaTime = np.timedelta64(timedelta(seconds=1))
	for index, timeSeries in enumerate(timeSerieses):
		sendStatus(now, msg, index, slength)
		time.extend(timeSeries.time)
	time.append(time[-1] + 2 * deltaTime)
	time = np.array(time, dtype=np.datetime64)
	time.sort()
	keep = (time[1:] - time[:-1]) > deltaTime
	time = time[:-1][keep]

	sendStatus(now, msg, slength, slength)
	
	msg = 'export time serieses 2/2 writing'
	row = ['time']
	row.extend([timeSeries.tag for timeSeries in timeSerieses])
	writer.writerow(row)
	indexes = np.zeros(slength, dtype=np.int)
	maxIndexes = np.array([len(timeSeries.time) for timeSeries in timeSerieses], dtype=np.int)
	length = len(time)
	for index in range(length):
		if index % 10 == 0:
			sendStatus(now, msg, index, length)
		current = time[index]
		select = indexes < maxIndexes
		select &= np.array([(np.abs(timeSerieses[i].time[indexes[i]] - current) < deltaTime) if select[i] else False for i in range(slength)])
		row = [current.astype(datetime).strftime(OribitoolBase.timeFormat)]
		row.extend([timeSerieses[i].intensity[indexes[i]] if select[i] else '' for i in range(slength) ])
		indexes[select] += 1
		writer.writerow(row)
	sendStatus(now, msg, length, length)

@checkOpenCsv
def exportIsotope(writer:csv.writer, fileTime: datetime, peaks: List[Peak], sendStatus=nullSendStatus):
	
	msg = "mapping isotope"
	formulaMap: Dict[FormulaHint, Tuple[int, FormulaHint]] = {}
	length = len(peaks)
	for index, peak in enumerate(peaks):
		if index % 20 == 0:
			sendStatus(fileTime, msg, index, length)
		for formula in peak.formulaList:
			if formula.isIsotope:
				origin = formula.findOrigin()
				formulaMap.setdefault(origin,[]).append((index, formula))
	sendStatus(fileTime, msg, length, length)
			
	msg = "exporting isotope"

	writer.writerow(['original formula/isotope',
						'measured mz', 'intensity', 'intensity ratio','theoretic ratio'])
	for index, peak in enumerate(peaks):
		if index % 20 == 0:
			sendStatus(fileTime, msg, index, length)
		formulaList = [f for f in peak.formulaList if not f.isIsotope]
		if len(formulaList) == 0:
			continue
		isotopes = [formulaMap.get(formula, []) for formula in formulaList]
		isotopes = sum(isotopes, [])
		writer.writerow(['/'.join([str(f) for f in formulaList]), peak.peakPosition, peak.peakIntensity, 1, 1])
		for i, isotope in isotopes:
			isotopePeak = peaks[i]
			writer.writerow([str(isotope), isotopePeak.peakPosition, isotopePeak.peakIntensity, isotopePeak.peakIntensity / peak.peakIntensity, isotope.relativeAbundance()])
		writer.writerow([''])
	sendStatus(fileTime, msg, length, length)

@checkOpenCsv
def exportCalibrationInfo(writer:csv.writer, fileList:FileList, ionList:List[Tuple[str, FormulaHint]], calibrators: SortedDict, sendStatus=nullSendStatus):
	msg = "exporting calibration infomation"
	header = ['','ppm']
	header.extend([s for s, _ in ionList])
	writer.writerow(header)

	header = ['file','mz']
	header.extend([f.mass() for _, f in ionList])
	writer.writerow(header)

	length = len(calibrators)
	for index, (fileTime, calibrator) in enumerate(calibrators.items()):
		sendStatus(fileTime, msg, index, length)
		file = fileList[fileTime]
		row = [file.name, fileTime.strftime(OribitoolBase.timeFormat)]
		row.extend(list(calibrator.ionsPpm * 1e6))
		writer.writerow(row)

	sendStatus(calibrators.peekitem(-1)[0], msg, length, length)

@checkOpenCsv
def exportMassList(writer: csv.writer, massList: MassList, sendStatus=nullSendStatus):
	msg = "exporting mass list"
	header = ['formula/mz']
	now = datetime.now()
	writer.writerow(header)
	length = len(massList)
	for index, peak in enumerate(massList):
		sendStatus(now, msg, index, length)
		writer.writerow([str(peak.formulaList[0] if len(peak.formulaList) == 1 else peak.peakPosition)])
		