// server.js
// API: Resize halaman PDF (kertas melebar, konten tetap) + tambah teks
// Engine: tools/resize_and_stamp.py (Python: pikepdf + reportlab)
// Compatible: Windows + Ubuntu

require("dotenv").config();

const express = require("express");
const multer = require("multer");
const fs = require("fs");
const fsp = require("fs/promises");
const path = require("path");
const os = require("os");
const crypto = require("crypto");
const { spawn } = require("child_process");

const app = express();

// ---------- Config ----------
const PORT = parseInt(process.env.PORT || "3000", 10);

const TMP_DIR = process.env.TMP_DIR
  ? path.resolve(process.env.TMP_DIR)
  : path.resolve(__dirname, "temp");

const PYTHON_BIN = (process.env.PYTHON_BIN || "").trim(); // optional override
const PY_SCRIPT = path.resolve(__dirname, "tools", "resize_and_stamp.py");

// upload limit default 50MB
const MAX_FILE_MB = parseInt(process.env.MAX_FILE_MB || "50", 10);
const MAX_FILE_BYTES = MAX_FILE_MB * 1024 * 1024;

// Default stamping params when user only sends "text"
const DEFAULT_ADD_WIDTH_CM = Number(process.env.DEFAULT_ADD_WIDTH_CM || 0);
const DEFAULT_SIDE = (process.env.DEFAULT_SIDE || "right").toLowerCase(); // right|left|both
const DEFAULT_APPLY_TO = process.env.DEFAULT_APPLY_TO || "both"; // MediaBox|CropBox|Both
const DEFAULT_X_CM = Number(process.env.DEFAULT_X_CM || 19); // negative -> condong ke halaman asli
const DEFAULT_Y_CM = Number(process.env.DEFAULT_Y_CM || 14);
const DEFAULT_FONT_SIZE = Number(process.env.DEFAULT_FONT_SIZE || 8);
const DEFAULT_FONT = process.env.DEFAULT_FONT || "Helvetica";
const DEFAULT_ALIGN = (process.env.DEFAULT_ALIGN || "right").toLowerCase();
const DEFAULT_CHAR_SPACE = Number(process.env.DEFAULT_CHAR_SPACE || 0.5);

// Ensure tmp dir exists
if (!fs.existsSync(TMP_DIR)) fs.mkdirSync(TMP_DIR, { recursive: true });

// ---------- NEW: JSON body parser (untuk Base64 input) ----------
// Base64 PDF bisa besar, jadi set limit lebih longgar.
// Ini TIDAK mengubah perilaku endpoint multipart (/resize-stamp).
const JSON_LIMIT_MB = Math.max(100, MAX_FILE_MB * 3); // aman untuk base64 overhead
app.use(express.json({ limit: `${JSON_LIMIT_MB}mb` }));
app.use(express.urlencoded({ extended: true, limit: `${JSON_LIMIT_MB}mb` }));

// ---------- Helpers ----------
function randomId() {
  return crypto.randomBytes(16).toString("hex");
}

function resolvePythonBin() {
  if (PYTHON_BIN) return PYTHON_BIN;
  if (os.platform() === "win32") return "python";
  return "python3";
}

async function safeUnlink(filePath) {
  try {
    await fsp.unlink(filePath);
  } catch (_) {
    // ignore
  }
}

function safeNumber(v, fallback) {
  const n = Number(v);
  return Number.isFinite(n) ? n : fallback;
}

function normalizeOptions(options) {
  return {
    addWidthCm: Number(options.addWidthCm ?? DEFAULT_ADD_WIDTH_CM),
    side: String(options.side ?? DEFAULT_SIDE).toLowerCase(),
    applyTo: String(options.applyTo ?? DEFAULT_APPLY_TO).toLowerCase(),
    texts: Array.isArray(options.texts) ? options.texts : [],
  };
}

