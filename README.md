<<<<<<< HEAD



=======
# API PDF Resize & Write Text

API based on Node.js + Python for:

Expanding PDF page canvas (paper becomes wider, original content stays unchanged)

Adding text (stamp / annotation) onto the PDF

Supporting multi-page PDFs

Accepting simple text input or advanced JSON options

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
DEFAULT (can be change)

-
- The text starts from a **top margin of 5 cm** (`marginTopCm = 5`).
- The horizontal position uses an offset of **`x = -1 cm` relative to the original PDF content**, so the text visually aligns closer to the original page edge.
- As a result, the text effectively occupies a **6 cm horizontal area**:
  - 5 cm from the added page width
  - - 1 cm overlap/alignment offset toward the original page

This approach ensures:

- No overlap with the original PDF content
- Consistent spacing for annotations
- Clean and predictable layout for any PDF size

**IT WORKS MORE THAN 1 PAGES**

---

## How to call API - Windows

---

copy envwindows.example to .env

## cmd/term

npm install

node -v

python --version

pip install -r requirements.txt

npm start

## formula:

curl.exe [opsi] -X POST <URL_API>

-F "<field>=<value>"

-F "<field>=@<path_file>"

-o <file_output>

## examples cmd windows

curl.exe -sS -X POST "http://localhost:3000/resize-stamp" ^

-F "file=@\"D:\Documents\contoh pdf\NKNK.pdf\";type=application/pdf" ^

-F "text=TEST" ^

-o "D:\Documents\contoh pdf\out.pdf"

or

- curl.exe -sS -X POST "http://localhost:3000/resize-stamp" -F "file=@\"D:\Documents\contoh pdf\NKNK.pdf\";type=application/pdf" -F "text=TEST"\ -o "D:\Documents\contoh pdf\out.pdf"

## If want custom position text, edit dxCm and dyCm:

curl.exe -sS -X POST "http://localhost:3000/resize-stamp" ^

-F "file=@\"D:\Documents\contoh pdf\NKNK.pdf\";type=application/pdf" ^

-F "text=TEST" ^

-F "dxCm=-1.5" ^

-F "dyCm=-4" ^

-o "D:\Documents\contoh pdf\out.pdf"

## or

curl.exe -sS -X POST "http://localhost:3000/resize-stamp" -F "file=@\"D:\Documents\contoh pdf\NKNK.pdf\";type=application/pdf" -F "text=TEST" -F "dxCm=-1.5" -o "D:\Documents\contoh pdf\out.pdf"

## If more than 1 page

curl.exe -sS -X POST "http://localhost:3000/resize-stamp" -F "file=@D:\Documents\contoh pdf\NKNK.pdf;type=application/pdf" -F "text=TEST Halaman 1" -F "text=TEST Halaman 2" -F "dxCm=-1" -F"dyCm=4" -o "D:\Documents\contoh pdf\out.pdf"

---

## How to call API - Ubuntu / Linux

---

## term

npm install

node -v

python3 --version

sudo apt install python3-pip

pip install -r requirements.txt

npm start

## examples term ubuntu/linux

curl -X POST "http://localhost:3000/resize-stamp" \

-F "file=@/home/user/input.pdf" \

-F "text=Hello World" \

-o /home/user/output.pdf

## or

curl -X POST "http://localhost:3000/resize-stamp" -F "file=@/home/user/input.pdf" -F "text=Hello World" -o /home/user/output.pdf

## If want custom position text, edit dxCm and dyCm:

curl -X POST "http://localhost:3000/resize-stamp" \

-F "file=@/home/user/input.pdf" \

-F "text=Hello World" \

-F "dxCm=-1.5" \

-F "dyCm=-3" \

-o /home/user/output.pdf

## or
curl -X POST "http://localhost:3000/resize-stamp" -F "file=@/home/user/input.pdf" -F "text=Hello World" -F "dxCm=-1.5" -F "dyCm=-3"-o /home/user/output.pdf

