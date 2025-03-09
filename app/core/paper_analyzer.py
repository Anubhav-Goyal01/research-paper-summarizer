import asyncio
import logging
import os
import tempfile
from typing import Dict, List, Any, Optional

from app.clients.groq_ai import GroqAIClient
from app.prompts.templates import PromptTemplates
from app.utils.pdf_processor import PDFProcessor

class PaperAnalyzer:
    """
    Core service for analyzing research papers using parallel LLM calls.
    """
    
    def __init__(self):
        self.llm_client = GroqAIClient()
        self.prompt_templates = PromptTemplates()
    
    async def save_upload_file(self, file_content: bytes) -> str:
        """
        Save uploaded file content to a temporary location.
        
        Args:
            file_content: Raw bytes of the uploaded file
            
        Returns:
            Path to the saved file
        """
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_path = temp_file.name
                temp_file.write(file_content)
                
            return temp_path
        except Exception as e:
            logging.error(f"Error saving uploaded file: {str(e)}")
            raise
    
    async def analyze_paper(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze a research paper by extracting text and making parallel LLM calls.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary containing the combined results of all analyses
        """
        try:
            paper_text = PDFProcessor.extract_text_from_pdf(file_path)
            title, authors = PDFProcessor.get_paper_metadata(file_path)
            
            if len(paper_text) > 15000:
                paper_text = paper_text[:15000] 
                
            shared_context: Dict[str, Any] = {}
            
            tasks = []
            
            # First call - identify key concepts
            tasks.append(self._analyze_key_concepts(paper_text, shared_context))
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            if isinstance(results[0], Dict) and results[0]:
                shared_context["key_concepts"] = results[0]
            
            # Second call - identify problem statement
            problem_task = self._analyze_problem_statement(paper_text, shared_context)
            problem_result = await problem_task
            
            if isinstance(problem_result, Dict) and problem_result:
                shared_context["problem_statement"] = problem_result
            
            # Third call - full explanation
            explanation_task = self._analyze_full_explanation(paper_text, shared_context)
            explanation_result = await explanation_task
            
            if isinstance(explanation_result, Dict) and explanation_result:
                shared_context["full_explanation"] = explanation_result
            
            # Fourth call - generate pseudo code
            pseudocode_task = self._generate_pseudo_code(paper_text, shared_context)
            pseudocode_result = await pseudocode_task
            
            final_result = {
                "metadata": {
                    "title": title or "Unknown Title",
                    "authors": authors or "Unknown Authors",
                },
                "key_concepts": shared_context.get("key_concepts", {}),
                "problem_statement": shared_context.get("problem_statement", {}),
                "full_explanation": shared_context.get("full_explanation", {}),
                "pseudo_code": pseudocode_result or {}
            }
            
            return final_result
        except Exception as e:
            logging.error(f"Error analyzing paper: {str(e)}")
            raise
        finally:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                logging.error(f"Error cleaning up temporary file: {str(e)}")
    
    async def _analyze_key_concepts(self, paper_text: str, shared_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make LLM call to identify key concepts in the paper.
        
        Args:
            paper_text: The text content of the paper
            shared_context: Shared context from other calls (empty for first call)
            
        Returns:
            Dictionary containing key concepts analysis
        """
        messages = PromptTemplates.key_concepts_prompt(paper_text)
        return await self.llm_client.call_llm(messages)
    
    async def _analyze_problem_statement(self, paper_text: str, shared_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make LLM call to identify the problem statement and existing approaches.
        
        Args:
            paper_text: The text content of the paper
            shared_context: Shared context from other calls
            
        Returns:
            Dictionary containing problem statement analysis
        """
        messages = PromptTemplates.problem_statement_prompt(paper_text, shared_context)
        return await self.llm_client.call_llm(messages)
    
    async def _analyze_full_explanation(self, paper_text: str, shared_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make LLM call to get a comprehensive explanation of the paper.
        
        Args:
            paper_text: The text content of the paper
            shared_context: Shared context from other calls
            
        Returns:
            Dictionary containing full explanation
        """
        messages = PromptTemplates.full_explanation_prompt(paper_text, shared_context)
        return await self.llm_client.call_llm(messages)
    
    async def _generate_pseudo_code(self, paper_text: str, shared_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make LLM call to generate pseudo-code implementation based on the paper.
        
        Args:
            paper_text: The text content of the paper
            shared_context: Shared context from other calls
            
        Returns:
            Dictionary containing pseudo-code implementation
        """
        messages = PromptTemplates.pseudo_code_prompt(paper_text, shared_context)
        return await self.llm_client.call_llm(messages)