function buildDefaultOptionsFromText({ textRaw, dxCm, dyCm }) {
  // text bisa string atau array jika field "text" dikirim berulang kali
  const textList = Array.isArray(textRaw)
    ? textRaw.map((t) => String(t || "").trim()).filter(Boolean)
    : [String(textRaw || "").trim()].filter(Boolean);

  return {
    addWidthCm: DEFAULT_ADD_WIDTH_CM,
    side: DEFAULT_SIDE,
    applyTo: DEFAULT_APPLY_TO,
    texts: textList.length
      ? textList.length > 1
        ? textList.map((t, idx) => ({
            value: t,
            align: DEFAULT_ALIGN, // ✅ DEFAULT RIGHT ALIGN
            charSpace: DEFAULT_CHAR_SPACE,
            position: "right_top",
            marginTopCm: 5,
            dxCm: dxCm,
            dyCm: dyCm,
            fontSize: DEFAULT_FONT_SIZE,
            font: DEFAULT_FONT,
            page: idx + 1, // 1-based page number
          }))
        : [
            {
              value: textList[0],
              position: "right_top",
              marginTopCm: 5,
              dxCm: dxCm,
              dyCm: dyCm,
              fontSize: DEFAULT_FONT_SIZE,
              font: DEFAULT_FONT,
              page: "all", // tetap seperti sebelumnya
            },
          ]
      : [],
  };
}

function stripDataUrlPrefix(b64) {
  // dukung input: "data:application/pdf;base64,AAAA..."
  const s = String(b64 || "").trim();
  const m = s.match(/^data:application\/pdf;base64,(.*)$/i);
  return m ? m[1] : s;
}

function looksLikeBase64(s) {
  if (!s || typeof s !== "string") return false;
  // longgar saja, yang penting bukan kosong dan tidak ada karakter aneh
  // (kita akan validasi lebih lanjut saat decode)
  return /^[A-Za-z0-9+/=\s]+$/.test(s) && s.replace(/\s/g, "").length > 0;
}

async function runPythonResizeStamp({ inputPath, outputPath, options }) {
  const pythonBin = resolvePythonBin();

  // Pass options as JSON string arg to avoid shell quoting issues
  const args = [
    PY_SCRIPT,
    "--input",
    inputPath,
    "--output",
    outputPath,
    "--options",
    JSON.stringify(options),
  ];

  return await new Promise((resolve) => {
    const child = spawn(pythonBin, args, {
      windowsHide: true,
      stdio: ["ignore", "pipe", "pipe"],
    });

    let stdout = "";
    let stderr = "";

    child.stdout.on("data", (d) => (stdout += d.toString()));
    child.stderr.on("data", (d) => (stderr += d.toString()));

    child.on("error", (err) => {
      resolve({
        ok: false,
        code: -1,
        stdout,
        stderr,
        error: String(err?.message || err),
      });
    });

    child.on("close", (code) => {
      resolve({
        ok: code === 0,
        code,
        stdout,
        stderr,
      });
    });
  });
}

async function returnOutput({ req, res, outputPath }) {
  const outMode = String(req.query?.out || "both").toLowerCase(); // pdf | base64 | both
  const stat = await fsp.stat(outputPath);

  if (outMode === "both") {
    const buf = await fsp.readFile(outputPath);
    const b64 = buf.toString("base64");
    await safeUnlink(outputPath);

    const boundary = "pdfBoundary_" + randomId();
    res.status(200);
    res.setHeader("Content-Type", `multipart/mixed; boundary=${boundary}`);

    res.write(`--${boundary}\r\n`);
    res.write(`Content-Type: application/pdf\r\n`);
    res.write(
      `Content-Disposition: attachment; filename="resized_stamped_${Date.now()}.pdf"\r\n`,
    );
    res.write(`Content-Length: ${buf.length}\r\n\r\n`);
    res.write(buf);
    res.write(`\r\n`);

    const json = JSON.stringify({
      ok: true,
      mime: "application/pdf",
      size: buf.length,
      outputBase64: b64,
    });

    res.write(`--${boundary}\r\n`);
    res.write(`Content-Type: application/json\r\n\r\n`);
    res.write(json);
    res.write(`\r\n--${boundary}--\r\n`);
    return res.end();
  }

  if (outMode === "base64") {
    const buf = await fsp.readFile(outputPath);
    const b64 = buf.toString("base64");
    await safeUnlink(outputPath);

    return res.json({
      ok: true,
      mime: "application/pdf",
      size: stat.size,
      outputBase64: b64,
    });
  }

  // default pdf stream
  res.setHeader("Content-Type", "application/pdf");
  res.setHeader("Content-Length", String(stat.size));
  res.setHeader(
    "Content-Disposition",
    `attachment; filename="resized_stamped_${Date.now()}.pdf"`,
  );

  const rs = fs.createReadStream(outputPath);

  rs.on("error", async () => {
    await safeUnlink(outputPath);
    return res.status(500).end("Failed to read output PDF.");
  });

  rs.on("close", async () => {
    await safeUnlink(outputPath);
  });

  rs.pipe(res);
}

