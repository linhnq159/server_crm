import re
import cv2
from PIL import Image
import pytesseract
from pytesseract import Output
import os
import numpy as np

# Đổi thành chữ không dấu
def no_accent_vietnamese(s):
    s = re.sub(r'[àáạảãâầấậẩẫăằắặẳẵ]', 'a', s)
    s = re.sub(r'[ÀÁẠẢÃĂẰẮẶẲẴÂẦẤẬẨẪ]', 'A', s)
    s = re.sub(r'[èéẹẻẽêềếệểễ]', 'e', s)
    s = re.sub(r'[ÈÉẸẺẼÊỀẾỆỂỄ]', 'E', s)
    s = re.sub(r'[òóọỏõôồốộổỗơờớợởỡ]', 'o', s)
    s = re.sub(r'[ÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠ]', 'O', s)
    s = re.sub(r'[ìíịỉĩ]', 'i', s)
    s = re.sub(r'[ÌÍỊỈĨ]', 'I', s)
    s = re.sub(r'[ùúụủũưừứựửữ]', 'u', s)
    s = re.sub(r'[ƯỪỨỰỬỮÙÚỤỦŨ]', 'U', s)
    s = re.sub(r'[ỳýỵỷỹ]', 'y', s)
    s = re.sub(r'[ỲÝỴỶỸ]', 'Y', s)
    s = re.sub(r'[Đ]', 'D', s)
    s = re.sub(r'[đ]', 'd', s)
    return s

# Xóa các dấu câu
def no_end(s):
    s = re.sub(r'[.,;!?:`~—#-]', '', s)
    return s

def adjust_gamma(image,gamma):
    invGamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** invGamma) * 255
                      for i in np.arange(0, 256)]).astype("uint8")
    return cv2.LUT(image, table)

