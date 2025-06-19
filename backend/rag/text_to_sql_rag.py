import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
import chromadb
import os
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class TextToSQLRAG:
    def __init__(self):
        self.embeddings = None
        self.vectorstore = None
        self.llm = None
        self.text_splitter = None
        self.schema_collection = None
        self.query_examples_collection = None
        self.persist_directory = os.getenv("CHROMA_PERSIST_DIRECTORY", "./chroma_db")
        
    async def initialize(self):
        self.embeddings = SentenceTransformerEmbeddings(
            model_name=os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        )
        
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0,
            max_tokens=2000
        )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", " ", ""]
        )
        
        client = chromadb.PersistentClient(path=self.persist_directory)
        
        self.schema_collection = client.get_or_create_collection(
            name="database_schema",
            metadata={"hnsw:space": "cosine"}
        )
        
        self.query_examples_collection = client.get_or_create_collection(
            name="query_examples",
            metadata={"hnsw:space": "cosine"}
        )
        
        await self._initialize_example_queries()
        logger.info("TextToSQL RAG system initialized successfully")
    
    async def _initialize_example_queries(self):
        example_queries = [
            {
                "question": "Show all employees in the engineering department",
                "sql": "SELECT * FROM employees WHERE department = 'Engineering'",
                "explanation": "This query filters employees by department using a WHERE clause",
                "complexity": "simple"
            },
            {
                "question": "What is the average salary by department?",
                "sql": "SELECT department, AVG(salary) as avg_salary FROM employees GROUP BY department",
                "explanation": "This query calculates average salary using GROUP BY and AVG aggregate function",
                "complexity": "medium"
            },
            {
                "question": "Show top 5 highest paid employees with their department info",
                "sql": """SELECT e.first_name, e.last_name, e.salary, d.name as department_name, d.location
                         FROM employees e 
                         JOIN departments d ON e.department = d.name 
                         ORDER BY e.salary DESC 
                         LIMIT 5""",
                "explanation": "This query uses JOIN to combine employee and department data, with ORDER BY and LIMIT",
                "complexity": "complex"
            },
            {
                "question": "Which projects have budget exceeding 100000?",
                "sql": "SELECT name, budget, status FROM projects WHERE budget > 100000",
                "explanation": "Simple comparison query filtering projects by budget threshold",
                "complexity": "simple"
            },
            {
                "question": "Show sales performance by region for this year",
                "sql": """SELECT region, COUNT(*) as total_sales, SUM(sale_amount) as total_revenue, AVG(sale_amount) as avg_sale
                         FROM sales 
                         WHERE EXTRACT(YEAR FROM sale_date) = EXTRACT(YEAR FROM CURRENT_DATE)
                         GROUP BY region 
                         ORDER BY total_revenue DESC""",
                "explanation": "Complex aggregation query with date filtering, multiple aggregate functions, and grouping",
                "complexity": "complex"
            },
            {
                "question": "Find employees working on more than one active project",
                "sql": """SELECT e.first_name, e.last_name, COUNT(ep.project_id) as project_count
                         FROM employees e
                         JOIN employee_projects ep ON e.id = ep.employee_id
                         JOIN projects p ON ep.project_id = p.id
                         WHERE p.status = 'active'
                         GROUP BY e.id, e.first_name, e.last_name
                         HAVING COUNT(ep.project_id) > 1""",
                "explanation": "Complex query with multiple JOINs, GROUP BY, and HAVING clause",
                "complexity": "complex"
            }
        ]
        
        try:
            existing_count = self.query_examples_collection.count()
            if existing_count == 0:
                documents = []
                metadatas = []
                ids = []
                
                for i, example in enumerate(example_queries):
                    doc_text = f"Question: {example['question']}\nSQL: {example['sql']}\nExplanation: {example['explanation']}"
                    documents.append(doc_text)
                    metadatas.append({
                        "question": example['question'],
                        "sql": example['sql'],
                        "explanation": example['explanation'],
                        "complexity": example['complexity']
                    })
                    ids.append(f"example_{i}")
                
                embeddings = self.embeddings.embed_documents(documents)
                
                self.query_examples_collection.add(
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                
                logger.info(f"Added {len(example_queries)} example queries to vector store")
        
        except Exception as e:
            logger.error(f"Failed to initialize example queries: {str(e)}")
    
    async def index_database_schema(self, schema_info: Dict[str, Any]):
        try:
            documents = []
            metadatas = []
            ids = []
            
            for table_name, table_info in schema_info.items():
                table_doc = self._create_table_document(table_name, table_info)
                
                documents.append(table_doc)
                metadatas.append({
                    "table_name": table_name,
                    "column_count": len(table_info.get("columns", [])),
                    "has_sample_data": len(table_info.get("sample_data", [])) > 0
                })
                ids.append(f"table_{table_name}")
                
                for column_info in table_info.get("columns", []):
                    column_doc = self._create_column_document(table_name, column_info)
                    documents.append(column_doc)
                    metadatas.append({
                        "table_name": table_name,
                        "column_name": column_info["name"],
                        "data_type": column_info["type"]
                    })
                    ids.append(f"column_{table_name}_{column_info['name']}")
            
            if documents:
                embeddings = self.embeddings.embed_documents(documents)
                
                self.schema_collection.add(
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                
                logger.info(f"Indexed schema for {len(schema_info)} tables")
        
        except Exception as e:
            logger.error(f"Failed to index database schema: {str(e)}")
    
    def _create_table_document(self, table_name: str, table_info: Dict[str, Any]) -> str:
        doc_parts = [f"Table: {table_name}"]
        
        columns = table_info.get("columns", [])
        if columns:
            doc_parts.append("Columns:")
            for col in columns:
                nullable_str = "nullable" if col.get("nullable") else "not null"
                default_str = f" (default: {col.get('default')})" if col.get("default") else ""
                doc_parts.append(f"  - {col['name']}: {col['type']} {nullable_str}{default_str}")
        
        sample_data = table_info.get("sample_data", [])
        if sample_data:
            doc_parts.append("Sample data:")
            for i, row in enumerate(sample_data[:2]):
                doc_parts.append(f"  Row {i+1}: {json.dumps(row, default=str)}")
        
        return "\n".join(doc_parts)
    
    def _create_column_document(self, table_name: str, column_info: Dict[str, Any]) -> str:
        return f"Column {column_info['name']} in table {table_name}: {column_info['type']} data type"
    
    async def retrieve_relevant_context(self, question: str, k: int = 5) -> Tuple[List[str], List[str]]:
        try:
            query_embedding = self.embeddings.embed_query(question)
            
            schema_results = self.schema_collection.query(
                query_embeddings=[query_embedding],
                n_results=k//2 + 1
            )
            
            example_results = self.query_examples_collection.query(
                query_embeddings=[query_embedding],
                n_results=k//2 + 1
            )
            
            schema_context = schema_results["documents"][0] if schema_results["documents"] else []
            example_context = example_results["documents"][0] if example_results["documents"] else []
            
            return schema_context, example_context
        
        except Exception as e:
            logger.error(f"Failed to retrieve relevant context: {str(e)}")
            return [], []
    
    async def generate_sql_with_explanation(self, question: str, schema_context: List[str], 
                                          example_context: List[str]) -> Dict[str, Any]:
        try:
            prompt_template = PromptTemplate(
                input_variables=["question", "schema_context", "example_context"],
                template="""
You are an expert SQL query generator. Given a natural language question, generate a precise SQL query along with a detailed explanation.

Database Schema Context:
{schema_context}

Example Queries:
{example_context}

Question: {question}

Requirements:
1. Generate a syntactically correct SQL query
2. Use proper table and column names from the schema
3. Include appropriate WHERE clauses, JOINs, and aggregations as needed
4. Optimize for performance when possible
5. Provide a clear explanation of the query logic

Response format:
SQL_QUERY: [Your SQL query here]
EXPLANATION: [Detailed explanation of the query logic]
CONFIDENCE: [Confidence score from 0.0 to 1.0]
COMPLEXITY: [simple/medium/complex]
"""
            )
            
            formatted_schema = "\n".join(schema_context)
            formatted_examples = "\n".join(example_context)
            
            chain = prompt_template | self.llm
            
            response = await chain.ainvoke({
                "question": question,
                "schema_context": formatted_schema,
                "example_context": formatted_examples
            })
            
            return self._parse_llm_response(response.content)
        
        except Exception as e:
            logger.error(f"Failed to generate SQL: {str(e)}")
            return {
                "sql_query": "SELECT 1",
                "explanation": f"Error generating SQL: {str(e)}",
                "confidence_score": 0.0,
                "complexity": "error"
            }
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        try:
            lines = response.strip().split('\n')
            result = {
                "sql_query": "",
                "explanation": "",
                "confidence_score": 0.5,
                "complexity": "medium"
            }
            
            current_section = None
            content_lines = []
            
            for line in lines:
                line = line.strip()
                if line.startswith("SQL_QUERY:"):
                    if current_section:
                        result[current_section] = "\n".join(content_lines).strip()
                    current_section = "sql_query"
                    content_lines = [line[10:].strip()]
                elif line.startswith("EXPLANATION:"):
                    if current_section:
                        result[current_section] = "\n".join(content_lines).strip()
                    current_section = "explanation"
                    content_lines = [line[12:].strip()]
                elif line.startswith("CONFIDENCE:"):
                    if current_section:
                        result[current_section] = "\n".join(content_lines).strip()
                    try:
                        result["confidence_score"] = float(line[11:].strip())
                    except ValueError:
                        result["confidence_score"] = 0.5
                    current_section = None
                    content_lines = []
                elif line.startswith("COMPLEXITY:"):
                    complexity = line[11:].strip().lower()
                    if complexity in ["simple", "medium", "complex"]:
                        result["complexity"] = complexity
                    current_section = None
                    content_lines = []
                elif current_section and line:
                    content_lines.append(line)
            
            if current_section and content_lines:
                result[current_section] = "\n".join(content_lines).strip()
            
            if not result["sql_query"]:
                result["sql_query"] = "SELECT 1"
                result["explanation"] = "Failed to parse SQL query from response"
            
            return result
        
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {str(e)}")
            return {
                "sql_query": "SELECT 1",
                "explanation": f"Error parsing response: {str(e)}",
                "confidence_score": 0.0,
                "complexity": "error"
            }
    
    def health_check(self) -> bool:
        try:
            return (self.embeddings is not None and 
                   self.llm is not None and 
                   self.schema_collection is not None and 
                   self.query_examples_collection is not None)
        except Exception:
            return False