## If more than 1 page
curl -X POST "http://localhost:3000/resize-stamp" -F "file=@/home/user/input.pdf" -F "text=Hello World" -F "text=Hello World2" -F "dxCm=-1.5" -F "dyCm=-3"-o /home/user/output.pdf

=======



=======
# API PDF Resize & Write Text

API based on Node.js + Python for:

Expanding PDF page canvas (paper becomes wider, original content stays unchanged)

Adding text (stamp / annotation) onto the PDF

Supporting multi-page PDFs

Accepting simple text input or advanced JSON options

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
DEFAULT (can be change)

-
- The text starts from a **top margin of 5 cm** (`marginTopCm = 5`).
- The horizontal position uses an offset of **`x = -1 cm` relative to the original PDF content**, so the text visually aligns closer to the original page edge.
- As a result, the text effectively occupies a **6 cm horizontal area**:
  - 5 cm from the added page width
  - - 1 cm overlap/alignment offset toward the original page

This approach ensures:

- No overlap with the original PDF content
- Consistent spacing for annotations
- Clean and predictable layout for any PDF size

**IT WORKS MORE THAN 1 PAGES**

---

## How to call API - Windows

---

copy envwindows.example to .env

## cmd/term

npm install

node -v

python --version

pip install -r requirements.txt

npm start

## formula:

curl.exe [opsi] -X POST <URL_API>

-F "<field>=<value>"

-F "<field>=@<path_file>"

-o <file_output>

## examples cmd windows

curl.exe -sS -X POST "http://localhost:3000/resize-stamp" ^

-F "file=@\"D:\Documents\contoh pdf\NKNK.pdf\";type=application/pdf" ^

-F "text=TEST" ^

-o "D:\Documents\contoh pdf\out.pdf"

or

- curl.exe -sS -X POST "http://localhost:3000/resize-stamp" -F "file=@\"D:\Documents\contoh pdf\NKNK.pdf\";type=application/pdf" -F "text=TEST"\ -o "D:\Documents\contoh pdf\out.pdf"

## If want custom position text, edit dxCm and dyCm:

curl.exe -sS -X POST "http://localhost:3000/resize-stamp" ^

-F "file=@\"D:\Documents\contoh pdf\NKNK.pdf\";type=application/pdf" ^

-F "text=TEST" ^

-F "dxCm=-1.5" ^

-F "dyCm=-4" ^

-o "D:\Documents\contoh pdf\out.pdf"

## or

curl.exe -sS -X POST "http://localhost:3000/resize-stamp" -F "file=@\"D:\Documents\contoh pdf\NKNK.pdf\";type=application/pdf" -F "text=TEST" -F "dxCm=-1.5" -o "D:\Documents\contoh pdf\out.pdf"

## If more than 1 page

curl.exe -sS -X POST "http://localhost:3000/resize-stamp" -F "file=@D:\Documents\contoh pdf\NKNK.pdf;type=application/pdf" -F "text=TEST Halaman 1" -F "text=TEST Halaman 2" -F "dxCm=-1" -F"dyCm=4" -o "D:\Documents\contoh pdf\out.pdf"

