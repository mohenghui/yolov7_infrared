import os
root_path="./detect_auto/images"
index=0
for idx,i in enumerate(os.listdir(root_path)):
    filename=os.path.join(root_path,i)
    
    if idx%3==0:continue
    os.remove(filename)