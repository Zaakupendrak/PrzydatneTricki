import base64
import pytesseract
import io
import json
import fitz
from PIL import Image
import cld3
import cv2
import numpy as np
import sys
from helpers.document_reader import *
import math
from collections import OrderedDict


def str_to_json_name(literal, toRemoveList=['\'', ':', '(', ')']):
    for tr in toRemoveList:
        literal = literal.replace(tr, '')
    return literal.lower().strip().replace(' ', '_').replace('-', '_')



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


def fix_word_typo(literal, typo_dict):
    fixed_literal = literal
    for typo, correction in zip(typo_dict.keys(), typo_dict.values()):
        if typo in literal:
            fixed_literal = fixed_literal.replace(typo, correction)
    return fixed_literal


def fix_sentence_typo(literal):
    literal = literal.strip()
    # Naprawiamy literówki w obrębie słów zgodnie ze słownikiem:
    typo_dict = {'adaptaiion': 'adaptation', 'centro': 'control', 'conirol': 'control', 'fram': 'from',
                 'laft': 'left', 'medule': 'module', 'maifunction': 'malfunction', 'senscr': 'sensor',
                 'senser': 'sensor', 'supplemenial': 'supplemental', 'temperaiure': 'temperature', 'toc': 'too',
                 'Cbar': '0bar', '.00C': '.00°C'}
    literal_sp = literal.split(' ')
    for word in literal_sp:
        if len(word) == 0:
            continue
        is_capital = word[0].isupper()
        word_lower = word.lower()
        if word.lower() in typo_dict:
            correction = typo_dict[word_lower]
            if is_capital:
                correction = correction.capitalize()
            literal_sp[literal_sp.index(word)] = correction
    return ' '.join(literal_sp)


def del_preceding_following_sign(literal):
    char_delete_list = ['-', '~', 'I ', '|', '&', '_', '+']
    if any(map(literal[:2].__contains__, char_delete_list)):
        literal = literal[1:]
    if any(map(literal[-2:].__contains__, char_delete_list)):
        literal = literal[:-1]
    return literal

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


class MyOrderedDict(OrderedDict):
    def get_last_key(self):
        if len(self) ==0:
            return None
        k = next(reversed(self))
        return k


def add_or_update_dict(ret_dict, key, kv_list, tolerance=17):
    # Tesseract czasami gubi linie dlatego sprawdzamy po założonej tolerancji czy nie przypiąć wartości
    # do istniejącego klucza z tolerancją
    for i in range(-tolerance, tolerance + 1):
        tmp_index = key + i
        tmp_key = ret_dict.get(tmp_index)
        if tmp_key:
            ret_dict[tmp_index][kv_list[0]] = kv_list[1]
            return
    # Wpp dodajemy nowy klucz
    # ret_dict[key] = {kv_list[0]: kv_list[1]}
    ret_dict[key] = MyOrderedDict([(kv_list[0], kv_list[1])])


