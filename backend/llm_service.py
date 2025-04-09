from typing import List, Dict
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class LLMService:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4"  # Can be changed to other models

    def generate_answer(self, query: str, context_chunks: List[Dict]) -> str:
        """
        Generate an answer based on the query and relevant context chunks
        """
        # Prepare context with page numbers
        context = "\n\n".join([
            f"Source: {chunk['source']}" + 
            (f" (Page {chunk['page']})" if 'page' in chunk else "") +
            f"\nContent: {chunk['text']}"
            for chunk in context_chunks
        ])

        # Prepare the prompt
        prompt = f"""You are a helpful AI assistant. Answer the question based on the following context.
        If the answer cannot be found in the context, say "I don't have enough information to answer that question."
        Include specific page numbers or paragraph numbers in your answer when available.

        Context:
        {context}

        Question: {query}

        Answer:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant that answers questions based on provided context."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error generating answer: {str(e)}"

    def generate_summary(self, content: str) -> str:
        """
        Generate a summary of the document content
        """
        prompt = f"""Please provide a comprehensive summary of the following document.
        Include key points and main ideas. If the document has sections, summarize each major section.
        Present the summary in a clear, structured format with bullet points for main ideas.

        Document Content:
        {content}

        Summary:"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant that creates clear and concise document summaries."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Error generating summary: {str(e)}"

    def format_answer_with_sources(self, answer: str, context_chunks: List[Dict]) -> Dict:
        """
        Format the answer with source references
        """
        sources = []
        seen_sources = set()
        
        for chunk in context_chunks:
            source_key = f"{chunk['source']}_{chunk.get('page', '')}"
            if source_key not in seen_sources:
                source_info = {
                    "source": chunk['source'],
                    "text": chunk['text']
                }
                if 'page' in chunk:
                    source_info['page'] = chunk['page']
                sources.append(source_info)
                seen_sources.add(source_key)
        
        return {
            "text": answer,
            "sources": sources
        } 