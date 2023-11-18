from collections import Counter
from datetime import timedelta
from math import isnan
from PyQt6 import QtCore, QtWidgets
from Orbitool.config import setting
from Orbitool.UI.utils import TableUtils

from Orbitool.models.file import Path
from Orbitool.utils.readers import spectrum_filter
from . import FileDetailUi
from ..manager import Manager

COL_HEADER = ["datetime", "rtime"]


class Dialog(QtWidgets.QDialog):
    def __init__(self, manager: Manager, file_index: int) -> None:
        super().__init__()
        self.ui = FileDetailUi.Ui_Dialog()
        self.ui.setupUi(self)

        self.manager = manager
        self.showFile(
            manager.workspace.info.file_tab.pathlist.paths[file_index])

    def showFile(self, file: Path):
        self.setWindowTitle(f"Filter Detail: {file.get_show_name()}")
        handler = file.getFileHandler()

        table = self.ui.spectraListTableWidget
        header = [*COL_HEADER, *spectrum_filter.filter_headers.values(), *spectrum_filter.stats_header.values()]
        TableUtils.clearAndSetColumnCount(table, len(header))
        TableUtils.clearAndSetRowCount(table, handler.totalScanNum)

        table.setHorizontalHeaderLabels(header)
        counter: Counter[str] = Counter()
        for row, (time, filter, stats) in enumerate(zip(handler.getSpectrumRetentionTimes(), handler.getFilterList(), handler.get_stats_list())):
            counter[filter["string"]] += 1
            TableUtils.setRow(
                table, row,
                setting.format_time(
                    (handler.startDatetime+time).replace(microsecond=0)),
                timedelta(seconds=int(time.total_seconds())),
                *spectrum_filter.filter_to_row(filter),
                *spectrum_filter.stats_to_row(stats)
            )

        table.resizeColumnsToContents()
        table.update()

        table = self.ui.filterCountsTableWidget
        TableUtils.clearAndSetRowCount(table, len(counter))
        for row, (filter, cnt) in enumerate(counter.most_common()):
            TableUtils.setRow(
                table, row,
                cnt,
                filter,
            )
        table.resizeColumnsToContents()
        table.update()
