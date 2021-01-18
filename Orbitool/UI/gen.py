import os

content = open('FileUiPy.py','r').read()

for file in os.listdir('.'):
    if not file.endswith("Ui.py"):
        continue
    output_file = os.path.splitext(file)[0]+'Py.py'
    if os.path.exists(output_file):
        continue
    output_content = content.replace("FileUi",os.path.splitext(file)[0])
    with open(output_file,'w') as target:
        target.write(output_content)