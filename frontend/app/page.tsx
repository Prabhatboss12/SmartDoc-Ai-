'use client';

import { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';
import { DocumentArrowUpIcon, PaperAirplaneIcon, TrashIcon, EyeIcon, ArrowDownTrayIcon, DocumentTextIcon } from '@heroicons/react/24/outline';
import ReactMarkdown from 'react-markdown';
import toast from 'react-hot-toast';
import DarkModeToggle from './components/DarkModeToggle';

interface Document {
  name: string;
  uploadedAt: string;
}

interface Answer {
  text: string;
  sources: Array<{
    text: string;
    source: string;
    page?: number;
  }>;
}

export default function Home() {
  const [files, setFiles] = useState<File[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<string | null>(null);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
    },
    onDrop: (acceptedFiles) => {
      setFiles(acceptedFiles);
    },
  });

  const handleUpload = async () => {
    if (files.length === 0) {
      toast.error('Please select files to upload');
      return;
    }

    setIsLoading(true);
    const formData = new FormData();
    files.forEach((file) => {
      formData.append('files', file);
    });

    try {
      const response = await axios.post('http://localhost:8000/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      toast.success('Files uploaded successfully');
      // Add uploaded documents to the list
      const newDocs = files.map(file => ({
        name: file.name,
        uploadedAt: new Date().toLocaleString()
      }));
      setDocuments([...documents, ...newDocs]);
      setFiles([]);
    } catch (error) {
      toast.error('Error uploading files');
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAskQuestion = async () => {
    if (!question.trim()) {
      toast.error('Please enter a question');
      return;
    }

    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append('question', question);
      if (selectedDocument) {
        formData.append('document', selectedDocument);
      }

      const response = await axios.post('http://localhost:8000/ask', formData);
      setAnswer(response.data);
    } catch (error) {
      toast.error('Error getting answer');
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSummarize = async (docName: string) => {
    setIsLoading(true);
    try {
      const response = await axios.post('http://localhost:8000/summarize', {
        document: docName
      }, {
        headers: {
          'Content-Type': 'application/json'
        }
      });
      setAnswer(response.data);
      toast.success('Summary generated successfully');
    } catch (error: any) {
      console.error('Summarization error:', error);
      toast.error(error.response?.data?.detail || 'Error generating summary');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownload = () => {
    if (!answer) return;
    
    const content = `Question: ${question}\n\nAnswer: ${answer.text}\n\nSources:\n${
      answer.sources.map(s => `- ${s.source}: ${s.text}`).join('\n')
    }`;
    
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'qa-session.txt';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <main className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8 px-4 sm:px-6 lg:px-8 transition-colors">
      <DarkModeToggle />
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold text-center text-gray-900 dark:text-white mb-8">SmartDoc AI</h1>
        
        {/* Document Management Section */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Document Management</h2>
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer ${
              isDragActive ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20' : 'border-gray-300 dark:border-gray-600'
            }`}
          >
            <input {...getInputProps()} />
            <DocumentArrowUpIcon className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500" />
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">
              {isDragActive
                ? 'Drop the files here'
                : 'Drag and drop files here, or click to select files'}
            </p>
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              Supported formats: PDF, DOCX, TXT
            </p>
          </div>
          
          {files.length > 0 && (
            <div className="mt-4">
              <h3 className="text-sm font-medium text-gray-900 dark:text-white">Selected files:</h3>
              <ul className="mt-2 divide-y divide-gray-200 dark:divide-gray-700">
                {files.map((file) => (
                  <li key={file.name} className="py-2">
                    <p className="text-sm text-gray-600 dark:text-gray-300">{file.name}</p>
                  </li>
                ))}
              </ul>
              <button
                onClick={handleUpload}
                disabled={isLoading}
                className="mt-4 w-full bg-primary-600 text-white py-2 px-4 rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 dark:focus:ring-offset-gray-800"
              >
                {isLoading ? 'Uploading...' : 'Upload Files'}
              </button>
            </div>
          )}

          {/* Document History */}
          {documents.length > 0 && (
            <div className="mt-6">
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">Document History</h3>
              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                {documents.map((doc) => (
                  <div key={doc.name} className="flex items-center justify-between py-2">
                    <div className="flex items-center space-x-4">
                      <DocumentTextIcon className="h-5 w-5 text-gray-400 dark:text-gray-500" />
                      <div>
                        <p className="text-sm font-medium text-gray-900 dark:text-white">{doc.name}</p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">{doc.uploadedAt}</p>
                      </div>
                    </div>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleSummarize(doc.name)}
                        className="text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300"
                      >
                        Summarize
                      </button>
                      <button
                        onClick={() => setSelectedDocument(doc.name)}
                        className="text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300"
                      >
                        Select
                      </button>
                      <TrashIcon
                        className="h-5 w-5 text-red-500 cursor-pointer hover:text-red-600 dark:text-red-400 dark:hover:text-red-300"
                        onClick={() => {
                          setDocuments(documents.filter(d => d.name !== doc.name));
                          if (selectedDocument === doc.name) setSelectedDocument(null);
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Question Section */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Ask a Question</h2>
          <div className="flex gap-4">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Enter your question here..."
              className="flex-1 rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm focus:border-primary-500 focus:ring-primary-500 dark:focus:border-primary-400 dark:focus:ring-primary-400"
            />
            <button
              onClick={handleAskQuestion}
              disabled={isLoading}
              className="bg-primary-600 text-white p-2 rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 dark:focus:ring-offset-gray-800"
            >
              <PaperAirplaneIcon className="h-6 w-6" />
            </button>
          </div>

          {answer && (
            <div className="mt-6">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">Answer:</h3>
                <button
                  onClick={handleDownload}
                  className="flex items-center space-x-2 text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300"
                >
                  <ArrowDownTrayIcon className="h-5 w-5" />
                  <span>Download</span>
                </button>
              </div>
              <div className="prose dark:prose-invert max-w-none">
                <ReactMarkdown>{answer.text}</ReactMarkdown>
              </div>
              
              {answer.sources && answer.sources.length > 0 && (
                <div className="mt-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">Sources:</h4>
                  <ul className="space-y-2">
                    {answer.sources.map((source, index) => (
                      <li key={index} className="text-sm">
                        <span className="font-medium text-gray-900 dark:text-white">{source.source}</span>
                        {source.page && <span className="text-gray-500 dark:text-gray-400"> (Page {source.page})</span>}
                        <p className="text-gray-600 dark:text-gray-300 mt-1">{source.text}</p>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </main>
  );
} 