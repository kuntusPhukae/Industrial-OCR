import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTabWidget
from setting_tab import SettingTab
from ocr_tab import OCRTab

class OCRApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Industrial OCR Full GUI")
        self.resize(900,600)
        self.setStyleSheet("""
            QWidget, QFrame, QScrollArea {
                background-color: #181818;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
            }
            QPushButton {
                background-color: #232323;
                color: #e0e0e0;
                border: 1px solid #333;
                border-radius: 8px;
                padding: 8px 0;
            }
            QPushButton:hover {
                background-color: #333;
            }
            QTextEdit {
                background-color: #232323;
                color: #e0e0e0;
                border-radius: 8px;
                border: 1px solid #333;
            }
            QDialog {
                background-color: #181818;
                color: #e0e0e0;
                border-radius: 12px;
                border: 1px solid #333;
            }
            QTabBar::tab {
                color: #e0e0e0;
                font-weight: normal;
                min-width: 10px;
                padding: 8px 24px;
            }
        """)
        self.tabs = QTabWidget()
        self.setting_tab = SettingTab()
        self.ocr_tab = OCRTab(self.setting_tab)
        self.tabs.addTab(self.ocr_tab,"OCR")
        self.tabs.addTab(self.setting_tab,"Setting")
        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        self.setLayout(layout)
        
if __name__=="__main__":
    app = QApplication(sys.argv)
    window = OCRApp()
    window.show()
    sys.exit(app.exec_())