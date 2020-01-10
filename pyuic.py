import os

for ui in os.listdir('.'):
    if os.path.splitext(ui)[1].lower() == '.ui':
        uipy=os.path.splitext(ui)[0]+'Ui.Py'
        if os.path.exists(uipy):
            if os.path.getmtime(ui) > os.path.getmtime(uipy):
                os.system('pyuic5 %s -o %s'%(ui,uipy))
        else:
            os.system('pyuic5 %s -o %s'%(ui,uipy))

