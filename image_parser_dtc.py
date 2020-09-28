import base64
import pytesseract
import io
import json
import fitz
from PIL import Image
import cv2
import numpy as np
import sys
from helpers.document_reader import *
import math
from collections import OrderedDict


def str_to_json_name(literal, toRemoveList=['\'', ':', '(', ')']):
    for tr in toRemoveList:
        literal = literal.replace(tr, '')
    return literal.lower().strip().replace(' ', '_')



def __insert_into_dict(_dict, key, value):
    # currently no key in dict -> insert value
    if key not in _dict:
        _dict[key] = value
    # currently single value as string -> convert to list
    elif type(_dict[key]) is not list:
        _dict[key] = [_dict[key], value]
    # already a list -> append value
    else:
        _dict[key].append(value)


def img_data_to_cv2(img_data):
    if not isinstance(img_data, bytes):
        img_data = base64.b64decode(img_data)
    np_arr = np.fromstring(img_data, np.uint8)
    # return cv2.imdecode(np_arr, cv2.IMREAD_GRAYSCALE)
    return cv2.imdecode(np_arr, cv2.IMREAD_COLOR)


def rotate_image(mat, angle):
   """
   Rotates an image (angle in degrees) and expands image to avoid cropping
   """
   #
   height, width = mat.shape[:2]  # image shape has 3 dimensions
   center = (
   width / 2, height / 2)  # getRotationMatrix2D needs coordinates in reverse order (width, height) compared to shape
   #
   rotation_mat = cv2.getRotationMatrix2D(center, angle, 1.)
   # rotation calculates the cos and sin, taking absolutes of those.
   abs_cos = abs(rotation_mat[0, 0])
   abs_sin = abs(rotation_mat[0, 1])
   # find the new width and height bounds
   bound_w = int(height * abs_sin + width * abs_cos)
   bound_h = int(height * abs_cos + width * abs_sin)
   # subtract old image center (bringing image back to origo) and adding the new image center coordinates
   rotation_mat[0, 2] += bound_w / 2 - center[0]
   rotation_mat[1, 2] += bound_h / 2 - center[1]
   # rotate image with the new bounds and translated rotation matrix
   rotated_mat = cv2.warpAffine(mat, rotation_mat, (bound_w, bound_h))
   return rotated_mat

def PrintWordsBoxes(img):
    #[   0          1           2           3           4          5         6       7       8        9        10       11 ]
    #['level', 'page_num', 'block_num', 'par_num', 'line_num', 'word_num', 'left', 'top', 'width', 'height', 'conf', 'text']
    boxes = pytesseract.image_to_data(img)
    for a,b in enumerate(boxes.splitlines()):
            # print(b)
            if a!=0:
                b = b.split()
                if len(b)==12:
                    x,y,w,h = int(b[6]),int(b[7]),int(b[8]),int(b[9])
                    cv2.putText(img,b[11],(x,y-5),cv2.FONT_HERSHEY_SIMPLEX,1,(50,50,255),2)
                    cv2.rectangle(img, (x,y), (x+w, y+h), (50, 50, 255), 2)


def stack_images(img_array, scale=1):
    rows = len(img_array)
    cols = len(img_array[0])
    rows_available = isinstance(img_array[0], list)
    width = img_array[0][0].shape[1]
    height = img_array[0][0].shape[0]
    if rows_available:
        for x in range(0, rows):
            for y in range(0, cols):
                if img_array[x][y].shape[:2] == img_array[0][0].shape[:2]:
                    img_array[x][y] = cv2.resize(img_array[x][y], (0, 0), None, scale, scale)
                else:
                    img_array[x][y] = cv2.resize(img_array[x][y], (img_array[0][0].shape[1], img_array[0][0].shape[0]),
                                                 None, scale, scale)
                if len(img_array[x][y].shape) == 2:
                    img_array[x][y] = cv2.cvtColor(img_array[x][y], cv2.COLOR_GRAY2BGR)
        image_blank = np.zeros((height, width, 3), np.uint8)
        hor = [image_blank] * rows
        for x in range(0, rows):
            hor[x] = np.hstack(img_array[x])
        ver = np.vstack(hor)
    else:
        for x in range(0, rows):
            if img_array[x].shape[:2] == img_array[0].shape[:2]:
                img_array[x] = cv2.resize(img_array[x], (0, 0), None, scale, scale)
            else:
                img_array[x] = cv2.resize(img_array[x], (img_array[0].shape[1], img_array[0].shape[0]),
                                          None, scale, scale)
            if len(img_array[x].shape) == 2:
                img_array[x] = cv2.cvtColor(img_array[x], cv2.COLOR_GRAY2BGR)
        hor = np.hstack(img_array)
        ver = hor
    return ver


