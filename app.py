from fastapi import FastAPI, UploadFile, File
from docling.document_converter import DocumentConverter
import tempfile
import os

app = FastAPI()

@app.post("/extract")
async def extract(file: UploadFile = File(...)):

    # Force cache to writable location
    os.environ["DOCLING_CACHE_DIR"] = "/tmp"
    os.environ["XDG_CACHE_HOME"] = "/tmp"

    with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp:
        tmp.write(await file.read())
        temp_path = tmp.name

    try:
        converter = DocumentConverter()
        result = converter.convert(temp_path)

        if not result or not result.document:
            return {"extracted_text": ""}

        text = result.document.export_to_markdown()

        return {"extracted_text": text}

    except Exception as e:
        return {"error": str(e)}

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