def xoa_contour(gray):
    # Xóa các logo
    contours, hierarchy = cv2.findContours(gray.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    for c in contours:
        area = cv2.contourArea(c)
        if area > 1000 and area < 100000:
            cv2.drawContours(gray, [c], -1, (255, 255, 255), cv2.FILLED)
    return gray

def xoa_duong_thang(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    clean = thresh.copy()
    # cv2.imshow('thresh.jpg',thresh)
    # cv2.waitKey()

    # Remove horizontal lines
    horizal = thresh
    vertical = thresh

    scale_height = 20  # Scale này để càng cao thì số dòng dọc xác định sẽ càng nhiều
    scale_long = 15

    long = int(image.shape[1] / scale_long)
    height = int(image.shape[0] / scale_height)

    # Tìm đường thẳng dọc
    horizalStructure = cv2.getStructuringElement(cv2.MORPH_RECT, (long, 1))
    horizal = cv2.erode(horizal, horizalStructure, (-1, -1))
    horizal = cv2.dilate(horizal, horizalStructure, (-1, -1))

    # Tìm đường thẳng ngang
    verticalStructure = cv2.getStructuringElement(cv2.MORPH_RECT, (1, height))
    vertical = cv2.erode(vertical, verticalStructure, (-1, -1))
    vertical = cv2.dilate(vertical, verticalStructure, (-1, -1))
    mask = vertical + horizal
    cnts, hierarchy = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    for c in cnts:
        cv2.drawContours(image, [c], -1, (255, 255, 255), 3)

    return image


# Sử dụng tesseract để predict
def tesseract_predict(image):
    # Đọc ảnh đầu vào
    image = cv2.imread(image)

    # Set up gamma ảnh sáng tối
    image = adjust_gamma(image, gamma=1.0)

    # Xóa đường thẳng
    image = xoa_duong_thang(image)

    # Chuyển về ảnh xám đặt ngưỡng threshold
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # image = cv2.GaussianBlur(image, (1, 1), 0)
    gray = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

    # Xóa các logo
    gray = xoa_contour(gray)

    # Ghi tạm ảnh xuống ổ cứng để sau đó apply OCR
    filename = "result.png".format(os.getpid())
    # cv2.imwrite("result1.png", gray)
    cv2.imwrite(filename, gray)

    # text = pytesseract.image_to_string(Image.open(filename),config='--psm 4 + --oem 2', lang='vie')
    # print(text)

    # Trả về đặc tính các từ
    results = pytesseract.image_to_data(Image.open(filename),config='--psm 4 + --oem 2', output_type=Output.DICT, lang='vie')
    return results

# Tìm chuỗi khớp
def tim_chuoi_khop(text_change_org, results):
    text_change = no_end(no_accent_vietnamese(text_change_org))
    # text_change = text_change.lower()
    text_change = text_change.split(' ')
    text_change = [text_remove for text_remove in text_change if text_remove != '']
    # tìm chuỗi khớp cả câu
    bien_check = 0
    j = 0
    paint_list = []
    paint_cong = []
    i = 0
    # loop over each of the individual text localizations
    # for i in range(len(results["text"])):
    if len(text_change) != 1:
        while i < len(results["text"]):
            if no_end(results["text"][i]).replace(' ', '') != '':
                # extract the OCR text itself along with the confidence of the
                # filter out weak confidence text localizations
                if bien_check % 2 == 0 and no_end(text_change[0]) == no_end(
                        no_accent_vietnamese(results["text"][i])):
                    bien_check += 1
                    paint_cong.append(i)
                    j = j + 1
                    i = i + 1
                    continue
                if bien_check % 2 == 1:
                    if no_end(text_change[j]) == no_end(no_accent_vietnamese(results["text"][i])):
                        if (j + 1) == len(text_change):
                            paint_cong.append(i)
                            j = 0
                            i = i + 1
                            bien_check += 1
                            paint_list += paint_cong
                            paint_cong = []
                            continue

                        j = j + 1
                        paint_cong.append(i)
                        i = i + 1
                        continue
                    else:
                        j = 0
                        paint_cong = []
                        bien_check = 0
                        i = i - 1
            i = i + 1
    else:
        while i < len(results["text"]):
            if float(results["conf"][i]) > 50:
                if no_end(text_change[0]) == no_end(no_accent_vietnamese(results["text"][i])):
                    paint_list.append(i)
                    i = i + 1
                    continue
            i += 1
    # print(paint_list)
    return paint_list


# def to_vang(image, paint_list, results, text_change_org):
#     input_img , img_end = os.path.splitext(image)
#     image_output = input_img + '_output' + img_end
#     img = cv2.imread(image)
#     img1 = img.copy()
#     text_change = no_end(no_accent_vietnamese(text_change_org))
#     text_change = text_change.split(' ')
#     text_change = [text_remove for text_remove in text_change if text_remove != '']
#     h_max = 0
#     x_index = paint_list[0]
#     list_dong_tren = []
#     list_new_text = []
#     for i in range(len(paint_list)):
#         # extract the bounding box coordinates of the text region from
#         # the current result
#         h = results["top"][paint_list[i]] + results["height"][paint_list[i]]
#         if h > h_max:
#             h_max = h
#         if (i + 1) % len(text_change) == 0:
#             x_t = results["left"][x_index]
#             x_s = results["left"][paint_list[i]]
#             y = min(results["top"][x_index: paint_list[i] + 1])
#             w = results["width"][paint_list[i]]
#             for j in range(x_t, x_s + w):
#                 for k in range(y, h_max):
#                     if 175 < img1[k][j][0] <= 255 and 175 < img1[k][j][1] <= 255 and 175 < img1[k][j][2] <= 255:
#                         img1[k][j][0] = 0
#                         img1[k][j][1] = 255
#                         img1[k][j][2] = 255
#
#             cv2.imwrite(image, img1)
#             cv2.imshow(image, img1)
#             print("Bạn muốn thay đổi thành :")
#             new_text = str(input())
#             if new_text != '':
#                 list_new_text.append(new_text)
#                 cv2.rectangle(img1, (x_t, y), (x_s + w, h_max), (255, 255, 255), cv2.FILLED)
#                 if list_dong_tren != []:
#                     cv2.rectangle(img1, (list_dong_tren[0], list_dong_tren[2]), (list_dong_tren[1], list_dong_tren[3]),
#                                   (255, 255, 255), cv2.FILLED)
#                     list_dong_tren = []
#                 img = img1.copy()
#             if new_text == '':
#                 list_new_text.append(' ')
#                 img1 = img.copy()
#             h_max = 0
#             if i < len(paint_list) - 1:
#                 x_index = paint_list[i + 1]
#
#             continue
#
#         if results["word_num"][paint_list[i + 1]] - results["word_num"][paint_list[i]] < 0:
#             x_t = results["left"][x_index]
#             x_s = results["left"][paint_list[i]]
#             y = min(results["top"][x_index:paint_list[i] + 1])
#             w = results["width"][paint_list[i]]
#             # Tô vàng
#             for j in range(x_t, x_s + w):
#                 for k in range(y, h_max):
#                     if 175 < img1[k][j][0] <= 255 and 175 < img1[k][j][1] <= 255 and 175 < img1[k][j][2] <= 255:
#                         img1[k][j][0] = 0
#                         img1[k][j][1] = 255
#                         img1[k][j][2] = 255
#             list_dong_tren = (x_t, x_s + w, y, h_max)
#             h_max = 0
#             x_index = paint_list[i + 1]
#             continue
#     cv2.imwrite(image, img1)
#     return list_new_text