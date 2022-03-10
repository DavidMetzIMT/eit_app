

from queue import Queue
from typing import List
import logging
import numpy as np
from eit_app.eit.imaging_type import Imaging
from eit_app.eit.eit_model import EITModelClass
from eit_app.eit.plots import CustomPlots, PlotType
from eit_app.eit.rec_abs import Reconstruction
from eit_app.io.sciospec.meas_dataset import EitMeasurementSet
from eit_app.threads_process.threads_worker import Poller
from glob_utils.flags.flag import CustomFlag
from glob_utils.pth.path_utils import get_datetime_s
from glob_utils.decorator.decorator import catch_error


class Data4GUI():

    def pack():
        """"""
    def unpack():
        """"""

logger = logging.getLogger(__name__)


class ComputeMeas():


    def __init__(self, input_buf: Queue, output_buf:Queue):
        """Constructor """
        self.input_buf= input_buf
        self.output_buf= output_buf
        self.compute_worker=Poller(
            name='compute', pollfunc=self.get_last_rx_frame, sleeptime=0.01)
        self.compute_worker.start()
        self.compute_worker.start_polling()
        self._post_init_()
    
    def _post_init_(self):
        """ init the """
        self.channel = 32
        self.flag_new_plots=CustomFlag()
        self.flag_new_rec_image=CustomFlag()
        self.imaging_type=None
        self.eit_model=None
        self.U, self.labels, self.rec=None, None, None
        self.extract_voltages=False
        self.rec:Reconstruction=None

    def set_imaging_mode(self, imaging_type:Imaging):
        self.imaging_type= imaging_type

    def set_eit_model(self, eit_model:EITModelClass):
        self.eit_model= eit_model

    def set_plotings(self, plots_to_show:List[CustomPlots], fig):
        self.plots_to_show= plots_to_show
        self.fig= fig
    
    def set_reconstruction(self, rec:Reconstruction):
        self.rec=rec()
        logger.info(f'Recocntructions selected: {self.rec}')

    def get_last_rx_frame(self):
        """ Get last RX Frame contained in the input_buffer"""

        if self.input_buf.empty():
            return
            
        # loosing some informations
        while not self.input_buf.empty():
            data = self.input_buf.get(block=True)
        self.process(data)

    @catch_error
    def process(self, data):

        dataset, idx_frame, cmd = data
        self.U, self.labels = self.preprocess(dataset, idx_frame)
        if self.plots_to_show[0].visible:
            self.eit_model, self.U= self.rec.run(cmd, self.eit_model, self.U)
                # if rec_result is not None:
                    # self.eit_model, self.U= rec_result
            if dataset == 'random':
                logger.info(f'Dummy data - reconstructed (time {get_datetime_s()})')
            else:
                logger.info(f'Frame #{dataset.get_idx_frame(idx_frame)} - reconstructed (time {get_datetime_s()})')
        data_4_gui = { 
                'dataset': dataset,
                'idx_frame':idx_frame,
                'U':self.U,
                'labels':self.labels,
                'eit_model':self.eit_model
            }
        self.output_buf.put_nowait(data_4_gui)


    def preprocess(self,dataset:EitMeasurementSet, idx_frame:int):

        if not self.imaging_type or not self.eit_model or dataset == 'random':
            lab= {  
                'title': 'random',
                'legend': ['random', 'random'],
                'xylabel': ['random', 'random']}
            logger.debug('Random data - preproccessed')
            return  np.random.rand(256,2),\
                    { 
                        PlotType.Image_2D: lab,
                        PlotType.U_plot: lab,
                        PlotType.Diff_plot: lab}

        U, labels= self.imaging_type.process_data(
                        dataset=dataset,
                        eit_model=self.eit_model,
                        idx_frame=idx_frame,
                        extract_voltages=self.extract_voltages)
        logger.info(f'Frame #{dataset.get_idx_frame(idx_frame)} - preproccessed (time {get_datetime_s()})')
        return U, labels