// ---------- Multer (upload PDF + optional JSON) ----------
const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, TMP_DIR),
  filename: (req, file, cb) => {
    const id = randomId();
    const original = file.originalname || `${file.fieldname}`;
    const safeBase = original
      .replace(/[^\w.\-()+\s]/g, "")
      .trim()
      .replace(/\s+/g, "_");
    cb(null, `${Date.now()}_${id}_${safeBase}`);
  },
});

// IMPORTANT:
// Jangan pakai pdfOnlyFilter untuk semua field, karena field "options" (JSON) akan ketolak.
// Kita bedakan berdasarkan fieldname.
function uploadFilter(req, file, cb) {
  const name = file.fieldname;

  if (name === "file") {
    const isPdfMime = file.mimetype === "application/pdf";
    const isPdfExt = (file.originalname || "").toLowerCase().endsWith(".pdf");
    if (isPdfMime || isPdfExt) return cb(null, true);
    return cb(new Error("Only PDF files are allowed for field 'file'."));
  }

  if (name === "options") {
    // allow JSON file
    const isJsonMime =
      file.mimetype === "application/json" || file.mimetype === "text/json";
    const isJsonExt = (file.originalname || "").toLowerCase().endsWith(".json");
    // Multer kadang memberi mimetype "application/octet-stream"; tetap izinkan jika ekstensi .json
    if (isJsonMime || isJsonExt) return cb(null, true);
    return cb(new Error("Only JSON files are allowed for field 'options'."));
  }

  // text/dxCm/dyCm tidak akan masuk ke sini karena itu bukan file
  return cb(null, true);
}

const upload = multer({
  storage,
  fileFilter: uploadFilter,
  limits: { fileSize: MAX_FILE_BYTES },
});

// ---------- Routes ----------
app.get("/", (req, res) => {
  res.json({
    ok: true,
    service: "pdf-resize-stamp",
    endpoints: {
      health: "GET /health",
      resizeStamp:
        "POST /resize-stamp (multipart form-data: file + (text|options) + optional dxCm/dyCm)",
      // NEW:
      resizeStampBase64:
        "POST /resize-stamp-base64 (application/json: fileBase64 + (text|options) + optional dxCm/dyCm)",
    },
  });
});

app.get("/health", (req, res) => {
  res.json({
    ok: true,
    python: resolvePythonBin(),
    scriptExists: fs.existsSync(PY_SCRIPT),
    tmpDir: TMP_DIR,
    defaults: {
      addWidthCm: DEFAULT_ADD_WIDTH_CM,
      side: DEFAULT_SIDE,
      applyTo: DEFAULT_APPLY_TO,
      xCm: DEFAULT_X_CM,
      yCm: DEFAULT_Y_CM,
      fontSize: DEFAULT_FONT_SIZE,
      font: DEFAULT_FONT,
    },
  });
});

/**
 * POST /resize-stamp
 *
 * multipart/form-data:
 *   - file: PDF (required)
 *   - text: string (optional)  -> DEFAULT MODE (paling simple)
 *   - dxCm: number (optional)  -> override per request
 *   - dyCm: number (optional)  -> override per request
 *
 * Advanced:
 *   - options: JSON string (optional)
 *   - options: JSON file upload (optional)  (mis. payload.json)
 *
 * Priority:
 *   1) options (string) / options (file) jika dikirim
 *   2) kalau tidak ada options, pakai DEFAULT MODE berbasis field "text"
 */
