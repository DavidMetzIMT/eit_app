
from queue import Queue
import traceback
from typing import List

import numpy as np
from eit_app.eit import reconstruction


from eit_app.eit.imaging_type import Imaging
from eit_app.eit.model import EITModelClass
from eit_app.eit.plots import CustomPlots, PlotType, plot_measurements
from eit_app.eit.rec_abs import RecCMDs, Reconstruction
from eit_app.io.sciospec.meas_dataset import EitMeasurementDataset
# from eit_app.io.sciospec.com_constants import *

from eit_app.threads_process.threads_worker import Poller
from eit_app.utils.flag import CustomFlag
from eit_app.utils.utils_path import get_date_time



class Data4GUI():

    def pack():
        """"""
    def unpack():
        """"""


class ComputeMeas():

    def __init__(self, queue_in: Queue, queue_out:Queue):
        """Constructor """
        self.queue_in= queue_in
        self.queue_out= queue_out
        self.compute_worker=Poller(name='compute',pollfunc=self.get_last_rx_frame,sleeptime=0.01)
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

    def set_computation(self, imaging_type:Imaging):
        self.imaging_type= imaging_type

    def set_eit_model(self, eit_model:EITModelClass):
        self.eit_model= eit_model

    def set_plotings(self, plots_to_show:List[CustomPlots], fig):
        self.plots_to_show= plots_to_show
        self.fig= fig
    
    def set_reconstruction(self, rec:Reconstruction):
        self.rec=rec()
        print(f'Recocntructions selected: {self.rec}')

    def get_last_rx_frame(self):
        try:
            data = self.queue_in.get(block=True)
            dataset, idx_frame, cmd = data
            
            self.U, self.labels = self.compute(dataset, idx_frame)
            if isinstance(dataset, EitMeasurementDataset):
                print(f'idx_frame computed :     #{dataset.get_idx_frame(idx_frame)}, time {get_date_time()}')
            if self.plots_to_show[0].is_visible:
                    self.eit_model, self.U= self.rec.run(cmd, self.eit_model, self.U)

            
            data_4_gui = { 
                'dataset': dataset,
                'idx_frame':idx_frame,
                'U':self.U,
                'labels':self.labels,
                'eit_model':self.eit_model
            }
            self.queue_out.put_nowait(data_4_gui)
        except BaseException as error:
            print(f'computation: {error}\n {traceback.format_exc()}')

    def compute(self,dataset, idx_frame):

        if not self.imaging_type or not self.eit_model or dataset == 'random':
            lab= {
                    'title': 'random',
                    'legend': ['random', 'random'],
                    'xylabel': ['random', 'random']
                }

            return  np.random.rand(256,2),\
                    {   PlotType.Image_2D: lab,
                        PlotType.U_plot: lab,
                        PlotType.Diff_plot: lab
                    }

        return self.imaging_type.process_data(
            dataset=dataset,
            eit_model=self.eit_model,
            idx_frame=idx_frame,
            extract_voltages=self.extract_voltages
        )
