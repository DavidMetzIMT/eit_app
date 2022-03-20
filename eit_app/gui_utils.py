from dataclasses import dataclass
from typing import Any, Callable, List
from PyQt5.QtWidgets import QComboBox, QTableWidgetItem, QTableWidget, QSlider
import numpy as np
import logging

logger = logging.getLogger(__name__)


def set_comboBox_items(
    comboBox: QComboBox,
    items: List[Any] = None,
    reset_box: bool = True,
    set_index: int = 0,
    block: bool = True,
) -> None:
    """_summary_

    Args:
        comboBox (QComboBox): _description_
        items (List[Any], optional): _description_. Defaults to None.
        reset_box (bool, optional): _description_. Defaults to True.
        set_index (int, optional): _description_. Defaults to 0.
        block (bool, optional): _description_. Defaults to True.
    """

    comboBox.blockSignals(block)
    if reset_box:
        comboBox.clear()
    if items is not None:
        if not items:
            logger.error("could not set combobox: ", comboBox.objectName)
        elif len(items) == 1:
            comboBox.addItem(
                str(items[0]),
            )
        else:
            comboBox.addItems([str(item) for item in items])

    if set_index != -1:
        comboBox.setCurrentIndex(set_index)
    else:
        comboBox.setCurrentIndex(comboBox.count() - 1)  # last item

    comboBox.blockSignals(False)
    # if handler:
    #     comboBox.activated.connect(handler)


def set_table_widget(
    tableWidget: QTableWidget, list2display: List[List[float]], decimal=4
):
    """_summary_

    Args:
        tableWidget (QTableWidget): _description_
        list2display (List[List[float]]): _description_
        decimal (int, optional): _description_. Defaults to 4.
    """

    list2display = np.array(list2display)
    if np.prod(list2display.shape) > 1:
        numrows = len(list2display)  # 6 rows in your example
        numcols = len(list2display[0])  # 3 columns in your example
        tableWidget.setColumnCount(numcols)  # Set colums and rows in QTableWidget
        tableWidget.setRowCount(numrows)
        for row in range(numrows):  # Loops to add values into QTableWidget
            for column in range(numcols):
                val = f"{list2display[row][column]:.{decimal}f}"
                tableWidget.setItem(
                    row,
                    column,
                    QTableWidgetItem(val),
                )
    else:
        tableWidget.clearContents()


def set_slider(
    slider: QSlider,
    set_pos=0,
    pos_min=0,
    pos_max=None,
    single_step=1,
    page_step=1,
    next=False,
    loop=True,
):
    """_summary_

    Args:
        slider (QSlider): _description_
        set_pos (int, optional): _description_. Defaults to 0.
        pos_min (int, optional): _description_. Defaults to 0.
        pos_max (_type_, optional): _description_. Defaults to None.
        single_step (int, optional): _description_. Defaults to 1.
        page_step (int, optional): _description_. Defaults to 1.
        next (bool, optional): _description_. Defaults to False.
        loop (bool, optional): _description_. Defaults to True.

    Returns:
        _type_: _description_
    """
    if not next:
        if set_pos == -1:
            slider.setSliderPosition(slider.maximum())
        else:
            slider.setSliderPosition(set_pos)
    elif slider.sliderPosition() == slider.maximum():
        if loop:
            slider.setSliderPosition(0)
    else:
        slider.setSliderPosition(slider.sliderPosition() + 1)

    if pos_max is not None:  # change axis of slider only when the max change!
        slider.setMaximum(pos_max)
        slider.setMinimum(pos_min)
        slider.setSingleStep(single_step)
        slider.setPageStep(page_step)

    return slider.sliderPosition(), slider.maximum()


def change_value_withblockSignal(method: Callable, val):
    obj = method.__self__
    obj.blockSignals(True)
    method(val)
    obj.blockSignals(False)


def set_multi_cB_same(cB_list, items: List[Any]):
    [set_comboBox_items(cB, items) for cB in cB_list]


if __name__ == "__main__":

    @dataclass
    class test:
        t: int

    print(type(test(1)))