app.post(
  "/resize-stamp",
  upload.fields([
    { name: "file", maxCount: 1 },
    { name: "options", maxCount: 1 }, // JSON file upload
  ]),
  async (req, res) => {
    const inputPath = req.files?.file?.[0]?.path;
    if (!inputPath) {
      return res
        .status(400)
        .json({ ok: false, error: "Missing PDF file (field name: file)." });
    }

    const id = randomId();
    const outputPath = path.join(TMP_DIR, `${Date.now()}_${id}_output.pdf`);

    // NOTE: text/dxCm/dyCm datang dari req.body (bukan file)
    const textRaw = req.body?.text;
    const dxCm = safeNumber(req.body?.dxCm, 0);
    const dyCm = safeNumber(req.body?.dyCm, 0);

    let options = null;

    try {
      // A) options sebagai string JSON
      if (req.body?.options && typeof req.body.options === "string") {
        options = JSON.parse(req.body.options);
      }
      // B) options sebagai file JSON upload
      else if (req.files?.options?.[0]?.path) {
        const raw = await fsp.readFile(req.files.options[0].path, "utf-8");
        options = JSON.parse(raw);
      }
      // C) default mode: hanya "text"
      else {
        options = buildDefaultOptionsFromText({ textRaw, dxCm, dyCm });
      }

      if (!options || typeof options !== "object" || Array.isArray(options)) {
        throw new Error("Options must be a JSON object");
      }
    } catch (e) {
      // cleanup
      if (req.files?.options?.[0]?.path)
        await safeUnlink(req.files.options[0].path);
      await safeUnlink(inputPath);
      await safeUnlink(outputPath);

      return res.status(400).json({
        ok: false,
        error: "Invalid JSON in 'options' (or invalid options object).",
        detail: String(e?.message || e),
      });
    } finally {
      // hapus file options JSON setelah dibaca (kalau ada)
      if (req.files?.options?.[0]?.path)
        await safeUnlink(req.files.options[0].path);
    }

    options = normalizeOptions(options);

    // Guard: nothing to do
    if (options.texts.length === 0 && options.addWidthCm === 0) {
      await safeUnlink(inputPath);
      await safeUnlink(outputPath);
      return res.status(400).json({
        ok: false,
        error: "Nothing to do: no resize and no text to stamp",
      });
    }

    console.log("Normalized options:", options);
    console.log("req.body:", req.body);
    console.log("options before normalize:", options);

    const result = await runPythonResizeStamp({ inputPath, outputPath, options });

    await safeUnlink(inputPath);

    if (!result.ok) {
      await safeUnlink(outputPath);
      return res.status(500).json({
        ok: false,
        error:
          result.code === -1
            ? "Failed to start Python process."
            : "PDF processing failed.",
        exitCode: result.code,
        stderr: (result.stderr || "").trim() || null,
        stdout: (result.stdout || "").trim() || null,
        detail: result.error || null,
        usedOptions: options,
      });
    }

    try {
      return await returnOutput({ req, res, outputPath });
    } catch (e) {
      await safeUnlink(outputPath);
      return res.status(500).json({
        ok: false,
        error: "Could not return output PDF.",
        detail: String(e?.message || e),
      });
    }
  },
);

/**
 * NEW: POST /resize-stamp-base64
 *
 * Content-Type: application/json
 * Body:
 *   {
 *     "fileBase64": "<base64 pdf>"   // required (boleh juga data URL: data:application/pdf;base64,...)
 *     "options": {...}              // optional (object) OR string JSON
 *     "text": "..."                 // optional (dipakai kalau options tidak ada)
 *     "dxCm": 0, "dyCm": 0          // optional
 *   }
 *
 * Query:
 *   ?out=pdf | base64 | both   (sama seperti endpoint lama)
 */
