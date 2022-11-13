import os
root_path="D:\\vscode_work\\yolov7-main\\datasets\\mydata\\images"
for i in os.listdir(root_path):
    file_path=os.path.join(root_path,i)
    basename=os.path.basename(file_path)
    name,tail=os.path.splitext(basename)
    if tail==".jpg":
        new_name=os.path.join(root_path,name+".png")
        os.rename(file_path,new_name)
        print(new_name)