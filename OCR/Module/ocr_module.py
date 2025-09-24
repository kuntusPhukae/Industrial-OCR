import easyocr
reader = easyocr.Reader(['en'])  # ภาษา OCR
def ocr_process(img):
    results = reader.readtext(img)
    if not results:
        return "", 0.0   # ถ้าไม่เจอ text
    texts = []
    confs = []
    for (bbox, text, conf) in results:
        texts.append(text)
        try:
            confs.append(float(conf))   # ✅ บังคับแปลงเป็น float
        except:
            confs.append(0.0)
    text_out = " ".join(texts)
    avg_conf = sum(confs) / len(confs) if confs else 0.0
    return text_out, avg_conf