import itertools
from copy import deepcopy
from dataclasses import dataclass, field
import logging
import os
import sys
from typing import Union
import cv2
from matplotlib.axes import Axes
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
import skg
from glob_utils.file.txt_utils import save_as_txt
from glob_utils.file.utils import is_file, is_file_with_ext,search_for_file_with_ext, dialog_get_file_with_ext, OpenDialogFileCancelledException
from glob_utils.file.json_utils import save_to_json
import glob_utils.dialog.Qt_dialogs
from glob_utils.directory.utils import mk_dir, get_dir

logger = logging.getLogger(__name__) 


def fit_circle(contours)->np.ndarray:
    """
    _summary_

    Args:
        contours (_type_): _description_

    Returns:
        np.ndarray: circle pos(x,y) and radius, shape(n_circ, 3)
    """
    contours= np.array(contours)
    n_contours= contours.shape[0]
    circles= np.zeros((n_contours, 3))
    for i in range(n_contours):
        x= np.reshape(contours[i,:,0,:], (-1,2))
        r, c= skg.nsphere.nsphere_fit(x, axis=-1, scaling=False)
        c= np.reshape(c, (-1,1))
        circles[i,:]= np.array([c[0], c[1], r])

    return circles

def plot_img(img, cmap= None, title:str='Title figure', fig:Figure=None, ax:Axes= None):
    if fig is None or ax is None:
        fig, ax = plt.subplots()
    ax.set_title(title)
    ax.imshow(img, cmap)
    fig.show()
    return fig, ax

def draw_circle(x, y, r, ax, edgecolor= 'r', linewidth=3):
    ax.add_patch(plt.Circle((x, y), r, edgecolor=edgecolor, fill= False, linewidth= linewidth))


def get_files( initialdir: str, ext='.png') -> Union[list[str], None]:
        """Return files with extension contained in a directory"""
        try:
            dir= get_dir(initialdir=initialdir)
            filenames = search_for_file_with_ext(dir, ext=ext)
        except FileNotFoundError as e:
            logger.warning(f"FileNotFoundError: ({e})")
            glob_utils.dialog.Qt_dialogs.warningMsgBox(
                "FileNotFoundError",
                f"{e}",
            )
            return None, None

        return dir, filenames

def get_file(path:str= None, dir_path: str= None, ext='.png') -> Union[str, None]:
    """Return a valid path of a ext-file"""

    if not is_file_with_ext(path, ext):
        logger.debug(f'The {path=} is not a {ext}-file!')
        try:
            path= dialog_get_file_with_ext(ext=ext, initialdir= dir_path)
        except OpenDialogFileCancelledException: 
            return None
    return path


def find_contours(image, mask, color_contours= (0, 255, 0)):

    # find the contours from the thresholded image
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # draw all contours
    image_w_contours = cv2.drawContours(image, contours, -1, color_contours, 2)
    return image_w_contours , contours



def draw_contours(img, contours, color= (0, 255, 0)):
    return cv2.drawContours(deepcopy(img), contours, -1, color, 2)

def relative_size(circles, circle_ref):
    c= np.array(circles)
    c[:,:2] = c[:,:2]-circle_ref[0,:2]
    c[:,1] = -c[:,1] # invert Y axis
    c= c/circle_ref[0,2]

    return c