## More than 1 option text at 1 page
LOGIC STANDART
-
---
```json
curl.exe -sS -X POST "http://localhost:3000/resize-stamp" -F "file=@D:\Documents\contoh pdf\rekening.pdf;type=application/pdf" -F "options={\"texts\":[{\"value\":\"Hello World!\",\"page\":1,\"dxCm\":0,\"dyCm\":-6.3},{\"value\":\"Hello World2!\",\"page\":1,\"dxCm\":0,\"dyCm\":-6.6},{\"value\":\"Hello World!3\",\"page\":1,\"dxCm\":0,\"dyCm\":-6.9},{\"value\":\"PAGE 2 - A\",\"page\":2,\"dxCm\":1,\"dyCm\":-6.3},{\"value\":\"PAGE 2 - B\",\"page\":2,\"dxCm\":1,\"dyCm\":-6.6}]}" -o "D:\Documents\contoh pdf\rekeningvstandart.pdf"  

```
logic for -F option
```json

{
  "addWidthCm": 5,
  "side": "right",
  "applyTo": "Both",
  "texts": [
    {
      "value": "Hello World!",
      "page": 1,
      "dxCm": 0,
      "dyCm": -6.3,
    },
    {
      "value": "Hello World2!",
      "page": 1,
      "dxCm": 0,
      "dyCm": -6.6,
    }
    {
      "value": "Hello World3!",
      "page": 1,
      "dxCm": 0,
      "dyCm": -6.9,
    }
    {
      "value": "PAGE 2 - A",
      "page": 2,
      "dxCm": 0,
      "dyCm": -6.3,
      }
      {
      "value": "PAGE 2 - B",
      "page": 2,
      "dxCm": 0,
      "dyCm": -6.6,
      }
  ],
}
```
LOGIC FULL
-
----

```json
curl.exe -sS -X POST "http://localhost:3000/resize-stamp" -F "file=@D:\Documents\contoh pdf\rekening.pdf;type=application/pdf" -F "options={\"addWidthCm\":5,\"side\":\"right\",\"applyTo\":\"Both\",\"texts\":[{\"value\":\"Hello World!\",\"page\":1,\"dxCm\":20,\"dyCm\":-6.3,\"position\":\"left_top\",\"marginTopCm\":5,\"marginRightCm\":1,\"font\":\"Helvetica\",\"fontSize\":8.5,\"align\":\"right\",\"charSpace\":0.5},{\"value\":\"Hello World2!\",\"page\":1,\"dxCm\":20,\"dyCm\":-6.6,\"position\":\"left_top\",\"marginTopCm\":5,\"marginRightCm\":1,\"font\":\"Helvetica\",\"fontSize\":8.5,\"align\":\"right\",\"charSpace\":0.5},{\"value\":\"Hello World3!\",\"page\":1,\"dxCm\":20,\"dyCm\":-6.9,\"position\":\"left_top\",\"marginTopCm\":5,\"marginRightCm\":1,\"font\":\"Helvetica\",\"fontSize\":8.5,\"align\":\"right\",\"charSpace\":0.5},{\"value\":\"PAGE 2 - A\",\"page\":2,\"dxCm\":20,\"dyCm\":-6.3,\"position\":\"left_top\",\"marginTopCm\":5,\"marginRightCm\":1,\"font\":\"Helvetica\",\"fontSize\":8.5,\"align\":\"right\",\"charSpace\":0.5},{\"value\":\"PAGE 2 - B\",\"page\":2,\"dxCm\":20,\"dyCm\":-6.6,\"position\":\"left_top\",\"marginTopCm\":5,\"marginRightCm\":1,\"font\":\"Helvetica\",\"fontSize\":8.5,\"align\":\"right\",\"charSpace\":0.5}]}" -o "D:\Documents\contoh pdf\rekeningvfull.pdf"
```

logic -F option
```
{
  "addWidthCm": 5,
  "side": "right",
  "applyTo": "Both",
  "texts": [
    {
      "value": "Hello World!",
      "page": 1,
      "position": "left_top",
      "marginTopCm": 5,
      "marginRightCm": 1,
      "dxCm": 0,
      "dyCm": -6.3,
      "font": "Helvetica",
      "fontSize": 8.5,
      "align": "right",
      "charSpace": 0.5
    }
    {
      "value": "Hello World2!",
      "page": 1,
      "position": "left_top",
      "marginTopCm": 5,
      "marginRightCm": 1,
      "dxCm": 0,
      "dyCm": -6.6,
      "font": "Helvetica",
      "fontSize": 8.5,
      "align": "right",
      "charSpace": 0.5
    }
    {
      "value": "Hello World3!",
      "page": 1,
      "position": "left_top",
      "marginTopCm": 5,
      "marginRightCm": 1,
      "dxCm": 0,
      "dyCm": -6.9,
      "font": "Helvetica",
      "fontSize": 8.5,
      "align": "right",
      "charSpace": 0.5
    }
    {
      "value": "PAGE 2 - A",
      "page": 2,
      "position": "left_top",
      "marginTopCm": 5,
      "marginRightCm": 1,
      "dxCm": 0,
      "dyCm": -6.3,
      "font": "Helvetica",
      "fontSize": 8.5,
      "align": "right",
      "charSpace": 0.5
    }
    {
      "value": "PAGE 2 - B",
      "page": 2,
      "position": "left_top",
      "marginTopCm": 5,
      "marginRightCm": 1,
      "dxCm": 0,
      "dyCm": -6.6,
      "font": "Helvetica",
      "fontSize": 8.5,
      "align": "right",
      "charSpace": 0.5
      }
  ],
}
```
---