def process_ocr(img):
    # cfg = r'--psm 6 --oem 3'
    # tesseract_boxes = pytesseract.image_to_data(img, config=cfg)
    tesseract_boxes = pytesseract.image_to_data(img)
    out_dict = MyOrderedDict()
    last_key_property = {}  # block_num:par_num:line_num:
    last_x = 0
    last_y = 0
    last_val = ''
    boxes = []
    for box in tesseract_boxes.splitlines()[1:]:
        # Pojedynczy box to lista metadanych opisana słownikiem box_field_dict
        line = box.split()
        if len(line) == 12:
            boxes.append(line)

    box_field_dict = {0: 'level', 1: 'page_num', 2: 'block_num', 3: 'par_num', 4: 'line_num',
                      5: 'word_num', 6: 'left', 7: 'top', 8: 'width', 9: 'height', 10: 'conf',
                      11: 'text'}
    for box in boxes:
        # print(box)
        this_key_property = {}
        for it in range(12):
            if it == 11:
                this_key_property[box_field_dict[it]] = box[it]
            else:
                this_key_property[box_field_dict[it]] = int(box[it])
        # this_key = '%s:%s:%s' % (box[2], box[3], box[4], )


        #Funkcja sprawdza czy text_box znajduje się w tej samej komórce co porpzedni napis
        def is_same_cell(last_key_prop, this_key_prop, tolerance=30):
            if len(last_key_prop) != 12:
                return False
            # Sprawdzamy czy porzedni i aktualny rekord Tesseract zinterpretował jako 'jedną komórkę'
            field_check_list = ['block_num', 'par_num', 'line_num']
            for field_name in field_check_list:
                if last_key_prop[field_name] != this_key_prop[field_name]:
                    return False
            # Sprawdzamy szerokość czy szerokość spacji nie przekroczyła tolerancji
            if this_key_prop['left'] - (last_key_prop['left'] + last_key_prop['width']) > tolerance:
                return False
            return True

        # Usunięcie wybranych znaków
        def repair_string(word):
            def replace_str_index(text, index=0, replacement=''):
                return '%s%s%s' % (text[:index], replacement, text[index + 1:])

            char_change_dict = {'|': 'I', '‘': '\''}
            tmp_word = word
            for char in word:
                if char in char_change_dict:
                    idx = word.index(char)
                    replace_val = char_change_dict[char]
                    # Jeśli kolejny znak jest taką samą wielką literą to pomijamy go
                    if replace_val.isupper() and len(word) >= idx+2 and word[idx + 1] == replace_val:
                        tmp_word = replace_str_index(tmp_word, idx, '')
                    else:
                        tmp_word = replace_str_index(tmp_word, idx, char_change_dict[char])

            return tmp_word

        this_val = repair_string(this_key_property['text'])
        if is_same_cell(last_key_property, this_key_property):
            if last_val == '':
                last_val += this_val
            else:
                last_val += ' %s' % this_val
        else:
            # Usuwamy niechciane znaki z początku lub końca napisu
            if len(last_val) >= 18:
                last_val = del_preceding_following_sign(last_val)

            # Usuwamy whitespace na końcu
            last_val = last_val.strip()
            last_val = fix_sentence_typo(last_val)

            # Dodajemy do słownika kompletną parę k:v
            if last_val != '':
                add_or_update_dict(out_dict, last_y, [last_x, last_val])
            # Ustawiamy nowe k:v
            last_val = this_val
            last_x = this_key_property['left']
            last_y = this_key_property['top']
        last_key_property = this_key_property
        # Dla ostatniego boxa dodajemy go od razu do  output dicta
        if boxes.index(box) == len(boxes) - 1:
            add_or_update_dict(out_dict, last_y, [last_x, last_val])

    return out_dict


def is_code_line(literal):
    literal_0_7 = literal[:7]
    has_many_words = len(literal.split(' ')) > 1
    return len(literal) > 8 and has_many_words and (literal_0_7.isupper() or literal_0_7.isnumeric())

