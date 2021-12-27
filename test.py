import os

path = './'
filename = 'BCTH.docx'
sess_id = '1111'
file_name,file_end = os.path.splitext(filename)
path_file = file_name + '_' + sess_id
if not os.path.exists(path_file):
    os.makedirs(path_file)

save_path = os.path.join(path_file,filename)
print(save_path)