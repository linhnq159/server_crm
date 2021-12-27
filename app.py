from flask import Flask, flash, request, redirect, url_for , jsonify , send_file ,send_from_directory
from werkzeug.utils import secure_filename
from OCR_CRM import *
import requests
import json
import time

class DataModel:
    def __init__(self, result, message, item):
        self.result = result
        self.message = message
        self.item = item

class ErrorModel:
    def __init__(self, code, message):
        self.code = code
        self.message = message

class ResponseModel:
    def __init__(self, data, error):
        self.data = data
        self.error = error

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'docx','doc','pdf'}

# app = Flask(__name__)
app = Flask(__name__, static_url_path='/static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

results = {}
word_index = {}
input_image = {}
output_file = {}
dic_stt = {}
list_new_text = {}
number_img = {}
@app.route('/', methods=['GET', 'POST'])
def upload_file():
    time_t = time.time()
    sess_id = request.args.get('sess_id')
    print(sess_id)
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            # return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            # return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # print(filename)
            file_name, file_end = os.path.splitext(filename)
            path_file_name = file_name + '_' + sess_id
            path_file = os.path.join(app.config['UPLOAD_FOLDER'], path_file_name )
            if not os.path.exists(path_file):
                os.makedirs(path_file)
            save_path = os.path.join(path_file, filename)
            # print(save_path)
            file.save(save_path)
            results[sess_id], input_image[sess_id], output_file[sess_id] = xu_li_dau_vao(save_path)
            word_index[sess_id] = 0
            # print(results)
            # return redirect(url_for('upload_file',
            #                         filename=filename))
    time_s = time.time()
    print("Time upload file : {}".format(time_s-time_t))
    return ' '

@app.route('/search', methods=['GET', 'POST'])
def search():
    global word_index
    text_change = request.args.get('text_change')
    sess_id = request.args.get('sess_id')
    print(word_index[sess_id])
    if word_index[sess_id] == 0 :
        dic_stt[sess_id] = find_paint_list(text_change,input_image[sess_id],results[sess_id])
        number_img[sess_id] = len(dic_stt[sess_id])
        if number_img[sess_id] == 0:
            return str(number_img[sess_id])
        else:
            img_base64 = xu_li_text_change(text_change, word_index[sess_id], input_image[sess_id], results[sess_id], dic_stt[sess_id])
            if word_index[sess_id] + 1 == number_img[sess_id]:
                word_index[sess_id] = 0
            else:
                word_index[sess_id] += 1
            sc = jsonify({'image': 'data:image/png;base64,' + img_base64, 'number_img': number_img[sess_id]})
            sc.status_code = 200
            return sc

    else:
        img_base64 = xu_li_text_change(text_change, word_index[sess_id], input_image[sess_id], results[sess_id], dic_stt[sess_id])
        if word_index[sess_id] + 1 == number_img[sess_id]:
            word_index[sess_id] = 0
        else:
            word_index[sess_id] += 1
        return 'data:image/png;base64,' + img_base64

@app.route('/replace_file', methods=['GET', 'POST'])
def replace():
    error = None
    data = None
    text_change = request.args.get('text_change')
    sess_id = request.args.get('sess_id')
    # [{
    #     "new_text": ["BANTHE", "", "BANTHE"]
    # }]
    contents = request.json
    for content in contents:
        list_new_text[sess_id] = content['new_text']
    thay_doi_chu_word(output_file[sess_id], text_change, list_new_text[sess_id])
    # print(output_file[sess_id])

    item = {"sess_id" : sess_id , "url": output_file[sess_id]}
    data = DataModel(True, "File thay đổi thành công ", item)
    if error is not None:
        error = vars(error)
    if data is not None:
        data = vars(data)
    response = ResponseModel(data, error)
    return json.dumps(vars(response))

@app.route("/static/<path:path>")
def static_dir(path):
    return send_from_directory("static", path)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