def process_ocr(img):
    tesseract_boxes = pytesseract.image_to_data(img)
    out_dict = {}
    last_key = '-1:-1:-1'  # block_num:par_num:line_num
    last_x_start = 0
    last_y_ave = 0
    last_val = ''
    # Boxy przechowują dane
    # ['level', 'page_num', 'block_num', 'par_num', 'line_num', 'word_num', 'left','top', 'width', 'height', 'conf', 'text']
    boxes = []
    for box in tesseract_boxes.splitlines()[1:]:
        line = box.split()
        if len(line) == 12:
            boxes.append(line)

    for box in boxes:
        this_key = '%s:%s:%s' % (box[2], box[3], box[4])
        def add_or_update_dict(ret_dict, key, kv_list, tolerance=15):
            # Tesseract czasami gubi linie dlatego sprawdzamy po założonej tolerancji czy nie przypiąć wartości
            # do istniejącego klucza
            for i in range(0, tolerance + 1):
                tmp_key = key + i
                if ret_dict.get(tmp_key):
                    ret_dict[tmp_key][kv_list[0]] = kv_list[1]
                    return
            # Wpp dodajemy nowy klucz
            ret_dict[key] = {kv_list[0]: kv_list[1]}

        if this_key == last_key:
            last_val += ' %s' % box[11]
        else:
            # Dodajemy do słownika kompletną parę k:v
            if last_val != 0:
                add_or_update_dict(out_dict, last_y_ave, [last_x_start, last_val])
            # Ustawiamy nowe k:v
            last_val = box[11]
            last_y_ave = int(box[7])
            last_x_start = int(box[6])
            last_key = this_key
        # Dla ostatniego boxa dodajemy go od razu do  output dicta
        if boxes.index(box) == len(boxes) - 1:
            add_or_update_dict(out_dict, last_y_ave, [last_x_start, last_val])

    return out_dict


def parse_ocr_data(ocr_data_page_list):
    class MyOrderedDict(OrderedDict):
        def last_key(self):
            k = next(reversed(self))
            return k

    def get_data_type(parsed_data_list):
        event_memory_keys = ['event_type', 'status', 'total_distance_at_first_occurrence_of_event',
                             'total_distance_at_last_occurrence_of_event', 'frequency_counter',
                             'number_of_ignition_cycles_since_last_occurrence_of_event']
        service_memory_keys = ['entry', 'main_odometer_reading', 'day_cycle_counter',
                               'travel_distance_since_last_service_due', 'days_since_last_service_due',
                               'maintenance_type', 'reset', 'operations_performed', 'workshop_code']
        # optional_keys = ['symbol', 'text']

        parsed_data_block = parsed_data_list[0]
        for list_type, expected_key_list in [('event_memory', event_memory_keys),
                                             ('service_memory', service_memory_keys)]:
            if all(expected_key in parsed_data_block for expected_key in expected_key_list):
                return list_type
        return None

    parsed_block_list = []
    for ocr_page_data in ocr_data_page_list:
        for y_key in ocr_page_data.values():
            x_keys = list(y_key.values())
            if len(x_keys) != 2:
                continue

            key = str_to_json_name(x_keys[0].lower())
            value = x_keys[1]
            if len(parsed_block_list) > 0:
                last_dict = parsed_block_list[-1]
            else:
                last_dict = MyOrderedDict()
                parsed_block_list.append(last_dict)
            # Jesli kolejny klucz jest w slowniku ale nie jest ostatnim kluczem to dodajemy nowy slownik
            if last_dict.get(key) and last_dict.last_key() != key:
                last_dict = MyOrderedDict()
                parsed_block_list.append(last_dict)
            # W niektórych tabelach klucze się powtarzają jeden po drugim
            __insert_into_dict(last_dict, key, value)

    # print(json.dumps(parsed_block_list, indent=2, sort_keys=False, ensure_ascii=False))
    if not parsed_block_list:
        return
    data_list_type = get_data_type(parsed_block_list)
    if data_list_type is not None:
        return {data_list_type: parsed_block_list}
    return


