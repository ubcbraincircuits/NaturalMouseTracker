import cv2
from naturalmousetracker.detection_utils.MouseTracker import MouseTracker
import numpy as np
from PIL import Image, ImageDraw

class ImageProcessing:
    def convertBack(x, y, w, h):
        xmin = int(round(x - (w / 2)))
        xmax = int(round(x + (w / 2)))
        ymin = int(round(y - (h / 2)))
        ymax = int(round(y + (h / 2)))
        return xmin, ymin, xmax, ymax

    background_images = np.ones((50,640,640), np.uint8)*127
    frameCount = 0
    background = np.zeros((640,640), np.uint8)

    def cvDrawBoxes(detections, img, mice):
        entranceX, entranceY = 550,350
        maxSwapDistance = 100
        output_im = img.copy()
        new_bg = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        new_bg[new_bg > 254] = 254
        for mouse in mice:
            if mouse.visualTracker is not None:
                pos = mouse.getPosition()
                x, y, w, h =  pos[0], pos[1], pos[4], pos[5]
                xmin, ymin, xmax, ymax = ImageProcessing.convertBack(
                    float(x), float(y), float(w), float(h))
                pt1 = (xmin, ymin)
                pt2 = (xmax, ymax)
                cv2.rectangle(img, pt1, pt2, (255, 0, 255), 1)
                cv2.putText(img,
                     str(mouse.tag()) +
                     " [vis]",
                      (pt1[0], pt1[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                      [255, 0, 255], 2)
        masks = []
        for detection in detections:
            x, y, w, h = detection[2][0],\
                detection[2][1],\
                detection[2][2],\
                detection[2][3]
            vx = detection[3][0]
            vy = detection[3][1]
            xmin, ymin, xmax, ymax = ImageProcessing.convertBack(
                float(x), float(y), float(w), float(h))
            pt1 = (max(xmin, 0), max(ymin, 0))
            pt2 = (min(xmax, 640), min(ymax, 640))
            try:
                mask = ImageProcessing.findMask(img, pt1, pt2, output_im, new_bg)
                masks.append((detection[0], mask))
            except Exception as e:
                print(str(e))
            cv2.rectangle(output_im, pt1, pt2, (0, 255, 0), 1)
            cv2.rectangle(output_im, (entranceX, entranceY), (640, 640), [0, 120,120])
            cv2.circle(output_im, (int(x), int(y)), 5, [0, 0, 255])
            cv2.circle(output_im, (int(550*640/640), int(350*640/480)), 5, [0, 255, 0])
            cv2.circle(output_im, (int(550*640/640), int(100*640/480)), 5, [0, 255, 0])
            cv2.circle(output_im, (int(100*640/640), int(100*640/480)), 5, [0, 255, 0])
            cv2.circle(output_im, (int(100*640/640), int(350*640/480)), 5, [0, 255, 0])
            cv2.circle(output_im, (int(x), int(y)), maxSwapDistance, [255, 0, 0])
            cv2.arrowedLine(output_im, (int(x - vx/2), int(y - vy/2)), (int(x + vx/2), int(y + vy/2)), [0, 0, 255])
            cv2.putText(output_im,
                        str(detection[0]) +
                        " [" + str(round(detection[1] * 100, 2)) + "]",
                        (pt1[0], pt1[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        [0, 255, 0], 2)
            # ELLIPSE
        ImageProcessing.frameCount += 1
        if ImageProcessing.frameCount % 10 == 0:
            ImageProcessing.background_images = np.roll(ImageProcessing.background_images, 1, axis=0)
            # print(ImageProcessing.background_images)
            ImageProcessing.background = np.nanmean(ImageProcessing.background_images, axis=0)
            ImageProcessing.background = ImageProcessing.background.astype(np.uint8)
            # new_bg[detection_indices] = ImageProcessing.background_im[detection_indices]
            # print(np.where(new_bg > 254))
            ImageProcessing.background_images[0] = np.where(new_bg > 254,
                ImageProcessing.background, new_bg)
        return output_im, masks

    def findMask(img, pt1, pt2, output_im, new_bg):
        pt1_ex = (max(pt1[0] -20, 0), max(pt1[1] -20, 0))
        pt2_ex = (min(pt2[0] + 20, 640), min(pt2[1] +20, 640))
        crop_img = img[pt1[1]:pt2[1], pt1[0]:pt2[0]]
        new_bg[pt1_ex[1]:pt2_ex[1], pt1_ex[0]:pt2_ex[0]] = 255
        gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
        # OTSU thresholing
        difference = cv2.absdiff(gray, ImageProcessing.background[pt1[1]:pt2[1], pt1[0]:pt2[0]])
        thresh_val, thresh = cv2.threshold(difference, 40, 255, cv2.THRESH_BINARY)
        if thresh is None:
            raise Exception('some')
        kernel = np.ones((5,5),np.uint8)
        opening = cv2.morphologyEx(thresh,cv2.MORPH_OPEN,kernel, iterations = 1)
        contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        bestContour = None
        maxArea = 0
        for i, c in enumerate(contours):
            area = cv2.contourArea(c)
            if maxArea < area:
                bestContour = c
                maxArea = area
        bestContour[:, :, 0] += pt1[0]
        bestContour[:, :, 1] += pt1[1]
        thresh = cv2.cvtColor(thresh, cv2.COLOR_GRAY2RGB)
        cv2.drawContours(output_im, bestContour, -1, (0,255,0), 3)
        bestContour[:, :, 0] = bestContour[:, :, 0] * 912/640
        bestContour[:, :, 1] = bestContour[:, :, 1] * 720/640
        bestContour = np.int32(bestContour, casting="unsafe")
        return bestContour
        # output_im[pt1[1]:pt2[1], pt1[0]:pt2[0]] = t
        # if bestContour.shape[0] > 5:
        #     ellipse = list(cv2.fitEllipse(bestContour))
        #     ellipse[0] = ellipse[0][0] + pt1[0], ellipse[0][1] + pt1[1]
        #     cv2.ellipse(output_im, tuple(ellipse), (255,0,255), 2)