## How to call API - Ubuntu / Linux

---

## term

npm install

node -v

python3 --version

sudo apt install python3-pip

pip install -r requirements.txt

npm start

## examples term ubuntu/linux

curl -X POST "http://localhost:3000/resize-stamp" \

-F "file=@/home/user/input.pdf" \

-F "text=Hello World" \

-o /home/user/output.pdf

## or

curl -X POST "http://localhost:3000/resize-stamp" -F "file=@/home/user/input.pdf" -F "text=Hello World" -o /home/user/output.pdf

## If want custom position text, edit dxCm and dyCm:

curl -X POST "http://localhost:3000/resize-stamp" \

-F "file=@/home/user/input.pdf" \

-F "text=Hello World" \

-F "dxCm=-1.5" \

-F "dyCm=-3" \

-o /home/user/output.pdf

## or
curl -X POST "http://localhost:3000/resize-stamp" -F "file=@/home/user/input.pdf" -F "text=Hello World" -F "dxCm=-1.5" -F "dyCm=-3"-o /home/user/output.pdf

## If more than 1 page
curl -X POST "http://localhost:3000/resize-stamp" -F "file=@/home/user/input.pdf" -F "text=Hello World" -F "text=Hello World2" -F "dxCm=-1.5" -F "dyCm=-3"-o /home/user/output.pdf

## More than 1 option text at 1 page

LOGIC STANDART
-
---

