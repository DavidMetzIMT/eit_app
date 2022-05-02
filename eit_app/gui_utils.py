import itertools
from dataclasses import dataclass
from typing import Any, Callable, List
from PyQt5.QtWidgets import QComboBox, QTableWidgetItem, QTableWidget, QSlider
import numpy as np
import logging

logger = logging.getLogger(__name__)


def set_comboBox_items(
    comboBox: QComboBox,
    items: list[Any] = None,
    reset_box: bool = True,
    init_index: int = 0,
    block: bool = True,
) -> None:
    """Set items of a comboBox

    Args:
        comboBox (QComboBox):comboBox to set
        items (list[Any], optional): new items list to set if reste_box is
        `True`, otherwsie the list will be append to the existing one.
        Defaults to None.
        reset_box (bool, optional): clear the list of items before adding new items. Defaults to True.
        init_index (int, optional): set default item index . Defaults to 0.
        block (bool, optional): block signal emitted (e.g. activated, ...)
        from the comboBox during new setting. Defaults to `True`.
    """

    comboBox.blockSignals(block)

    if reset_box:
        comboBox.clear()

    if items is not None:
        if not items:
            logger.error("could not set combobox: ", comboBox.objectName)
        elif len(items) == 1:
            comboBox.addItem(str(items[0]))
        else:
            comboBox.addItems([str(item) for item in items])

    set_comboBox_index(comboBox, init_index)

    comboBox.blockSignals(False)


def set_comboBox_index(comboBox: QComboBox, index: int = 0, block: bool = True) -> None:
    """Set the actual item index of a comboBox/DropdownMenu

    Args:
        comboBox (QComboBox): comboBox to set
        index (int, optional): item index val to set. Defaults to 0.
        block (bool, optional): block signal emitted (e.g. activated, ...)
        from the comboBox during new setting. Defaults to `True`.
    """

    comboBox.blockSignals(block)

    if index != -1:
        comboBox.setCurrentIndex(index)
    else:
        comboBox.setCurrentIndex(comboBox.count() - 1)  # last item

    comboBox.blockSignals(False)


def set_QTableWidget(
    table: QTableWidget, mat: list[list[float]], decimal: int = 4
) -> None:
    """Set a table with float values

    Args:
        tableWidget (QTableWidget): table to set
        val (list[list[float]]): values / matrix
        decimal (int, optional): number of decimal digit to display.
        Defaults to 4.
    """

    mat = np.array(mat)
    if np.prod(mat.shape) > 1:
        numrows = len(mat)  # 6 rows in your example
        numcols = len(mat[0])  # 3 columns in your example
        table.setColumnCount(numcols)  # Set colums and rows in QTableWidget
        table.setRowCount(numrows)
        for row, column in itertools.product(range(numrows), range(numcols)):
            val = f"{mat[row][column]:.{decimal}f}"
            table.setItem(
                row,
                column,
                QTableWidgetItem(val),
            )
    else:
        table.clearContents()


def set_comboBox_items(
    comboBox: QComboBox,
    items: list[Any] = None,
    reset_box: bool = True,
    init_index: int = 0,
    block: bool = True,
) -> None:
    """Set items of a comboBox

    Args:
        comboBox (QComboBox):comboBox to set
        items (list[Any], optional): new items list to set if reste_box is
        `True`, otherwsie the list will be append to the existing one.
        Defaults to None.
        reset_box (bool, optional): clear the list of items before adding new items. Defaults to True.
        init_index (int, optional): set default item index . Defaults to 0.
        block (bool, optional): block signal emitted (e.g. activated, ...)
        from the comboBox during new setting. Defaults to `True`.
    """

    comboBox.blockSignals(block)

    if reset_box:
        comboBox.clear()

    if items is not None:
        if not items:
            logger.error("could not set combobox: ", comboBox.objectName)
        elif len(items) == 1:
            comboBox.addItem(str(items[0]))
        else:
            comboBox.addItems([str(item) for item in items])

    set_comboBox_index(comboBox, init_index)

    comboBox.blockSignals(False)


