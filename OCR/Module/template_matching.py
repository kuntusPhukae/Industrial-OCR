# templeatematching.py
import cv2
import numpy as np

def find_roi_by_template(frame, template, threshold=0.7):
    """หา ROI ใน frame โดยใช้ template matching"""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    t_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(gray, t_gray, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

    if max_val >= threshold:
        h, w = t_gray.shape
        x, y = max_loc
        roi = frame[y:y+h, x:x+w]   # ✨ crop ROI จากตำแหน่งที่เจอ
        return x, y, w, h, max_val, roi

    return None, None, None, None, None, None