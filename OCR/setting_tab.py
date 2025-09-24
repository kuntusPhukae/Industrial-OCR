#setting_tab.py
import cv2, os, configparser
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QFileDialog, QHBoxLayout
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QEvent, Qt
from PyQt5.QtGui import QMouseEvent
from Module.draggable_rect import DraggableRect
from Module.roi_module import ROIManager
from Module.template_matching import find_roi_by_template

class SettingTab(QWidget):
    def __init__(self):
        super().__init__()
        self.roi_manager = ROIManager()
        self.roi_manager.load_config()

        # Load ROI parameters from config.ini
        config = configparser.ConfigParser()
        config.read("config.ini")

        # Load main ROI
        if "ROI" in config:
            r = config["ROI"]
            try:
                self.main_rect = DraggableRect(
                    int(r.get("x", 0)),
                    int(r.get("y", 0)),
                    int(r.get("w", 100)),
                    int(r.get("h", 100)),
                    "Main ROI",
                    color=(0, 255, 0)
                )
            except ValueError:
                print("Invalid ROI values in config.ini. Using default values.")
                self.main_rect = DraggableRect(0, 0, 100, 100, "Main ROI", color=(0, 255, 0))
        else:
            self.main_rect = DraggableRect(0, 0, 100, 100, "Main ROI", color=(0, 255, 0))

        # Load template parameters
        if "TEMPLATE" in config:
            t = config["TEMPLATE"]
            self.template_rect = DraggableRect(int(t.get("x", 50)), int(t.get("y", 50)), int(t.get("w", 200)), int(t.get("h", 200)), "Template", color=(255, 128, 0))
        else:
            self.template_rect = DraggableRect(50, 50, 200, 200, "Template", color=(255, 128, 0))

        # Load OCR ROIs
        self.ocr_rects = []
        for section in config.sections():
            if section.startswith("OCR"):
                ocr = config[section]
                self.ocr_rects.append(DraggableRect(int(ocr.get("x", 0)), int(ocr.get("y", 0)), int(ocr.get("w", 100)), int(ocr.get("h", 50)), section, color=(0, 0, 255)))

        self.selected_rect = None
        self.drag_start = None
        self.img = None
        self.initUI()

    def initUI(self):
        self.image_label = QLabel("Please Load Image")
        self.image_label.setFixedSize(640,480)
        self.image_label.setMouseTracking(True)
        self.image_label.installEventFilter(self)
        self.btn_load = QPushButton("Load Image")
        self.btn_load.clicked.connect(self.load_image)
        self.btn_capture = QPushButton("Capture Camera")
        self.btn_capture.clicked.connect(self.capture_camera)
        self.btn_add = QPushButton("Add OCR")
        self.btn_add.clicked.connect(self.add_ocr)
        self.btn_save = QPushButton("Save Config")
        self.btn_save.clicked.connect(self.save_config)
        self.btn_update_temp = QPushButton("Update Template")
        self.btn_update_temp.clicked.connect(self.update_template)
        self.btn_test_template = QPushButton("Test Template")
        self.btn_test_template.clicked.connect(self.test_template)

        # Initialize btn_remove_ocr
        self.btn_remove_ocr = QPushButton("Remove OCR")
        self.btn_remove_ocr.clicked.connect(self.remove_ocr)

        btn_row = QHBoxLayout()
        btn_row.addWidget(self.btn_load)
        btn_row.addWidget(self.btn_capture)
        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_save)
        btn_row.addWidget(self.btn_update_temp)
        btn_row.addWidget(self.btn_test_template)
        btn_row.addWidget(self.btn_remove_ocr)
        layout = QVBoxLayout()
        image_row = QHBoxLayout()
        image_row.addWidget(self.image_label, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(image_row)
        layout.addLayout(btn_row)
        self.setLayout(layout)
    def test_template(self):
        # Test template matching and display result (search only in ROI area)
        if self.img is not None:
            template_img = cv2.imread("./ROI/temp.jpg")
            if template_img is not None:
                # Restrict search to main_rect area
                r = self.main_rect
                roi_crop = self.img[r.y:r.y+r.h, r.x:r.x+r.w]
                x, y, w, h, max_val, _ = find_roi_by_template(roi_crop, template_img, threshold=0.8)
                if x is not None and y is not None and w is not None and h is not None:
                    if w > 0 and h > 0:
                        x, y, w, h = int(x), int(y), int(w), int(h)
                        temp = self.img.copy()
                        # Draw match in global coordinates
                        cv2.rectangle(temp, (r.x + x, r.y + y), (r.x + x + w, r.y + y + h), (255, 0, 255), 2)
                        cv2.putText(temp, "Template Match", (r.x + x, r.y + y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
                        rgb = cv2.cvtColor(temp, cv2.COLOR_BGR2RGB)
                        h_img, w_img = rgb.shape[:2]
                        qimg = QImage(rgb.data, w_img, h_img, 3 * w_img, QImage.Format_RGB888)
                        pixmap = QPixmap.fromImage(qimg)
                        self.image_label.setPixmap(pixmap)
                    else:
                        self.image_label.setText("No template match found.")
                else:
                    self.image_label.setText("No template match found.")
            else:
                self.image_label.setText("Template image not found.")
        else:
            self.image_label.setText("No image loaded.")
    def update_template(self):
        # Save current template_rect position to TEMPLATE in config.ini and crop image at TEMPLATE to update temp.jpg
        if self.img is not None and self.template_rect is not None:
            import configparser
            config = configparser.ConfigParser()
            config.read("config.ini")
            # Save current template_rect to config
            if "TEMPLATE" not in config:
                config.add_section("TEMPLATE")
            config.set("TEMPLATE", "x", str(self.template_rect.x))
            config.set("TEMPLATE", "y", str(self.template_rect.y))
            config.set("TEMPLATE", "w", str(self.template_rect.w))
            config.set("TEMPLATE", "h", str(self.template_rect.h))
            with open("config.ini", "w") as f:
                config.write(f)
            # Crop image at TEMPLATE and update temp.jpg
            x, y, w, h = self.template_rect.x, self.template_rect.y, self.template_rect.w, self.template_rect.h
            if None not in (x, y, w, h):
                x, y, w, h = int(x), int(y), int(w), int(h)
                crop = self.img[y:y+h, x:x+w]
                if crop is not None and crop.size > 0:
                    cv2.imwrite("./ROI/temp.jpg", crop)

    def mousePressEvent(self, a0):
        if self.img is None or not isinstance(a0, QMouseEvent):
            return
        px, py = a0.pos().x(), a0.pos().y()
        label_w = self.image_label.width()
        label_h = self.image_label.height()
        img_h, img_w = self.img.shape[:2]
        scale_x = img_w / label_w
        scale_y = img_h / label_h
        img_x = int(px * scale_x)
        img_y = int(py * scale_y)
        # Check template_rect first
        if self.template_rect.handle_contains(img_x, img_y) >= 0 or self.template_rect.contains(img_x, img_y):
            self.selected_rect = self.template_rect
            self.selected_rect.start_drag_or_resize(img_x, img_y)
            self.drag_start = (img_x, img_y)
            return
        # Check main_rect
        if self.main_rect.handle_contains(img_x, img_y) >= 0 or self.main_rect.contains(img_x, img_y):
            self.selected_rect = self.main_rect
            self.selected_rect.start_drag_or_resize(img_x, img_y)
            self.drag_start = (img_x, img_y)
            return
        # Check OCR rects
        for roi in self.ocr_rects:
            if roi.handle_contains(img_x, img_y) >= 0 or roi.contains(img_x, img_y):
                self.selected_rect = roi
                roi.start_drag_or_resize(img_x, img_y)
                self.drag_start = (img_x, img_y)
                return
        self.selected_rect = None
        self.drag_start = None

    def mouseMoveEvent(self, a0):
        if self.img is None or self.selected_rect is None or self.drag_start is None or not isinstance(a0, QMouseEvent):
            return
        px, py = a0.pos().x(), a0.pos().y()
        label_w = self.image_label.width()
        label_h = self.image_label.height()
        img_h, img_w = self.img.shape[:2]
        scale_x = img_w / label_w
        scale_y = img_h / label_h
        img_x = int(px * scale_x)
        img_y = int(py * scale_y)
        dx = img_x - self.drag_start[0]
        dy = img_y - self.drag_start[1]
        if self.selected_rect.mode == "drag":
            self.selected_rect.move(dx, dy, img_w, img_h)
        elif self.selected_rect.mode == "resize":
            self.selected_rect.resize(dx, dy, img_w, img_h)
        self.drag_start = (img_x, img_y)
        self.update_display()

    def mouseReleaseEvent(self, a0):
        if self.selected_rect is not None and isinstance(a0, QMouseEvent):
            self.selected_rect.end_drag_or_resize()
            self.selected_rect = None
            self.drag_start = None

    def eventFilter(self, a0, a1):
        if a0 == self.image_label and isinstance(a1, QMouseEvent):
            if a1.type() == QEvent.Type.MouseButtonPress:
                self.mousePressEvent(a1)
                return True
            elif a1.type() == QEvent.Type.MouseMove:
                self.mouseMoveEvent(a1)
                return True
            elif a1.type() == QEvent.Type.MouseButtonRelease:
                self.mouseReleaseEvent(a1)
                return True
        return super().eventFilter(a0, a1)

    def load_image(self):
        path,_ = QFileDialog.getOpenFileName(self,"Open Image","","Image Files (*.jpg *.png *.bmp)")
        if path:
            self.img = cv2.imread(path)
            self.update_display()

    def capture_camera(self):
        cap = cv2.VideoCapture(1)
        ret, frame = cap.read()
        if ret:
            self.img = frame
            cv2.imwrite("temp.jpg", frame)  # save template
            self.update_display()
        cap.release()

    def add_ocr(self):
        label = f"OCR {len(self.ocr_rects)+1}"
        self.ocr_rects.append(DraggableRect(60,60,100,50,label))
        self.update_display()

    def remove_ocr(self):
        # Remove the last OCR rectangle from the list
        if self.ocr_rects:
            self.ocr_rects.pop()
            self.update_display()

    def save_config(self):
        # Find template in ROI position and update main_rect
        if self.img is not None:
            template_img = cv2.imread("./ROI/temp.jpg")
            if template_img is not None:
                x, y, w, h, max_val, _ = find_roi_by_template(self.img, template_img, threshold=0.8)
                if all(isinstance(v, int) and v is not None for v in (x, y, w, h)) and w is not None and h is not None and w > 0 and h > 0:
                    ix, iy, iw, ih = x, y, w, h
                    self.main_rect.x, self.main_rect.y, self.main_rect.w, self.main_rect.h = ix, iy, iw, ih
                    # Save the matched region as new temp.jpg
                    crop = self.img[iy:iy+ih, ix:ix+iw]
                    if crop is not None and crop.size > 0:
                        cv2.imwrite("./ROI/temp.jpg", crop)
        # Save main_rect and OCR rects
        r = self.main_rect
        self.roi_manager.main_roi = {'x':r.x, 'y':r.y, 'w':r.w, 'h':r.h, 'label':r.label}
        self.roi_manager.ocr_rois = [{'x':r.x, 'y':r.y, 'w':r.w, 'h':r.h, 'label':r.label} for r in self.ocr_rects]
        self.roi_manager.save_config()

    def update_display(self):
        if self.img is None:
            return
        temp = self.img.copy()
        # Draw template_rect
        t = self.template_rect
        template_coords = (t.x, t.y, t.w, t.h)
        if all(isinstance(v, int) and v is not None for v in template_coords):
            tx, ty, tw, th = template_coords
            cv2.rectangle(temp, (tx, ty), (tx + tw, ty + th), t.color, 2)
            cv2.putText(temp, t.label, (tx, ty - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, t.color, 1)
            corners = [(tx, ty), (tx + tw, ty), (tx, ty + th), (tx + tw, ty + th)]
            for (cx, cy) in corners:
                if all(isinstance(val, int) and val is not None for val in (cx, cy)):
                    cv2.circle(temp, (cx, cy), t.handle_size, (0, 255, 255), -1)
        # Draw main_rect
        r = self.main_rect
        main_coords = (r.x, r.y, r.w, r.h)
        if all(isinstance(v, int) and v is not None for v in main_coords):
            x, y, w, h = main_coords
            cv2.rectangle(temp, (x, y), (x + w, y + h), r.color, 2)
            cv2.putText(temp, r.label, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, r.color, 1)
            main_corners = [(x, y), (x + w, y), (x, y + h), (x + w, y + h)]
            for (cx, cy) in main_corners:
                if all(isinstance(val, int) and val is not None for val in (cx, cy)):
                    cv2.circle(temp, (cx, cy), r.handle_size, (0, 255, 255), -1)
        # Draw OCR rects and handles
        for roi in self.ocr_rects:
            roi_coords = (roi.x, roi.y, roi.w, roi.h)
            if all(isinstance(v, int) and v is not None for v in roi_coords):
                rx, ry, rw, rh = roi_coords
                cv2.rectangle(temp, (rx, ry), (rx + rw, ry + rh), roi.color, 2)
                cv2.putText(temp, roi.label, (rx, ry - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, roi.color, 1)
                corners = [(rx, ry), (rx + rw, ry), (rx, ry + rh), (rx + rw, ry + rh)]
                for (cx, cy) in corners:
                    if all(isinstance(val, int) and val is not None for val in (cx, cy)):
                        cv2.circle(temp, (cx, cy), roi.handle_size, (0, 255, 255), -1)
        # Draw template position in ROI (if found)
        template_img = cv2.imread("./ROI/temp.jpg")
        if self.img is not None and template_img is not None:
            x, y, w, h, max_val, _ = find_roi_by_template(self.img, template_img, threshold=0.8)
            if all(isinstance(v, int) and v is not None for v in (x, y, w, h)) and w is not None and h is not None and w > 0 and h > 0:
                ix, iy, iw, ih = x, y, w, h
                if ix is not None and iy is not None and iw is not None and ih is not None:
                    ix, iy, iw, ih = int(ix), int(iy), int(iw), int(ih)
                    cv2.rectangle(temp, (ix, iy), (ix + iw, iy + ih), (255, 0, 255), 2)
                    label_y = iy - 5
                    cv2.putText(temp, "Template", (ix, label_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)
        # Image rendering block (properly indented)
        rgb = cv2.cvtColor(temp, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        # Auto resize to fit QLabel
        label_w = self.image_label.width()
        label_h = self.image_label.height()
        scaled_pixmap = pixmap.scaled(label_w, label_h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
