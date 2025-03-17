import json
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class KnowledgeGraphExtractor:
    """
    Extracts knowledge graph data from research paper analysis results.
    Creates a graph representation with concepts as nodes and their relationships as edges.
    """
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        
    async def extract_graph_data(self, paper_text: str, analysis_result: Dict[str, Any]) -> Dict:
        """
        Extract nodes and edges for a knowledge graph from paper text and existing analysis.
        
        Args:
            paper_text: The full text of the research paper
            analysis_result: The existing analysis results containing concepts, problem statement, etc.
            
        Returns:
            A dictionary containing nodes and edges for the knowledge graph
        """
        # Create a specialized prompt for the LLM
        prompt = self._create_graph_extraction_prompt(paper_text, analysis_result)
        
        try:
            # Call the LLM to extract graph structure
            messages = [
                {"role": "system", "content": "You are an expert at extracting conceptual relationships from research papers. Output valid JSON only."},
                {"role": "user", "content": prompt}
            ]
            response = await self.llm_client.call_llm(messages)
            
            # Process and validate the response
            graph_data = self._process_graph_response(response)
            
            # Add graph metadata
            graph_data["metadata"] = {
                "paper_title": analysis_result.get("title", "Untitled Paper"),
                "node_count": len(graph_data.get("nodes", [])),
                "edge_count": len(graph_data.get("edges", []))
            }
            
            return graph_data
            
        except Exception as e:
            logger.error(f"Error extracting knowledge graph: {str(e)}")
            # Return empty graph structure on error
            return {"nodes": [], "edges": [], "metadata": {"error": str(e)}}
    
    def _create_graph_extraction_prompt(self, paper_text: str, analysis_result: Dict[str, Any]) -> str:
        """Create a prompt for extracting knowledge graph data"""
        # Extract useful information from analysis result
        concepts_data = analysis_result.get("concepts", {})
        # Ensure key_concepts items are strings
        raw_key_concepts = concepts_data.get("key_concepts", [])
        if isinstance(raw_key_concepts, list):
            key_concepts = [str(k) for k in raw_key_concepts if k is not None]
        else:
            # Handle case where key_concepts might not be a list
            key_concepts = []
            
        # Ensure technologies items are strings
        raw_technologies = concepts_data.get("technologies", [])
        if isinstance(raw_technologies, list):
            technologies = [str(t) for t in raw_technologies if t is not None]
        else:
            technologies = []
        
        problem_data = analysis_result.get("problem", {})
        problem_statement = str(problem_data.get("problem_statement", ""))
        
        # Ensure approaches items are strings
        raw_approaches = problem_data.get("alternative_approaches", [])
        if isinstance(raw_approaches, list):
            approaches = [str(a) for a in raw_approaches if a is not None]
        else:
            approaches = []
        
        explanation = analysis_result.get("explanation", {})
        methodology = str(explanation.get("methodology", ""))
        
        prompt = f"""
        Extract a knowledge graph from this research paper. 
        
        I'll provide you with the paper text and concepts we've already identified. Create a graph with:
        1. Nodes representing key concepts, methods, datasets, and results
        2. Edges representing relationships between these nodes
        
        ALREADY IDENTIFIED INFORMATION:
        - Key concepts: {", ".join(key_concepts)}
        - Technologies: {", ".join(technologies)}
        - Problem statement: {problem_statement[:200]}...
        - Alternative approaches: {", ".join(approaches[:3])}
        
        INSTRUCTIONS:
        1. Create 15-25 nodes representing the most important concepts
        2. Create 20-40 edges showing relationships between nodes
        3. Use the following node types: "concept", "method", "dataset", "result", "entity"
        4. Use the following relationship types: "uses", "improves", "contradicts", "part_of", "results_in", "depends_on", "applied_to", "evaluated_on"
        
        OUTPUT FORMAT:
        Return a JSON object with this exact structure:
        {{
          "nodes": [
            {{"id": "unique_id", "label": "Concept Name", "type": "concept|method|dataset|result|entity", "description": "Brief description"}},
            ...
          ],
          "edges": [
            {{"source": "source_node_id", "target": "target_node_id", "label": "relationship type", "description": "explanation of relationship"}}
            ...
          ]
        }}
        
        Paper text excerpt:
        {paper_text[:5000]}
        """
        
        return prompt
    
    def _process_graph_response(self, response) -> Dict:
        """Process and validate the LLM response"""
        try:
            # Check if response is already a dictionary (parsed JSON)
            if isinstance(response, dict):
                graph_data = response
            else:
                # Extract JSON from response string (handle cases where LLM might add extra text)
                json_content = response
                
                # If response contains multiple lines, try to extract the JSON part
                if isinstance(response, str):
                    if "```json" in response:
                        json_content = response.split("```json")[1].split("```")[0].strip()
                    elif "```" in response:
                        json_content = response.split("```")[1].strip()
                    
                    graph_data = json.loads(json_content)
                else:
                    # If response is neither dict nor str, raise error
                    raise TypeError(f"Unexpected response type: {type(response)}")
            
            # Validate required keys
            if not all(k in graph_data for k in ["nodes", "edges"]):
                raise ValueError("Missing required keys in graph data")
                
            # Ensure all nodes have required fields
            for node in graph_data["nodes"]:
                if not all(k in node for k in ["id", "label", "type"]):
                    node["id"] = node.get("id", f"node_{len(graph_data['nodes'])}")
                    node["label"] = node.get("label", "Unnamed Concept")
                    node["type"] = node.get("type", "concept")
                if "description" not in node:
                    node["description"] = f"A {node['type']} in the paper"
            
            # Validate node references in edges
            node_ids = {node["id"] for node in graph_data["nodes"]}
            valid_edges = []
            
            for edge in graph_data["edges"]:
                if not all(k in edge for k in ["source", "target", "label"]):
                    continue
                
                if edge["source"] in node_ids and edge["target"] in node_ids:
                    if "description" not in edge:
                        edge["description"] = f"A {edge['label']} relationship"
                    valid_edges.append(edge)
            
            graph_data["edges"] = valid_edges
            
            return graph_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {str(e)}")
            return {"nodes": [], "edges": []}
        except Exception as e:
            logger.error(f"Error processing graph response: {str(e)}")
            return {"nodes": [], "edges": []}
