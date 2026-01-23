# API PDF Resize & Write Text

API berbasis **Node.js + Python** untuk:
- Memperlebar halaman PDF (kertas melebar, konten asli tetap)
- Menambahkan teks (stamp / annotation) ke PDF
- Mendukung **multi-page PDF**
- Bisa input **teks sederhana** atau **JSON options lanjutan**

Engine PDF:
- Python (`pikepdf`, `reportlab`)
- Node.js (`express`, `multer`, `child_process`)

Compatible:
- ✅ Windows
- ✅ Ubuntu / Linux




-------------------------
How to call API - Windows
-
-------------------------


copy envwindows.example to .env

cmd/term
-

npm install

node -v

python --version

pip install -r requirements.txt

npm start



formula:
-
curl.exe [opsi] -X POST <URL_API> 

  -F "<field>=<value>" 
  
  -F "<field>=@<path_file>"
  
  -o <file_output>

examples cmd windows
-
curl.exe -sS -X POST "http://localhost:3000/resize-stamp" ^

  -F "file=@\"D:\Documents\contoh pdf\NKNK.pdf\";type=application/pdf" ^
 
  -F "text=TEST" ^
 
  -o "D:\Documents\contoh pdf\out.pdf"



--------------------------------
How to call API - Ubuntu / Linux
-
--------------------------------


term
-
npm install

node -v

python3 --version

sudo apt install python3-pip

pip install -r requirements.txt

npm start



examples term ubuntu/linux
-
curl -X POST "http://localhost:3000/resize-stamp" \
 
  -F "file=@/home/user/input.pdf" \
  
  -F "text=Hello World" \
  
  -o /home/user/output.pdf

