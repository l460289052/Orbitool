from typing import Union

from PyQt6 import QtCore, QtWidgets, QtGui
from Orbitool import logger

from Orbitool.utils.readers import spectrum_filter

from .. import Manager, state_node
from ..utils import TableUtils

TAG = "TableFilterHelper"


class TableFilterHelper:
    def __init__(self, manager: Manager, table: QtWidgets.QTableWidget) -> None:
        self.manager = manager
        self.table = table

        table.itemDoubleClicked.connect(self.edit_filter)
        self.current_edit_filter_pos = None
        self.current_previous_pair = None
        self.current_filter_widget: Union[QtWidgets.QComboBox,
                                          QtWidgets.QDoubleSpinBox, None] = None

    @property
    def info(self):
        return self.manager.workspace.info.file_tab

    @state_node
    def refresh_filter(self):
        info = self.info
        file_filters = info.getCastedFilesSpectrumFilters()
        file_filters.clear()
        for path in info.pathlist:
            for filter in path.getFileHandler().getUniqueFilters():
                info.add_filter(filter)
        self.show_filter()

    def refresh_filter_polarity(self):
        file_filters = self.info.getCastedFilesSpectrumFilters()
        used_filters = self.info.getCastedUsedSpectrumFilters()
        key = "polarity"
        if key not in used_filters and file_filters.get(key, False):
            used_filters[key] = self.info.getMostCommonValue_forFilter(key)

    def show_filter(self):
        table = self.table
        use_filter = self.info.getCastedUsedSpectrumFilters()
        scanstats_filter = self.info.getCastedScanstatsFilters()
        logger.d(TAG, f"showFilter() {use_filter=} {scanstats_filter=}")
        self.current_filter_widget = None
        self.current_edit_filter_pos = None
        TableUtils.clearAndSetRowCount(table, len(
            use_filter) + sum(map(len, scanstats_filter.values())))

        for row, (name, value) in enumerate(use_filter.items()):
            TableUtils.setRow(
                table, row,
                name,
                "==",
                value)

        row = len(use_filter)
        for name, ops in scanstats_filter.items():
            for op, value in ops.items():
                TableUtils.setRow(
                    table, row,
                    name,
                    op,
                    value)
                row += 1
        table.resizeColumnsToContents()

    @state_node(withArgs=True, mode="e")
    def edit_filter(self, item: QtWidgets.QTableWidgetItem):
        table = self.table
        file_filter = self.info.getCastedFilesSpectrumFilters()
        use_filter = self.info.getCastedUsedSpectrumFilters()
        row = item.row()
        col = item.column()

        key = table.item(row, 0).text()
        op = table.item(row, 1).text()
        value = table.item(row, 2).text()

        if self.current_edit_filter_pos:
            self.text_changed()
            # textActivated may delete current item
            item = table.item(row, col)
        self.current_edit_filter_pos = (row, col)
        self.current_previous_pair = (key, op, value)
        is_stats = key in spectrum_filter.stats_header

        match col:
            case 0:
                widget = QtWidgets.QComboBox()
                keys = set(file_filter.keys())
                keys -= use_filter.keys()
                keys.add(key)
                keys.update(spectrum_filter.stats_header)
                widget.addItems(keys)
                widget.setCurrentText(key)
            case 1:
                widget = QtWidgets.QComboBox()
                if is_stats:
                    widget.addItems(["==", "<=", ">="])
                else:
                    widget.addItem("==")
                widget.setCurrentText(item.text())
            case 2:
                if is_stats:
                    widget = QtWidgets.QDoubleSpinBox()
                    widget.setMinimum(-1e8)
                    widget.setMaximum(1e8)
                    widget.setDecimals(2)
                    widget.setValue(float(value))
                else:
                    widget = QtWidgets.QComboBox()
                    widget.addItems(file_filter[key].keys())
                    widget.setCurrentText(value)
        table.setCellWidget(row, col, widget)
        self.current_filter_widget = widget
        table.resizeColumnsToContents()
        widget.setFocus()
        if isinstance(widget, QtWidgets.QComboBox):
            widget.showPopup()
            widget.currentTextChanged.connect(self.text_changed)
        else:
            widget.focusOutEvent = self.text_changed

    @state_node(mode='e')
    def text_changed(self):
        if self.current_previous_pair is None:
            return
        table = self.table
        key, op, value = self.current_previous_pair
        row, col = self.current_edit_filter_pos
        widget = self.current_filter_widget
        self.current_filter_widget = None
        self.current_edit_filter_pos = None
        self.current_filter_widget = None

        match col:
            case 0: previous = key
            case 1: previous = op
            case 2: previous = value
        if isinstance(widget, QtWidgets.QComboBox):
            current = widget.currentText()
        elif isinstance(widget, QtWidgets.QDoubleSpinBox):
            current = widget.text()
        else:
            current = None
        is_stats = key in spectrum_filter.stats_header
        use_filter = self.info.getCastedUsedSpectrumFilters()
        stats_filter = self.info.getCastedScanstatsFilters()
        if previous == current:
            return
        match col:
            case 0:
                if is_stats:
                    del stats_filter[key][op]
                    if not stats_filter[key]:
                        return stats_filter[key]
                else:
                    del use_filter[key]
                key = current
                if current in spectrum_filter.stats_header:
                    op, value = spectrum_filter.stats_default_filter
                    stats_filter.setdefault(key, {})[op] = value
                else:
                    op = "=="
                    value = use_filter[key] = self.info.getMostCommonValue_forFilter(
                        key)
            case 1:
                if is_stats:
                    del stats_filter[key][op]
                    op = current
                    stats_filter[key][op] = float(value)
                else:
                    pass
            case 2:
                value = current
                if is_stats:
                    stats_filter[key][op] = float(value)
                else:
                    use_filter[key] = current
        self.show_filter()

    @state_node
    def add_filter(self):
        file_filter = self.info.getCastedFilesSpectrumFilters()
        use_filter = self.info.getCastedUsedSpectrumFilters()
        stats_filter = self.info.getCastedScanstatsFilters()
        if len(use_filter) < len(file_filter):
            for key in file_filter.keys():
                if key not in use_filter:
                    use_filter[key] = self.info.getMostCommonValue_forFilter(
                        key)
                    break
        else:
            key = spectrum_filter.stats_header[0]
            op, value = spectrum_filter.stats_default_filter
            stats_filter.setdefault(key, {})[op] = value

        self.show_filter()

    @state_node
    def del_filter(self):
        table = self.table
        slt = TableUtils.getSelectedRow(table)
        use_filter = self.info.getCastedUsedSpectrumFilters()
        stats_filter = self.info.getCastedScanstatsFilters()
        for index in slt:
            key = table.item(index, 0).text()
            if key in use_filter:
                filter = use_filter.pop(key)
                logger.d(TAG, f"delFilter() useFilter:{key=} {filter=}")
            elif key in stats_filter:
                sub_key = table.item(index, 1).text()
                sub_filter = stats_filter.get(key, {})
                value = sub_filter.pop(sub_key, None)  # type: ignore
                if not sub_filter:
                    stats_filter.pop(key, None)
                logger.d(TAG, f"delFilter() statsFilter:{key=} {sub_key=} {value=}")

        self.show_filter()
