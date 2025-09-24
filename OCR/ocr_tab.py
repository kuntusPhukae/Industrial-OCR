# ocr_tab.py
import cv2
import os
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QTextEdit, QVBoxLayout, QHBoxLayout, QFrame, QFileDialog, QSizePolicy
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QTimer
from Module.ocr_module import ocr_process
from Module.template_matching import find_roi_by_template

class OCRTab(QWidget):
    def __init__(self, setting_tab):
        super().__init__()
        self.setting_tab = setting_tab
        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.best_results = {}
        self.roi_widgets = {}
        self.template = cv2.imread("./ROI/temp.jpg")
        self.initUI()

    def initUI(self):
        # Apply dark mode stylesheet to main widget
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
        """)
        # Left: Results panel (30%)
        self.results_panel = QVBoxLayout()
        self.results_widget = QWidget()
        self.results_widget.setLayout(self.results_panel)
        self.results_widget.setMinimumWidth(270)  # 30% of 900px window
        self.results_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        # Mini log widget
        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        self.log_widget.setMaximumHeight(120)
        self.results_panel.addWidget(QLabel("Mini OCR Log:"))
        self.results_panel.addWidget(self.log_widget)

        # Right: Image and controls (70%)
        self.image_label = QLabel("No Camera Feed")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(320, 240)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.btn_start = QPushButton("Start Camera")
        self.btn_start.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_start.clicked.connect(self.start_camera)

        self.btn_load_file = QPushButton("Load File")
        self.btn_load_file.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_load_file.clicked.connect(self.load_file)

        self.btn_runstop = QPushButton("Run")
        self.btn_runstop.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn_runstop.clicked.connect(self.toggle_run_stop)

        right_panel = QVBoxLayout()
        right_panel.addWidget(self.image_label, 1)
        right_panel.addWidget(self.btn_start)
        right_panel.addWidget(self.btn_load_file)
        right_panel.addWidget(self.btn_runstop)
        right_panel.setStretch(0, 1)  # image_label expands
        right_panel.setStretch(1, 0)  # buttons do not expand
        right_panel.setStretch(2, 0)
        right_panel.setStretch(3, 0)

        self.right_widget = QWidget()
        self.right_widget.setLayout(right_panel)
        self.right_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Main horizontal layout
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.results_widget, 1)
        main_layout.addWidget(self.right_widget, 2)
        self.setLayout(main_layout)

    def toggle_run_stop(self):
        if self.btn_runstop.text() == "Run":
            # Resume/start video/camera or image if loaded
            if self.cap is not None or (hasattr(self, 'loaded_image') and self.loaded_image is not None):
                self.timer.start(30)
                self.btn_runstop.setText("Stop")
        else:
            # Pause process (do not release cap)
            if self.timer.isActive():
                self.timer.stop()
            self.btn_runstop.setText("Run")

    def start_camera(self):
        if self.cap is not None:
            self.cap.release()
        self.cap = cv2.VideoCapture(1) # ใช้กล้องที่ 1
        self.timer.start(30) # อัพเดตทุก 30 ms
        self.btn_runstop.setText("Stop")

    def load_file(self):
        # Reset all state before loading new file
        self.reset_all()
        path, _ = QFileDialog.getOpenFileName(self, "Select File", "", "All Files (*.jpg *.jpeg *.png *.bmp *.mp4 *.avi *.mov)")
        if path:
            ext = os.path.splitext(path)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.bmp']:
                self.loaded_image = cv2.imread(path)
                self.cap = None
                if self.loaded_image is not None:
                    rgb = cv2.cvtColor(self.loaded_image, cv2.COLOR_BGR2RGB)
                    h, w, ch = rgb.shape
                    qimg = QImage(rgb.data, w, h, ch*w, QImage.Format_RGB888)
                    self.image_label.setPixmap(QPixmap.fromImage(qimg))
                    self.btn_runstop.setText("Run")
            elif ext in ['.mp4', '.avi', '.mov']:
                if self.cap is not None:
                    self.cap.release()
                self.cap = cv2.VideoCapture(path)
                self.loaded_image = None
                self.btn_runstop.setText("Run")
                # Show preview frame
                ret, frame = self.cap.read()
                if ret:
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w, ch = rgb.shape
                    qimg = QImage(rgb.data, w, h, ch*w, QImage.Format_RGB888)
                    self.image_label.setPixmap(QPixmap.fromImage(qimg))
    def reset_all(self):
        # Release camera
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
        # Stop timer
        if self.timer.isActive():
            self.timer.stop()
        # Clear loaded image
        self.loaded_image = None
        # Clear results and widgets
        self.best_results.clear()
        self.roi_widgets.clear()
        self.clear_results_panel()
        # Clear image label
        self.image_label.clear()
        self.image_label.setText("No Camera Feed")
        # Clear log widget
        self.log_widget.clear()

    def update_frame(self):
        # Handle both image and video
        frame = None
        if self.cap is not None:
            ret, frame = self.cap.read()
            if not ret:
                return  # วิดีโอหมด
        elif hasattr(self, 'loaded_image') and self.loaded_image is not None:
            frame = self.loaded_image.copy()
        else:
            return

        # ใช้ template + offset
        r = self.setting_tab.main_rect
        pt_x, pt_y, pt_w, pt_h, score, pt_roi = find_roi_by_template(frame, self.template, threshold=0.8)

        if pt_roi is None:
            return  # Only show/update if template can be detected

        dx, dy = 0, 0
        results = []
        log_entries = []
        ocr_crops = []
        coords = (pt_x, pt_y, pt_w, pt_h)
        if all(v is not None and isinstance(v, int) for v in coords):
            if coords:
                x1, y1, w1, h1 = (int(v) if v is not None else 0 for v in coords)
            else:
                x1, y1, w1, h1 = 0, 0, 0, 0
            cv2.rectangle(frame, (x1, y1), (x1 + w1, y1 + h1), (0,255,0), 2)
            cv2.putText(frame, f"{score:.2f}", (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)
            if r.x is not None and r.y is not None:
                dx = x1 - r.x
                dy = y1 - r.y
            else:
                dx = dy = 0
        else:
            dx = dy = 0

        # Always show ROI areas on the main frame
        for roi in self.setting_tab.ocr_rects:
            x = roi.x + dx
            y = roi.y + dy
            w, h = roi.w, roi.h
            if all(isinstance(v, int) and v is not None for v in (x, y, w, h)):
                x2, y2, w2, h2 = int(x), int(y), int(w), int(h)
                # Draw ROI rectangle and label
                cv2.rectangle(frame, (x2, y2), (x2 + w2, y2 + h2), (0, 255, 255), 2)
                cv2.putText(frame, roi.label, (x2, y2 - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                # OCR logic
                crop = frame[y2:y2+h2, x2:x2+w2]
                text, conf = '', 0.0
                if crop.size > 0:
                    crop = cv2.rotate(crop, cv2.ROTATE_180)  # Rotate crop if needed
                    crop_gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
                    #_, crop_bin = cv2.threshold(crop_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)  # Binarize
                    text, conf = ocr_process(crop_gray)
                    rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
                    h3, w3, ch3 = rgb.shape
                    qimg2 = QImage(rgb.data, w3, h3, ch3*w3, QImage.Format_RGB888)
                    qpix = QPixmap.fromImage(qimg2).scaled(160, 120, Qt.AspectRatioMode.KeepAspectRatio)
                    ocr_crops.append((roi.label, crop, text, conf, qpix))
                    log_entry = f"{roi.label}: {text} (conf {conf:.2f})"
                    log_entries.append(log_entry)
                # Show OCR result on main frame
                txt_show = text if text is not None else ''
                conf_show = conf if conf is not None else 0.0
                cv2.putText(frame, f'{txt_show} ({conf_show:.2f})',
                            (x2, y2 + h2 + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
                results.append(f"{roi.label}: {txt_show} (conf {conf_show:.2f})")

        # Update results panel (left)
        self.clear_results_panel()
        import datetime
        for roi in self.setting_tab.ocr_rects:
            label = roi.label
            timestamp = datetime.datetime.now().strftime('%H:%M:%S')
            # Find latest crop for this label
            found = [item for item in ocr_crops if item[0] == label]
            if found:
                _, crop, txt, conf, qpix = found[-1]
            else:
                crop, txt, conf, qpix = None, '', 0.0, None
            # Card layout (dark mode)
            card = QVBoxLayout()
            card.setContentsMargins(12, 12, 12, 12)
            card.setSpacing(6)
            card_widget = QWidget()
            card_widget.setLayout(card)
            # Title
            title_lbl = QLabel(label)
            title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title_lbl.setStyleSheet("font-weight:bold; font-size:15px; color:#e0e0e0; margin-bottom:4px;")
            card.addWidget(title_lbl)
            # Timestamp
            ts_lbl = QLabel(f"Updated: {timestamp}")
            ts_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ts_lbl.setStyleSheet("font-size:12px; color:#a0a0a0; margin-bottom:2px;")
            card.addWidget(ts_lbl)
            # Image
            img_lbl = QLabel()
            if qpix:
                img_lbl.setPixmap(qpix)
            else:
                img_lbl.setText("Pending...")
                img_lbl.setStyleSheet("color:#888; font-size:15px; border-radius:8px; border:2px solid #ff9800; background:#222; margin:8px; padding:32px 0;")
            img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card.addWidget(img_lbl)
            # Text
            txt_lbl = QLabel(txt if txt else "Pending...")
            txt_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            txt_lbl.setStyleSheet("font-size:16px; color:#e0e0e0; margin-bottom:2px; font-weight:bold; background:#333; border-radius:6px; padding:2px 8px;")
            card.addWidget(txt_lbl)
            # Confidence
            conf_lbl = QLabel(f"Confidence: {conf:.2f}" if conf is not None else "Confidence: Pending")
            conf_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            conf_lbl.setStyleSheet("font-size:13px; color:#ff9800; margin-bottom:2px; font-weight:bold;")
            card.addWidget(conf_lbl)
            # Add card to results panel
            card_widget.setStyleSheet("background:#232323; border-radius:12px; border:2px solid #ff9800; margin-bottom:12px;")
            self.results_panel.addWidget(card_widget)

        # Update mini log widget
        if log_entries:
            for entry in log_entries:
                self.log_widget.append(entry)
            # Write to logfile
            with open("./logging/ocr_log.txt", "a", encoding="utf-8") as f:
                for entry in log_entries:
                    f.write(entry + "\n")

        # แสดง main frame (right)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch*w, QImage.Format_RGB888)
        self.image_label.setPixmap(QPixmap.fromImage(qimg))

    def clear_results_panel(self):
        # Remove all widgets from results_panel except log_widget
        widgets_to_keep = [self.log_widget]
        i = 0
        while i < self.results_panel.count():
            item = self.results_panel.itemAt(i)
            widget = item.widget() if item is not None else None
            if widget is not None and widget not in widgets_to_keep:
                item = self.results_panel.takeAt(i)
                widget.deleteLater()
            else:
                i += 1
        # Also clear roi_widgets to avoid updating deleted widgets
        self.roi_widgets.clear()

    def update_roi_widget(self, label):
        br = self.best_results[label]
        if label not in self.roi_widgets:
            frame_box = QVBoxLayout()
            frame_widget = QFrame()
            frame_widget.setLayout(frame_box)
            lbl_img = QLabel()
            lbl_img.setFixedSize(160, 120)
            lbl_text = QLabel()
            lbl_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
            frame_box.addWidget(lbl_img)
            frame_box.addWidget(lbl_text)
            self.results_panel.addWidget(frame_widget)
            self.roi_widgets[label] = (lbl_img, lbl_text)

        lbl_img, lbl_text = self.roi_widgets[label]
        lbl_img.setPixmap(br["pixmap"])
        lbl_text.setText(f"{label}: {br['text']} (conf {br['conf']:.2f})")

    def _update_results_panel(self, ocr_crops):
        self.clear_results_panel()
        for label, crop, text, conf in ocr_crops:
            card = QVBoxLayout()
            card_widget = QWidget()
            card_widget.setLayout(card)

            # Display cropped OCR image with fixed size
            if crop is not None:
                fixed_width, fixed_height = 160, 120
                resized_crop = cv2.resize(crop, (fixed_width, fixed_height), interpolation=cv2.INTER_AREA)
                crop_rgb = cv2.cvtColor(resized_crop, cv2.COLOR_BGR2RGB)
                qimg = QImage(crop_rgb.data, fixed_width, fixed_height, 3 * fixed_width, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qimg)
                img_label = QLabel()
                img_label.setPixmap(pixmap)
                img_label.setFixedSize(fixed_width, fixed_height)
                img_label.setScaledContents(True)
                card.addWidget(img_label)

            # Add label, text, and confidence
            card.addWidget(QLabel(label))
            card.addWidget(QLabel(text if text else "Pending..."))
            card.addWidget(QLabel(f"Confidence: {conf:.2f}" if conf else "Confidence: Pending"))

            self.results_panel.addWidget(card_widget)


