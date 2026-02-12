from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from docling.document_converter import DocumentConverter
import tempfile
import shutil
import os

app = FastAPI()

# 🔥 Force lightweight OCR (Tesseract only)
converter = DocumentConverter(
    ocr_engine="tesseract"
)


@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    try:
        # Save uploaded file temporarily
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_file_path = temp_file.name

        # Convert document
        result = converter.convert(temp_file_path)

        # Extract text
        extracted_text = result.document.export_to_text()

        # Cleanup
        os.remove(temp_file_path)

        return JSONResponse(content={
            "extracted_text": extracted_text
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