def parse_ocr_data(ocr_data_page_list):
    data_list_type = ''
    parsed_block_list = []
    # print(json.dumps(ocr_data_page_list, indent=2, sort_keys=False, ensure_ascii=False))
    # Iterowanie po stronach
    for ocr_page_data in ocr_data_page_list:
        y_value_list = list(ocr_page_data.values())
        y_key_list = list(ocr_page_data.keys())
        # print('%s' % list(y_value_list[1].values())[0])
        # Srawdzenie czy dtc
        dtc_unique_list = ['supplemental information on time of occurrence',
                           'control unit-specific environmental data']
        is_dtc = False
        if len(y_value_list) >= 1:
            if any(map(list(y_value_list[1].values())[0].lower().__contains__, dtc_unique_list)):
                is_dtc = True
        # Inicjuję puste obiekty
        group_dict = MyOrderedDict()
        error_dict = MyOrderedDict()
        last_dict = MyOrderedDict()
        preproc_list = []

        for y_key, y_val in zip(y_key_list, y_value_list):
            x_keys = list(y_val.values())
            len_x_keys = len(x_keys)
            # print('y_key: %s' % y_val)
            # print('len_x_keys: %s' % len_x_keys)
            # if len(parsed_block_list) > 0:
            #     last_dict = parsed_block_list[-1]
            # else:
            #     last_dict = MyOrderedDict()
            #     parsed_block_list.append(last_dict)

            if is_dtc:
                data_list_type = 'dtc'
                key_0 = x_keys[0]
                key_0_lower = key_0.lower()
                is_code_record = is_code_line(key_0)
                # Nowy reokord błędu/odczuty
                if is_code_record or len_x_keys == 1:
                # if len(key_0) > 8 and key_0_lower not in dtc_unique_list:
                    # Sprawdzenie czy nie mamy doczynienia z multiline
                    print('x_keys:\n%s' % x_keys)
                    print('len(group_dict): %s' % len(group_dict))
                    # Dodanie całej grupy 'supplemental../control unit-specific..'
                    if key_0_lower in dtc_unique_list:
                        print(1)
                        # Dla kolejnej grupy w obrębie pliku dodajemy grupę do wyjsciowej listy
                        # if group_name != '':
                        #     parsed_block_list.append(MyOrderedDict([(group_name, group_dict)]))
                        group_name = str_to_json_name(key_0)
                        group_dict = MyOrderedDict()
                        __insert_into_dict(error_dict, group_name, group_dict)
                        # parsed_block_list.append(MyOrderedDict([(group_name, group_dict)]))
                    # Dodanie głównego obiektu błędu/odczytu
                    elif is_code_record:
                        print(2)

                        # if len(last_dict) == 0:
                        #     last_dict = MyOrderedDict()
                        #     parsed_block_list.append(last_dict)

                        def get_valid_code(code):
                            # Funkcja naprawia kody błędów wynikające z interprtacji tesseracta
                            code = code.replace('O', '0')
                            code_typo_dict = {'B00S': 'B009'}
                            for typo, correction in zip(code_typo_dict.keys(), code_typo_dict.values()):
                                code = code.replace(typo, correction)
                            return code

                        # Kod ma siedem znaków, później spacja i opis
                        error_dict = MyOrderedDict()
                        __insert_into_dict(error_dict, 'code', get_valid_code(key_0[:7]))
                        __insert_into_dict(error_dict, 'description', key_0[8:])
                        __insert_into_dict(error_dict, 'status', x_keys[1])
                        parsed_block_list.append(error_dict)
                        # __insert_into_dict(last_dict, 'error', error_dict)

                    # Uzupełnienie wiersza podzielonego w multiline
                    elif len(group_dict) > 0:
                        print(3)
                        prev_x = list(y_value_list[y_value_list.index(y_val)-1].keys())[0]
                        curr_x = y_val.get_last_key()
                        prev_y = y_key_list[y_key_list.index(y_key)-1]
                        curr_y = y_key
                        print('prev_x: %s, curr_x: %s, prev_y: %s, curr_y: %s' % (prev_x, curr_x, prev_y, curr_y))
                        if len_x_keys == 1 and abs(curr_y-prev_y) < 51 and abs(prev_x-curr_x) < 7:
                            key_to_update = group_dict.get_last_key()
                            new_key = '%s_%s' % (key_to_update, str_to_json_name(key_0.replace('’', '')))
                            group_dict[new_key] = group_dict.pop(key_to_update)

                        # print('y_value_list[y_value_list.index(y_val)-1]: %s' % y_value_list[y_value_list.index(y_val)-1])
                        # print(y_value_list.index(y_val))
                        # print('last_dict.get_last_key(): %s' % last_dict.get_last_key())


                # Pomijamy rekord ['Name', 'First occurrence', 'Last occurrence']
                else:
                    possible_row_start = ['ambient', 'average', 'battery', 'calculated', 'camshaft', 'cause', 'charge',
                                          'control', 'coolant', 'current', 'development', 'engine', 'exhaust', 'fault',
                                          'fuel', 'frequency', 'intake', 'main', 'number', 'operating', 'position',
                                          'pressure', 'status', 'supplemental', 'torque', 'total', 'variation']
                    if key_0.split(' ')[0].lower() not in possible_row_start:
                        continue
                    elif [k.split(' ')[0].lower() for k in x_keys] == ['name', 'first', 'last']:
                        continue
                    elif len_x_keys == 3:
                        main_key = str_to_json_name(key_0)
                        last_dict = MyOrderedDict()
                        value_typo_dict = {' ': '', '0Cbar': '00bar', 'mm*3/hub': 'mm^3/hub'}
                        __insert_into_dict(last_dict, 'first_occurrence', fix_word_typo(x_keys[1], value_typo_dict))
                        __insert_into_dict(last_dict, 'last_occurrence', fix_word_typo(x_keys[2], value_typo_dict))
                        __insert_into_dict(group_dict, main_key, last_dict)
                    elif len_x_keys == 2:
                        __insert_into_dict(group_dict, str_to_json_name(key_0), x_keys[1].replace(' ', ''))

            # Przetwarzanie dla service_memory i event_memory
            else:
                if len(x_keys) != 2:
                    continue
                preproc_list.append([str_to_json_name(x_keys[0].lower()), x_keys[1]])

        if preproc_list:
            unique_keys = []
            for k in [l[0] for l in preproc_list]:
                if k not in unique_keys:
                    unique_keys.append(k)

            em_data_dict = {'data_type': 'event_memory',
                            'required_key_list':
                                ['event_type', 'status', 'total_distance_at_first_occurrence_of_event',
                                 'total_distance_at_last_occurrence_of_event', 'frequency_counter',
                                 'number_of_ignition_cycles_since_last_occurrence_of_event']}
            sm_data_dict = {'data_type': 'service_memory',
                            'required_key_list':
                                ['entry', 'main_odometer_reading', 'day_cycle_counter',
                                 'travel_distance_since_last_service_due', 'days_since_last_service_due',
                                 'maintenance_type', 'reset', 'operations_performed', 'workshop_code']}

            def try_get_data_type(unique_key_list, data_type_dict_list):
                optional_keys = ['symbol', 'text']
                for data_type_dict in data_type_dict_list:
                    data_type = data_type_dict['data_type']
                    required_key_list = data_type_dict['required_key_list']

                    if all(required_key in unique_key_list for required_key in required_key_list):
                        required_key_list.extend(optional_keys)
                        return data_type, required_key_list
                return None, None

            data_list_type, possible_key_list = try_get_data_type(unique_keys, [em_data_dict, sm_data_dict])
            if data_list_type is None:
                return

            for k, v in preproc_list:
                if k not in possible_key_list:
                    continue
                if possible_key_list.index(k) == 0:
                    last_dict = MyOrderedDict()
                    parsed_block_list.append(last_dict)
                else:
                    last_dict = parsed_block_list[-1]
                # W niektórych tabelach klucze się powtarzają jeden po drugim
                __insert_into_dict(last_dict, k, v)
            # if len(parsed_block_list) > 0:
            #     last_dict = parsed_block_list[-1]
            # else:
            #     last_dict = MyOrderedDict()
            #     parsed_block_list.append(last_dict)

        # Jesli kolejny klucz jest w slowniku ale nie jest ostatnim kluczem to dodajemy nowy slownik
        # print('key: %s ' % key)
        # if last_dict.get(key) and last_dict.get_last_key() != key:
        #     print('last_dict.get_last_key(): %s' % last_dict.get_last_key())
        #     last_dict = MyOrderedDict()
        #     parsed_block_list.append(last_dict)
        # # W niektórych tabelach klucze się powtarzają jeden po drugim
        # __insert_into_dict(last_dict, key, value)

    # print(json.dumps(parsed_block_list, indent=2, sort_keys=False, ensure_ascii=False))
    if not parsed_block_list:
        return

    # data_list_type = try_get_data_type(parsed_block_list) if not data_list_type else data_list_type
    if data_list_type:
        return {data_list_type: parsed_block_list}
    return


