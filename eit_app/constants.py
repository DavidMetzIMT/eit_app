"""[summary]
"""





MEAS_DIR='measurements'
ICONS_DIR= 'icons'
SETUPS_DIR= 'setups'
DEFAULT_DIR= 'default'

DEFAULT_INJECTIONS= {   'ad':'InjPattern_default_ad.txt',
                        'op':'InjPattern_default_op.txt'}
DEFAULT_MEASUREMENTS= { 'ad':'MeasPattern_default_ad.txt',
                        'op':'MeasPattern_default_op.txt'}

DEFAULT_ELECTRODES_CHIP_RING='Chip_Ring.txt'


#####

FORMAT_DATE_TIME= "%Y%m%d_%H%M%S"
FORMAT_TIME= "%Hh %Mm %Ss"
DEFAULT_OUTPUTS_DIR= 'outputs'



EXT_MAT= '.mat'
EXT_PKL= '.pkl'
EXT_TXT= '.txt'




DEFAULT_IMG_SIZES={  #'1600 x 1200':(1600,1200), 
        #'1280 x 960':(1280, 960),
        #'800 x 600':(800,600),
        '640 x 480':(640,480)
        }
EXT_IMG= {'PNG': '.png', 'JPEG':'.jpg'}


# EXT_IDX_FILE= '_idx_samples' + EXT_MAT
# EXT_EIDORS_SOLVING_FILE= '_test_elem_data'+ EXT_MAT



# TRAIN_INPUT_FILENAME='train_inputs' + EXT_TXT
# MODEL_SUMMARY_FILENAME='model_summary' + EXT_TXT
# TENSORBOARD_LOG_FOLDER ='log'