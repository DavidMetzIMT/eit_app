

from typing import List
from PyQt5.QtWidgets import QComboBox, QTableWidgetItem, QTableWidget, QSlider
import numpy as np


def set_comboBox_items(comboBox:QComboBox, items=None, handler=None, reset_box = True, set_index=0):
    if handler:
        #handler =self._callback_show_frame
        comboBox.activated.disconnect()
    if reset_box:
        comboBox.clear()
    if items is not None:
        if len(items)==0:
            print('could not set combobox: ' , comboBox.objectName )
        elif len(items)==1: 
            comboBox.addItem(str(items[0]))
        else:
            comboBox.addItems([str(item) for item in items])

    if set_index!=-1:
        comboBox.setCurrentIndex(set_index)
    else:
        comboBox.setCurrentIndex(comboBox.count()-1) #last item

    if handler:
        comboBox.activated.connect(handler)

def set_table_widget(tableWidget:QTableWidget,list2display:List[List[float]], decimal=4):

        list2display=np.array(list2display)
        if np.prod(list2display.shape)>1: 
            numrows = len(list2display)  # 6 rows in your example
            numcols = len(list2display[0])  # 3 columns in your example
            tableWidget.setColumnCount(numcols)# Set colums and rows in QTableWidget
            tableWidget.setRowCount(numrows)
            for row in range(numrows):# Loops to add values into QTableWidget
                for column in range(numcols):
                    tableWidget.setItem(row, column, QTableWidgetItem(f"{list2display[row][column]:.{decimal}f}"))
        else:
            tableWidget.clearContents()

def set_slider(self, slider:QSlider,  slider_pos=0, pos_min=0, pos_max=None, single_step=1,page_step=1, next=False, loop=True):
    if not next:
        if slider_pos==-1:
            slider.setSliderPosition(slider.maximum())
        else:
            slider.setSliderPosition(slider_pos)
    elif slider.sliderPosition()==slider.maximum():
        if loop:
            slider.setSliderPosition(0)
    else:
        slider.setSliderPosition(slider.sliderPosition()+1)

    if pos_max is not None: # change axis of slider only when the max change!
        slider.setMaximum(pos_max)
        slider.setMinimum(pos_min)    
        slider.setSingleStep(single_step)
        slider.setPageStep(page_step)

    return slider.sliderPosition(), slider.maximum()
    