def is_image_document(document_img_list):
    for page_img_list in document_img_list:
        if len(page_img_list) > 2:
            return True
    return False


def init_property_dict():
    return {
        'last_x': -1,
        'last_y_start': -1,
        'last_x_end': -1,
        'last_y_end': -1
    }


def set_bbox_prop(property_dict, bbox):
    property_dict['last_x'] = bbox[0]
    property_dict['last_y_start'] = bbox[1]
    property_dict['last_x_end'] = bbox[2]
    property_dict['last_y_end'] = bbox[3]


def get_last_bbox(property_dict):
    return (
        property_dict['last_x'],
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
    cv2.createTrackbar("kernel_11", "Trackbars", 3, 100, nothing)
    cv2.createTrackbar("kernel_12", "Trackbars", 3, 100, nothing)
    cv2.createTrackbar("kernel_21", "Trackbars", 1, 100, nothing)
    cv2.createTrackbar("kernel_22", "Trackbars", 1, 100, nothing)

def init_img_window(name):
    cv2.namedWindow(name)
    cv2.moveWindow(name, 0, 0)

def get_trackbars_val():
    Threshold1 = cv2.getTrackbarPos("thres_1", "Trackbars")
    Threshold2 = cv2.getTrackbarPos("thres_2", "Trackbars")
    kernel = cv2.getTrackbarPos("kernel", "Trackbars")
    itr = cv2.getTrackbarPos("blur_iter", "Trackbars")
    kernel11 = cv2.getTrackbarPos("kernel_11", "Trackbars")
    kernel12 = cv2.getTrackbarPos("kernel_12", "Trackbars")
    kernel21 = cv2.getTrackbarPos("kernel_21", "Trackbars")
    kernel22 = cv2.getTrackbarPos("kernel_22", "Trackbars")
    return Threshold1, Threshold2, kernel, itr, kernel11, kernel12, kernel21, kernel22,
#DEBUG


def clear_blue_box(img, x, y, w, h):
    # Czarna maska o wymiarach obrazu wejściowego
    mask2 = np.zeros_like(img)
    # Konwersja do palety szarości. Przy operacjach bitowych należy posługiwać się tą samą paletą
    # aby móc przeprowadzić operacje na macierzach o tym samym rozmiarze.
    mask2 = cv2.cvtColor(mask2, cv2.COLOR_BGR2GRAY)
    # Narysowanie na czarnej masce białego prostokąta o wymiarach poszukiwanego niebieskiego paska
    cv2.rectangle(mask2, (x, y), (x + w, y + h), (255, 255, 255), -1)
    # Inwersja kolorów maski: czarne tło, biały prostokąt
    mask2_inv = 255 - mask2
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img_gray_2 = img_gray.copy()
    # TODO nie wiem co to robi
    # img_gray_2[mask > 0] = (255, 255, 255)
    # Uzyskanie obrazu B&W. Wyciągnięcie białego tła - parametry dobrane w debuggowaniu.
    # thresh=195 - moc, maxval=255 - maksymalna jasność
    b_w_img = cv2.threshold(img_gray, 195, 255, cv2.THRESH_BINARY)[1]
    # Wybielenie tła poza prostokątem oraz uzyskanie bialego napisu na czarnym prostokącie
    b_w_masked = cv2.bitwise_or(b_w_img, mask2_inv)
    # Inwersja - biały napis, czarne tło
    b_w_masked_inv = 255 - b_w_masked
    # Z orginalnego obrazu w szarej palecie zastępujemy poszukiwany (niebieski) prostokąt nakładając
    # czarną maskę
    img_gray_2_masked = cv2.bitwise_and(img_gray_2, mask2_inv)
    # Czarny prostokąt zastępujemy białym z czarnym napisem
    res = cv2.bitwise_or(img_gray_2_masked, b_w_masked_inv)
    # Powrót do domyślnej palety barw
    return cv2.cvtColor(res, cv2.COLOR_GRAY2BGR)


if __name__ == "__main__":
    file_name = sys.argv[1]
    reader = DocumentReader()
    reader.read(file_name)
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
        #init_trackbars()
        # TODO DEBUG ↑
        # Zakładam dwie opcje orientacji obrazu
        for i in range(2):
        # for i in range(1):
            ocred_data_list = []
            k = 0
            is_image_cropped = False
            cropped_processing_type_list = ['event_memory', 'instrument_cluster', 'next_service', 'service_date',
                                            'service_memory']
            cropped_processing_type = None
            for img in img_list:
                k += 1
                if i > 0:
                    img = rotate_image(img, -90)
                img_h, img_w = img.shape[:2]
                # Konwersja do HSV żeby łatwiej wyfiltrować niebieski pasek
                hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                # Zakres koloru niebieskiego w palecie Hue (HSV)
                lower_blue = np.array([100, 50, 50])
                upper_blue = np.array([130, 255, 255])
                # Wyciągnięcie maski dla niebieskiego zakresu
                mask = cv2.inRange(hsv, lower_blue, upper_blue)
                # cv2.imwrite('out/mask_11.png', mask)
                # Przeszukanie kontórów w celu odfiltrowania niebieskiego paska
                blue_contours = cv2.findContours(
                    mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
                # Minimalna wysokość i szerokość paska
                min_h = 29
                min_w = img_w*0.97
                # cv2.imwrite('out/service_memory.png', img)
                for cnt in blue_contours:
                    x, y, w, h = cv2.boundingRect(cnt)
                    # Filtorowanie dla znalezienia konturu o wymaganym rozmiarze
                    if w > h >= min_h and w >= min_w:
                        img = clear_blue_box(img, x, y, w, h)
                    # Przypadek gdy istnieje pasek i nie zajmuję prawie całej szerokości
                    # Np dla plików service_memory
                    elif min_w > w > h >= min_h or min_h <= w < h <= min_w:
                        # print('\n\n\n\n\n ==========   EEEELO ============= \n\n\n')
                        img = clear_blue_box(img, x, y, w, h)
                        # Wycinamy text z boxa w celu dopasowania przetwarzania
                        selected_box = img[y:y+h, x:x+w]
                        cropped_processing_type = \
                            pytesseract.image_to_string(selected_box).lower().strip().replace(' ', '_')
                        # cv2.imwrite('out/service_memory_box.png', selected_box)
                        # Pasek wskazujący na typ pliku
                        if w > h:
                            img = img[0:img_h, (x + w):img_w]
                        else:
                            img = img[0:y, 0:img_w]
                        img_h, img_w = img.shape[:2]
                        is_image_cropped = True
                        # cv2.imwrite('out/service_memory_cropped.png', img)
                # Konwersja do palety szarości
                img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                # Uzyskanie obrazu B&W. Wyciągnięcie białego tła - parametry dobrane w debuggowaniu.
                # thresh=140 - moc, maxval=255 - maksymalna jasność
                if is_image_cropped:
                    if cropped_processing_type not in cropped_processing_type_list:
                        continue
                    img = cv2.threshold(img, 180, 255, cv2.THRESH_BINARY)[1]
                else:
                    img = cv2.threshold(img, 140, 255, cv2.THRESH_BINARY)[1]

                # USUWANIE LINII
                # B&W - czarne tło, białe napisy
                thresh = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
                vertical = np.copy(thresh)
                horizontal = np.copy(thresh)
                # Pogrubienie tylko w kierunku Y (czarne elementy powiększają wysokość)
                horizontal = cv2.dilate(horizontal, kernel=cv2.getStructuringElement(cv2.MORPH_RECT, (1, 17)))
                # cv2.imwrite('out/h1.jpg', horizontal)
                # Pocienienie w obu kierunkach X i Y z przewagą X w celu pozostawienia widocznych samych linii
                horizontal = cv2.erode(horizontal, kernel=cv2.getStructuringElement(cv2.MORPH_RECT, (34, 16)))
                # cv2.imwrite('out/h2.jpg', horizontal)
                # Wydłużenie linii w kierunku X
                horizontal = cv2.dilate(horizontal, kernel=cv2.getStructuringElement(cv2.MORPH_RECT, (40, 3)))
                # cv2.imwrite('out/h3.jpg', horizontal)
                # Pogrubienie tylko w kierunku X (czarne elementy powiększają szerokość)
                vertical = cv2.dilate(vertical, kernel=cv2.getStructuringElement(cv2.MORPH_RECT, (3, 1)))
                # Pocienienie w obu kierunkach X i Y z przewagą Y w celu pozostawienia widocznych samych linii
                vertical = cv2.erode(vertical, kernel=cv2.getStructuringElement(cv2.MORPH_RECT, (1, 18)))
                # Wydłużenie linii w kierunku Y
                vertical = cv2.dilate(vertical, kernel=cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25)))
                # Usunięcie kolejno linii pionowych i poziomych przy użyciu masek
                b_or = cv2.bitwise_or(img, vertical)
                img = cv2.bitwise_or(b_or, horizontal)
                # Wygładzenie krawędzi (liter)
                blur = cv2.GaussianBlur(img, (5, 5), 0)
                # Przeskalowanie x2 wygładzonego obrazu i orginalnego
                scale_factor = 2
                blur = cv2.resize(blur, (img_w * scale_factor, img_h * scale_factor))
                img = cv2.resize(img, (img_w * scale_factor, img_h * scale_factor))
                # Macierz filtrująca - wyostrzająca
                # kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
                # img = cv2.filter2D(blur, -1, kernel)
                # Druga metoda wyostrzenia, daje mocniejszy efekt w zależności od róznicy parametrów alpha i beta
                img = cv2.addWeighted(img, 1.5, blur, -0.5, 0)
                # cv2.imwrite('out/res.png', img)
                # cv2.imwrite('out/%s.png' % file_name.split('.')[0], img)
                ocred_data_list.append(process_ocr(img))

                f = open('out/%s_debug.json' % file_name.split('.')[0], 'w')
                f.write(json.dumps(ocred_data_list, indent=2, sort_keys=False, ensure_ascii=False))
                f.close()

            # print(json.dumps(ocred_data_list, indent=2, sort_keys=False, ensure_ascii=False))
            out_data = parse_ocr_data(ocred_data_list)
            print(json.dumps(out_data, indent=2, sort_keys=False, ensure_ascii=False))
            if out_data:
                # print(json.dumps(out_data, indent=2, sort_keys=False, ensure_ascii=False))
                f = open('out/%s.json' % file_name.split('.')[0], 'w')
                f.write(json.dumps(out_data, indent=2, sort_keys=False, ensure_ascii=False))
                f.close()
                break
