# Document Q&A Application

A full-stack web application that allows users to upload documents, process them, and ask questions about their content using natural language.

## Features

- Document upload (PDF, DOCX, TXT)
- Document processing and vector storage
- Natural language question answering
- Context-aware responses with source references
- Modern UI with TailwindCSS

## Tech Stack

### Frontend
- Next.js
- React
- TailwindCSS
- TypeScript

### Backend
- FastAPI
- Python
- FAISS/ChromaDB for vector storage
- SentenceTransformers for embeddings
- OpenAI API for LLM

## Project Structure

```
.
├── frontend/           # Next.js frontend application
├── backend/           # FastAPI backend application
├── README.md          # Project documentation
└── .gitignore         # Git ignore file
```

## Setup Instructions

### Backend Setup
1. Navigate to the backend directory
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment
4. Install dependencies: `pip install -r requirements.txt`
5. Start the server: `uvicorn main:app --reload`

### Frontend Setup
1. Navigate to the frontend directory
2. Install dependencies: `npm install`
3. Start the development server: `npm run dev`

## Environment Variables

Create a `.env` file in the backend directory with:
```
OPENAI_API_KEY=your_api_key
```

## License

MIT 