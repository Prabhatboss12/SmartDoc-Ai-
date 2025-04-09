import fitz  # PyMuPDF
from docx import Document
from typing import List, Dict, Any, Optional
import os
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

class DocumentProcessor:
    def __init__(self):
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.chroma_client = chromadb.Client(Settings(
            persist_directory="vector_store",
            anonymized_telemetry=False
        ))
        self.collection = self.chroma_client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"}
        )

    def process_document(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Process a document and return chunks with metadata
        """
        file_extension = os.path.splitext(file_path)[1].lower()
        text = ""
        
        if file_extension == '.pdf':
            text = self._read_pdf(file_path)
        elif file_extension == '.docx':
            text = self._read_docx(file_path)
        elif file_extension == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        
        chunks = self._chunk_text(text)
        return self._process_chunks(chunks, file_path)

    def _read_pdf(self, file_path: str) -> str:
        """Extract text from PDF file with page numbers"""
        doc = fitz.open(file_path)
        text_with_pages = []
        for page_num, page in enumerate(doc, 1):
            text = page.get_text()
            if text.strip():
                text_with_pages.append(f"[Page {page_num}] {text}")
        return "\n".join(text_with_pages)

    def _read_docx(self, file_path: str) -> str:
        """Extract text from DOCX file with paragraph numbers"""
        doc = Document(file_path)
        text_with_paragraphs = []
        for i, paragraph in enumerate(doc.paragraphs, 1):
            if paragraph.text.strip():
                text_with_paragraphs.append(f"[Paragraph {i}] {paragraph.text}")
        return "\n".join(text_with_paragraphs)

    def _chunk_text(self, text: str, chunk_size: int = 500) -> List[str]:
        """Split text into chunks"""
        # Simple sentence-based chunking
        sentences = text.split('.')
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            if current_size + len(sentence) > chunk_size and current_chunk:
                chunks.append('. '.join(current_chunk) + '.')
                current_chunk = []
                current_size = 0
                
            current_chunk.append(sentence)
            current_size += len(sentence)
            
        if current_chunk:
            chunks.append('. '.join(current_chunk) + '.')
            
        return chunks

    def _process_chunks(self, chunks: List[str], file_path: str) -> List[Dict[str, Any]]:
        """Process chunks and store in vector database"""
        file_name = os.path.basename(file_path)
        embeddings = self.embedding_model.encode(chunks)
        
        # Extract page numbers from chunks if present
        chunk_metadata = []
        for chunk in chunks:
            metadata = {"source": file_name}
            # Try to extract page number
            if "[Page " in chunk:
                try:
                    page_num = int(chunk[chunk.find("[Page ") + 6:chunk.find("]")])
                    metadata["page"] = page_num
                except:
                    pass
            chunk_metadata.append(metadata)
        
        # Store in ChromaDB
        self.collection.add(
            embeddings=embeddings.tolist(),
            documents=chunks,
            metadatas=chunk_metadata,
            ids=[f"{file_name}_{i}" for i in range(len(chunks))]
        )
        
        return [{
            "text": chunk,
            "source": file_name,
            "chunk_index": i,
            **metadata
        } for i, (chunk, metadata) in enumerate(zip(chunks, chunk_metadata))]

    def search_similar(self, query: str, k: int = 5, document_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for similar chunks to the query"""
        query_embedding = self.embedding_model.encode([query])[0]
        
        # Apply document filter if specified
        where = {"source": document_filter} if document_filter else None
        
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=k,
            where=where
        )
        
        return [{
            "text": doc,
            "source": meta["source"],
            "page": meta.get("page"),
            "score": score
        } for doc, meta, score in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        )]

    def get_document_content(self, filename: str) -> str:
        """Retrieve the full content of a document"""
        file_path = os.path.join("uploads", filename)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Document {filename} not found")
        
        file_extension = os.path.splitext(filename)[1].lower()
        if file_extension == '.pdf':
            return self._read_pdf(file_path)
        elif file_extension == '.docx':
            return self._read_docx(file_path)
        elif file_extension == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")

    def remove_document(self, filename: str):
        """Remove a document's chunks from the vector store"""
        try:
            # Get all IDs for the document
            results = self.collection.get(
                where={"source": filename}
            )
            if results["ids"]:
                self.collection.delete(
                    ids=results["ids"]
                )
        except Exception as e:
            print(f"Error removing document from vector store: {e}") 