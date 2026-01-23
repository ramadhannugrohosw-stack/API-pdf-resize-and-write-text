#!/usr/bin/env bash
set -euo pipefail

# -----------------------------------------------------------------------------
# Example: call /resize-stamp API
# - Upload a PDF
# - Resize page canvas (+5 cm width by default)
# - Stamp custom text on the blank area (anchor: blank_right)
#
# Usage (Linux/Mac/WSL/Git Bash):
#   chmod +x examples/curl_resize_and_stamp.sh
#   ./examples/curl_resize_and_stamp.sh ./input.pdf
#
# Optional env:
#   API_BASE="http://localhost:3000"  (default)
#   OUT="output.pdf"                  (default: resized_stamped_output.pdf)
# -----------------------------------------------------------------------------

API_BASE="${API_BASE:-http://localhost:3000}"
OUT="${OUT:-resized_stamped_output.pdf}"

if [ $# -lt 1 ]; then
  echo "Usage: $0 <input.pdf>"
  echo "Example: $0 ./sample.pdf"
  exit 1
fi

INPUT_PDF="$1"

if [ ! -f "$INPUT_PDF" ]; then
  echo "Input file not found: $INPUT_PDF"
  exit 1
fi

# JSON options (sent as form field named "options")
# Notes:
# - addWidthCm: add canvas width by cm (kertas melebar, konten tetap)
# - side: right|left|both
# - applyTo: MediaBox|CropBox|Both
# - texts[].anchor:
#     - "page"       => x/y from bottom-left of page
#     - "blank_right"=> x/y from bottom-left of new blank area on right (only for side=right)
# - texts[].page: "all" or 1-based page number (e.g., 1)
OPTIONS_JSON='{
  "addWidthCm": 5,
  "side": "right",
  "applyTo": "Both",
  "texts": [
    {
      "value": "TEST AREA KOSONG (kanan)",
      "xCm": 1.0,
      "yCm": 25.0,
      "fontSize": 14,
      "font": "Helvetica",
      "page": "all",
      "anchor": "blank_right"
    },
    {
      "value": "Label dari page origin",
      "xCm": 1.0,
      "yCm": 2.0,
      "fontSize": 10,
      "font": "Helvetica",
      "page": 1,
      "anchor": "page"
    }
  ]
}'

echo "API_BASE : $API_BASE"
echo "INPUT    : $INPUT_PDF"
echo "OUT      : $OUT"
echo "Calling  : POST $API_BASE/resize-stamp"

curl -sS -X POST "$API_BASE/resize-stamp" \
  -F "file=@${INPUT_PDF};type=application/pdf" \
  -F "options=${OPTIONS_JSON}" \
  -o "$OUT"

echo "Done. Output saved: $OUT"
