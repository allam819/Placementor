from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
import io
from pypdf import PdfReader
from .auth import verify_user, get_supabase_client
from supabase import Client
from app.ai.resume_analyzer import structure_job_description, analyze_resume, StructuredJD
import uuid

router = APIRouter()

class AnalyzeRequest(BaseModel):
    resume_id: str
    job_description_raw: str

import fitz
import pytesseract
from PIL import Image

def extract_text_from_pdf_content(content: bytes) -> str:
    # 1. Try standard text extraction
    reader = PdfReader(io.BytesIO(content))
    parsed_text = ""
    for page in reader.pages:
        text = page.extract_text()
        if text:
            parsed_text += text + "\n"
            
    parsed_text = parsed_text.strip()
    
    # 2. Fallback to OCR if empty (image-based PDF)
    if not parsed_text:
        # Rely on PATH or environment variables instead of hardcoding OS-specific locations
        tesseract_path = os.environ.get("TESSERACT_PATH")
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            
        try:
            doc = fitz.open(stream=content, filetype="pdf")
            for page in doc:
                pix = page.get_pixmap(dpi=300)
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                parsed_text += pytesseract.image_to_string(img) + "\n"
        except Exception as e:
            print(f"OCR Fallback failed: {e}")
            # If OCR fails, just return what we have (even if empty) to gracefully degrade
            pass
            
    return parsed_text.strip()

@router.post("/upload")
async def upload_resume(file: UploadFile = File(...), user = Depends(verify_user)):
    supabase: Client = get_supabase_client()
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
    content = await file.read()
    
    try:
        parsed_text = extract_text_from_pdf_content(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse PDF: {str(e)}")
        
    file_id = str(uuid.uuid4())
    file_path = f"{user.user.id}/{file_id}.pdf"
    
    try:
        supabase.storage.from_("resumes").upload(file_path, content, {"content-type": "application/pdf"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload to storage: {str(e)}")
        
    data = {
        "user_id": user.user.id,
        "file_path": file_path,
        "file_name": file.filename,
        "parsed_content": parsed_text
    }
    
    try:
        res = supabase.table("resumes").insert(data).execute()
        return res.data[0]
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Database error (Did you run the SQL migration?): {str(e)}")

@router.post("/parse-jd-pdf")
async def parse_jd_pdf(file: UploadFile = File(...), user = Depends(verify_user)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
    content = await file.read()
    
    try:
        parsed_text = extract_text_from_pdf_content(content)
        return {"text": parsed_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse JD PDF: {str(e)}")

@router.post("/analyze")
async def perform_analysis(req: AnalyzeRequest, user = Depends(verify_user)):
    supabase: Client = get_supabase_client()
    
    # 1. Fetch the resume
    resume_res = supabase.table("resumes").select("parsed_content").eq("id", req.resume_id).eq("user_id", user.user.id).execute()
    if not resume_res.data:
        raise HTTPException(status_code=404, detail="Resume not found")
    parsed_resume = resume_res.data[0]["parsed_content"]
    
    # 2. Structure JD
    try:
        structured_jd = structure_job_description(req.job_description_raw)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to structure JD: {str(e)}")
        
    # 3. Save JD
    jd_data = {
        "user_id": user.user.id,
        "title": structured_jd.title,
        "company": structured_jd.company,
        "raw_text": req.job_description_raw,
        "structured_requirements": structured_jd.model_dump()
    }
    jd_res = supabase.table("job_descriptions").insert(jd_data).execute()
    jd_id = jd_res.data[0]["id"]
    
    # 4. Run Analysis
    try:
        analysis = analyze_resume(parsed_resume, structured_jd)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to analyze resume: {str(e)}")
        
    # 5. Process Semantic Search for Preparation Recommendations
    for rec in analysis.preparation_recommendations:
        if rec.gap_type == "MISSING_SKILL":
            from app.ai.embeddings import generate_embedding
            try:
                query_embedding = generate_embedding(f"{rec.topic} {rec.reason}")
                match_res = supabase.rpc("match_learning_activities", {
                    "query_embedding": query_embedding,
                    "match_threshold": 0.6,
                    "match_count": 3,
                    "p_user_id": user.user.id
                }).execute()
                matches = match_res.data or []
                rec.related_learning_ids = [m["id"] for m in matches]
                if rec.related_learning_ids:
                    rec.recommendation_type = "REVISE_EXISTING"
                else:
                    rec.recommendation_type = "LEARN_NEW"
            except Exception as e:
                import logging
                logging.error(f"Semantic search failed for prep recommendation: {e}")
                rec.recommendation_type = "LEARN_NEW"

    # 6. Save Analysis (Storing structured recommendations directly inside recommendations to avoid schema issues)
    analysis_data = {
        "user_id": user.user.id,
        "resume_id": req.resume_id,
        "job_description_id": jd_id,
        "overall_score": analysis.overall_score,
        "gaps": analysis.gaps,
        "recommendations": [r.model_dump() for r in analysis.preparation_recommendations] if hasattr(analysis, "preparation_recommendations") and analysis.preparation_recommendations else analysis.recommendations,
    }
    analysis_res = supabase.table("resume_analyses").insert(analysis_data).execute()
    
    return {
        "analysis": analysis_res.data[0],
        "job_description": jd_res.data[0]
    }
