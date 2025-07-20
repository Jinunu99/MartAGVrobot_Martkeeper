import sys
from PyQt5 import QtWidgets, uic
from user_shopping_gui import UserShoppingGui


app = QtWidgets.QApplication(sys.argv)
window = UserShoppingGui()
window.show()
sys.exit(app.exec_())