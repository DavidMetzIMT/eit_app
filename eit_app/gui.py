# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'eit_app/gui.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.setWindowModality(QtCore.Qt.NonModal)
        MainWindow.resize(1516, 846)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        icon = QtGui.QIcon()
        icon.addPixmap(
            QtGui.QPixmap(":/icons/icons/EIT.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off
        )
        MainWindow.setWindowIcon(icon)
        MainWindow.setIconSize(QtCore.QSize(20, 20))
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Preferred
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.centralwidget.sizePolicy().hasHeightForWidth()
        )
        self.centralwidget.setSizePolicy(sizePolicy)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout_13 = QtWidgets.QHBoxLayout(self.centralwidget)
        self.horizontalLayout_13.setSizeConstraint(
            QtWidgets.QLayout.SetDefaultConstraint
        )
        self.horizontalLayout_13.setObjectName("horizontalLayout_13")
        self.tabW_settings = QtWidgets.QTabWidget(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.tabW_settings.sizePolicy().hasHeightForWidth()
        )
        self.tabW_settings.setSizePolicy(sizePolicy)
        self.tabW_settings.setMinimumSize(QtCore.QSize(0, 0))
        self.tabW_settings.setMaximumSize(QtCore.QSize(430, 16777215))
        self.tabW_settings.setObjectName("tabW_settings")
        self.tab_device = QtWidgets.QWidget()
        self.tab_device.setObjectName("tab_device")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.tab_device)
        self.verticalLayout.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.verticalLayout.setObjectName("verticalLayout")
        self.groupBox_3 = QtWidgets.QGroupBox(self.tab_device)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.groupBox_3.sizePolicy().hasHeightForWidth())
        self.groupBox_3.setSizePolicy(sizePolicy)
        self.groupBox_3.setMinimumSize(QtCore.QSize(0, 0))
        self.groupBox_3.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.groupBox_3.setObjectName("groupBox_3")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.groupBox_3)
        self.verticalLayout_3.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.horizontalLayout_11 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_11.setObjectName("horizontalLayout_11")
        self.pB_refresh = QtWidgets.QPushButton(self.groupBox_3)
        self.pB_refresh.setEnabled(True)
        self.pB_refresh.setMinimumSize(QtCore.QSize(0, 23))
        self.pB_refresh.setMaximumSize(QtCore.QSize(16777215, 23))
        self.pB_refresh.setToolTip("")
        self.pB_refresh.setAutoFillBackground(False)
        self.pB_refresh.setObjectName("pB_refresh")
        self.horizontalLayout_11.addWidget(self.pB_refresh)
        self.pB_connect = QtWidgets.QPushButton(self.groupBox_3)
        self.pB_connect.setMinimumSize(QtCore.QSize(0, 23))
        self.pB_connect.setMaximumSize(QtCore.QSize(16777215, 23))
        self.pB_connect.setAutoFillBackground(False)
        self.pB_connect.setObjectName("pB_connect")
        self.horizontalLayout_11.addWidget(self.pB_connect)
        self.pB_disconnect = QtWidgets.QPushButton(self.groupBox_3)
        self.pB_disconnect.setMinimumSize(QtCore.QSize(0, 23))
        self.pB_disconnect.setMaximumSize(QtCore.QSize(16777215, 23))
        self.pB_disconnect.setToolTip("")
        self.pB_disconnect.setAutoFillBackground(False)
        self.pB_disconnect.setObjectName("pB_disconnect")
        self.horizontalLayout_11.addWidget(self.pB_disconnect)
        self.verticalLayout_3.addLayout(self.horizontalLayout_11)
        self.verticalLayout_13 = QtWidgets.QVBoxLayout()
        self.verticalLayout_13.setObjectName("verticalLayout_13")
        self.cB_ports = QtWidgets.QComboBox(self.groupBox_3)
        self.cB_ports.setMinimumSize(QtCore.QSize(0, 23))
        self.cB_ports.setMaximumSize(QtCore.QSize(16777215, 23))
        self.cB_ports.setToolTip("")
        self.cB_ports.setObjectName("cB_ports")
        self.verticalLayout_13.addWidget(self.cB_ports)
        self.lab_device_status = QtWidgets.QLabel(self.groupBox_3)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.lab_device_status.sizePolicy().hasHeightForWidth()
        )
        self.lab_device_status.setSizePolicy(sizePolicy)
        self.lab_device_status.setMinimumSize(QtCore.QSize(0, 23))
        self.lab_device_status.setMaximumSize(QtCore.QSize(16777215, 23))
        self.lab_device_status.setStatusTip("")
        self.lab_device_status.setAutoFillBackground(True)
        self.lab_device_status.setAlignment(QtCore.Qt.AlignCenter)
        self.lab_device_status.setObjectName("lab_device_status")
        self.verticalLayout_13.addWidget(self.lab_device_status)
        self.verticalLayout_3.addLayout(self.verticalLayout_13)
        self.verticalLayout.addWidget(self.groupBox_3)
        self.toolBox_4 = QtWidgets.QToolBox(self.tab_device)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.toolBox_4.sizePolicy().hasHeightForWidth())
        self.toolBox_4.setSizePolicy(sizePolicy)
        self.toolBox_4.setObjectName("toolBox_4")
        self.toolBox_4Page1 = QtWidgets.QWidget()
        self.toolBox_4Page1.setGeometry(QtCore.QRect(0, 0, 406, 546))
        self.toolBox_4Page1.setObjectName("toolBox_4Page1")
        self.verticalLayout_12 = QtWidgets.QVBoxLayout(self.toolBox_4Page1)
        self.verticalLayout_12.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.verticalLayout_12.setObjectName("verticalLayout_12")
        self.horizontalLayout_10 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_10.setObjectName("horizontalLayout_10")
        self.pB_set_setup = QtWidgets.QPushButton(self.toolBox_4Page1)
        self.pB_set_setup.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pB_set_setup.sizePolicy().hasHeightForWidth())
        self.pB_set_setup.setSizePolicy(sizePolicy)
        self.pB_set_setup.setAutoFillBackground(False)
        self.pB_set_setup.setObjectName("pB_set_setup")
        self.horizontalLayout_10.addWidget(self.pB_set_setup)
        self.pB_get_setup = QtWidgets.QPushButton(self.toolBox_4Page1)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pB_get_setup.sizePolicy().hasHeightForWidth())
        self.pB_get_setup.setSizePolicy(sizePolicy)
        self.pB_get_setup.setAutoFillBackground(False)
        self.pB_get_setup.setObjectName("pB_get_setup")
        self.horizontalLayout_10.addWidget(self.pB_get_setup)
        self.pB_reset = QtWidgets.QPushButton(self.toolBox_4Page1)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pB_reset.sizePolicy().hasHeightForWidth())
        self.pB_reset.setSizePolicy(sizePolicy)
        self.pB_reset.setAutoFillBackground(False)
        self.pB_reset.setObjectName("pB_reset")
        self.horizontalLayout_10.addWidget(self.pB_reset)
        self.verticalLayout_12.addLayout(self.horizontalLayout_10)
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.LayoutParameters = QtWidgets.QFormLayout()
        self.LayoutParameters.setFieldGrowthPolicy(
            QtWidgets.QFormLayout.AllNonFixedFieldsGrow
        )
        self.LayoutParameters.setHorizontalSpacing(6)
        self.LayoutParameters.setObjectName("LayoutParameters")
        self.lab_exc_amp = QtWidgets.QLabel(self.toolBox_4Page1)
        self.lab_exc_amp.setMinimumSize(QtCore.QSize(0, 20))
        self.lab_exc_amp.setMaximumSize(QtCore.QSize(16777215, 20))
        self.lab_exc_amp.setObjectName("lab_exc_amp")
        self.LayoutParameters.setWidget(
            0, QtWidgets.QFormLayout.LabelRole, self.lab_exc_amp
        )
        self.sBd_exc_amp = QtWidgets.QDoubleSpinBox(self.toolBox_4Page1)
        self.sBd_exc_amp.setDecimals(4)
        self.sBd_exc_amp.setMinimum(0.0001)
        self.sBd_exc_amp.setMaximum(10.0)
        self.sBd_exc_amp.setSingleStep(0.1)
        self.sBd_exc_amp.setObjectName("sBd_exc_amp")
        self.LayoutParameters.setWidget(
            0, QtWidgets.QFormLayout.FieldRole, self.sBd_exc_amp
        )
        self.lab_burst = QtWidgets.QLabel(self.toolBox_4Page1)
        self.lab_burst.setObjectName("lab_burst")
        self.LayoutParameters.setWidget(
            1, QtWidgets.QFormLayout.LabelRole, self.lab_burst
        )
        self.sB_burst = QtWidgets.QSpinBox(self.toolBox_4Page1)
        self.sB_burst.setMaximum(255)
        self.sB_burst.setObjectName("sB_burst")
        self.LayoutParameters.setWidget(
            1, QtWidgets.QFormLayout.FieldRole, self.sB_burst
        )
        self.lab_minF = QtWidgets.QLabel(self.toolBox_4Page1)
        self.lab_minF.setObjectName("lab_minF")
        self.LayoutParameters.setWidget(
            2, QtWidgets.QFormLayout.LabelRole, self.lab_minF
        )
        self.sBd_freq_min = QtWidgets.QDoubleSpinBox(self.toolBox_4Page1)
        self.sBd_freq_min.setMinimum(100.0)
        self.sBd_freq_min.setMaximum(1000000.0)
        self.sBd_freq_min.setObjectName("sBd_freq_min")
        self.LayoutParameters.setWidget(
            2, QtWidgets.QFormLayout.FieldRole, self.sBd_freq_min
        )
        self.lab_maxF = QtWidgets.QLabel(self.toolBox_4Page1)
        self.lab_maxF.setObjectName("lab_maxF")
        self.LayoutParameters.setWidget(
            3, QtWidgets.QFormLayout.LabelRole, self.lab_maxF
        )
        self.sBd_freq_max = QtWidgets.QDoubleSpinBox(self.toolBox_4Page1)
        self.sBd_freq_max.setAutoFillBackground(False)
        self.sBd_freq_max.setMinimum(100.0)
        self.sBd_freq_max.setMaximum(1000000.0)
        self.sBd_freq_max.setObjectName("sBd_freq_max")
        self.LayoutParameters.setWidget(
            3, QtWidgets.QFormLayout.FieldRole, self.sBd_freq_max
        )
        self.lab_steps = QtWidgets.QLabel(self.toolBox_4Page1)
        self.lab_steps.setObjectName("lab_steps")
        self.LayoutParameters.setWidget(
            4, QtWidgets.QFormLayout.LabelRole, self.lab_steps
        )
        self.sB_freq_steps = QtWidgets.QSpinBox(self.toolBox_4Page1)
        self.sB_freq_steps.setMinimum(1)
        self.sB_freq_steps.setMaximum(255)
        self.sB_freq_steps.setObjectName("sB_freq_steps")
        self.LayoutParameters.setWidget(
            4, QtWidgets.QFormLayout.FieldRole, self.sB_freq_steps
        )
        self.lab_scale = QtWidgets.QLabel(self.toolBox_4Page1)
        self.lab_scale.setObjectName("lab_scale")
        self.LayoutParameters.setWidget(
            5, QtWidgets.QFormLayout.LabelRole, self.lab_scale
        )
        self.cB_scale = QtWidgets.QComboBox(self.toolBox_4Page1)
        self.cB_scale.setEditable(False)
        self.cB_scale.setMaxVisibleItems(2)
        self.cB_scale.setObjectName("cB_scale")
        self.LayoutParameters.setWidget(
            5, QtWidgets.QFormLayout.FieldRole, self.cB_scale
        )
        self.lab_frame_rate = QtWidgets.QLabel(self.toolBox_4Page1)
        self.lab_frame_rate.setObjectName("lab_frame_rate")
        self.LayoutParameters.setWidget(
            6, QtWidgets.QFormLayout.LabelRole, self.lab_frame_rate
        )
        self.sBd_frame_rate = QtWidgets.QDoubleSpinBox(self.toolBox_4Page1)
        self.sBd_frame_rate.setDecimals(3)
        self.sBd_frame_rate.setMaximum(100.0)
        self.sBd_frame_rate.setSingleStep(0.001)
        self.sBd_frame_rate.setObjectName("sBd_frame_rate")
        self.LayoutParameters.setWidget(
            6, QtWidgets.QFormLayout.FieldRole, self.sBd_frame_rate
        )
        self.lab_max_frame_rate = QtWidgets.QLabel(self.toolBox_4Page1)
        self.lab_max_frame_rate.setObjectName("lab_max_frame_rate")
        self.LayoutParameters.setWidget(
            7, QtWidgets.QFormLayout.LabelRole, self.lab_max_frame_rate
        )
        self.sBd_max_frame_rate = QtWidgets.QDoubleSpinBox(self.toolBox_4Page1)
        self.sBd_max_frame_rate.setEnabled(False)
        self.sBd_max_frame_rate.setDecimals(3)
        self.sBd_max_frame_rate.setMaximum(100.0)
        self.sBd_max_frame_rate.setSingleStep(0.001)
        self.sBd_max_frame_rate.setObjectName("sBd_max_frame_rate")
        self.LayoutParameters.setWidget(
            7, QtWidgets.QFormLayout.FieldRole, self.sBd_max_frame_rate
        )
        self.lab_sn = QtWidgets.QLabel(self.toolBox_4Page1)
        self.lab_sn.setObjectName("lab_sn")
        self.LayoutParameters.setWidget(8, QtWidgets.QFormLayout.LabelRole, self.lab_sn)
        self.lE_sn = QtWidgets.QLineEdit(self.toolBox_4Page1)
        self.lE_sn.setEnabled(False)
        self.lE_sn.setToolTip("")
        self.lE_sn.setWhatsThis("")
        self.lE_sn.setInputMask("")
        self.lE_sn.setFrame(True)
        self.lE_sn.setObjectName("lE_sn")
        self.LayoutParameters.setWidget(8, QtWidgets.QFormLayout.FieldRole, self.lE_sn)
        self.lab_ip = QtWidgets.QLabel(self.toolBox_4Page1)
        self.lab_ip.setObjectName("lab_ip")
        self.LayoutParameters.setWidget(9, QtWidgets.QFormLayout.LabelRole, self.lab_ip)
        self.lE_ip = QtWidgets.QLineEdit(self.toolBox_4Page1)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lE_ip.sizePolicy().hasHeightForWidth())
        self.lE_ip.setSizePolicy(sizePolicy)
        self.lE_ip.setToolTip("")
        self.lE_ip.setWhatsThis("")
        self.lE_ip.setInputMask("")
        self.lE_ip.setFrame(True)
        self.lE_ip.setObjectName("lE_ip")
        self.LayoutParameters.setWidget(9, QtWidgets.QFormLayout.FieldRole, self.lE_ip)
        self.lab_mac = QtWidgets.QLabel(self.toolBox_4Page1)
        self.lab_mac.setObjectName("lab_mac")
        self.LayoutParameters.setWidget(
            10, QtWidgets.QFormLayout.LabelRole, self.lab_mac
        )
        self.lE_mac = QtWidgets.QLineEdit(self.toolBox_4Page1)
        self.lE_mac.setEnabled(False)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.lE_mac.sizePolicy().hasHeightForWidth())
        self.lE_mac.setSizePolicy(sizePolicy)
        self.lE_mac.setObjectName("lE_mac")
        self.LayoutParameters.setWidget(
            10, QtWidgets.QFormLayout.FieldRole, self.lE_mac
        )
        self.chB_dhcp = QtWidgets.QCheckBox(self.toolBox_4Page1)
        self.chB_dhcp.setEnabled(False)
        self.chB_dhcp.setChecked(False)
        self.chB_dhcp.setObjectName("chB_dhcp")
        self.LayoutParameters.setWidget(
            11, QtWidgets.QFormLayout.FieldRole, self.chB_dhcp
        )
        self.lab_output_config = QtWidgets.QLabel(self.toolBox_4Page1)
        self.lab_output_config.setObjectName("lab_output_config")
        self.LayoutParameters.setWidget(
            12, QtWidgets.QFormLayout.LabelRole, self.lab_output_config
        )
        self.chB_exc_stamp = QtWidgets.QCheckBox(self.toolBox_4Page1)
        self.chB_exc_stamp.setEnabled(False)
        self.chB_exc_stamp.setChecked(True)
        self.chB_exc_stamp.setObjectName("chB_exc_stamp")
        self.LayoutParameters.setWidget(
            12, QtWidgets.QFormLayout.FieldRole, self.chB_exc_stamp
        )
        self.chB_current_stamp = QtWidgets.QCheckBox(self.toolBox_4Page1)
        self.chB_current_stamp.setEnabled(False)
        self.chB_current_stamp.setChecked(True)
        self.chB_current_stamp.setObjectName("chB_current_stamp")
        self.LayoutParameters.setWidget(
            13, QtWidgets.QFormLayout.FieldRole, self.chB_current_stamp
        )
        self.chB_time_stamp = QtWidgets.QCheckBox(self.toolBox_4Page1)
        self.chB_time_stamp.setEnabled(False)
        self.chB_time_stamp.setChecked(True)
        self.chB_time_stamp.setObjectName("chB_time_stamp")
        self.LayoutParameters.setWidget(
            14, QtWidgets.QFormLayout.FieldRole, self.chB_time_stamp
        )
        self.horizontalLayout_7.addLayout(self.LayoutParameters)
        self.groupBox = QtWidgets.QGroupBox(self.toolBox_4Page1)
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout_20 = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout_20.setObjectName("verticalLayout_20")
        self.tabWidget = QtWidgets.QTabWidget(self.groupBox)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
        self.tabWidget.setSizePolicy(sizePolicy)
        self.tabWidget.setObjectName("tabWidget")
        self.tab_exc_model = QtWidgets.QWidget()
        self.tab_exc_model.setObjectName("tab_exc_model")
        self.verticalLayout_18 = QtWidgets.QVBoxLayout(self.tab_exc_model)
        self.verticalLayout_18.setObjectName("verticalLayout_18")
        self.tw_exc_mat_model = QtWidgets.QTableWidget(self.tab_exc_model)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.tw_exc_mat_model.sizePolicy().hasHeightForWidth()
        )
        self.tw_exc_mat_model.setSizePolicy(sizePolicy)
        self.tw_exc_mat_model.setObjectName("tw_exc_mat_model")
        self.tw_exc_mat_model.setColumnCount(2)
        self.tw_exc_mat_model.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.tw_exc_mat_model.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tw_exc_mat_model.setHorizontalHeaderItem(1, item)
        self.tw_exc_mat_model.horizontalHeader().setDefaultSectionSize(40)
        self.verticalLayout_18.addWidget(self.tw_exc_mat_model)
        self.tabWidget.addTab(self.tab_exc_model, "")
        self.tab_exc_chip = QtWidgets.QWidget()
        self.tab_exc_chip.setObjectName("tab_exc_chip")
        self.verticalLayout_19 = QtWidgets.QVBoxLayout(self.tab_exc_chip)
        self.verticalLayout_19.setObjectName("verticalLayout_19")
        self.tw_exc_mat_chip = QtWidgets.QTableWidget(self.tab_exc_chip)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.tw_exc_mat_chip.sizePolicy().hasHeightForWidth()
        )
        self.tw_exc_mat_chip.setSizePolicy(sizePolicy)
        self.tw_exc_mat_chip.setObjectName("tw_exc_mat_chip")
        self.tw_exc_mat_chip.setColumnCount(2)
        self.tw_exc_mat_chip.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.tw_exc_mat_chip.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.tw_exc_mat_chip.setHorizontalHeaderItem(1, item)
        self.tw_exc_mat_chip.horizontalHeader().setDefaultSectionSize(40)
        self.verticalLayout_19.addWidget(self.tw_exc_mat_chip)
        self.tabWidget.addTab(self.tab_exc_chip, "")
        self.verticalLayout_20.addWidget(self.tabWidget)
        self.horizontalLayout_7.addWidget(self.groupBox)
        self.verticalLayout_12.addLayout(self.horizontalLayout_7)
        self.horizontalLayout_8 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        self.lab_chip = QtWidgets.QLabel(self.toolBox_4Page1)
        self.lab_chip.setObjectName("lab_chip")
        self.horizontalLayout_8.addWidget(self.lab_chip)
        self.cB_chip_ctlg = QtWidgets.QComboBox(self.toolBox_4Page1)
        self.cB_chip_ctlg.setEditable(False)
        self.cB_chip_ctlg.setMaxVisibleItems(2)
        self.cB_chip_ctlg.setObjectName("cB_chip_ctlg")
        self.horizontalLayout_8.addWidget(self.cB_chip_ctlg)
        self.pB_chip_refresh_ctlg = QtWidgets.QPushButton(self.toolBox_4Page1)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.pB_chip_refresh_ctlg.sizePolicy().hasHeightForWidth()
        )
        self.pB_chip_refresh_ctlg.setSizePolicy(sizePolicy)
        self.pB_chip_refresh_ctlg.setAutoFillBackground(False)
        self.pB_chip_refresh_ctlg.setObjectName("pB_chip_refresh_ctlg")
        self.horizontalLayout_8.addWidget(self.pB_chip_refresh_ctlg)
        self.horizontalLayout_8.setStretch(0, 1)
        self.horizontalLayout_8.setStretch(1, 4)
        self.horizontalLayout_8.setStretch(2, 1)
        self.verticalLayout_12.addLayout(self.horizontalLayout_8)
        self.horizontalLayout_9 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        self.pB_load_setup = QtWidgets.QPushButton(self.toolBox_4Page1)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.pB_load_setup.sizePolicy().hasHeightForWidth()
        )
        self.pB_load_setup.setSizePolicy(sizePolicy)
        self.pB_load_setup.setMinimumSize(QtCore.QSize(0, 23))
        self.pB_load_setup.setAutoFillBackground(False)
        self.pB_load_setup.setObjectName("pB_load_setup")
        self.horizontalLayout_9.addWidget(self.pB_load_setup)
        self.pB_save_setup = QtWidgets.QPushButton(self.toolBox_4Page1)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.pB_save_setup.sizePolicy().hasHeightForWidth()
        )
        self.pB_save_setup.setSizePolicy(sizePolicy)
        self.pB_save_setup.setMinimumSize(QtCore.QSize(0, 23))
        self.pB_save_setup.setAutoFillBackground(False)
        self.pB_save_setup.setObjectName("pB_save_setup")
        self.horizontalLayout_9.addWidget(self.pB_save_setup)
        self.verticalLayout_12.addLayout(self.horizontalLayout_9)
        self.toolBox_4.addItem(self.toolBox_4Page1, "")
        self.verticalLayout.addWidget(self.toolBox_4)
        spacerItem = QtWidgets.QSpacerItem(
            20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding
        )
        self.verticalLayout.addItem(spacerItem)
        self.verticalLayout.setStretch(1, 1)
        self.tabW_settings.addTab(self.tab_device, "")
        self.tab_measurements = QtWidgets.QWidget()
        self.tab_measurements.setObjectName("tab_measurements")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.tab_measurements)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.toolBox = QtWidgets.QToolBox(self.tab_measurements)
        self.toolBox.setObjectName("toolBox")
        self.Acquisition = QtWidgets.QWidget()
        self.Acquisition.setGeometry(QtCore.QRect(0, 0, 406, 169))
        self.Acquisition.setObjectName("Acquisition")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout(self.Acquisition)
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.pB_start_meas = QtWidgets.QPushButton(self.Acquisition)
        self.pB_start_meas.setAutoFillBackground(False)
        self.pB_start_meas.setObjectName("pB_start_meas")
        self.horizontalLayout_4.addWidget(self.pB_start_meas)
        self.pB_stop_meas = QtWidgets.QPushButton(self.Acquisition)
        self.pB_stop_meas.setAutoFillBackground(False)
        self.pB_stop_meas.setObjectName("pB_stop_meas")
        self.horizontalLayout_4.addWidget(self.pB_stop_meas)
        self.lab_live_meas_status = QtWidgets.QLabel(self.Acquisition)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Maximum
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.lab_live_meas_status.sizePolicy().hasHeightForWidth()
        )
        self.lab_live_meas_status.setSizePolicy(sizePolicy)
        self.lab_live_meas_status.setMinimumSize(QtCore.QSize(0, 23))
        self.lab_live_meas_status.setAutoFillBackground(True)
        self.lab_live_meas_status.setAlignment(QtCore.Qt.AlignCenter)
        self.lab_live_meas_status.setObjectName("lab_live_meas_status")
        self.horizontalLayout_4.addWidget(self.lab_live_meas_status)
        self.verticalLayout_4.addLayout(self.horizontalLayout_4)
        self.lE_meas_dataset_dir = QtWidgets.QLineEdit(self.Acquisition)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.lE_meas_dataset_dir.sizePolicy().hasHeightForWidth()
        )
        self.lE_meas_dataset_dir.setSizePolicy(sizePolicy)
        self.lE_meas_dataset_dir.setObjectName("lE_meas_dataset_dir")
        self.verticalLayout_4.addWidget(self.lE_meas_dataset_dir)
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.chB_dataset_autosave = QtWidgets.QCheckBox(self.Acquisition)
        self.chB_dataset_autosave.setChecked(True)
        self.chB_dataset_autosave.setObjectName("chB_dataset_autosave")
        self.horizontalLayout_6.addWidget(self.chB_dataset_autosave)
        self.chB_dataset_save_img = QtWidgets.QCheckBox(self.Acquisition)
        self.chB_dataset_save_img.setChecked(True)
        self.chB_dataset_save_img.setObjectName("chB_dataset_save_img")
        self.horizontalLayout_6.addWidget(self.chB_dataset_save_img)
        self.chB_load_after_meas = QtWidgets.QCheckBox(self.Acquisition)
        self.chB_load_after_meas.setChecked(True)
        self.chB_load_after_meas.setObjectName("chB_load_after_meas")
        self.horizontalLayout_6.addWidget(self.chB_load_after_meas)
        self.verticalLayout_4.addLayout(self.horizontalLayout_6)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.lab_actual_frame_cnt = QtWidgets.QLabel(self.Acquisition)
        self.lab_actual_frame_cnt.setObjectName("lab_actual_frame_cnt")
        self.horizontalLayout_5.addWidget(self.lab_actual_frame_cnt)
        self.sB_actual_frame_cnt = QtWidgets.QSpinBox(self.Acquisition)
        self.sB_actual_frame_cnt.setEnabled(True)
        self.sB_actual_frame_cnt.setFrame(True)
        self.sB_actual_frame_cnt.setAlignment(
            QtCore.Qt.AlignLeading | QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
        )
        self.sB_actual_frame_cnt.setMaximum(999)
        self.sB_actual_frame_cnt.setObjectName("sB_actual_frame_cnt")
        self.horizontalLayout_5.addWidget(self.sB_actual_frame_cnt)
        self.meas_progress_bar = QtWidgets.QProgressBar(self.Acquisition)
        self.meas_progress_bar.setProperty("value", 0)
        self.meas_progress_bar.setOrientation(QtCore.Qt.Horizontal)
        self.meas_progress_bar.setObjectName("meas_progress_bar")
        self.horizontalLayout_5.addWidget(self.meas_progress_bar)
        self.verticalLayout_4.addLayout(self.horizontalLayout_5)
        self.toolBox.addItem(self.Acquisition, "")
        self.Replay = QtWidgets.QWidget()
        self.Replay.setGeometry(QtCore.QRect(0, 0, 307, 242))
        self.Replay.setObjectName("Replay")
        self.verticalLayout_11 = QtWidgets.QVBoxLayout(self.Replay)
        self.verticalLayout_11.setObjectName("verticalLayout_11")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.pB_meas_dataset_load = QtWidgets.QPushButton(self.Replay)
        self.pB_meas_dataset_load.setAutoFillBackground(False)
        self.pB_meas_dataset_load.setObjectName("pB_meas_dataset_load")
        self.horizontalLayout_2.addWidget(self.pB_meas_dataset_load)
        self.lab_replay_status = QtWidgets.QLabel(self.Replay)
        self.lab_replay_status.setAutoFillBackground(True)
        self.lab_replay_status.setAlignment(QtCore.Qt.AlignCenter)
        self.lab_replay_status.setObjectName("lab_replay_status")
        self.horizontalLayout_2.addWidget(self.lab_replay_status)
        self.verticalLayout_11.addLayout(self.horizontalLayout_2)
        self.tE_load_dataset_dir = QtWidgets.QTextEdit(self.Replay)
        self.tE_load_dataset_dir.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.tE_load_dataset_dir.sizePolicy().hasHeightForWidth()
        )
        self.tE_load_dataset_dir.setSizePolicy(sizePolicy)
        self.tE_load_dataset_dir.setMaximumSize(QtCore.QSize(16777215, 116))
        self.tE_load_dataset_dir.setObjectName("tE_load_dataset_dir")
        self.verticalLayout_11.addWidget(self.tE_load_dataset_dir)
        self.splitter = QtWidgets.QSplitter(self.Replay)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.pB_replay_begin = QtWidgets.QPushButton(self.splitter)
        self.pB_replay_begin.setAutoFillBackground(False)
        self.pB_replay_begin.setText("")
        icon1 = QtGui.QIcon()
        icon1.addPixmap(
            QtGui.QPixmap(":/icons/icons/icon_begin.png"),
            QtGui.QIcon.Normal,
            QtGui.QIcon.Off,
        )
        self.pB_replay_begin.setIcon(icon1)
        self.pB_replay_begin.setIconSize(QtCore.QSize(32, 16))
        self.pB_replay_begin.setCheckable(False)
        self.pB_replay_begin.setChecked(False)
        self.pB_replay_begin.setAutoDefault(False)
        self.pB_replay_begin.setFlat(False)
        self.pB_replay_begin.setObjectName("pB_replay_begin")
        self.pB_replay_back = QtWidgets.QPushButton(self.splitter)
        self.pB_replay_back.setAutoFillBackground(False)
        self.pB_replay_back.setText("")
        icon2 = QtGui.QIcon()
        icon2.addPixmap(
            QtGui.QPixmap(":/icons/icons/icon_back.png"),
            QtGui.QIcon.Normal,
            QtGui.QIcon.Off,
        )
        self.pB_replay_back.setIcon(icon2)
        self.pB_replay_back.setIconSize(QtCore.QSize(32, 16))
        self.pB_replay_back.setCheckable(False)
        self.pB_replay_back.setAutoDefault(False)
        self.pB_replay_back.setFlat(False)
        self.pB_replay_back.setObjectName("pB_replay_back")
        self.pB_replay_play = QtWidgets.QPushButton(self.splitter)
        self.pB_replay_play.setAutoFillBackground(False)
        self.pB_replay_play.setText("")
        icon3 = QtGui.QIcon()
        icon3.addPixmap(
            QtGui.QPixmap(":/icons/icons/icon_play.png"),
            QtGui.QIcon.Normal,
            QtGui.QIcon.Off,
        )
        self.pB_replay_play.setIcon(icon3)
        self.pB_replay_play.setIconSize(QtCore.QSize(32, 16))
        self.pB_replay_play.setCheckable(False)
        self.pB_replay_play.setAutoDefault(False)
        self.pB_replay_play.setFlat(False)
        self.pB_replay_play.setObjectName("pB_replay_play")
        self.pB_replay_next = QtWidgets.QPushButton(self.splitter)
        self.pB_replay_next.setAutoFillBackground(False)
        self.pB_replay_next.setText("")
        icon4 = QtGui.QIcon()
        icon4.addPixmap(
            QtGui.QPixmap(":/icons/icons/icon_next.png"),
            QtGui.QIcon.Normal,
            QtGui.QIcon.Off,
        )
        self.pB_replay_next.setIcon(icon4)
        self.pB_replay_next.setIconSize(QtCore.QSize(32, 16))
        self.pB_replay_next.setCheckable(False)
        self.pB_replay_next.setAutoDefault(False)
        self.pB_replay_next.setFlat(False)
        self.pB_replay_next.setObjectName("pB_replay_next")
        self.pB_replay_end = QtWidgets.QPushButton(self.splitter)
        self.pB_replay_end.setAutoFillBackground(False)
        self.pB_replay_end.setText("")
        icon5 = QtGui.QIcon()
        icon5.addPixmap(
            QtGui.QPixmap(":/icons/icons/icon_end.png"),
            QtGui.QIcon.Normal,
            QtGui.QIcon.Off,
        )
        self.pB_replay_end.setIcon(icon5)
        self.pB_replay_end.setIconSize(QtCore.QSize(32, 16))
        self.pB_replay_end.setAutoDefault(False)
        self.pB_replay_end.setFlat(False)
        self.pB_replay_end.setObjectName("pB_replay_end")
        self.pB_replay_stop = QtWidgets.QPushButton(self.splitter)
        self.pB_replay_stop.setAutoFillBackground(False)
        self.pB_replay_stop.setText("")
        icon6 = QtGui.QIcon()
        icon6.addPixmap(
            QtGui.QPixmap(":/icons/icons/icon_stop.png"),
            QtGui.QIcon.Normal,
            QtGui.QIcon.Off,
        )
        self.pB_replay_stop.setIcon(icon6)
        self.pB_replay_stop.setIconSize(QtCore.QSize(32, 16))
        self.pB_replay_stop.setAutoDefault(False)
        self.pB_replay_stop.setFlat(False)
        self.pB_replay_stop.setObjectName("pB_replay_stop")
        self.verticalLayout_11.addWidget(self.splitter)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.lab_current_frame_indx = QtWidgets.QLabel(self.Replay)
        self.lab_current_frame_indx.setObjectName("lab_current_frame_indx")
        self.horizontalLayout_3.addWidget(self.lab_current_frame_indx)
        self.cB_replay_frame_idx = QtWidgets.QComboBox(self.Replay)
        self.cB_replay_frame_idx.setObjectName("cB_replay_frame_idx")
        self.horizontalLayout_3.addWidget(self.cB_replay_frame_idx)
        self.lab_replay_time_2 = QtWidgets.QLabel(self.Replay)
        self.lab_replay_time_2.setObjectName("lab_replay_time_2")
        self.horizontalLayout_3.addWidget(self.lab_replay_time_2)
        self.sB_replay_time = QtWidgets.QDoubleSpinBox(self.Replay)
        self.sB_replay_time.setDecimals(1)
        self.sB_replay_time.setMinimum(0.1)
        self.sB_replay_time.setMaximum(10.0)
        self.sB_replay_time.setSingleStep(0.1)
        self.sB_replay_time.setProperty("value", 1.0)
        self.sB_replay_time.setObjectName("sB_replay_time")
        self.horizontalLayout_3.addWidget(self.sB_replay_time)
        self.verticalLayout_11.addLayout(self.horizontalLayout_3)
        self.slider_replay = QtWidgets.QSlider(self.Replay)
        self.slider_replay.setOrientation(QtCore.Qt.Horizontal)
        self.slider_replay.setTickPosition(QtWidgets.QSlider.TicksAbove)
        self.slider_replay.setTickInterval(0)
        self.slider_replay.setObjectName("slider_replay")
        self.verticalLayout_11.addWidget(self.slider_replay)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.pB_export_meas_csv = QtWidgets.QPushButton(self.Replay)
        self.pB_export_meas_csv.setAutoFillBackground(False)
        self.pB_export_meas_csv.setObjectName("pB_export_meas_csv")
        self.horizontalLayout.addWidget(self.pB_export_meas_csv)
        self.pB_load_ref_dataset = QtWidgets.QPushButton(self.Replay)
        self.pB_load_ref_dataset.setAutoFillBackground(False)
        self.pB_load_ref_dataset.setObjectName("pB_load_ref_dataset")
        self.horizontalLayout.addWidget(self.pB_load_ref_dataset)
        self.verticalLayout_11.addLayout(self.horizontalLayout)
        self.toolBox.addItem(self.Replay, "")
        self.verticalLayout_2.addWidget(self.toolBox)
        self.groupBox_2 = QtWidgets.QGroupBox(self.tab_measurements)
        self.groupBox_2.setObjectName("groupBox_2")
        self.gridLayout_16 = QtWidgets.QGridLayout(self.groupBox_2)
        self.gridLayout_16.setObjectName("gridLayout_16")
        self.tE_frame_info = QtWidgets.QTextEdit(self.groupBox_2)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.tE_frame_info.sizePolicy().hasHeightForWidth()
        )
        self.tE_frame_info.setSizePolicy(sizePolicy)
        self.tE_frame_info.setObjectName("tE_frame_info")
        self.gridLayout_16.addWidget(self.tE_frame_info, 0, 0, 1, 1)
        self.verticalLayout_2.addWidget(self.groupBox_2)
        self.gridLayout_14 = QtWidgets.QGridLayout()
        self.gridLayout_14.setObjectName("gridLayout_14")
        self.sB_eidors_factor = QtWidgets.QDoubleSpinBox(self.tab_measurements)
        self.sB_eidors_factor.setAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter
        )
        self.sB_eidors_factor.setSuffix("")
        self.sB_eidors_factor.setDecimals(3)
        self.sB_eidors_factor.setMinimum(-1000000.0)
        self.sB_eidors_factor.setMaximum(1000000.0)
        self.sB_eidors_factor.setSingleStep(0.1)
        self.sB_eidors_factor.setProperty("value", 1.0)
        self.sB_eidors_factor.setObjectName("sB_eidors_factor")
        self.gridLayout_14.addWidget(self.sB_eidors_factor, 0, 1, 1, 1)
        self.pB_export_data_meas_vs_eidors = QtWidgets.QPushButton(
            self.tab_measurements
        )
        self.pB_export_data_meas_vs_eidors.setAutoFillBackground(False)
        self.pB_export_data_meas_vs_eidors.setObjectName(
            "pB_export_data_meas_vs_eidors"
        )
        self.gridLayout_14.addWidget(self.pB_export_data_meas_vs_eidors, 1, 0, 1, 1)
        self.pB_load_eidors_fwd_solution = QtWidgets.QPushButton(self.tab_measurements)
        self.pB_load_eidors_fwd_solution.setAutoFillBackground(False)
        self.pB_load_eidors_fwd_solution.setObjectName("pB_load_eidors_fwd_solution")
        self.gridLayout_14.addWidget(self.pB_load_eidors_fwd_solution, 0, 0, 1, 1)
        self.verticalLayout_2.addLayout(self.gridLayout_14)
        spacerItem1 = QtWidgets.QSpacerItem(
            20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding
        )
        self.verticalLayout_2.addItem(spacerItem1)
        self.tabW_settings.addTab(self.tab_measurements, "")
        self.tab_eit = QtWidgets.QWidget()
        self.tab_eit.setObjectName("tab_eit")
        self.verticalLayout_10 = QtWidgets.QVBoxLayout(self.tab_eit)
        self.verticalLayout_10.setObjectName("verticalLayout_10")
        self.pB_compute = QtWidgets.QPushButton(self.tab_eit)
        self.pB_compute.setAutoFillBackground(False)
        self.pB_compute.setObjectName("pB_compute")
        self.verticalLayout_10.addWidget(self.pB_compute)
        self.groupBox_9 = QtWidgets.QGroupBox(self.tab_eit)
        self.groupBox_9.setObjectName("groupBox_9")
        self.verticalLayout_8 = QtWidgets.QVBoxLayout(self.groupBox_9)
        self.verticalLayout_8.setObjectName("verticalLayout_8")
        self.horizontalLayout_12 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_12.setObjectName("horizontalLayout_12")
        self.lab_eit_mdl_ctlg = QtWidgets.QLabel(self.groupBox_9)
        self.lab_eit_mdl_ctlg.setObjectName("lab_eit_mdl_ctlg")
        self.horizontalLayout_12.addWidget(self.lab_eit_mdl_ctlg)
        self.cB_eit_mdl_ctlg = QtWidgets.QComboBox(self.groupBox_9)
        self.cB_eit_mdl_ctlg.setCurrentText("")
        self.cB_eit_mdl_ctlg.setObjectName("cB_eit_mdl_ctlg")
        self.horizontalLayout_12.addWidget(self.cB_eit_mdl_ctlg)
        self.pB_eit_mdl_refresh_ctlg = QtWidgets.QPushButton(self.groupBox_9)
        self.pB_eit_mdl_refresh_ctlg.setAutoFillBackground(False)
        self.pB_eit_mdl_refresh_ctlg.setObjectName("pB_eit_mdl_refresh_ctlg")
        self.horizontalLayout_12.addWidget(self.pB_eit_mdl_refresh_ctlg)
        self.horizontalLayout_12.setStretch(0, 1)
        self.horizontalLayout_12.setStretch(1, 4)
        self.horizontalLayout_12.setStretch(2, 1)
        self.verticalLayout_8.addLayout(self.horizontalLayout_12)
        self.formLayout_2 = QtWidgets.QFormLayout()
        self.formLayout_2.setObjectName("formLayout_2")
        self.label_FEMRefinement = QtWidgets.QLabel(self.groupBox_9)
        self.label_FEMRefinement.setObjectName("label_FEMRefinement")
        self.formLayout_2.setWidget(
            1, QtWidgets.QFormLayout.LabelRole, self.label_FEMRefinement
        )
        self.sBd_eit_model_fem_refinement = QtWidgets.QDoubleSpinBox(self.groupBox_9)
        self.sBd_eit_model_fem_refinement.setDecimals(4)
        self.sBd_eit_model_fem_refinement.setMinimum(0.0)
        self.sBd_eit_model_fem_refinement.setMaximum(10.0)
        self.sBd_eit_model_fem_refinement.setSingleStep(0.001)
        self.sBd_eit_model_fem_refinement.setProperty("value", 0.5)
        self.sBd_eit_model_fem_refinement.setObjectName("sBd_eit_model_fem_refinement")
        self.formLayout_2.setWidget(
            1, QtWidgets.QFormLayout.FieldRole, self.sBd_eit_model_fem_refinement
        )
        self.lE_eit_model_name = QtWidgets.QLineEdit(self.groupBox_9)
        self.lE_eit_model_name.setEnabled(True)
        self.lE_eit_model_name.setFrame(True)
        self.lE_eit_model_name.setReadOnly(True)
        self.lE_eit_model_name.setObjectName("lE_eit_model_name")
        self.formLayout_2.setWidget(
            0, QtWidgets.QFormLayout.FieldRole, self.lE_eit_model_name
        )
        self.label_eit_model_name = QtWidgets.QLabel(self.groupBox_9)
        self.label_eit_model_name.setObjectName("label_eit_model_name")
        self.formLayout_2.setWidget(
            0, QtWidgets.QFormLayout.LabelRole, self.label_eit_model_name
        )
        self.chB_eit_mdl_normalize = QtWidgets.QCheckBox(self.groupBox_9)
        self.chB_eit_mdl_normalize.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.chB_eit_mdl_normalize.setInputMethodHints(QtCore.Qt.ImhSensitiveData)
        self.chB_eit_mdl_normalize.setObjectName("chB_eit_mdl_normalize")
        self.formLayout_2.setWidget(
            2, QtWidgets.QFormLayout.FieldRole, self.chB_eit_mdl_normalize
        )
        self.verticalLayout_8.addLayout(self.formLayout_2)
        self.verticalLayout_10.addWidget(self.groupBox_9)
        self.groupBox_8 = QtWidgets.QGroupBox(self.tab_eit)
        self.groupBox_8.setObjectName("groupBox_8")
        self.verticalLayout_7 = QtWidgets.QVBoxLayout(self.groupBox_8)
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.pB_set_reconstruction = QtWidgets.QPushButton(self.groupBox_8)
        self.pB_set_reconstruction.setAutoFillBackground(False)
        self.pB_set_reconstruction.setObjectName("pB_set_reconstruction")
        self.verticalLayout_7.addWidget(self.pB_set_reconstruction)
        self.tabW_reconstruction = QtWidgets.QTabWidget(self.groupBox_8)
        self.tabW_reconstruction.setObjectName("tabW_reconstruction")
        self.tab_pyeit = QtWidgets.QWidget()
        self.tab_pyeit.setObjectName("tab_pyeit")
        self.gridLayout_9 = QtWidgets.QGridLayout(self.tab_pyeit)
        self.gridLayout_9.setObjectName("gridLayout_9")
        self.groupBox_6 = QtWidgets.QGroupBox(self.tab_pyeit)
        self.groupBox_6.setObjectName("groupBox_6")
        self.verticalLayout_6 = QtWidgets.QVBoxLayout(self.groupBox_6)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.lab_solver = QtWidgets.QLabel(self.groupBox_6)
        self.lab_solver.setObjectName("lab_solver")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.lab_solver)
        self.cB_pyeit_solver = QtWidgets.QComboBox(self.groupBox_6)
        self.cB_pyeit_solver.setObjectName("cB_pyeit_solver")
        self.formLayout.setWidget(
            0, QtWidgets.QFormLayout.FieldRole, self.cB_pyeit_solver
        )
        self.label_vmax_7 = QtWidgets.QLabel(self.groupBox_6)
        self.label_vmax_7.setObjectName("label_vmax_7")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_vmax_7)
        self.sBd_pyeit_p = QtWidgets.QDoubleSpinBox(self.groupBox_6)
        self.sBd_pyeit_p.setDecimals(1)
        self.sBd_pyeit_p.setMinimum(-1000000000000000.0)
        self.sBd_pyeit_p.setMaximum(1000000000000000.0)
        self.sBd_pyeit_p.setProperty("value", 0.5)
        self.sBd_pyeit_p.setObjectName("sBd_pyeit_p")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.sBd_pyeit_p)
        self.label_vmax_8 = QtWidgets.QLabel(self.groupBox_6)
        self.label_vmax_8.setObjectName("label_vmax_8")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.label_vmax_8)
        self.sBd_pyeit_lamda = QtWidgets.QDoubleSpinBox(self.groupBox_6)
        self.sBd_pyeit_lamda.setDecimals(4)
        self.sBd_pyeit_lamda.setMinimum(-1000000000000000.0)
        self.sBd_pyeit_lamda.setMaximum(1000000000000000.0)
        self.sBd_pyeit_lamda.setProperty("value", 0.01)
        self.sBd_pyeit_lamda.setObjectName("sBd_pyeit_lamda")
        self.formLayout.setWidget(
            2, QtWidgets.QFormLayout.FieldRole, self.sBd_pyeit_lamda
        )
        self.label_vmax_9 = QtWidgets.QLabel(self.groupBox_6)
        self.label_vmax_9.setObjectName("label_vmax_9")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.label_vmax_9)
        self.sBd_pyeit_greit_n = QtWidgets.QDoubleSpinBox(self.groupBox_6)
        self.sBd_pyeit_greit_n.setDecimals(0)
        self.sBd_pyeit_greit_n.setMinimum(-1000000000000000.0)
        self.sBd_pyeit_greit_n.setMaximum(1000000000000000.0)
        self.sBd_pyeit_greit_n.setProperty("value", 64.0)
        self.sBd_pyeit_greit_n.setObjectName("sBd_pyeit_greit_n")
        self.formLayout.setWidget(
            3, QtWidgets.QFormLayout.FieldRole, self.sBd_pyeit_greit_n
        )
        self.label_FEMRefinement_2 = QtWidgets.QLabel(self.groupBox_6)
        self.label_FEMRefinement_2.setObjectName("label_FEMRefinement_2")
        self.formLayout.setWidget(
            4, QtWidgets.QFormLayout.LabelRole, self.label_FEMRefinement_2
        )
        self.sBd_pyeit_bckgrnd = QtWidgets.QDoubleSpinBox(self.groupBox_6)
        self.sBd_pyeit_bckgrnd.setDecimals(4)
        self.sBd_pyeit_bckgrnd.setMaximum(1000.0)
        self.sBd_pyeit_bckgrnd.setSingleStep(0.001)
        self.sBd_pyeit_bckgrnd.setProperty("value", 0.1)
        self.sBd_pyeit_bckgrnd.setObjectName("sBd_pyeit_bckgrnd")
        self.formLayout.setWidget(
            4, QtWidgets.QFormLayout.FieldRole, self.sBd_pyeit_bckgrnd
        )
        self.verticalLayout_6.addLayout(self.formLayout)
        self.gridLayout_9.addWidget(self.groupBox_6, 0, 0, 1, 1)
        self.tabW_reconstruction.addTab(self.tab_pyeit, "")
        self.tab_nn = QtWidgets.QWidget()
        self.tab_nn.setObjectName("tab_nn")
        self.gridLayout_15 = QtWidgets.QGridLayout(self.tab_nn)
        self.gridLayout_15.setObjectName("gridLayout_15")
        self.lE_ai_model_dir = QtWidgets.QLineEdit(self.tab_nn)
        self.lE_ai_model_dir.setEnabled(False)
        self.lE_ai_model_dir.setObjectName("lE_ai_model_dir")
        self.gridLayout_15.addWidget(self.lE_ai_model_dir, 0, 0, 1, 1)
        self.tabW_reconstruction.addTab(self.tab_nn, "")
        self.verticalLayout_7.addWidget(self.tabW_reconstruction)
        self.verticalLayout_10.addWidget(self.groupBox_8)
        self.groupBox_5 = QtWidgets.QGroupBox(self.tab_eit)
        self.groupBox_5.setObjectName("groupBox_5")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout(self.groupBox_5)
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setVerticalSpacing(2)
        self.gridLayout.setObjectName("gridLayout")
        self.cB_eit_imaging_type = QtWidgets.QComboBox(self.groupBox_5)
        self.cB_eit_imaging_type.setCurrentText("")
        self.cB_eit_imaging_type.setObjectName("cB_eit_imaging_type")
        self.gridLayout.addWidget(self.cB_eit_imaging_type, 0, 0, 1, 5)
        self.cB_eit_imaging_meas_freq = QtWidgets.QComboBox(self.groupBox_5)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.cB_eit_imaging_meas_freq.sizePolicy().hasHeightForWidth()
        )
        self.cB_eit_imaging_meas_freq.setSizePolicy(sizePolicy)
        self.cB_eit_imaging_meas_freq.setMinimumSize(QtCore.QSize(78, 0))
        self.cB_eit_imaging_meas_freq.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.cB_eit_imaging_meas_freq.setObjectName("cB_eit_imaging_meas_freq")
        self.gridLayout.addWidget(self.cB_eit_imaging_meas_freq, 2, 2, 1, 2)
        self.lab_ref_frame_idx = QtWidgets.QLabel(self.groupBox_5)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.lab_ref_frame_idx.sizePolicy().hasHeightForWidth()
        )
        self.lab_ref_frame_idx.setSizePolicy(sizePolicy)
        self.lab_ref_frame_idx.setObjectName("lab_ref_frame_idx")
        self.gridLayout.addWidget(self.lab_ref_frame_idx, 1, 4, 1, 1)
        self.cB_eit_imaging_ref_frame = QtWidgets.QComboBox(self.groupBox_5)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.cB_eit_imaging_ref_frame.sizePolicy().hasHeightForWidth()
        )
        self.cB_eit_imaging_ref_frame.setSizePolicy(sizePolicy)
        self.cB_eit_imaging_ref_frame.setMinimumSize(QtCore.QSize(78, 0))
        self.cB_eit_imaging_ref_frame.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.cB_eit_imaging_ref_frame.setObjectName("cB_eit_imaging_ref_frame")
        self.gridLayout.addWidget(self.cB_eit_imaging_ref_frame, 2, 4, 1, 1)
        self.lab_freq_meas_0 = QtWidgets.QLabel(self.groupBox_5)
        self.lab_freq_meas_0.setObjectName("lab_freq_meas_0")
        self.gridLayout.addWidget(self.lab_freq_meas_0, 1, 0, 1, 2)
        self.lab_freq_meas_1 = QtWidgets.QLabel(self.groupBox_5)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.lab_freq_meas_1.sizePolicy().hasHeightForWidth()
        )
        self.lab_freq_meas_1.setSizePolicy(sizePolicy)
        self.lab_freq_meas_1.setObjectName("lab_freq_meas_1")
        self.gridLayout.addWidget(self.lab_freq_meas_1, 1, 2, 1, 2)
        self.cB_eit_imaging_ref_freq = QtWidgets.QComboBox(self.groupBox_5)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.cB_eit_imaging_ref_freq.sizePolicy().hasHeightForWidth()
        )
        self.cB_eit_imaging_ref_freq.setSizePolicy(sizePolicy)
        self.cB_eit_imaging_ref_freq.setCurrentText("")
        self.cB_eit_imaging_ref_freq.setObjectName("cB_eit_imaging_ref_freq")
        self.gridLayout.addWidget(self.cB_eit_imaging_ref_freq, 2, 0, 1, 2)
        self.verticalLayout_5.addLayout(self.gridLayout)
        self.verticalLayout_15 = QtWidgets.QVBoxLayout()
        self.verticalLayout_15.setObjectName("verticalLayout_15")
        self.cB_eit_imaging_trans = QtWidgets.QComboBox(self.groupBox_5)
        self.cB_eit_imaging_trans.setCurrentText("")
        self.cB_eit_imaging_trans.setObjectName("cB_eit_imaging_trans")
        self.verticalLayout_15.addWidget(self.cB_eit_imaging_trans)
        self.chB_eit_imaging_trans_abs = QtWidgets.QCheckBox(self.groupBox_5)
        self.chB_eit_imaging_trans_abs.setObjectName("chB_eit_imaging_trans_abs")
        self.verticalLayout_15.addWidget(self.chB_eit_imaging_trans_abs)
        self.verticalLayout_5.addLayout(self.verticalLayout_15)
        self.verticalLayout_10.addWidget(self.groupBox_5)
        spacerItem2 = QtWidgets.QSpacerItem(
            20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding
        )
        self.verticalLayout_10.addItem(spacerItem2)
        self.tabW_settings.addTab(self.tab_eit, "")
        self.tab_3 = QtWidgets.QWidget()
        self.tab_3.setObjectName("tab_3")
        self.verticalLayout_23 = QtWidgets.QVBoxLayout(self.tab_3)
        self.verticalLayout_23.setObjectName("verticalLayout_23")
        self.pB_pyvista = QtWidgets.QPushButton(self.tab_3)
        self.pB_pyvista.setAutoFillBackground(False)
        self.pB_pyvista.setObjectName("pB_pyvista")
        self.verticalLayout_23.addWidget(self.pB_pyvista)
        self.groupBox_4 = QtWidgets.QGroupBox(self.tab_3)
        self.groupBox_4.setObjectName("groupBox_4")
        self.gridLayout_7 = QtWidgets.QGridLayout(self.groupBox_4)
        self.gridLayout_7.setObjectName("gridLayout_7")
        self.formLayout_5 = QtWidgets.QFormLayout()
        self.formLayout_5.setObjectName("formLayout_5")
        self.label_vmin = QtWidgets.QLabel(self.groupBox_4)
        self.label_vmin.setObjectName("label_vmin")
        self.formLayout_5.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.label_vmin)
        self.scalePlot_vmin = QtWidgets.QDoubleSpinBox(self.groupBox_4)
        self.scalePlot_vmin.setDecimals(4)
        self.scalePlot_vmin.setMinimum(-1000000000000000.0)
        self.scalePlot_vmin.setMaximum(1000000000000000.0)
        self.scalePlot_vmin.setObjectName("scalePlot_vmin")
        self.formLayout_5.setWidget(
            0, QtWidgets.QFormLayout.FieldRole, self.scalePlot_vmin
        )
        self.label_vmax = QtWidgets.QLabel(self.groupBox_4)
        self.label_vmax.setObjectName("label_vmax")
        self.formLayout_5.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.label_vmax)
        self.scalePlot_vmax = QtWidgets.QDoubleSpinBox(self.groupBox_4)
        self.scalePlot_vmax.setDecimals(4)
        self.scalePlot_vmax.setMinimum(-1000000000000000.0)
        self.scalePlot_vmax.setMaximum(1000000000000000.0)
        self.scalePlot_vmax.setObjectName("scalePlot_vmax")
        self.formLayout_5.setWidget(
            1, QtWidgets.QFormLayout.FieldRole, self.scalePlot_vmax
        )
        self.dsB_dpi_rec = QtWidgets.QDoubleSpinBox(self.groupBox_4)
        self.dsB_dpi_rec.setDecimals(1)
        self.dsB_dpi_rec.setMinimum(0.1)
        self.dsB_dpi_rec.setMaximum(200.0)
        self.dsB_dpi_rec.setSingleStep(0.1)
        self.dsB_dpi_rec.setProperty("value", 100.0)
        self.dsB_dpi_rec.setObjectName("dsB_dpi_rec")
        self.formLayout_5.setWidget(
            2, QtWidgets.QFormLayout.FieldRole, self.dsB_dpi_rec
        )
        self.lab_dpi_rec = QtWidgets.QLabel(self.groupBox_4)
        self.lab_dpi_rec.setObjectName("lab_dpi_rec")
        self.formLayout_5.setWidget(
            2, QtWidgets.QFormLayout.LabelRole, self.lab_dpi_rec
        )
        self.pB_set_dpi = QtWidgets.QPushButton(self.groupBox_4)
        self.pB_set_dpi.setObjectName("pB_set_dpi")
        self.formLayout_5.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.pB_set_dpi)
        self.gridLayout_7.addLayout(self.formLayout_5, 0, 0, 1, 1)
        self.verticalLayout_23.addWidget(self.groupBox_4)
        self.groupBox_7 = QtWidgets.QGroupBox(self.tab_3)
        self.groupBox_7.setObjectName("groupBox_7")
        self.verticalLayout_21 = QtWidgets.QVBoxLayout(self.groupBox_7)
        self.verticalLayout_21.setObjectName("verticalLayout_21")
        self.cB_monitoring_trans = QtWidgets.QComboBox(self.groupBox_7)
        self.cB_monitoring_trans.setCurrentText("")
        self.cB_monitoring_trans.setObjectName("cB_monitoring_trans")
        self.verticalLayout_21.addWidget(self.cB_monitoring_trans)
        self.chB_monitoring_trans_abs = QtWidgets.QCheckBox(self.groupBox_7)
        self.chB_monitoring_trans_abs.setObjectName("chB_monitoring_trans_abs")
        self.verticalLayout_21.addWidget(self.chB_monitoring_trans_abs)
        self.verticalLayout_23.addWidget(self.groupBox_7)
        self.tabW_settings.addTab(self.tab_3, "")
        self.tab_6 = QtWidgets.QWidget()
        self.tab_6.setObjectName("tab_6")
        self.verticalLayout_14 = QtWidgets.QVBoxLayout(self.tab_6)
        self.verticalLayout_14.setObjectName("verticalLayout_14")
        self.groupBox_10 = QtWidgets.QGroupBox(self.tab_6)
        self.groupBox_10.setObjectName("groupBox_10")
        self.gridLayout_8 = QtWidgets.QGridLayout(self.groupBox_10)
        self.gridLayout_8.setObjectName("gridLayout_8")
        self.formLayout_4 = QtWidgets.QFormLayout()
        self.formLayout_4.setObjectName("formLayout_4")
        self.lab_measdataset_gdir = QtWidgets.QLabel(self.groupBox_10)
        self.lab_measdataset_gdir.setObjectName("lab_measdataset_gdir")
        self.formLayout_4.setWidget(
            0, QtWidgets.QFormLayout.LabelRole, self.lab_measdataset_gdir
        )
        self.lE_measdataset_gdir = QtWidgets.QLineEdit(self.groupBox_10)
        self.lE_measdataset_gdir.setEnabled(True)
        self.lE_measdataset_gdir.setText("")
        self.lE_measdataset_gdir.setFrame(True)
        self.lE_measdataset_gdir.setReadOnly(True)
        self.lE_measdataset_gdir.setObjectName("lE_measdataset_gdir")
        self.formLayout_4.setWidget(
            0, QtWidgets.QFormLayout.FieldRole, self.lE_measdataset_gdir
        )
        self.lab_snapshot_gdir = QtWidgets.QLabel(self.groupBox_10)
        self.lab_snapshot_gdir.setObjectName("lab_snapshot_gdir")
        self.formLayout_4.setWidget(
            1, QtWidgets.QFormLayout.LabelRole, self.lab_snapshot_gdir
        )
        self.lE_snapshot_gdir = QtWidgets.QLineEdit(self.groupBox_10)
        self.lE_snapshot_gdir.setEnabled(True)
        self.lE_snapshot_gdir.setText("")
        self.lE_snapshot_gdir.setFrame(True)
        self.lE_snapshot_gdir.setReadOnly(True)
        self.lE_snapshot_gdir.setObjectName("lE_snapshot_gdir")
        self.formLayout_4.setWidget(
            1, QtWidgets.QFormLayout.FieldRole, self.lE_snapshot_gdir
        )
        self.lab_export_gdir = QtWidgets.QLabel(self.groupBox_10)
        self.lab_export_gdir.setObjectName("lab_export_gdir")
        self.formLayout_4.setWidget(
            2, QtWidgets.QFormLayout.LabelRole, self.lab_export_gdir
        )
        self.lE_export_gdir = QtWidgets.QLineEdit(self.groupBox_10)
        self.lE_export_gdir.setEnabled(True)
        self.lE_export_gdir.setText("")
        self.lE_export_gdir.setFrame(True)
        self.lE_export_gdir.setReadOnly(True)
        self.lE_export_gdir.setObjectName("lE_export_gdir")
        self.formLayout_4.setWidget(
            2, QtWidgets.QFormLayout.FieldRole, self.lE_export_gdir
        )
        self.lab_eit_mdl_ctlg_gdir = QtWidgets.QLabel(self.groupBox_10)
        self.lab_eit_mdl_ctlg_gdir.setObjectName("lab_eit_mdl_ctlg_gdir")
        self.formLayout_4.setWidget(
            3, QtWidgets.QFormLayout.LabelRole, self.lab_eit_mdl_ctlg_gdir
        )
        self.lE_eit_mdl_ctlg_gdir = QtWidgets.QLineEdit(self.groupBox_10)
        self.lE_eit_mdl_ctlg_gdir.setEnabled(True)
        self.lE_eit_mdl_ctlg_gdir.setText("")
        self.lE_eit_mdl_ctlg_gdir.setFrame(True)
        self.lE_eit_mdl_ctlg_gdir.setReadOnly(True)
        self.lE_eit_mdl_ctlg_gdir.setObjectName("lE_eit_mdl_ctlg_gdir")
        self.formLayout_4.setWidget(
            3, QtWidgets.QFormLayout.FieldRole, self.lE_eit_mdl_ctlg_gdir
        )
        self.lab_chip_ctlg_gdir = QtWidgets.QLabel(self.groupBox_10)
        self.lab_chip_ctlg_gdir.setObjectName("lab_chip_ctlg_gdir")
        self.formLayout_4.setWidget(
            4, QtWidgets.QFormLayout.LabelRole, self.lab_chip_ctlg_gdir
        )
        self.lE_chip_ctlg_gdir = QtWidgets.QLineEdit(self.groupBox_10)
        self.lE_chip_ctlg_gdir.setEnabled(True)
        self.lE_chip_ctlg_gdir.setText("")
        self.lE_chip_ctlg_gdir.setFrame(True)
        self.lE_chip_ctlg_gdir.setReadOnly(True)
        self.lE_chip_ctlg_gdir.setObjectName("lE_chip_ctlg_gdir")
        self.formLayout_4.setWidget(
            4, QtWidgets.QFormLayout.FieldRole, self.lE_chip_ctlg_gdir
        )
        self.gridLayout_8.addLayout(self.formLayout_4, 0, 0, 1, 1)
        self.verticalLayout_14.addWidget(self.groupBox_10)
        spacerItem3 = QtWidgets.QSpacerItem(
            20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding
        )
        self.verticalLayout_14.addItem(spacerItem3)
        self.tabW_settings.addTab(self.tab_6, "")
        self.horizontalLayout_13.addWidget(self.tabW_settings)
        self.verticalLayout_22 = QtWidgets.QVBoxLayout()
        self.verticalLayout_22.setObjectName("verticalLayout_22")
        self.horizontalLayout_16 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_16.setObjectName("horizontalLayout_16")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setObjectName("label")
        self.horizontalLayout_16.addWidget(self.label)
        self.chB_eit_image_plot = QtWidgets.QCheckBox(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.chB_eit_image_plot.sizePolicy().hasHeightForWidth()
        )
        self.chB_eit_image_plot.setSizePolicy(sizePolicy)
        self.chB_eit_image_plot.setChecked(True)
        self.chB_eit_image_plot.setObjectName("chB_eit_image_plot")
        self.horizontalLayout_16.addWidget(self.chB_eit_image_plot)
        self.chB_eit_data_monitoring = QtWidgets.QCheckBox(self.centralwidget)
        self.chB_eit_data_monitoring.setChecked(True)
        self.chB_eit_data_monitoring.setObjectName("chB_eit_data_monitoring")
        self.horizontalLayout_16.addWidget(self.chB_eit_data_monitoring)
        self.verticalLayout_22.addLayout(self.horizontalLayout_16)
        self.tabW_rec = QtWidgets.QTabWidget(self.centralwidget)
        self.tabW_rec.setObjectName("tabW_rec")
        self.tab_5 = QtWidgets.QWidget()
        self.tab_5.setObjectName("tab_5")
        self.gridLayout_6 = QtWidgets.QGridLayout(self.tab_5)
        self.gridLayout_6.setObjectName("gridLayout_6")
        self.layout_rec = QtWidgets.QVBoxLayout()
        self.layout_rec.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.layout_rec.setObjectName("layout_rec")
        self.gridLayout_6.addLayout(self.layout_rec, 0, 0, 1, 1)
        self.tabW_rec.addTab(self.tab_5, "")
        self.verticalLayout_22.addWidget(self.tabW_rec)
        self.tabW_monitoring = QtWidgets.QTabWidget(self.centralwidget)
        self.tabW_monitoring.setObjectName("tabW_monitoring")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.tab)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.layout_Uplot = QtWidgets.QVBoxLayout()
        self.layout_Uplot.setObjectName("layout_Uplot")
        self.gridLayout_3.addLayout(self.layout_Uplot, 0, 0, 1, 1)
        self.tabW_monitoring.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.gridLayout_4 = QtWidgets.QGridLayout(self.tab_2)
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.layout_Uch = QtWidgets.QVBoxLayout()
        self.layout_Uch.setObjectName("layout_Uch")
        self.gridLayout_4.addLayout(self.layout_Uch, 0, 0, 1, 1)
        self.tabW_monitoring.addTab(self.tab_2, "")
        self.tab_4 = QtWidgets.QWidget()
        self.tab_4.setObjectName("tab_4")
        self.gridLayout_5 = QtWidgets.QGridLayout(self.tab_4)
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.layout_error = QtWidgets.QVBoxLayout()
        self.layout_error.setObjectName("layout_error")
        self.gridLayout_5.addLayout(self.layout_error, 0, 0, 1, 1)
        self.tabW_monitoring.addTab(self.tab_4, "")
        self.verticalLayout_22.addWidget(self.tabW_monitoring)
        spacerItem4 = QtWidgets.QSpacerItem(
            20, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding
        )
        self.verticalLayout_22.addItem(spacerItem4)
        self.verticalLayout_22.setStretch(1, 1)
        self.verticalLayout_22.setStretch(2, 1)
        self.horizontalLayout_13.addLayout(self.verticalLayout_22)
        self.groupBox_video = QtWidgets.QGroupBox(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.groupBox_video.sizePolicy().hasHeightForWidth()
        )
        self.groupBox_video.setSizePolicy(sizePolicy)
        self.groupBox_video.setMinimumSize(QtCore.QSize(230, 0))
        self.groupBox_video.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.groupBox_video.setObjectName("groupBox_video")
        self.verticalLayout_9 = QtWidgets.QVBoxLayout(self.groupBox_video)
        self.verticalLayout_9.setObjectName("verticalLayout_9")
        self.cB_capture_devices = QtWidgets.QComboBox(self.groupBox_video)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.cB_capture_devices.sizePolicy().hasHeightForWidth()
        )
        self.cB_capture_devices.setSizePolicy(sizePolicy)
        self.cB_capture_devices.setMinimumSize(QtCore.QSize(125, 23))
        self.cB_capture_devices.setToolTip("")
        self.cB_capture_devices.setEditable(False)
        self.cB_capture_devices.setObjectName("cB_capture_devices")
        self.verticalLayout_9.addWidget(self.cB_capture_devices)
        self.lab_capture_status = QtWidgets.QLabel(self.groupBox_video)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.lab_capture_status.sizePolicy().hasHeightForWidth()
        )
        self.lab_capture_status.setSizePolicy(sizePolicy)
        self.lab_capture_status.setMinimumSize(QtCore.QSize(0, 23))
        self.lab_capture_status.setAutoFillBackground(True)
        self.lab_capture_status.setAlignment(QtCore.Qt.AlignCenter)
        self.lab_capture_status.setObjectName("lab_capture_status")
        self.verticalLayout_9.addWidget(self.lab_capture_status)
        self.gridLayout_2 = QtWidgets.QGridLayout()
        self.gridLayout_2.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.pB_capture_connect = QtWidgets.QPushButton(self.groupBox_video)
        self.pB_capture_connect.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.pB_capture_connect.sizePolicy().hasHeightForWidth()
        )
        self.pB_capture_connect.setSizePolicy(sizePolicy)
        self.pB_capture_connect.setMinimumSize(QtCore.QSize(125, 23))
        self.pB_capture_connect.setAutoFillBackground(False)
        self.pB_capture_connect.setObjectName("pB_capture_connect")
        self.gridLayout_2.addWidget(self.pB_capture_connect, 0, 1, 1, 1)
        self.pB_capture_start_stop = QtWidgets.QPushButton(self.groupBox_video)
        self.pB_capture_start_stop.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.pB_capture_start_stop.sizePolicy().hasHeightForWidth()
        )
        self.pB_capture_start_stop.setSizePolicy(sizePolicy)
        self.pB_capture_start_stop.setMinimumSize(QtCore.QSize(0, 23))
        self.pB_capture_start_stop.setAutoFillBackground(False)
        self.pB_capture_start_stop.setObjectName("pB_capture_start_stop")
        self.gridLayout_2.addWidget(self.pB_capture_start_stop, 1, 1, 1, 1)
        self.verticalLayout_9.addLayout(self.gridLayout_2)
        self.horizontalLayout_14 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_14.setObjectName("horizontalLayout_14")
        self.pB_capture_refresh = QtWidgets.QPushButton(self.groupBox_video)
        self.pB_capture_refresh.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.pB_capture_refresh.sizePolicy().hasHeightForWidth()
        )
        self.pB_capture_refresh.setSizePolicy(sizePolicy)
        self.pB_capture_refresh.setMinimumSize(QtCore.QSize(100, 23))
        self.pB_capture_refresh.setAutoFillBackground(False)
        self.pB_capture_refresh.setObjectName("pB_capture_refresh")
        self.horizontalLayout_14.addWidget(self.pB_capture_refresh)
        self.pB_capture_snapshot = QtWidgets.QPushButton(self.groupBox_video)
        self.pB_capture_snapshot.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.pB_capture_snapshot.sizePolicy().hasHeightForWidth()
        )
        self.pB_capture_snapshot.setSizePolicy(sizePolicy)
        self.pB_capture_snapshot.setMinimumSize(QtCore.QSize(100, 23))
        self.pB_capture_snapshot.setAutoFillBackground(False)
        self.pB_capture_snapshot.setObjectName("pB_capture_snapshot")
        self.horizontalLayout_14.addWidget(self.pB_capture_snapshot)
        self.verticalLayout_9.addLayout(self.horizontalLayout_14)
        self.verticalLayout_16 = QtWidgets.QVBoxLayout()
        self.verticalLayout_16.setObjectName("verticalLayout_16")
        self.video_frame = QtWidgets.QLabel(self.groupBox_video)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.video_frame.sizePolicy().hasHeightForWidth())
        self.video_frame.setSizePolicy(sizePolicy)
        self.video_frame.setCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))
        self.video_frame.setMouseTracking(True)
        self.video_frame.setAutoFillBackground(False)
        self.video_frame.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.video_frame.setFrameShadow(QtWidgets.QFrame.Plain)
        self.video_frame.setAlignment(QtCore.Qt.AlignCenter)
        self.video_frame.setObjectName("video_frame")
        self.verticalLayout_16.addWidget(self.video_frame)
        self.verticalLayout_9.addLayout(self.verticalLayout_16)
        self.lE_path_video_frame = QtWidgets.QLineEdit(self.groupBox_video)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.lE_path_video_frame.sizePolicy().hasHeightForWidth()
        )
        self.lE_path_video_frame.setSizePolicy(sizePolicy)
        self.lE_path_video_frame.setMinimumSize(QtCore.QSize(0, 23))
        self.lE_path_video_frame.setMaximumSize(QtCore.QSize(16777215, 46))
        self.lE_path_video_frame.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.lE_path_video_frame.setAlignment(QtCore.Qt.AlignCenter)
        self.lE_path_video_frame.setReadOnly(True)
        self.lE_path_video_frame.setObjectName("lE_path_video_frame")
        self.verticalLayout_9.addWidget(self.lE_path_video_frame)
        self.horizontalLayout_15 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_15.setObjectName("horizontalLayout_15")
        self.cB_capture_img_size = QtWidgets.QComboBox(self.groupBox_video)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.cB_capture_img_size.sizePolicy().hasHeightForWidth()
        )
        self.cB_capture_img_size.setSizePolicy(sizePolicy)
        self.cB_capture_img_size.setMinimumSize(QtCore.QSize(0, 23))
        self.cB_capture_img_size.setCurrentText("")
        self.cB_capture_img_size.setObjectName("cB_capture_img_size")
        self.horizontalLayout_15.addWidget(self.cB_capture_img_size)
        self.cB_capture_img_file_ext = QtWidgets.QComboBox(self.groupBox_video)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Preferred
        )
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.cB_capture_img_file_ext.sizePolicy().hasHeightForWidth()
        )
        self.cB_capture_img_file_ext.setSizePolicy(sizePolicy)
        self.cB_capture_img_file_ext.setMinimumSize(QtCore.QSize(0, 23))
        self.cB_capture_img_file_ext.setCurrentText("")
        self.cB_capture_img_file_ext.setObjectName("cB_capture_img_file_ext")
        self.horizontalLayout_15.addWidget(self.cB_capture_img_file_ext)
        self.verticalLayout_9.addLayout(self.horizontalLayout_15)
        spacerItem5 = QtWidgets.QSpacerItem(
            20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding
        )
        self.verticalLayout_9.addItem(spacerItem5)
        self.formLayout_3 = QtWidgets.QFormLayout()
        self.formLayout_3.setObjectName("formLayout_3")
        self.cB_log_level = QtWidgets.QComboBox(self.groupBox_video)
        self.cB_log_level.setMinimumSize(QtCore.QSize(0, 23))
        self.cB_log_level.setToolTip("")
        self.cB_log_level.setObjectName("cB_log_level")
        self.formLayout_3.setWidget(
            0, QtWidgets.QFormLayout.FieldRole, self.cB_log_level
        )
        self.lab_log_level = QtWidgets.QLabel(self.groupBox_video)
        self.lab_log_level.setObjectName("lab_log_level")
        self.formLayout_3.setWidget(
            0, QtWidgets.QFormLayout.LabelRole, self.lab_log_level
        )
        self.verticalLayout_9.addLayout(self.formLayout_3)
        self.horizontalLayout_13.addWidget(self.groupBox_video)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1516, 21))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.action_exit = QtWidgets.QAction(MainWindow)
        self.action_exit.setObjectName("action_exit")
        self.menuFile.addAction(self.action_exit)
        self.menubar.addAction(self.menuFile.menuAction())

        self.retranslateUi(MainWindow)
        self.tabW_settings.setCurrentIndex(4)
        self.tabWidget.setCurrentIndex(1)
        self.toolBox.setCurrentIndex(0)
        self.tabW_reconstruction.setCurrentIndex(0)
        self.tabW_rec.setCurrentIndex(0)
        self.tabW_monitoring.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.groupBox_3.setTitle(_translate("MainWindow", "EIT device"))
        self.pB_refresh.setStatusTip(
            _translate(
                "MainWindow", "Refresh the available serial port list (Ctrl + R)"
            )
        )
        self.pB_refresh.setText(_translate("MainWindow", "Refresh"))
        self.pB_refresh.setShortcut(_translate("MainWindow", "Ctrl+R"))
        self.pB_connect.setStatusTip(
            _translate("MainWindow", "Connect to the selected serial port (Shift +C)")
        )
        self.pB_connect.setText(_translate("MainWindow", "Connect"))
        self.pB_connect.setShortcut(_translate("MainWindow", "Shift+C"))
        self.pB_disconnect.setStatusTip(
            _translate("MainWindow", "Disconnect the serial port (Shift + D)")
        )
        self.pB_disconnect.setText(_translate("MainWindow", "Disconnect"))
        self.pB_disconnect.setShortcut(_translate("MainWindow", "Shift+D"))
        self.cB_ports.setStatusTip(
            _translate("MainWindow", "Available serial port list")
        )
        self.lab_device_status.setText(_translate("MainWindow", "Not Connected"))
        self.pB_set_setup.setStatusTip(
            _translate(
                "MainWindow",
                "Send measurements parameters to connected device (Shift +S)",
            )
        )
        self.pB_set_setup.setText(_translate("MainWindow", "Set setup"))
        self.pB_set_setup.setShortcut(_translate("MainWindow", "Shift+S"))
        self.pB_get_setup.setStatusTip(
            _translate(
                "MainWindow",
                "Ask measurements parameters from connected device (Shift +G)",
            )
        )
        self.pB_get_setup.setText(_translate("MainWindow", "Get setup"))
        self.pB_get_setup.setShortcut(_translate("MainWindow", "Shift+G"))
        self.pB_reset.setStatusTip(
            _translate(
                "MainWindow",
                "Software reset of the device (reconnection needed after 10-15 sec) (Ctrl + Shift +C)",
            )
        )
        self.pB_reset.setText(_translate("MainWindow", "Reset"))
        self.pB_reset.setShortcut(_translate("MainWindow", "Ctrl+Shift+R"))
        self.lab_exc_amp.setText(_translate("MainWindow", "Current Amplitude [mA]"))
        self.lab_burst.setText(_translate("MainWindow", "Burst number"))
        self.lab_minF.setText(_translate("MainWindow", "Min Frequency [Hz]"))
        self.lab_maxF.setText(_translate("MainWindow", "Max Frequency [Hz]"))
        self.lab_steps.setText(_translate("MainWindow", "Steps number"))
        self.lab_scale.setText(_translate("MainWindow", "Scale"))
        self.lab_frame_rate.setText(_translate("MainWindow", "Frame rate [fps]"))
        self.lab_max_frame_rate.setText(
            _translate("MainWindow", "Max Frame rate [fps]")
        )
        self.lab_sn.setText(_translate("MainWindow", "S/N"))
        self.lab_ip.setText(_translate("MainWindow", "IP Adress"))
        self.lab_mac.setText(_translate("MainWindow", "MAC Adress"))
        self.chB_dhcp.setText(_translate("MainWindow", "DHCP_Activated"))
        self.lab_output_config.setText(_translate("MainWindow", "Output config"))
        self.chB_exc_stamp.setText(_translate("MainWindow", "Excitation_Stamp"))
        self.chB_current_stamp.setText(_translate("MainWindow", "Current_Stamp"))
        self.chB_time_stamp.setText(_translate("MainWindow", "Time_Stamp"))
        self.groupBox.setTitle(_translate("MainWindow", "Excitation Pattern"))
        item = self.tw_exc_mat_model.horizontalHeaderItem(0)
        item.setText(_translate("MainWindow", "Inj+ "))
        item = self.tw_exc_mat_model.horizontalHeaderItem(1)
        item.setText(_translate("MainWindow", "Inj-"))
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.tab_exc_model),
            _translate("MainWindow", "Model"),
        )
        item = self.tw_exc_mat_chip.horizontalHeaderItem(0)
        item.setText(_translate("MainWindow", "Inj+ "))
        item = self.tw_exc_mat_chip.horizontalHeaderItem(1)
        item.setText(_translate("MainWindow", "Inj-"))
        self.tabWidget.setTabText(
            self.tabWidget.indexOf(self.tab_exc_chip), _translate("MainWindow", "Chip")
        )
        self.lab_chip.setText(_translate("MainWindow", "Chip type"))
        self.pB_chip_refresh_ctlg.setStatusTip(
            _translate("MainWindow", "reload the catalog ")
        )
        self.pB_chip_refresh_ctlg.setText(_translate("MainWindow", "Upddate"))
        self.pB_load_setup.setStatusTip(
            _translate("MainWindow", "Load parameters from file (*.xlsx)")
        )
        self.pB_load_setup.setText(_translate("MainWindow", "Load_Setup"))
        self.pB_save_setup.setStatusTip(
            _translate("MainWindow", "Save parameters to files (*.xlsx)")
        )
        self.pB_save_setup.setText(_translate("MainWindow", "Save_Setup"))
        self.tabW_settings.setTabText(
            self.tabW_settings.indexOf(self.tab_device),
            _translate("MainWindow", "Device"),
        )
        self.pB_start_meas.setStatusTip(
            _translate("MainWindow", "Start measurement (Ctrl + Shift +Space)")
        )
        self.pB_start_meas.setText(_translate("MainWindow", "Start"))
        self.pB_start_meas.setShortcut(_translate("MainWindow", "Ctrl+Shift+Space"))
        self.pB_stop_meas.setStatusTip(
            _translate("MainWindow", "Stop measurement (Esc)")
        )
        self.pB_stop_meas.setText(_translate("MainWindow", "Stop"))
        self.pB_stop_meas.setShortcut(_translate("MainWindow", "Esc"))
        self.lab_live_meas_status.setText(_translate("MainWindow", "Meas status"))
        self.lE_meas_dataset_dir.setText(
            _translate("MainWindow", "default_autosave_dir")
        )
        self.chB_dataset_autosave.setText(_translate("MainWindow", "autosave"))
        self.chB_dataset_save_img.setText(_translate("MainWindow", "save img"))
        self.chB_load_after_meas.setText(_translate("MainWindow", "load after meas"))
        self.lab_actual_frame_cnt.setText(
            _translate("MainWindow", "Acquisition progress of frame")
        )
        self.sB_actual_frame_cnt.setPrefix(_translate("MainWindow", "#"))
        self.toolBox.setItemText(
            self.toolBox.indexOf(self.Acquisition),
            _translate("MainWindow", "Acquisition"),
        )
        self.pB_meas_dataset_load.setStatusTip(
            _translate("MainWindow", "Load measurements from a selected directory")
        )
        self.pB_meas_dataset_load.setText(_translate("MainWindow", "Load measurements"))
        self.lab_replay_status.setText(_translate("MainWindow", "Replay status"))
        self.tE_load_dataset_dir.setHtml(
            _translate(
                "MainWindow",
                '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">\n'
                '<html><head><meta name="qrichtext" content="1" /><style type="text/css">\n'
                "p, li { white-space: pre-wrap; }\n"
                "</style></head><body style=\" font-family:'MS Shell Dlg 2'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
                '<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">default_</p>\n'
                '<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">loading_</p>\n'
                '<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">dirpath</p></body></html>',
            )
        )
        self.pB_replay_begin.setStatusTip(
            _translate("MainWindow", "First frame (Pos1)")
        )
        self.pB_replay_begin.setShortcut(_translate("MainWindow", "Home"))
        self.pB_replay_back.setStatusTip(_translate("MainWindow", "Previous frame"))
        self.pB_replay_back.setShortcut(_translate("MainWindow", "Ctrl+Space"))
        self.pB_replay_play.setStatusTip(
            _translate("MainWindow", "Start Replay of measurements (Ctrl +Space)")
        )
        self.pB_replay_play.setShortcut(_translate("MainWindow", "Ctrl+Space"))
        self.pB_replay_next.setStatusTip(_translate("MainWindow", "Next frame"))
        self.pB_replay_next.setShortcut(_translate("MainWindow", "Ctrl+Space"))
        self.pB_replay_end.setStatusTip(_translate("MainWindow", "Last frame (End)"))
        self.pB_replay_end.setShortcut(_translate("MainWindow", "End"))
        self.pB_replay_stop.setStatusTip(
            _translate("MainWindow", "Display last meas. frame (End)")
        )
        self.pB_replay_stop.setShortcut(_translate("MainWindow", "End"))
        self.lab_current_frame_indx.setText(_translate("MainWindow", "Current frame #"))
        self.lab_replay_time_2.setText(_translate("MainWindow", "Refresh time"))
        self.sB_replay_time.setSuffix(_translate("MainWindow", " s"))
        self.pB_export_meas_csv.setStatusTip(
            _translate("MainWindow", "Load measurements from a selected directory")
        )
        self.pB_export_meas_csv.setText(
            _translate("MainWindow", "Export measurements to CSV")
        )
        self.pB_load_ref_dataset.setStatusTip(
            _translate("MainWindow", "Load measurements from a selected directory")
        )
        self.pB_load_ref_dataset.setText(
            _translate("MainWindow", "Load reference dataset")
        )
        self.toolBox.setItemText(
            self.toolBox.indexOf(self.Replay), _translate("MainWindow", "Replay")
        )
        self.groupBox_2.setTitle(_translate("MainWindow", "Frame infos"))
        self.pB_export_data_meas_vs_eidors.setStatusTip(
            _translate("MainWindow", "Load measurements from a selected directory")
        )
        self.pB_export_data_meas_vs_eidors.setText(
            _translate("MainWindow", "Export measurements vs EIDORS to CSV")
        )
        self.pB_load_eidors_fwd_solution.setStatusTip(
            _translate("MainWindow", "Load measurements from a selected directory")
        )
        self.pB_load_eidors_fwd_solution.setText(
            _translate("MainWindow", "Load EIDORS fwd solution")
        )
        self.tabW_settings.setTabText(
            self.tabW_settings.indexOf(self.tab_measurements),
            _translate("MainWindow", "Measurements"),
        )
        self.pB_compute.setStatusTip(_translate("MainWindow", "Stop measurement (Esc)"))
        self.pB_compute.setText(_translate("MainWindow", "Compute"))
        self.pB_compute.setShortcut(_translate("MainWindow", "Esc"))
        self.groupBox_9.setTitle(_translate("MainWindow", "EIT Model"))
        self.lab_eit_mdl_ctlg.setText(_translate("MainWindow", "Catalogue"))
        self.pB_eit_mdl_refresh_ctlg.setStatusTip(
            _translate("MainWindow", "reload the catalog ")
        )
        self.pB_eit_mdl_refresh_ctlg.setText(_translate("MainWindow", "Update"))
        self.label_FEMRefinement.setText(_translate("MainWindow", "FEM Refinement"))
        self.lE_eit_model_name.setText(
            _translate("MainWindow", "default_loading_dirpath")
        )
        self.label_eit_model_name.setText(_translate("MainWindow", "EIT model name"))
        self.chB_eit_mdl_normalize.setText(_translate("MainWindow", "Normalize"))
        self.groupBox_8.setTitle(_translate("MainWindow", "Recontruction Solver"))
        self.pB_set_reconstruction.setStatusTip(
            _translate("MainWindow", "Set the reconstruction")
        )
        self.pB_set_reconstruction.setText(
            _translate("MainWindow", "Set reconstruction")
        )
        self.groupBox_6.setTitle(_translate("MainWindow", "Reconstruction parameters"))
        self.lab_solver.setText(_translate("MainWindow", "Solver"))
        self.label_vmax_7.setText(_translate("MainWindow", "p"))
        self.label_vmax_8.setText(_translate("MainWindow", "lamda"))
        self.label_vmax_9.setText(_translate("MainWindow", "n"))
        self.label_FEMRefinement_2.setText(_translate("MainWindow", "BackGround"))
        self.tabW_reconstruction.setTabText(
            self.tabW_reconstruction.indexOf(self.tab_pyeit),
            _translate("MainWindow", "PyEIT"),
        )
        self.lE_ai_model_dir.setText(
            _translate("MainWindow", "default_loading_dirpath")
        )
        self.tabW_reconstruction.setTabText(
            self.tabW_reconstruction.indexOf(self.tab_nn),
            _translate("MainWindow", "NN"),
        )
        self.groupBox_5.setTitle(_translate("MainWindow", "Imaging type"))
        self.lab_ref_frame_idx.setText(_translate("MainWindow", "Reference frame#"))
        self.lab_freq_meas_0.setText(_translate("MainWindow", "Frequence"))
        self.lab_freq_meas_1.setText(_translate("MainWindow", "Frequence "))
        self.chB_eit_imaging_trans_abs.setText(
            _translate("MainWindow", "Show absolute values")
        )
        self.tabW_settings.setTabText(
            self.tabW_settings.indexOf(self.tab_eit), _translate("MainWindow", "EIT")
        )
        self.pB_pyvista.setStatusTip(_translate("MainWindow", "Stop measurement (Esc)"))
        self.pB_pyvista.setText(_translate("MainWindow", "Open Pyvista Viewer"))
        self.pB_pyvista.setShortcut(_translate("MainWindow", "Esc"))
        self.groupBox_4.setTitle(_translate("MainWindow", "Reconstruction settings"))
        self.label_vmin.setText(_translate("MainWindow", "vmin"))
        self.label_vmax.setText(_translate("MainWindow", "vmax"))
        self.lab_dpi_rec.setText(_translate("MainWindow", "dpi"))
        self.pB_set_dpi.setText(_translate("MainWindow", "Set DPI"))
        self.groupBox_7.setTitle(_translate("MainWindow", "Channel voltages settings"))
        self.chB_monitoring_trans_abs.setText(
            _translate("MainWindow", "Show absolute values")
        )
        self.tabW_settings.setTabText(
            self.tabW_settings.indexOf(self.tab_3),
            _translate("MainWindow", "Plot settings"),
        )
        self.groupBox_10.setTitle(_translate("MainWindow", "Global directories"))
        self.lab_measdataset_gdir.setText(_translate("MainWindow", "Measurement Sets"))
        self.lab_snapshot_gdir.setText(_translate("MainWindow", "Snapshot"))
        self.lab_export_gdir.setText(_translate("MainWindow", "Export"))
        self.lab_eit_mdl_ctlg_gdir.setText(_translate("MainWindow", "EIT Model"))
        self.lab_chip_ctlg_gdir.setText(_translate("MainWindow", "Chips"))
        self.tabW_settings.setTabText(
            self.tabW_settings.indexOf(self.tab_6),
            _translate("MainWindow", "Gui setttings"),
        )
        self.label.setText(_translate("MainWindow", "Show:"))
        self.chB_eit_image_plot.setText(_translate("MainWindow", "EIT image"))
        self.chB_eit_data_monitoring.setText(_translate("MainWindow", "EIT data"))
        self.tabW_rec.setTabText(
            self.tabW_rec.indexOf(self.tab_5),
            _translate("MainWindow", "Reconstruction"),
        )
        self.tabW_monitoring.setTabText(
            self.tabW_monitoring.indexOf(self.tab), _translate("MainWindow", "EIT data")
        )
        self.tabW_monitoring.setTabText(
            self.tabW_monitoring.indexOf(self.tab_2),
            _translate("MainWindow", "Channel voltages"),
        )
        self.tabW_monitoring.setTabText(
            self.tabW_monitoring.indexOf(self.tab_4),
            _translate("MainWindow", "Error ch voltage"),
        )
        self.groupBox_video.setTitle(_translate("MainWindow", "Video"))
        self.cB_capture_devices.setStatusTip(
            _translate("MainWindow", "Available serial port list")
        )
        self.lab_capture_status.setText(_translate("MainWindow", "Meas status"))
        self.pB_capture_connect.setToolTip(_translate("MainWindow", "test"))
        self.pB_capture_connect.setStatusTip(
            _translate("MainWindow", "Refresh the available serial port list")
        )
        self.pB_capture_connect.setText(_translate("MainWindow", "Connect"))
        self.pB_capture_start_stop.setToolTip(_translate("MainWindow", "test"))
        self.pB_capture_start_stop.setStatusTip(
            _translate("MainWindow", "Refresh the available serial port list")
        )
        self.pB_capture_start_stop.setText(_translate("MainWindow", "Start capture"))
        self.pB_capture_refresh.setToolTip(_translate("MainWindow", "test"))
        self.pB_capture_refresh.setStatusTip(
            _translate("MainWindow", "Refresh the available serial port list")
        )
        self.pB_capture_refresh.setText(_translate("MainWindow", "Refresh"))
        self.pB_capture_snapshot.setToolTip(_translate("MainWindow", "test"))
        self.pB_capture_snapshot.setStatusTip(
            _translate("MainWindow", "Refresh the available serial port list")
        )
        self.pB_capture_snapshot.setText(_translate("MainWindow", "Snapshot"))
        self.video_frame.setText(_translate("MainWindow", "Live Video"))
        self.cB_log_level.setStatusTip(
            _translate("MainWindow", "Available serial port list")
        )
        self.lab_log_level.setText(_translate("MainWindow", "log level"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.action_exit.setText(_translate("MainWindow", "Exit"))
        self.action_exit.setShortcut(_translate("MainWindow", "Ctrl+Q"))


import resource_rc


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