def is_image_document(document_img_list):
    for page_img_list in document_img_list:
        if len(page_img_list) > 2:
            return True
    return False


def init_property_dict():
    return {
        'last_x_start': -1,
        'last_y_start': -1,
        'last_x_end': -1,
        'last_y_end': -1
    }


def set_bbox_prop(property_dict, bbox):
    property_dict['last_x_start'] = bbox[0]
    property_dict['last_y_start'] = bbox[1]
    property_dict['last_x_end'] = bbox[2]
    property_dict['last_y_end'] = bbox[3]


def get_last_bbox(property_dict):
    return (
        property_dict['last_x_start'],
        property_dict['last_y_start'],
        property_dict['last_x_end'],
        property_dict['last_y_end']
    )


def is_img_continuation(current_bbox, last_bbox):
    # x_start równe
    if current_bbox[0] != last_bbox[0]:
        return False
    # x_end równe
    if current_bbox[2] != last_bbox[2]:
        return False
    # Zaokrąglone w góre curr_y_start równe last_y_end
    if abs(current_bbox[1]-last_bbox[3]) > 1:
        return False
    return True


#DEBUG
def nothing(x):
    pass

def init_trackbars():
    cv2.namedWindow("Trackbars")
    cv2.resizeWindow("Trackbars", 360, 240)
    cv2.moveWindow('Trackbars', 0, 0)
    cv2.createTrackbar("thres_1", "Trackbars", 144, 255, nothing)
    cv2.createTrackbar("thres_2", "Trackbars", 255, 255, nothing)
    cv2.createTrackbar("kernel", "Trackbars", 1, 7, nothing)
    cv2.createTrackbar("blur_iter", "Trackbars", 1, 7, nothing)

def init_img_window(name):
    cv2.namedWindow(name)
    cv2.moveWindow(name, 0, 0)

def get_trackbars_val():
    Threshold1 = cv2.getTrackbarPos("thres_1", "Trackbars")
    Threshold2 = cv2.getTrackbarPos("thres_2", "Trackbars")
    kernel = cv2.getTrackbarPos("kernel", "Trackbars")
    itr = cv2.getTrackbarPos("blur_iter", "Trackbars")
    return Threshold1, Threshold2, kernel, itr
#DEBUG

