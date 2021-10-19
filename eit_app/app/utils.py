

from PyQt5.QtWidgets import QComboBox


def setItems_comboBox(comboBox:QComboBox, items=None, handler=None, reset_box = True, set_index=0):
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
    