E:
cd E:\Software_dev\Python\eit_app
conda activate ai-app
python eit_app/main.py
pyuic5 -x eit_app/gui.ui -o eit_app/gui.py

pyrcc5 eit_app/resource.qrc -o eit_app/resource_rc.py