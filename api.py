from flask import Flask, request, send_file
from flask_cors import CORS
import convertapi
import os
import uuid
import replicate # ต้องมีอันนี้

app = Flask(__name__)
CORS(app)

# ==========================================
# 1. ตั้งค่า API Keys
# ==========================================
convertapi.api_credentials = 'YUEZgVh6C5WpwE65S1oNN1yBnuVZV8Jt'
os.environ["REPLICATE_API_TOKEN"] = "r8_NUTr4UIgJeYrJKidBTKP8eD2L4MzSdi1P7ErK" # <--- เปลี่ยนตรงนี้!

UPLOAD_FOLDER = '/tmp'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ==========================================
# 2. ระบบ PDF to Word
# ==========================================
@app.route('/convert', methods=['POST'])
def convert_pdf():
    if 'file' not in request.files: return "No file uploaded", 400
    file = request.files['file']
    if file.filename == '': return "No selected file", 400

    filename = str(uuid.uuid4())
    pdf_path = os.path.join(UPLOAD_FOLDER, f"{filename}.pdf")
    docx_path = os.path.join(UPLOAD_FOLDER, f"{filename}.docx")
    
    try:
        file.save(pdf_path)
        result = convertapi.convert('docx', { 'File': pdf_path }, from_format='pdf')
        result.save_files(docx_path)
        return send_file(
            docx_path, as_attachment=True, 
            download_name=f"{file.filename.replace('.pdf', '')}.docx",
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
    except Exception as e:
        return f"Server Error: {str(e)}", 500
    finally:
        try:
            if os.path.exists(pdf_path): os.remove(pdf_path)
            if os.path.exists(docx_path): os.remove(docx_path)
        except: pass

# ==========================================
# 3. ระบบ AI QR Code (Replicate)
# ==========================================
@app.route('/generate-ai-qr', methods=['POST'])
def generate_ai_qr():
    data = request.get_json()
    content = data.get('content')
    prompt = data.get('prompt')
    
    if not content or not prompt:
        return {"error": "Missing content or prompt"}, 400
        
    try:
        # สั่งให้ AI ทำงาน
        output = replicate.run(
            "nateraw/qrcode-stable-diffusion:9cdabf8f8a991351960c7ce2105de2909514b40bd27ac202dba57935b07d29d4",
            input={
                "prompt": prompt + ", masterpiece, high quality, highly detailed",
                "qr_code_content": content,
                "negative_prompt": "ugly, disfigured, low quality, blurry",
                "controlnet_conditioning_scale": 1.5,
            }
        )
        # ดึง URL รูปภาพส่งกลับไปให้หน้าเว็บ
        image_url = output[0] if isinstance(output, list) else output
        return {"success": True, "image_url": image_url}
        
    except Exception as e:
        print(f"Replicate Error: {str(e)}")
        # จัดการข้อความ Error ให้หน้าเว็บอ่านง่ายๆ
        if "402" in str(e) or "Insufficient credit" in str(e):
            return {"error": "เครดิต AI หมด กรุณาเปลี่ยน API Key ใหม่"}, 402
        return {"error": str(e)}, 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)