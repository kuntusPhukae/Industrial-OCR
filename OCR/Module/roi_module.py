import configparser
class ROIManager:
    def __init__(self, config_file='config.ini'):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self.config.read(self.config_file)
        # MAIN ROI
        self.main_roi = {"x":50,"y":50,"w":200,"h":150,"label":"ROI"}
        # OCR ROI
        self.ocr_rois = []  # list of dict {"x":..,"y":..,"w":..,"h":..,"label":..}
        # SEARCH AREA
        self.search_area = {"x":50,"y":50,"w":200,"h":200}
    def save_config(self):
        self.config['ROI'] = {k:str(v) for k,v in self.main_roi.items() if k!="label"}
        for i,roi in enumerate(self.ocr_rois):
            self.config[f"OCR{i}"] = {k:str(v) for k,v in roi.items()}
        with open(self.config_file,'w') as f:
            self.config.write(f)
    def load_config(self):
        self.config.read(self.config_file)
        if 'ROI' in self.config:
            self.main_roi.update({
                k: (None if v == 'None' else int(v) if v.isdigit() else None)
                for k, v in self.config['ROI'].items()
            })
        self.ocr_rois = []
        for section in self.config.sections():
            if section.startswith("OCR"):
                roi = {
                    k: (int(v) if k != 'label' and v.isdigit() else v)
                    for k, v in self.config[section].items()
                }
                self.ocr_rois.append(roi)
        # Remove SEARCH_AREA logic and use ROI as the search area
        self.search_area = {
            k: self.main_roi[k] for k in ['x', 'y', 'w', 'h']
        }