```bash
curl -sS -X POST "http://localhost:3000/resize-stamp" \
 -F "file=@/home/user/Documents/contoh_pdf/rekening.pdf;type=application/pdf" \
 -F "options={\"texts\":[{\"value\":\"Hello World!\",\"page\":1,\"dxCm\":0,\"dyCm\":-6.3},{\"value\":\"Hello World2!\",\"page\":1,\"dxCm\":0,\"dyCm\":-6.6},{\"value\":\"Hello World!3\",\"page\":1,\"dxCm\":0,\"dyCm\":-6.9},{\"value\":\"PAGE 2 - A\",\"page\":2,\"dxCm\":1,\"dyCm\":-6.3},{\"value\":\"PAGE 2 - B\",\"page\":2,\"dxCm\":1,\"dyCm\":-6.6}]}" \
 -o "/home/user/Documents/contoh_pdf/rekeningvstandart.pdf"
```
logic -F option
```
{
  "addWidthCm": 5,
  "side": "right",
  "applyTo": "Both",
  "texts": [
    {
      "value": "Hello World!",
      "page": 1,
      "dxCm": 0,
      "dyCm": -6.3
    },
    {
      "value": "Hello World2!",
      "page": 1,
      "dxCm": 0,
      "dyCm": -6.6
    },
    {
      "value": "Hello World3!",
      "page": 1,
      "dxCm": 0,
      "dyCm": -6.9
    },
    {
      "value": "PAGE 2 - A",
      "page": 2,
      "dxCm": 0,
      "dyCm": -6.3
    },
    {
      "value": "PAGE 2 - B",
      "page": 2,
      "dxCm": 0,
      "dyCm": -6.6
    }
  ]
}
```
```json
curl -sS -X POST "http://localhost:3000/resize-stamp" \
 -F "file=@/home/user/Documents/contoh_pdf/rekening.pdf;type=application/pdf" \
 -F "options={\"addWidthCm\":5,\"side\":\"right\",\"applyTo\":\"Both\",\"texts\":[{\"value\":\"Hello World!\",\"page\":1,\"dxCm\":20,\"dyCm\":-6.3,\"position\":\"left_top\",\"marginTopCm\":5,\"marginRightCm\":1,\"font\":\"Helvetica\",\"fontSize\":8.5,\"align\":\"right\",\"charSpace\":0.5},{\"value\":\"Hello World2!\",\"page\":1,\"dxCm\":20,\"dyCm\":-6.6,\"position\":\"left_top\",\"marginTopCm\":5,\"marginRightCm\":1,\"font\":\"Helvetica\",\"fontSize\":8.5,\"align\":\"right\",\"charSpace\":0.5},{\"value\":\"Hello World3!\",\"page\":1,\"dxCm\":20,\"dyCm\":-6.9,\"position\":\"left_top\",\"marginTopCm\":5,\"marginRightCm\":1,\"font\":\"Helvetica\",\"fontSize\":8.5,\"align\":\"right\",\"charSpace\":0.5},{\"value\":\"PAGE 2 - A\",\"page\":2,\"dxCm\":20,\"dyCm\":-6.3,\"position\":\"left_top\",\"marginTopCm\":5,\"marginRightCm\":1,\"font\":\"Helvetica\",\"fontSize\":8.5,\"align\":\"right\",\"charSpace\":0.5},{\"value\":\"PAGE 2 - B\",\"page\":2,\"dxCm\":20,\"dyCm\":-6.6,\"position\":\"left_top\",\"marginTopCm\":5,\"marginRightCm\":1,\"font\":\"Helvetica\",\"fontSize\":8.5,\"align\":\"right\",\"charSpace\":0.5}]}" \
 -o "/home/user/Documents/contoh_pdf/rekeningvfull.pdf"
```
logic -F option
```
{
  "addWidthCm": 5,
  "side": "right",
  "applyTo": "Both",
  "texts": [
    {
      "value": "Hello World!",
      "page": 1,
      "position": "left_top",
      "marginTopCm": 5,
      "marginRightCm": 1,
      "dxCm": 0,
      "dyCm": -6.3,
      "font": "Helvetica",
      "fontSize": 8.5,
      "align": "right",
      "charSpace": 0.5
    },
    {
      "value": "Hello World2!",
      "page": 1,
      "position": "left_top",
      "marginTopCm": 5,
      "marginRightCm": 1,
      "dxCm": 0,
      "dyCm": -6.6,
      "font": "Helvetica",
      "fontSize": 8.5,
      "align": "right",
      "charSpace": 0.5
    },
    {
      "value": "Hello World3!",
      "page": 1,
      "position": "left_top",
      "marginTopCm": 5,
      "marginRightCm": 1,
      "dxCm": 0,
      "dyCm": -6.9,
      "font": "Helvetica",
      "fontSize": 8.5,
      "align": "right",
      "charSpace": 0.5
    },
    {
      "value": "PAGE 2 - A",
      "page": 2,
      "position": "left_top",
      "marginTopCm": 5,
      "marginRightCm": 1,
      "dxCm": 0,
      "dyCm": -6.3,
      "font": "Helvetica",
      "fontSize": 8.5,
      "align": "right",
      "charSpace": 0.5
    },
    {
      "value": "PAGE 2 - B",
      "page": 2,
      "position": "left_top",
      "marginTopCm": 5,
      "marginRightCm": 1,
      "dxCm": 0,
      "dyCm": -6.6,
      "font": "Helvetica",
      "fontSize": 8.5,
      "align": "right",
      "charSpace": 0.5
    }
  ]
}
```
>>>>>>> 3581adb (Update API resize & stamp + README and gitignore)