def get_comboBox_allItemsText(comboBox: QComboBox) -> list[str]:
    """Set the actual item index of a comboBox/DropdownMenu

    Args:
        comboBox (QComboBox): comboBox to set
        index (int, optional): item index val to set. Defaults to 0.
        block (bool, optional): block signal emitted (e.g. activated, ...)
        from the comboBox during new setting. Defaults to `True`.
    """

    return [comboBox.itemText(i) for i in range(comboBox.count())]


def get_comboBox_allItemsIndex(comboBox: QComboBox) -> list[str]:
    """Set the actual item index of a comboBox/DropdownMenu

    Args:
        comboBox (QComboBox): comboBox to set
        index (int, optional): item index val to set. Defaults to 0.
        block (bool, optional): block signal emitted (e.g. activated, ...)
        from the comboBox during new setting. Defaults to `True`.
    """

    return [i for i in range(comboBox.count())]


def set_QTableWidget(
    table: QTableWidget, mat: list[list[float]], decimal: int = 4
) -> None:
    """Set a table with float values

    Args:
        tableWidget (QTableWidget): table to set
        val (list[list[float]]): values / matrix
        decimal (int, optional): number of decimal digit to display.
        Defaults to 4.
    """

    mat = np.array(mat)
    if np.prod(mat.shape) > 1:
        numrows = len(mat)  # 6 rows in your example
        numcols = len(mat[0])  # 3 columns in your example
        table.setColumnCount(numcols)  # Set colums and rows in QTableWidget
        table.setRowCount(numrows)
        for row, column in itertools.product(range(numrows), range(numcols)):
            val = f"{mat[row][column]:.{decimal}f}"
            table.setItem(
                row,
                column,
                QTableWidgetItem(val),
            )
    else:
        table.clearContents()


def set_QSlider_scale(slider: QSlider, nb_pos: int = 10) -> None:
    """Set scale of Qslider

    Args:
        slider (QSlider): slider object to set
        nb_pos (int, optional): number of position on the scale. Defaults to 10.
    """
    if (
        nb_pos is not None and nb_pos > 0
    ):  # change axis of slider only when the max change!
        slider.setMaximum(nb_pos - 1)
        slider.setMinimum(0)
        slider.setSingleStep(1)
        slider.setPageStep(1)


def set_QSlider_position(slider: QSlider, pos: int = 0):
    """Place the cursor as the passed position

    Args:
        slider (QSlider): slider object to set
        pos (int, optional): position to set. Defaults to `0`.
        If pos is `-1` the slider will be set to the end
        Pos has to be btw -1 >= pos >= slidermax, otherwise nothing will be done!
    """
    max_slider = slider.maximum()
    if pos.__lt__(-1) or pos.__gt__(max_slider):
        logger.error(f"Slider positionshould be between -1 and {max_slider}")
        return
    elif pos.__eq__(-1):
        slider.setSliderPosition(max_slider)
    else:
        slider.setSliderPosition(pos)


# def inc_QSlider_position(slider: QSlider, forward: bool = True, loop: bool = True):
#     """Increment the position of the cursor

#     Args:
#         slider (QSlider): slider object to set
#         set_pos (int, optional): position. Defaults to `0`.
#         If set to `-1` the slider will be set to the end
#     """
#     inc = {True: 1, False: -1}
#     pos = slider.sliderPosition()
#     max_slider = slider.maximum()
#     nb_pos = max_slider + 1

#     pos = pos + inc[forward]
#     pos = pos % nb_pos if loop else pos

#     if pos.__lt__(-1):
#         pos = 0
#     if pos.__gt__(max_slider):
#         pos = max_slider

#     set_QSlider_position(slider, pos)


def block_signals(method: Callable, *args, **kwargs):
    """Allow block signals emitted by an QtObject during execution of one
    of its method

    Args:
        method (Callable): Method to run
    """
    obj = method.__self__
    obj.blockSignals(True)
    method(*args, **kwargs)
    obj.blockSignals(False)


if __name__ == "__main__":

    @dataclass
    class test:
        t: int

    print(type(test(1)))
