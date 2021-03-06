import cv2
import numpy as np

def draw_blob(blob, img, globalize_coords):
    " draw a single blob "
    s = blob.sign
    y0, x0 = globalize_coords
    for seg in blob.e_:
        for P in seg[2]:
            for dert in P[2]:
                y, x = dert[:2]
                img[y+y0, x+x0] = 255 if s else 0

def draw_blobs(path, frame, isb=-1):
    " Rebuild image from blobs "

    height, width = frame[-1].shape[:2]
    frame_img = np.array([[127] * width] * height)

    for blob in frame[1]:
        if isb < 0:
            draw_blob(blob, frame_img, isb)
        elif blob.sign:
            y0, yn, x0, xn = blob.box
            for sub_blob in blob.sub_blob_[isb]:
                    draw_blob(sub_blob, frame_img, (y0, x0))

    cv2.imwrite(path + '.bmp', frame_img)
    # ---------- draw_blob() end ----------------------------------------------------------------------------------------
