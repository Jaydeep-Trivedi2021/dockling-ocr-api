from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import pdfplumber
import pytesseract
from PIL import Image
import tempfile
import os

app = FastAPI()

@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    try:
        suffix = os.path.splitext(file.filename)[1].lower()

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
            temp.write(await file.read())
            temp_path = temp.name

        extracted_text = ""

        if suffix == ".pdf":
            with pdfplumber.open(temp_path) as pdf:
                for page in pdf.pages:
                    extracted_text += page.extract_text() or ""

        elif suffix in [".jpg", ".jpeg", ".png"]:
            image = Image.open(temp_path)
            extracted_text = pytesseract.image_to_string(image)

        else:
            os.remove(temp_path)
            return JSONResponse(
                content={"error": "Unsupported file type"},
                status_code=400
            )

        os.remove(temp_path)

        return {"extracted_text": extracted_text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
