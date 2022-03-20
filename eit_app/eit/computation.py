from dataclasses import dataclass
import enum
from queue import Queue
import logging
from typing import Tuple

import numpy as np
from eit_model.imaging_type import Imaging
from eit_app.eit.plots import Data2Plot, LayoutEITChannelVoltage, LayoutEITImage2D, LayoutEITData
from glob_utils.thread_process.threads_worker import Poller
from glob_utils.decorator.decorator import catch_error
from glob_utils.thread_process.signal import Signal
import eit_model.solver_abc
import eit_model.model


class Data4GUI:
    def pack():
        """"""

    def unpack():
        """"""


logger = logging.getLogger(__name__)


class RecCMDs(enum.Enum):
    initialize = enum.auto()
    reconstruct = enum.auto()


@dataclass
class Data2Compute():
    v_ref:np.ndarray =None
    v_meas:np.ndarray = None
    labels:list = None
    

class ComputeMeas:
    def __init__(self):
        """Constructor"""
        self.input_buf = Queue()
        # self.output_buf_func = output_buf_func
        # self.plot_cllbck= send_2_plot
        self.compute_worker = Poller(
            name="compute", pollfunc=self.poll_input_buf, sleeptime=0.01
        )
        self.compute_worker.start()
        self.compute_worker.start_polling()

        self.eit_imaging = None
        self.ch_imaging=None
        self.eit_model = None
        self.U, self.labels = None, None
        self.extract_voltages = False
        self.solver: eit_model.solver_abc.Solver = None
        self.rec_enable=False
        self.computed= Signal(self)
    
    def send_2_plot(self, data):
        self.plot_cllbck(data)
    
    def add_data2compute(self, data:Data2Compute=None,**kwargs):

        # if isinstance(data, dict):
        #     data= Data2Compute(**data)
        if data is None:
            return

        if not isinstance(data, Data2Compute):
            logger.error(f'wrong type of data, type Data2Compute expected: {data=}')
            return
        self.input_buf.put(data)

    def set_imaging_mode(self, eit_imaging: Imaging):
        self.eit_imaging = eit_imaging
    
    def set_ch_imaging_mode(self,  ch_imaging:Imaging):
        self.ch_imaging = ch_imaging

    def set_eit_model(self, eit_model: eit_model.model.EITModel):
        self.eit_model = eit_model

    def enable_rec(self, enable:bool=True):
        self.rec_enable= enable

    def set_solver(self, solver: eit_model.solver_abc.Solver):

        if isinstance(self.eit_model, eit_model.model.EITModel):
            self.solver = solver(self.eit_model)
            logger.info(f"Recocntructions selected: {self.solver}")

    @catch_error
    def init_solver(self):
        img_rec, data_sim=self.solver.prepare_rec()
        self.computed.fire(data=Data2Plot(img_rec, {}, LayoutEITImage2D))
        self.computed.fire(data=Data2Plot(data_sim, {},LayoutEITData))
        # self.send_2_plot(Data2Plot(img_rec,{}))
        # self.send_2_plot()

    def poll_input_buf(self):
        """Get last RX Frame contained in the input_buffer"""

        if self.input_buf.empty():
            return

        # loosing some informations
        while not self.input_buf.empty():
            data = self.input_buf.get(block=True)
        self.process(data)
    
    @catch_error
    def process(self, data:Data2Compute) -> None:
        """ Responsible of preproces measurements data and reconstruct them

        Args:
            data (Data2Compute): _description_
        """
        # prepocess eitdata for eit_imaging
        eit_data, labels = self.eit_imaging.process_data(
            **data.__dict__, eit_model= self.eit_model)
        self.computed.fire(data=Data2Plot(eit_data, labels, LayoutEITData))

        # prepocess channel voltages for visualisation
        ch_data, ch_labels = self.ch_imaging.process_data(
             **data.__dict__, eit_model= self.eit_model)
        self.computed.fire(data=Data2Plot(ch_data, ch_labels, LayoutEITChannelVoltage))

        logger.info(f"{data.labels[1][0]} - Voltages preproccessed")

        if not self.rec_enable:
            return
        if not self.solver.ready.is_set():
            logger.warning("Solver not set ")
            return
        img_rec = self.solver.rec(eit_data)

        self.computed.fire(data=Data2Plot(img_rec, labels,LayoutEITImage2D))
        logger.info(f"Frame #{data.labels[1][0]} - Image rec")

