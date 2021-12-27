from pdf2image import convert_from_path
from subprocess import check_output
from docx2pdf import convert
import argparse
from tim_va_to_word import *
from thay_doi_chu_word import *
import time
from pdf2docx import Converter
import base64

# Xây dựng hệ thống tham số đầu vào
# ap = argparse.ArgumentParser()
# # -f : file đầu vào
# ap.add_argument("-f", "--file", required=True)
# args = vars(ap.parse_args())

# Xử lý file đầu vào
def xu_li_file_dau_vao(input_file):
    # Xử lý file đầu vào
    doc_end = ['.docx', '.doc']
    pdf_end = ['.pdf']

    input_file_name, input_file_end = os.path.splitext(input_file)

    # Tiếm kiếm nếu đầu vào là file doc docx
    if input_file_end in doc_end:
        input_pdf , output_file = convert_file_word(input_file_name,input_file)
        doc = Document(input_file)
        doc.save(output_file)
        return input_pdf, output_file

    # Nếu đầu vào là file pdf
    elif input_file_end in pdf_end:
        input_pdf, output_file = convert_file_pdf(input_file_name,input_file)
        return input_pdf, output_file
    # # Đầu vào khác docx , doc , pdf , jpg , png
    # else:
    #     print("Ko đúng định dạng yêu cầu")

def convert_file_word(input_file_name,input_file):
    # Convert doc , docx to pdf
    time_1 = time.time()
    convert(input_file)
    time_c = time.time()  # Time khi kết thúc
    fps = time_c - time_1
    print("Time run convert word : {}".format(fps))

    # Output = file pdf
    input_pdf = input_file_name + '.pdf'
    output_file = input_file_name + '_output.docx'
    return input_pdf,output_file

def convert_file_pdf(input_file_name,input_file):
    # Output = file pdf
    input_file_docx = input_file_name + '.docx'
    output_file = input_file_name + '_output.docx'

    # Convert pdf to docx
    time_1 = time.time()
    cv = Converter(input_file)
    cv.convert(output_file)  # all pages by default
    cv.close()
    time_c = time.time()  # Time khi kết thúc
    fps = time_c - time_1
    print("Time run convert to word : {}".format(fps))
    return input_file , output_file

# Đếm số trang pdf
def get_num_pages(pdf_path):
    output = check_output(["pdfinfo", pdf_path]).decode()
    pages_line = [line for line in output.splitlines() if "Pages:" in line][0]
    num_pages = int(pages_line.split(":")[1])
    return num_pages

# Tạo folder ảnh theo các trang pdf
def create_folder_pdf(input_pdf):
    number_page = get_num_pages(input_pdf)
    file = input_pdf.split('.pd')[0] + '_img'
    if not os.path.exists(file):
        os.makedirs(file)
    pages = convert_from_path(input_pdf, 200)
    counter = 1
    for page in pages:
        myfile = file+'/'+str(counter)+'.png'
        page.save(myfile, 'PNG')
        counter = counter+1
        if counter > number_page:
            break
    return file

# Dự đoán từ , tô và ghép ảnh
def ocr_folder_image(input_image):
    results = {}
    time_t = time.time()
    files = os.listdir(input_image)
    for file in files:
        input_file_anh = input_image + '/' + file
        results[file] = tesseract_predict(input_file_anh)
    time_s = time.time()
    print("Time tesseract predict file {}".format(time_s - time_t))
    return results

def imageToBase64(image):
    retval, buffer = cv2.imencode('.jpg', image)
    jpg_as_text = base64.b64encode(buffer)
    image_data = jpg_as_text.decode("utf-8")
    image_data = str(image_data)
    return image_data

def to_vang(image, paint_list, results, text_change_org):
    input_img, img_end = os.path.splitext(image)
    image_output = input_img + '_output' + img_end
    img = cv2.imread(image)
    img1 = img.copy()
    text_change = no_end(no_accent_vietnamese(text_change_org))
    text_change = text_change.split(' ')
    text_change = [text_remove for text_remove in text_change if text_remove != '']
    h_max = 0
    x_index = paint_list[0]
    for i in range(len(paint_list)):
        # extract the bounding box coordinates of the text region from
        # the current result
        h = results["top"][paint_list[i]] + results["height"][paint_list[i]]
        if h > h_max:
            h_max = h
        if (i + 1) % len(text_change) == 0:
            x_t = results["left"][x_index]
            x_s = results["left"][paint_list[i]]
            y = min(results["top"][x_index: paint_list[i] + 1])
            w = results["width"][paint_list[i]]
            for j in range(x_t, x_s + w):
                for k in range(y, h_max):
                    if 175 < img1[k][j][0] <= 255 and 175 < img1[k][j][1] <= 255 and 175 < img1[k][j][2] <= 255:
                        img1[k][j][0] = 0
                        img1[k][j][1] = 255
                        img1[k][j][2] = 255

            # cv2.imwrite(image_output, img1)
            # cv2.imshow(image_output, img1)
            h_max = 0
            if i < len(paint_list) - 1:
                x_index = paint_list[i + 1]

            continue

        if results["word_num"][paint_list[i + 1]] - results["word_num"][paint_list[i]] < 0:
            x_t = results["left"][x_index]
            x_s = results["left"][paint_list[i]]
            y = min(results["top"][x_index:paint_list[i] + 1])
            w = results["width"][paint_list[i]]
            # Tô vàng
            for j in range(x_t, x_s + w):
                for k in range(y, h_max):
                    if 175 < img1[k][j][0] <= 255 and 175 < img1[k][j][1] <= 255 and 175 < img1[k][j][2] <= 255:
                        img1[k][j][0] = 0
                        img1[k][j][1] = 255
                        img1[k][j][2] = 255
            h_max = 0
            x_index = paint_list[i + 1]
            continue
    # cv2.imwrite(image_output, img1)
    return imageToBase64(img1)

def find_paint_list(text_change_org,input_image,results):
    paint_dic = {}
    files = os.listdir(input_image)
    # Tìm chuỗi khớp
    for file in files:
        paint_dic[file] = tim_chuoi_khop(text_change_org, results[file])
        if paint_dic[file] == []:
            del paint_dic[file]

    text_change = no_end(no_accent_vietnamese(text_change_org))
    text_change = text_change.split(' ')
    text_change = [text_remove for text_remove in text_change if text_remove != '']
    # print(text_change)
    counter = -1
    dic_stt = {}
    len_text_change = len(text_change)

    for file in paint_dic:
        list_paint_stt = []
        for i in range(len(paint_dic[file])):
            list_paint_stt.append(paint_dic[file][i])
            if (i + 1) % len_text_change == 0:
                counter += 1
                dic_stt[counter] = {file: list_paint_stt}
                list_paint_stt = []
    return dic_stt


def xu_li_text_change(text_change_org,stt,input_image,results,dic_stt):
    for file in dic_stt[stt]:
        file = file
        paint_list = dic_stt[stt][file]
        image = input_image + '/' + file
        img_base64 = to_vang(image, paint_list, results[file], text_change_org)
        return img_base64

def xu_li_dau_vao(input_file):
    input_pdf, output_file = xu_li_file_dau_vao(input_file)
    input_image = create_folder_pdf(input_pdf)
    results = ocr_folder_image(input_image)
    return results , input_image , output_file
