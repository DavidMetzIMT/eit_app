from PyQt5.QtWidgets import QFileDialog, QMessageBox, QDialog

## ======================================================================================================================================================
##  DialogBoxes
## ======================================================================================================================================================
def show_dialog(text, title, attr=None):  # non blocking

    # NoIcon = ... # type: 'QMessageBox.Icon'
    # Information = ... # type: 'QMessageBox.Icon'
    # Warning = ... # type: 'QMessageBox.Icon'
    # Critical = ... # type: 'QMessageBox.Icon'
    # Question = ... # type: 'QMessageBox.Icon'

    msgBox = QDialog()
    # attr= attr if attr else 'NoIcon'
    # msgBox.setIcon(getattr(QMessageBox, attr))
    # msgBox.setText(text)
    msgBox.setWindowTitle(title)
    msgBox.adjustSize()
    return msgBox.show()


def show_msgBox(text, title, attr=None):

    # NoIcon = ... # type: 'QMessageBox.Icon'
    # Information = ... # type: 'QMessageBox.Icon'
    # Warning = ... # type: 'QMessageBox.Icon'
    # Critical = ... # type: 'QMessageBox.Icon'
    # Question = ... # type: 'QMessageBox.Icon'

    msgBox = QMessageBox()
    attr = attr or "NoIcon"
    msgBox.setIcon(getattr(QMessageBox, attr))
    msgBox.setText(text)
    msgBox.setWindowTitle(title)
    msgBox.adjustSize()
    return msgBox.exec()


def openFileNameDialog(Qwidget, path, fileExtensionFilter="*"):
    options = QFileDialog.Options()
    options |= QFileDialog.DontUseNativeDialog
    fileName, _ = QFileDialog.getOpenFileName(
        Qwidget, "Select a file to load", path, fileExtensionFilter, options=options
    )
    if fileName:
        return fileName, 0
    else:
        return fileName, 1


def openDirDialog(Qwidget, path):
    options = QFileDialog.Options()
    options |= QFileDialog.DontUseNativeDialog
    fileName = QFileDialog.getExistingDirectory(
        Qwidget, "Select a directory to load", path, options=options
    )
    if fileName:
        return fileName, 0
    else:
        return fileName, 1


def openFileNamesDialog(Qwidget, path, fileExtensionFilter="*"):
    options = QFileDialog.Options()
    options |= QFileDialog.DontUseNativeDialog
    fileNames, _ = QFileDialog.getOpenFileNames(
        Qwidget,
        "QFileDialog.getOpenFileNames()",
        path,
        fileExtensionFilter,
        options=options,
    )
    if fileNames:
        return fileNames, 0
    else:
        return fileNames, 1


def saveFileDialog(Qwidget, path, fileExtensionFilter="*"):
    options = QFileDialog.Options()
    options |= QFileDialog.DontUseNativeDialog
    fileName, _ = QFileDialog.getSaveFileName(
        Qwidget,
        "Select/create a file to save",
        path,
        fileExtensionFilter,
        options=options,
    )
    if fileName:
        return fileName, 0
    else:
        return fileName, 1
