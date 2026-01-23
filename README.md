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

# Dexcription
### How It Works (Layout Logic)

This API works by **extending the PDF page width on the right side by 5 cm**, while keeping the original PDF content unchanged.

**Layout behavior:**
- The original PDF page remains intact.
- An additional **5 cm space is added to the right side** of each page.
- Text annotations are placed inside this newly created space.

**Text positioning logic:**
- The text starts from a **top margin of 5 cm** (`marginTopCm = 5`).
- The horizontal position uses an offset of **`x = -1 cm` relative to the original PDF content**, so the text visually aligns closer to the original page edge.
- As a result, the text effectively occupies a **6 cm horizontal area**:
  - 5 cm from the added page width
  - + 1 cm overlap/alignment offset toward the original page

This approach ensures:
- No overlap with the original PDF content
- Consistent spacing for annotations
- Clean and predictable layout for any PDF size

**IT WILL WRITE AT ALL PAGES**

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


