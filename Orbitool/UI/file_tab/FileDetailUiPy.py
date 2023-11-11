from collections import Counter
from datetime import timedelta
from math import isnan
from PyQt6 import QtCore, QtWidgets
from Orbitool.config import setting
from Orbitool.UI.utils import TableUtils

from Orbitool.models.file import Path
from . import FileDetailUi
from ..manager import Manager


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
        TableUtils.clearAndSetRowCount(table,handler.totalScanNum)
        counter: Counter[str] = Counter()
        for row, (time, filter) in enumerate(zip(handler.getSpectrumRetentionTimes(), handler.getFilterList())):
            counter[filter["string"]] += 1
            TableUtils.setRow(table, row,
                timedelta(seconds=int(time.total_seconds())),
                setting.format_time((handler.startDatetime+time).replace(microsecond=0)),
                filter["mass_range"],
                filter["polarity"],
                filter["higher_energy_CiD"],
                filter["scan"],
                filter["string"]
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