app.post("/resize-stamp-base64", async (req, res) => {
  const id = randomId();
  const inputPath = path.join(TMP_DIR, `${Date.now()}_${id}_input.pdf`);
  const outputPath = path.join(TMP_DIR, `${Date.now()}_${id}_output.pdf`);

  // terima beberapa nama field yang umum dipakai
  const b64Raw =
    req.body?.fileBase64 ?? req.body?.pdfBase64 ?? req.body?.base64 ?? null;

  if (!b64Raw) {
    return res.status(400).json({
      ok: false,
      error: "Missing fileBase64 in JSON body.",
      hint: 'Send {"fileBase64":"..."} (base64 PDF)',
    });
  }

  const b64 = stripDataUrlPrefix(b64Raw);

  if (!looksLikeBase64(b64)) {
    return res.status(400).json({
      ok: false,
      error: "fileBase64 does not look like valid base64.",
    });
  }

  // Decode base64 -> buffer
  let pdfBuf = null;
  try {
    // jika base64 mengandung whitespace/newline, aman
    const cleaned = String(b64).replace(/\s/g, "");
    pdfBuf = Buffer.from(cleaned, "base64");

    // Validasi minimal: PDF biasanya diawali "%PDF"
    const head = pdfBuf.slice(0, 4).toString("utf-8");
    if (head !== "%PDF") {
      // masih mungkin PDF terenkripsi/aneh, tapi ini guard sederhana
      // kalau kamu mau longgar, boleh hapus blok ini.
      throw new Error("Decoded bytes do not look like a PDF (%PDF missing).");
    }

    if (pdfBuf.length > MAX_FILE_BYTES) {
      throw new Error(`File too large. Max ${MAX_FILE_MB}MB.`);
    }
  } catch (e) {
    await safeUnlink(inputPath);
    await safeUnlink(outputPath);
    return res.status(400).json({
      ok: false,
      error: "Invalid base64 PDF.",
      detail: String(e?.message || e),
    });
  }

  // Simpan buffer jadi file sementara
  try {
    await fsp.writeFile(inputPath, pdfBuf);
  } catch (e) {
    await safeUnlink(inputPath);
    await safeUnlink(outputPath);
    return res.status(500).json({
      ok: false,
      error: "Failed to write temp PDF file.",
      detail: String(e?.message || e),
    });
  }

  // Options handling (sama prioritas seperti endpoint lama)
  const textRaw = req.body?.text;
  const dxCm = safeNumber(req.body?.dxCm, 0);
  const dyCm = safeNumber(req.body?.dyCm, 0);

  let options = null;

  try {
    // A) options sebagai string JSON
    if (req.body?.options && typeof req.body.options === "string") {
      options = JSON.parse(req.body.options);
    }
    // B) options sebagai object JSON
    else if (req.body?.options && typeof req.body.options === "object") {
      options = req.body.options;
    }
    // C) default mode: hanya "text"
    else {
      options = buildDefaultOptionsFromText({ textRaw, dxCm, dyCm });
    }

    if (!options || typeof options !== "object" || Array.isArray(options)) {
      throw new Error("Options must be a JSON object");
    }
  } catch (e) {
    await safeUnlink(inputPath);
    await safeUnlink(outputPath);
    return res.status(400).json({
      ok: false,
      error: "Invalid JSON in 'options' (or invalid options object).",
      detail: String(e?.message || e),
    });
  }

  options = normalizeOptions(options);

  // Guard: nothing to do
  if (options.texts.length === 0 && options.addWidthCm === 0) {
    await safeUnlink(inputPath);
    await safeUnlink(outputPath);
    return res.status(400).json({
      ok: false,
      error: "Nothing to do: no resize and no text to stamp",
    });
  }

  console.log("[base64] Normalized options:", options);

  const result = await runPythonResizeStamp({ inputPath, outputPath, options });

  await safeUnlink(inputPath);

  if (!result.ok) {
    await safeUnlink(outputPath);
    return res.status(500).json({
      ok: false,
      error:
        result.code === -1
          ? "Failed to start Python process."
          : "PDF processing failed.",
      exitCode: result.code,
      stderr: (result.stderr || "").trim() || null,
      stdout: (result.stdout || "").trim() || null,
      detail: result.error || null,
      usedOptions: options,
    });
  }

  try {
    return await returnOutput({ req, res, outputPath });
  } catch (e) {
    await safeUnlink(outputPath);
    return res.status(500).json({
      ok: false,
      error: "Could not return output PDF.",
      detail: String(e?.message || e),
    });
  }
});

// ---------- Error handler ----------
app.use((err, req, res, next) => {
  if (!err) return next();

  if (err.code === "LIMIT_FILE_SIZE") {
    return res.status(413).json({
      ok: false,
      error: `File too large. Max ${MAX_FILE_MB}MB.`,
    });
  }

  return res.status(400).json({
    ok: false,
    error: err.message || "Bad Request",
  });
});

// ---------- Start ----------
app.listen(PORT, () => {
  console.log(`[pdf-resize-stamp] Listening on http://localhost:${PORT}`);
  console.log(`[pdf-resize-stamp] TMP_DIR=${TMP_DIR}`);
  console.log(`[pdf-resize-stamp] PYTHON=${resolvePythonBin()}`);
  console.log(`[pdf-resize-stamp] SCRIPT=${PY_SCRIPT}`);
});
