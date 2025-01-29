Steps to use:
1. install essential libraries and dependencies (Linux):
```
pip install pyqt6 easyocr mss requests numpy opencv-python regex
sudo apt install tesseract-ocr libtesseract-dev
```

2. Download OCR models to your local machine via bash:
```
  mkdir -p ~/.EasyOCR/model
  wget https://github.com/JaidedAI/EasyOCR/releases/download/pre-v1.1.6/craft_mlt_25k.zip -P ~/.EasyOCR/model
  unzip ~/.EasyOCR/model/craft_mlt_25k.zip -d ~/.EasyOCR/model
  wget https://github.com/JaidedAI/EasyOCR/releases/download/v1.3/english_g2.zip -P ~/.EasyOCR/model
  unzip ~/.EasyOCR/model/english_g2.zip -d ~/.EasyOCR/model
```

3. create a (free) account on deepl.com, and obtain a Deepl API key. Then replace ```DEEPL_KEY = "YOUR_DEEPL_API_KEY"``` with your key.

4. in ```selection_translator.py```, set source language and target language, e.g.
```
source_lang = "EN"
target_lang = "ZH"
```
6. run the Python script, e.g. ```python3 selection_translator.py```