if __name__ == "__main__":
    reader = DocumentReader()
    reader.read(sys.argv[1])
    doc = reader.get_images()
    out_data = []
    if is_image_document(doc):
        img_list = []
        for page in doc['pages']:
            prop_dict = init_property_dict()
            # Pierwsze dwa bloki to Xentry i Mercedes więc je pomijamy
            for block in page['images'][2:]:
                # TODO - tylko do debugowania
                # block['image'] = b'image_bytes/b64str_here'
                tmp_bbox = block['bbox']
                tmp_img = img_data_to_cv2(block['image'])
                if is_img_continuation(tmp_bbox, get_last_bbox(prop_dict)):
                    img_list[-1] = cv2.vconcat([img_list[-1], tmp_img])
                else:
                    img_list.append(tmp_img)
                set_bbox_prop(prop_dict, tmp_bbox)

        # TODO DEBUG ↓
        init_trackbars()
        # init_img_window('image_bw')
        # init_img_window('image_blur')
        # TODO DEBUG ↑
        # for i in range(2):
        for i in range(1):
            ocred_data_list = []
            for img in img_list:
                if i > 0:
                    img = rotate_image(img, -90)
                # # TODO DEBUG ↓
                while True:
                    tb = get_trackbars_val()
                    print('tb[0] = %s    | tb[1] = %s' % (tb[0], tb[1]))
                    # b_w_img = cv2.threshold(img, tb[0], tb[1], cv2.THRESH_BINARY)[1]


                    # # cv2.getStructuringElement(cv2.MORPH_RECT)
                    # cv2.imshow("img_orig", img)
                    # hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                    # # define range of black color in HSV
                    # lower_blue = np.array([100, 150, 0])
                    # upper_blue = np.array([140, 255, 255])
                    # # Threshold the HSV image to get only black colors
                    # mask = cv2.inRange(hsv, lower_blue, upper_blue)
                    # # Bitwise-AND mask and original image
                    # res = cv2.bitwise_and(img, img, mask=mask)
                    # # invert the mask to get black letters on white background
                    # res2 = cv2.bitwise_not(mask)
                    # cv2.imshow("img", res)
                    # cv2.imshow("img2", res2)

                    # # cv2.imshow('image_bw', b_w_img)

                    # Load image, create blank mask, convert to grayscale, Gaussian blur
                    # then adaptive threshold to obtain a binary image
                    # image = img
                    # mask = np.zeros(image.shape, dtype=np.uint8)
                    # gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                    # blur = cv2.GaussianBlur(gray, (7, 7), 0)
                    # thresh = cv2.adaptiveThreshold(
                    #     blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 51, 9)
                    #
                    # # Create horizontal kernel then dilate to connect text contours
                    # kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 2))
                    # dilate = cv2.dilate(thresh, kernel, iterations=2)
                    #
                    # # Find contours and filter out noise using contour approximation and area filtering
                    # cnts = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    # cnts = cnts[0] if len(cnts) == 2 else cnts[1]
                    # for c in cnts:
                    #     peri = cv2.arcLength(c, True)
                    #     approx = cv2.approxPolyDP(c, 0.04 * peri, True)
                    #     x, y, w, h = cv2.boundingRect(c)
                    #     area = w * h
                    #     ar = w / float(h)
                    #     if area > 1200 and area < 50000 and ar < 6:
                    #         cv2.drawContours(mask, [c], -1, (255, 255, 255), -1)
                    #
                    # # Bitwise-and input image and mask to get result
                    # mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
                    # result = cv2.bitwise_and(image, image, mask=mask)
                    # # result[mask == 0] = (255, 255, 255)  # Color background white
                    #
                    # cv2.imshow('thresh', thresh)
                    # cv2.imshow('mask', mask)
                    # cv2.imshow('result', result)

                    # b_w_img = cv2.threshold(img, tb[0], tb[1], cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
                    # cv2.imshow('image_bw', b_w_img)
                    # dist_img = cv2.distanceTransform(b_w_img, cv2.DIST_L2, cv2.DIST_MASK_PRECISE)
                    # stroke_width = 8
                    # dist_bw = cv2.threshold(dist_img, stroke_width/2, 255, cv2.THRESH_BINARY)[1]
                    # cv2.imshow('dist_bw', dist_bw)
                    # kernel = cv2.getStructuringElement(cv2.MORPH_RECT, Size(3, 3))
                    # morph = cv2.morphologyEx(dist_bw, cv2.MORPH_OPEN, kernel)
                    # arr_u8 = np.uint8(morph)
                    # binary = cv2.cvtColor(dist_bw, cv2.COLOR_GRAY2BGR)
                    #
                    # rows, cols = img.shape
                    # htresh = rows * 0.5
                    # contours, hierarchy = cv2.findContours(arr_u8, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
                    # for idx in hierarchy[0]:
                    #     rect = cv2.boundingRect(contours[idx])
                    #     if rect.height > htrsh:

                    # apply threshold
                    # gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    # thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)[1]
                    # # find contours and get one with area about 180*35
                    # # draw all contours in green and accepted ones in red
                    # contours = cv2.findContours(thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
                    # contours = contours[0] if len(contours) == 2 else contours[1]
                    # # area_thresh = 0
                    # height, width = img.shape[:2]
                    # min_h = 30
                    # min_w = width*0.97
                    #
                    # result = img.copy()
                    # for c in contours:
                    #     x, y, w, h = cv2.boundingRect(c)
                    #     cv2.drawContours(result, [c], -1, (0, 255, 0), 1)
                    #     if h >= min_w and w >= min_w:
                    #         cv2.drawContours(result, [c], -1, (0, 0, 255), 1)
                    #
                    # # save result
                    # cv2.imwrite("box_found.png", result)
                    #
                    # # show images
                    # cv2.imshow("orig", img)
                    # cv2.imshow("THRESH", thresh)
                    # cv2.imshow("RESULT", result)

                    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                    # define range of blue color in HSV
                    lower_blue = np.array([100, 50, 50])
                    upper_blue = np.array([130, 255, 255])
                    # Threshold the HSV image to get only blue colors
                    mask = cv2.inRange(hsv, lower_blue, upper_blue)
                    blue_contours = cv2.findContours(mask.copy(),
                                                cv2.RETR_EXTERNAL,
                                                cv2.CHAIN_APPROX_SIMPLE)[-2]
                    img_h, img_w = img.shape[:2]
                    min_h = 30
                    min_w = img_w*0.97
                    for cnt in blue_contours:
                        x, y, w, h = cv2.boundingRect(cnt)
                        if h >= min_h and w >= min_w:
                            image2 = img.copy()
                            # image2[mask > 0] = (255, 255, 255)
                            # image2[mask > 0] = (255, 255, 255)
                            mask2 = np.zeros_like(img)
                            cv2.rectangle(mask2, (x, y), (x + w, y + h), (255, 255, 255), -1)
                            cv2.imwrite('mask2.png', mask2)
                            cv2.imwrite('mask1.png', mask)
                            # invert mask
                            mask2_inv = 255 - mask2
                            # apply mask to image
                            img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                            cv2.imwrite('img_gray.png', img_gray)
                            # 195 - wartość otrzymana w debugowaniu, 255 - maksymalna jasność
                            b_w_img = cv2.threshold(img_gray, 195, 255, cv2.THRESH_BINARY)[1]
                            # cv2.imshow('b_w_img',  b_w_img)
                            b_w_bgr = cv2.cvtColor(b_w_img, cv2.COLOR_GRAY2BGR)
                            cv2.imwrite('b_w_bgr.png', b_w_bgr)
                            b_w_masked = cv2.bitwise_or(b_w_bgr, mask2_inv)
                            cv2.imwrite('b_w_masked.png', b_w_masked)
                            # invert
                            b_w_masked_inv = 255 - b_w_masked
                            cv2.imwrite('b_w_masked_inv.png', b_w_masked_inv)
                            image_masked = cv2.bitwise_and(img, mask2)
                            # cv2.imwrite('image_masked.png', image_masked)
                            # cv2.imwrite('image2.png', image2)
                            # cv2.imwrite('mask2_inv.png', mask2_inv)
                            # apply inverted mask to image2
                            image2_masked = cv2.bitwise_and(image2, mask2_inv)
                            cv2.imwrite('image_masked2.png', image2_masked)
                            result = cv2.bitwise_or(image2_masked, b_w_masked_inv)
                            cv2.imwrite('result.png', result)

                    # 140 - wartość otrzymana w debugowaniu, 255 - maksymalna jasność
                    img = cv2.threshold(result, 140, 255, cv2.THRESH_BINARY)[1]
                    cv2.imshow('result->img', img)
                    break
                    # cv2.imshow('frame', img)
                    # cv2.imshow('mask', mask)

                    if cv2.waitKey(1):
                        pass
                #
                # # TODO DEBUG ↑
                # img_g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                # b_w_img = cv2.threshold(img_g, 150, 255, cv2.THRESH_BINARY)[1]
                # cv2.imwrite('dtc1_b_w.png', b_w_img)
                # ocred_data_list.append(process_ocr(b_w_img))
                ocred_data_list.append(process_ocr(img))
                f = open('dtc1.json', 'w')
                f.write(json.dumps(ocred_data_list, indent=2, sort_keys=False, ensure_ascii=False))
                f.close()

            print(json.dumps(ocred_data_list, indent=2, sort_keys=False, ensure_ascii=False))
            out_data = parse_ocr_data(ocred_data_list)
            if out_data:
                # print(json.dumps(out_data, indent=2, sort_keys=False, ensure_ascii=False))
                break
