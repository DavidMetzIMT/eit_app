import sys
import cv2
import matplotlib.pyplot as plt
import numpy as np
import skg

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
        # x= np.concatenate((x_m, y_m), axis=1)
        r, c= skg.nsphere.nsphere_fit(x, axis=-1, scaling=False)
        # print(f'{c=}')
        # print(f'{type(c)=}')
        # print(f'{c.shape=}')
        c= np.reshape(c, (-1,1))
        circles[i,:]= np.array([c[0], c[1], r])

    # print(f'{circles=}')
    return circles

def plot_img_new_fig(img, cmap= None):
    plt.figure()
    plt.imshow(img, cmap)
    plt.show(block=False)


def find_contours(image, mask, color_contours= (0, 255, 0)):
     # find the contours from the thresholded image
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # draw all contours
    image = cv2.drawContours(image, contours, -1, color_contours, 2)
    return image , contours


def relative_size(circles, circle_ref):
    c= np.array(circles)
    c[:,:2] = c[:,:2]-circle_ref[0,:2]
    c[:,1] = -c[:,1] # invert Y axis
    c= c/circle_ref[0,2]

    return c

def main_demo(path, threshold_cell=150, threshold_chamber= 230, scale=2.5):
    img, img_gray= load_image(path)
    plot_img_new_fig(img)
    plot_img_new_fig(img_gray, cmap="gray")
    mask_cell= get_image_mask(img_gray, threshold_cell)
    plot_img_new_fig(mask_cell, cmap="gray")
    image_w_contours , contours_cells= find_contours(img, mask_cell)
    mask_chamber= get_image_mask(img_gray, threshold_chamber)
    plot_img_new_fig(mask_chamber, cmap="gray")
    image_w_contours , contours_chamber= find_contours(image_w_contours, mask_chamber, (255,0,0))
    plot_img_new_fig(image_w_contours)
    # contours= 
    chamber_r = fit_circle(contours_chamber)
    cells =fit_circle(contours_cells)

    chamber= relative_size(chamber_r, chamber_r) * scale
    cells= relative_size(cells, chamber_r)* scale
    print(f'{chamber=}')
    print(f'{cells=}')

def main_threshold_overview(path, img_nb_col:int=4, img_nb_row:int=5):
    _, gray= load_image(path)

    fig = plt.figure(figsize=(8, 8))
    n= img_nb_col*img_nb_row
    for i in range(1, n +1):
        fig.add_subplot(img_nb_row, img_nb_col, i)
        threshold= int((i+1)*255/(n+1))
        __, binary = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY_INV)  
        plt.imshow(binary, cmap="gray")
        plt.title(f'{threshold=}')
    plt.show(block=False)

def load_image(path:str):
    image = cv2.imread(path)
    # convert to RGB
    img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    # convert to grayscale
    img_gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    return img, img_gray

def get_image_mask(img_gray, threshold:int=128):
    __, binary = cv2.threshold(img_gray, threshold, 255, cv2.THRESH_BINARY_INV)  
    return binary



if __name__ == "__main__":
    """"""
    path = sys.argv[1]
    if path is None:
        path= "CNN_position1_noElec.png"
    main_threshold_overview(path)
    main_demo(path, threshold_cell=150, threshold_chamber= 230)

    plt.show()