@dataclass
class FitCircle():
    path:str
    img_rgb:np.ndarray=field(init=False)
    img_gray:np.ndarray=field(init=False)
    mask:np.ndarray=field(default=None, init=False)

    def __post_init__(self):
        self.img_rgb= get_img_rgb(self.path)
        self.img_gray= get_img_gray(self.path)
    
    def run(self, threshold:int=128)-> tuple[np.ndarray,list]:
        """
        fit circles on the mask using

        Args:
            threshold (int, optional): for the mask. Defaults to 128.

        Returns:
            np.ndarray: circle pos(x,y) and radius, shape(n_circ, 3)
            list: contours from cv2
        """
        __, self.mask = cv2.threshold(self.img_gray, threshold, 255, cv2.THRESH_BINARY_INV)  
        self.contours, _ = cv2.findContours(self.mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        return fit_circle(self.contours), self.contours, self.mask




def evaluate_single_image(
    path:str= None, 
    threshold_cell:int=150, 
    threshold_chamber:int= 230, 
    scale:float=2.5, 
    initialdir:str= None,
    out_dir:str= None

    )->str:
    """
    run two fit cricel with two different threhold to get relate size/psition between chamber and cells

    Args:
        path (str, optional): image path . Defaults to None, in that case dialog will be open.
        threshold_cell (int, optional): filter value for cells. Defaults to 150.
        threshold_chamber (int, optional): filter value for chamber. Defaults to 230.
        scale (float, optional): radius of the chamber. Defaults to 2.5.

    Returns:
        str: used path
    """    
    path = get_file(path, initialdir, ext= '.png')
    if path is None:
        return None

    fit= FitCircle(path)

    # set output name/dir
    img_name= os.path.split(path)[1]
    if out_dir is None:
        out_dir,_ = os.path.splitext(path)
    mk_dir(out_dir)

    # run the fit
    circle_c, contour_c, mask_c= fit.run(threshold_chamber)
    circle_cell, contour_cell, mask_cell= fit.run(threshold_cell)

    # if fits failed....
    if circle_c.shape[0]==0:
        logger.info(f'Fitting circle for chamber for {img_name=} - Failed')
        return path, circle_c
    
    if circle_cell.shape[0]==0:
        logger.info(f'Fitting circle for cell for {img_name=} - Failed')
        return path, circle_cell
    # compute relative pos and radius
    circle= np.vstack([circle_c, circle_cell])
    circle_rel= relative_size(circle, circle)
    circle_scaled= circle_rel* scale

    # plot
    fig, ax = plt.subplots(3, 2)
    fig.canvas.manager.set_window_title(f'{img_name}: Fit circle eval overview')
    plot_img(fit.img_rgb, title='Image loaded rgb', fig=fig, ax=ax[0,0])
    plot_img(fit.img_gray,title='Image loaded gray', fig=fig, ax=ax[0,1], cmap='gray')
    plot_img(mask_cell, title='Mask cell', fig=fig, ax=ax[1,0], cmap='gray')
    plot_img(mask_c,title='Mask chamber', fig=fig, ax=ax[1,1], cmap='gray')

    img_w_contours= draw_contours(fit.img_rgb, contour_c, color= (255, 0, 0))
    img_w_contours= draw_contours(img_w_contours, contour_cell, color= (0, 255, 0))
    plot_img(img_w_contours,title='Image with contours', fig=fig, ax=ax[2,0])
    f, a= plot_img(fit.img_rgb,title='Image with circles', fig=fig, ax=ax[2,1])
    c= circle_c[0]
    draw_circle(c[0], c[1], c[2], a, edgecolor= 'blue', linewidth=1.5)
    for c in circle_cell:
        draw_circle(c[0], c[1], c[2], a, edgecolor= 'green', linewidth=1.5)
    # save data, img
    filename,_=os.path.splitext(img_name)
    file = os.path.join(out_dir, filename)

    eval_res= {
        'img_name':img_name,
        'threshold_cell':threshold_cell, 
        'threshold_chamber':threshold_chamber, 
        'circle':circle,
        'circle_rel':circle_rel,
        'scale':scale,
        'circle_scaled':circle_scaled,
    }
    save_to_json(f'{file}_eval_results', eval_res)
    fig.savefig(f'{file}_eval_overview.png')
    return path, circle_scaled

def evaluate_multi_image(path:str= None, threshold_cell:int=150, threshold_chamber:int= 230, scale:float=2.5, initialdir:str= None)->str:
    """"""
    dir, files = get_files(initialdir, ext= '.png')
    if files is None:
        return None
    logger.info(f'found {files=}')
    results= {}
    out_dir=os.path.join(dir, 'eval_output')
    print(f'{out_dir=}')
    for file in files:
        """"""
        path, circle_scaled= evaluate_single_image(
            path=os.path.join(dir, file), 
            threshold_cell=threshold_cell, 
            threshold_chamber=threshold_chamber, 
            scale= scale, 
            initialdir=initialdir,
            out_dir= out_dir
            )
        results[file]= circle_scaled
    # save summry data
    save_to_json(os.path.join(out_dir, 'summary_eval_results'), results)
    return dir

def show_threshold_overview(path:str= None, img_nb_col:int=4, img_nb_row:int=5, initialdir:str= None) -> str:

    path = get_file(path, initialdir, ext= '.png')
    if path is None:
        return None

    fit= FitCircle(path)

    fig, ax = plt.subplots(1, 2)
    img_name= os.path.split(path)[1]
    fig.canvas.manager.set_window_title(f'{img_name}: Raw Image')
    plot_img(fit.img_rgb, title='Image loaded rgb', fig=fig, ax=ax[0])
    plot_img(fit.img_gray,title='Image loaded gray', fig=fig, ax=ax[1], cmap='gray')

    fig, ax = plt.subplots(img_nb_row,img_nb_col)
    fig.canvas.manager.set_window_title(f'{img_name} : threshold_overview')

    step_thres= int(255/(img_nb_col*img_nb_row))
    threshold= step_thres
    for row_i, col_i in itertools.product(range(img_nb_row), range(img_nb_col)):
        # fig.add_subplot(img_nb_row, img_nb_col, i)
        threshold += step_thres
        __, binary = cv2.threshold(fit.img_gray, threshold, 255, cv2.THRESH_BINARY_INV)
        ax[row_i, col_i].imshow(binary, cmap="gray")
        ax[row_i, col_i].set_title(f'{threshold=}')
    # plt.show(block=False)
    fig.show()
    return path

def get_img_rgb(path:str)->np.ndarray:
    return cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)

def get_img_gray(path:str):
    return cv2.cvtColor(cv2.imread(path), cv2.COLOR_RGB2GRAY)



if __name__ == "__main__":
    """"""
    # path = sys.a'rgv[1]
    # if path is None:'
    path= "E:\Software_dev\Python\eit_app\eit_app\experimental\CNN_position1_noElec.png"
    # show_threshold_overview(initialdir=path)
    # evaluate_single_image(path, threshold_cell=150, threshold_chamber= 230)
    evaluate_multi_image(initialdir=os.path.split(path)[0], threshold_cell=150, threshold_chamber= 230)

    plt.show()