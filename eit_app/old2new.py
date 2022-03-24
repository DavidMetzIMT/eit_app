import os
from eit_app.io.sciospec.setup import SciospecSetup
from eit_app.io.sciospec.measurement import MeasurementFrame, MeasurementDataset
from glob_utils.pth.path_utils import get_dir
from glob_utils.types.dict import visualise, dict_nested
from glob_utils.files.json import save_to_json, read_json
from glob_utils.files.files import save_as_txt
# from eit_app.io.sciospec.meas_dataset_o import EitMeasurementSet as DSOld


if __name__ == "__main__":
    """"""
    import glob_utils.log.log
    glob_utils.log.log.main_log()
    # dir = get_dir(title="Select a dire, where the setup will be saved",initialdir="E:\Software_dev\Python\eit_app\measurements")
    # ds_o=DSOld()
    ds=MeasurementDataset()

    # setup=SciospecSetup(32)
    # ds.meas_frame=[EITFrame(0,setup, "tests", "time1256151561")]
    # print(ds.__dict__)

    # ds.meas_frame[0].save()
    ds.load("E:\Software_dev\Python\eit_app\measurements\default_autosave_dir_20220316_160346")

    
    # ds.load("E:\Software_dev\Python\eit_app\measurements\default_autosave_dir_20220315_161423")
    # print(ds.__dict__)
    # a= dict_nested(ds.meas_frame[0])
    # visualise(a)
    # visualise(a)
    # save_to_json("test", a)
    # a_= read_json("test")
    # visualise(a_)
    # print(a_["meas"][0])



    # save_as_txt('test.txt', a)

    # setup=SciospecSetup(32)
    # setup.load(dir)
    # ds.


    # for file in files:
    #     filepath = os.path.join(dir_path, file)
    #     loaded_ds = ds.load_frame(filepath)

    #     self.meas_frame.append(loaded_ds)
    #     # correct the frame path (if dataset dir moved...)
    #     self.meas_frame[-1].frame_path = filepath
    #     self.meas_frame[-1].make_info_text()

    # loaded_ds = ds.load_frame(filepath)


    # ds.time_stamps = self.meas_frame[0].time_stamp
    # _, ds.name = os.path.split(dir_path)
    # ds.output_dir = dir_path
    # ds.dev_setup = self.meas_frame[0].dev_setup

    # ds.rx_meas_frame = None #not used with loaded dataset
    # ds._ref_frame_idx =0 # reset to initial frame
    # ds.flag_new_meas = CustomFlag()
    # ds.frame_cnt = len(self.meas_frame)


    # for idx in range(ds.frame_cnt):
    #     ds.save_frame(idx)

    # print(dir_path, files)
    # print(setup.__dict__)


    



