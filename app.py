from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from typing import Optional, Tuple
import pdfplumber
import pytesseract
from PIL import Image
import tempfile
import os
import httpx
from urllib.parse import urlparse

app = FastAPI()

async def download_file_from_url(url: str) -> Tuple[bytes, str]:
    """Download file from URL and return content and filename"""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        
        # Extract filename from URL
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        if not filename or '.' not in filename:
            # Try to get from content-disposition header
            content_disp = response.headers.get('content-disposition', '')
            if 'filename=' in content_disp:
                filename = content_disp.split('filename=')[1].strip('"')
            else:
                filename = 'document.pdf'  # default
        
        return response.content, filename

@app.post("/extract")
async def extract(
    file_url: Optional[str] = None,
    file: Optional[UploadFile] = File(None)
):
    try:
        # Handle file URL (from WXO)
        if file_url:
            file_content, filename = await download_file_from_url(file_url)
            suffix = os.path.splitext(filename)[1].lower()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
                temp.write(file_content)
                temp_path = temp.name
        
        # Handle direct file upload
        elif file:
            suffix = os.path.splitext(file.filename)[1].lower()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
                temp.write(await file.read())
                temp_path = temp.name
        
        else:
            return JSONResponse(
                content={"error": "Either file or file_url must be provided"},
                status_code=400
            )

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
