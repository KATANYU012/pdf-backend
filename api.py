from flask import Flask, request, send_file
from flask_cors import CORS
from pdf2docx import Converter
import os
import uuid

app = Flask(__name__)
CORS(app) # อนุญาตให้ HTML เรียกใช้งานได้

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/convert', methods=['POST'])
def convert_pdf():
    if 'file' not in request.files:
        return "No file uploaded", 400
    
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400

    # 1. บันทึกไฟล์ PDF ชั่วคราว
    filename = str(uuid.uuid4())
    pdf_path = os.path.join(UPLOAD_FOLDER, f"{filename}.pdf")
    docx_path = os.path.join(UPLOAD_FOLDER, f"{filename}.docx")
    
    file.save(pdf_path)

    try:
        # 2. แปลง PDF เป็น DOCX (หัวใจสำคัญตรงนี้)
        cv = Converter(pdf_path)
        cv.convert(docx_path, start=0, end=None)
        cv.close()

        # 3. ส่งไฟล์ Word กลับไปให้หน้าเว็บ
        return send_file(docx_path, as_attachment=True, download_name=f"{file.filename.split('.')[0]}.docx")

    except Exception as e:
        return str(e), 500
    
    finally:
        # 4. ลบไฟล์ขยะทิ้ง (Clean up)
        if os.path.exists(pdf_path): os.remove(pdf_path)
        # หมายเหตุ: docx_path จะถูกลบหลังจากส่งไฟล์เสร็จ หรือตั้ง Job ลบทีหลัง (ในโค้ดนี้เก็บไว้ก่อนเผื่อส่งพลาด)

if __name__ == '__main__':
    print("Server is running on http://localhost:5000")
    print("พร้อมแปลงไฟล์แล้วครับ...")
    app.run(port=5000, debug=True)