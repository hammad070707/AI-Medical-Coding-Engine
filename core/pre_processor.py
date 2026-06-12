import asyncio
from dotenv import load_dotenv
load_dotenv()
import re
import os
import fitz
import pytesseract
from PIL import Image
from typing import Dict
from loguru import logger
from openai import OpenAI
import json

class ClinicalPreProcessor:
    def __init__(self):
        logger.info("Initializing Clinical Pre-Processor...")
        self.client=OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    def extract_from_pdf(self,file_path:str)->str:
        if not os.path.exists(file_path):
            logger.error(f"File {file_path} not found.")
            return None

        text=""

        try:
            doc=fitz.open(file_path)
            for page in doc:
                text +=page.get_text()
            if not text.strip():
                logger.error(f"Digital text nhi mila.")
                return self.extract_from_scanned_pdf(file_path)
            return text

        except Exception as e:
            logger.error(f"PDF parhne mein galti {file_path}: {e}")
            return ""

    def extract_from_scanned_pdf(self, pdf_path: str) -> str:

        full_text = ""

        try:
            doc = fitz.open(pdf_path)
            for page in doc:
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                page_text = pytesseract.image_to_string(img)
                full_text += page_text + "\n"
            
            doc.close()
            return full_text

        except Exception as e:
            logger.error(f"Scanned PDF processing failed: {e}")
            return ""

    def extract_from_image(self, image_path: str) -> str:
        try:
            logger.info(f"OCR Processing Image: {image_path}")
            text = pytesseract.image_to_string(Image.open(image_path))
            return text
        except Exception as e:
            logger.error(f"Image OCR failed: {e}")
            return "" 

    async def process_document(self,file_path:str)->Dict:
        ext=os.path.splitext(file_path)[1].lower()
        raw_text=""

        if ext==".pdf":
            raw_text=self.extract_from_pdf(file_path)
        elif ext in [".jpg",".png",".jpeg"]:
            raw_text=self.extract_from_image(file_path)
        else:
            with open(file_path,"r",encoding="utf-8") as f:
                raw_text=f.read()
        if not raw_text.strip():
            logger.error("koi text nhi mila")
            return {"status":"failed","message":"koi text nhi mila"}

        result= await self.extract_entities(raw_text)
        result['raw_extracted_text'] = raw_text
        return result

    async def extract_entities(self,text:str)->Dict:

        prompt = f"""
        Analyze the following medical note and extract information in a structured JSON format.
        Note: {text[:5000]}

        Extract these fields:
        1. diagnosis_keywords: (Diseases/Symptoms for ICD-10 search)
        2. procedure_keywords: (Tests/Actions for CPT search)
        3. location: (Clinic, ER, or Inpatient?)
        4. laterality: (Left, Right, Bilateral, or None)
        5. complexity: (Low, Moderate, or High) 
        
        Respond ONLY with JSON.
        """

        try:
            response=self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role":"system","content":"You are a medical coding bot. You will extract information from a medical note and return it in a structured JSON format."},
                    {"role":"user","content":prompt}
                ],
                response_format={"type":"json_object"}
                
            )
            result=json.loads(response.choices[0].message.content)
            logger.success("AI ne medical entities nikaal li hain!")
            return result

        except Exception as e:
            logger.error(f"AI crashed: {e}")
            return {"status":"failed","message":"AI crashed"}

if __name__ == "__main__":
    import asyncio

    processor = ClinicalPreProcessor()
    asyncio.run(processor.process_document("data/notes/test_note.txt"))