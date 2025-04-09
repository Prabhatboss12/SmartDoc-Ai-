from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from typing import List, Optional, Dict
from dotenv import load_dotenv
from document_processor import DocumentProcessor
from llm_service import LLMService
import json
from datetime import datetime

# Load environment variables
load_dotenv()

app = FastAPI(
    title="SmartDoc AI",
    description="API for document processing and question answering",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create necessary directories
os.makedirs("uploads", exist_ok=True)
os.makedirs("vector_store", exist_ok=True)
os.makedirs("document_metadata", exist_ok=True)

# Initialize services
document_processor = DocumentProcessor()
llm_service = LLMService()

def save_document_metadata(filename: str):
    metadata_file = os.path.join("document_metadata", "documents.json")
    try:
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        else:
            metadata = []
        
        metadata.append({
            "name": filename,
            "uploadedAt": datetime.now().isoformat(),
            "size": os.path.getsize(os.path.join("uploads", filename))
        })
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)
    except Exception as e:
        print(f"Error saving metadata: {e}")

@app.get("/")
async def root():
    return {"message": "SmartDoc AI API is running"}

@app.get("/documents")
async def list_documents():
    """
    List all uploaded documents with their metadata
    """
    try:
        metadata_file = os.path.join("document_metadata", "documents.json")
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                return JSONResponse(status_code=200, content=json.load(f))
        return JSONResponse(status_code=200, content=[])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    """
    Upload multiple documents for processing
    """
    try:
        saved_files = []
        for file in files:
            # Validate file type
            if not file.filename.endswith(('.pdf', '.docx', '.txt')):
                raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.filename}")
            
            # Save file
            file_path = os.path.join("uploads", file.filename)
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            # Process document
            document_processor.process_document(file_path)
            saved_files.append(file.filename)
            
            # Save metadata
            save_document_metadata(file.filename)
        
        return JSONResponse(
            status_code=200,
            content={"message": "Files uploaded and processed successfully", "files": saved_files}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask")
async def ask_question(question: str = Form(...), document: Optional[str] = Form(None)):
    """
    Ask a question about the uploaded documents
    """
    try:
        # Search for relevant chunks
        context_chunks = document_processor.search_similar(question, document_filter=document)
        
        # Generate answer
        answer = llm_service.generate_answer(question, context_chunks)
        
        # Format response with sources
        response = llm_service.format_answer_with_sources(answer, context_chunks)
        
        return JSONResponse(
            status_code=200,
            content=response
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/summarize")
async def summarize_document(payload: Dict[str, str] = Body(...)):
    """
    Generate a summary of the specified document
    """
    try:
        document = payload.get("document")
        if not document:
            raise HTTPException(status_code=400, detail="Document name is required")
            
        # Get document content
        content = document_processor.get_document_content(document)
        
        # Generate summary
        summary = llm_service.generate_summary(content)
        
        return JSONResponse(
            status_code=200,
            content={
                "text": summary,
                "sources": [{
                    "source": document,
                    "text": "Full document summary"
                }]
            }
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/documents/{filename}")
async def delete_document(filename: str):
    """
    Delete a document and its associated data
    """
    try:
        # Delete file
        file_path = os.path.join("uploads", filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Update metadata
        metadata_file = os.path.join("document_metadata", "documents.json")
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            metadata = [doc for doc in metadata if doc["name"] != filename]
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f)
        
        # Remove from vector store
        document_processor.remove_document(filename)
        
        return JSONResponse(
            status_code=200,
            content={"message": f"Document {filename} deleted successfully"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 