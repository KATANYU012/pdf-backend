from flask import Flask, request, send_file
from flask_cors import CORS
import convertapi
import os
import uuid

app = Flask(__name__)
CORS(app)  # อนุญาตให้หน้าเว็บเรียกใช้งานได้

# ==========================================
# 🔴 แก้ไขแล้ว: ใช้ api_credentials แทน api_secret
# รหัสนี้คือ Production Token ของพี่ที่ถูกต้องครับ
convertapi.api_credentials = 'YUEZgVh6C5WpwE65S1oNN1yBnuVZV8Jt'
# ==========================================

# ใช้ /tmp เพราะ Render เป็น Linux (และไฟล์จะถูกลบเองเมื่อรีสตาร์ท)
UPLOAD_FOLDER = '/tmp'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/convert', methods=['POST'])
def convert_pdf():
    # 1. ตรวจสอบว่ามีการส่งไฟล์มาไหม
    if 'file' not in request.files:
        return "No file uploaded", 400
    
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400

    # 2. ตั้งชื่อไฟล์แบบสุ่ม (ป้องกันชื่อซ้ำ)
    filename = str(uuid.uuid4())
    pdf_path = os.path.join(UPLOAD_FOLDER, f"{filename}.pdf")
    docx_path = os.path.join(UPLOAD_FOLDER, f"{filename}.docx")
    
    try:
        # 3. บันทึกไฟล์ PDF ลงเครื่อง Server ชั่วคราว
        print(f"Receiving file: {file.filename}")
        file.save(pdf_path)

        # 4. ส่งไปแปลงที่ ConvertAPI
        print("Uploading to ConvertAPI...")
        # สั่งแปลงไฟล์โดยใช้ from_format='pdf'
        result = convertapi.convert('docx', { 'File': pdf_path }, from_format='pdf')
        
        # 5. บันทึกไฟล์ที่แปลงเสร็จแล้วกลับลงเครื่อง
        print("Saving converted file...")
        result.save_files(docx_path)

        # 6. ส่งไฟล์ Word กลับไปให้หน้าเว็บ
        print("Sending file back to client...")
        return send_file(
            docx_path, 
            as_attachment=True, 
            download_name=f"{file.filename.replace('.pdf', '')}.docx",
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

    except Exception as e:
        # กรณี Error อื่นๆ (ใช้ตัวดักจับแบบกว้างเพื่อป้องกันโปรแกรมพัง)
        print(f"Server Error: {str(e)}")
        return f"Server Error: {str(e)}", 500
    
    finally:
        # 7. ลบไฟล์ขยะทิ้งเพื่อคืนพื้นที่ (Clean up)
        try:
            if os.path.exists(pdf_path): os.remove(pdf_path)
            if os.path.exists(docx_path): os.remove(docx_path)
            print("Cleanup completed.")
        except Exception as e:
            print(f"Cleanup Error: {str(e)}")

# รัน Server
if __name__ == '__main__':
    # พอร์ต 5000 สำหรับ Localhost, Render จะใช้พอร์ตของเขาเอง
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)