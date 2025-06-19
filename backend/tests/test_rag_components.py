import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import sys
import tempfile
import os

# Add backend to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


class TestRAGSystemComponents:
    """Tests for RAG system components using mocks."""
    
    @pytest.fixture
    def mock_embeddings(self):
        """Mock embeddings for testing."""
        mock = Mock()
        mock.embed_documents.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        mock.embed_query.return_value = [0.1, 0.2, 0.3]
        return mock
    
    @pytest.fixture
    def mock_llm(self):
        """Mock LLM for testing."""
        mock = Mock()
        mock_response = Mock()
        mock_response.content = """
        SQL_QUERY: SELECT * FROM employees WHERE department = 'Engineering'
        EXPLANATION: This query filters employees by department
        CONFIDENCE: 0.9
        COMPLEXITY: simple
        """
        mock.ainvoke = AsyncMock(return_value=mock_response)
        return mock
    
    @pytest.fixture
    def mock_chroma_collection(self):
        """Mock Chroma collection for testing."""
        mock = Mock()
        mock.add = Mock()
        mock.query.return_value = {
            "documents": [["Sample schema document", "Sample query example"]],
            "metadatas": [[{"table": "employees"}, {"type": "example"}]]
        }
        mock.count.return_value = 0
        return mock
    
    @pytest.mark.asyncio
    @patch('rag.text_to_sql_rag.SentenceTransformerEmbeddings')
    @patch('rag.text_to_sql_rag.ChatOpenAI')
    @patch('rag.text_to_sql_rag.chromadb.PersistentClient')
    async def test_rag_system_initialization(self, mock_chromadb, mock_llm_class, mock_embeddings_class):
        """Test RAG system initialization with mocks."""
        # Setup mocks
        mock_embeddings_class.return_value = Mock()
        mock_llm_class.return_value = Mock()
        mock_client = Mock()
        mock_chromadb.return_value = mock_client
        mock_client.get_or_create_collection.return_value = Mock()
        
        # Import and test
        from rag.text_to_sql_rag import TextToSQLRAG
        
        rag_system = TextToSQLRAG()
        await rag_system.initialize()
        
        # Verify initialization
        assert rag_system.embeddings is not None
        assert rag_system.llm is not None
        assert rag_system.schema_collection is not None
        assert rag_system.query_examples_collection is not None
    
    @pytest.mark.asyncio
    @patch('rag.text_to_sql_rag.SentenceTransformerEmbeddings')
    @patch('rag.text_to_sql_rag.ChatOpenAI')
    @patch('rag.text_to_sql_rag.chromadb.PersistentClient')
    async def test_context_retrieval(self, mock_chromadb, mock_llm_class, mock_embeddings_class, 
                                   mock_embeddings, mock_chroma_collection):
        """Test context retrieval functionality."""
        # Setup mocks
        mock_embeddings_class.return_value = mock_embeddings
        mock_llm_class.return_value = Mock()
        mock_client = Mock()
        mock_chromadb.return_value = mock_client
        mock_client.get_or_create_collection.return_value = mock_chroma_collection
        
        from rag.text_to_sql_rag import TextToSQLRAG
        
        rag_system = TextToSQLRAG()
        await rag_system.initialize()
        
        # Test context retrieval
        schema_context, example_context = await rag_system.retrieve_relevant_context(
            "Show all employees", k=4
        )
        
        assert isinstance(schema_context, list)
        assert isinstance(example_context, list)
        # Should have called embedding and query methods
        mock_embeddings.embed_query.assert_called_once()
        assert mock_chroma_collection.query.call_count == 2  # Once for schema, once for examples
    
    @pytest.mark.asyncio
    @patch('rag.text_to_sql_rag.SentenceTransformerEmbeddings')
    @patch('rag.text_to_sql_rag.ChatOpenAI')
    @patch('rag.text_to_sql_rag.chromadb.PersistentClient')
    async def test_sql_generation_with_explanation(self, mock_chromadb, mock_llm_class, 
                                                 mock_embeddings_class, mock_llm, mock_chroma_collection):
        """Test SQL generation with explanation."""
        # Setup mocks
        mock_embeddings_class.return_value = Mock()
        mock_llm_class.return_value = mock_llm
        mock_client = Mock()
        mock_chromadb.return_value = mock_client
        mock_client.get_or_create_collection.return_value = mock_chroma_collection
        
        from rag.text_to_sql_rag import TextToSQLRAG
        
        rag_system = TextToSQLRAG()
        await rag_system.initialize()
        
        # Test SQL generation
        result = await rag_system.generate_sql_with_explanation(
            question="Show all employees",
            schema_context=["Table: employees with columns id, name, department"],
            example_context=["SELECT * FROM employees WHERE department = 'IT'"]
        )
        
        assert "sql_query" in result
        assert "explanation" in result
        assert "confidence_score" in result
        assert "complexity" in result
        
        # Should contain expected SQL
        assert "SELECT" in result["sql_query"]
        assert "employees" in result["sql_query"]
        
        # Should have called LLM
        mock_llm.ainvoke.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('rag.text_to_sql_rag.SentenceTransformerEmbeddings')
    @patch('rag.text_to_sql_rag.ChatOpenAI')
    @patch('rag.text_to_sql_rag.chromadb.PersistentClient')
    async def test_schema_indexing(self, mock_chromadb, mock_llm_class, mock_embeddings_class,
                                 mock_embeddings, mock_chroma_collection):
        """Test database schema indexing."""
        # Setup mocks
        mock_embeddings_class.return_value = mock_embeddings
        mock_llm_class.return_value = Mock()
        mock_client = Mock()
        mock_chromadb.return_value = mock_client
        mock_client.get_or_create_collection.return_value = mock_chroma_collection
        
        from rag.text_to_sql_rag import TextToSQLRAG
        
        rag_system = TextToSQLRAG()
        await rag_system.initialize()
        
        # Test schema indexing
        schema_info = {
            "employees": {
                "columns": [
                    {"name": "id", "type": "INTEGER", "nullable": False, "default": None},
                    {"name": "name", "type": "VARCHAR", "nullable": False, "default": None}
                ],
                "sample_data": [{"id": 1, "name": "John"}]
            }
        }
        
        await rag_system.index_database_schema(schema_info)
        
        # Should have called embedding and collection add methods
        mock_embeddings.embed_documents.assert_called()
        mock_chroma_collection.add.assert_called()
    
    def test_llm_response_parsing(self):
        """Test parsing of LLM responses."""
        from rag.text_to_sql_rag import TextToSQLRAG
        
        rag_system = TextToSQLRAG()
        
        # Test valid response
        response = """
        SQL_QUERY: SELECT * FROM employees WHERE department = 'Engineering'
        EXPLANATION: This query filters employees by the Engineering department
        CONFIDENCE: 0.9
        COMPLEXITY: simple
        """
        
        result = rag_system._parse_llm_response(response)
        
        assert result["sql_query"] == "SELECT * FROM employees WHERE department = 'Engineering'"
        assert "Engineering department" in result["explanation"]
        assert result["confidence_score"] == 0.9
        assert result["complexity"] == "simple"
    
    def test_llm_response_parsing_malformed(self):
        """Test parsing of malformed LLM responses."""
        from rag.text_to_sql_rag import TextToSQLRAG
        
        rag_system = TextToSQLRAG()
        
        # Test malformed response
        response = "This is not a properly formatted response"
        
        result = rag_system._parse_llm_response(response)
        
        # Should provide defaults
        assert "sql_query" in result
        assert "explanation" in result
        assert "confidence_score" in result
        assert result["confidence_score"] == 0.5  # Default value
    
    def test_table_document_creation(self):
        """Test creation of table documentation."""
        from rag.text_to_sql_rag import TextToSQLRAG
        
        rag_system = TextToSQLRAG()
        
        table_info = {
            "columns": [
                {"name": "id", "type": "INTEGER", "nullable": False, "default": None},
                {"name": "name", "type": "VARCHAR", "nullable": True, "default": "Unknown"}
            ],
            "sample_data": [{"id": 1, "name": "John"}]
        }
        
        doc = rag_system._create_table_document("employees", table_info)
        
        assert "Table: employees" in doc
        assert "id: INTEGER not null" in doc
        assert "name: VARCHAR nullable (default: Unknown)" in doc
        assert "Sample data:" in doc
        assert "John" in doc
    
    def test_column_document_creation(self):
        """Test creation of column documentation."""
        from rag.text_to_sql_rag import TextToSQLRAG
        
        rag_system = TextToSQLRAG()
        
        column_info = {"name": "employee_id", "type": "INTEGER"}
        
        doc = rag_system._create_column_document("employees", column_info)
        
        assert "Column employee_id in table employees" in doc
        assert "INTEGER data type" in doc
    
    def test_health_check(self):
        """Test RAG system health check."""
        from rag.text_to_sql_rag import TextToSQLRAG
        
        rag_system = TextToSQLRAG()
        
        # Before initialization
        assert rag_system.health_check() is False
        
        # Mock initialization
        rag_system.embeddings = Mock()
        rag_system.llm = Mock()
        rag_system.schema_collection = Mock()
        rag_system.query_examples_collection = Mock()
        
        # After initialization
        assert rag_system.health_check() is True
    
    @pytest.mark.asyncio
    async def test_error_handling_in_context_retrieval(self):
        """Test error handling in context retrieval."""
        from rag.text_to_sql_rag import TextToSQLRAG
        
        rag_system = TextToSQLRAG()
        
        # Test with uninitialized system
        schema_context, example_context = await rag_system.retrieve_relevant_context("test")
        
        # Should return empty lists on error
        assert schema_context == []
        assert example_context == []
    
    @pytest.mark.asyncio
    async def test_error_handling_in_sql_generation(self):
        """Test error handling in SQL generation."""
        from rag.text_to_sql_rag import TextToSQLRAG
        
        rag_system = TextToSQLRAG()
        
        # Test with uninitialized system
        result = await rag_system.generate_sql_with_explanation(
            question="test",
            schema_context=[],
            example_context=[]
        )
        
        # Should return error result
        assert result["confidence_score"] == 0.0
        assert result["complexity"] == "error"
        assert "Error generating SQL" in result["explanation"]


class TestRAGSystemIntegration:
    """Integration tests for RAG system components working together."""
    
    @pytest.mark.asyncio
    @patch('rag.text_to_sql_rag.SentenceTransformerEmbeddings')
    @patch('rag.text_to_sql_rag.ChatOpenAI')
    @patch('rag.text_to_sql_rag.chromadb.PersistentClient')
    async def test_end_to_end_query_processing(self, mock_chromadb, mock_llm_class, 
                                              mock_embeddings_class):
        """Test end-to-end query processing workflow."""
        # Setup comprehensive mocks
        mock_embeddings = Mock()
        mock_embeddings.embed_documents.return_value = [[0.1, 0.2, 0.3]]
        mock_embeddings.embed_query.return_value = [0.1, 0.2, 0.3]
        mock_embeddings_class.return_value = mock_embeddings
        
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = """
        SQL_QUERY: SELECT * FROM employees WHERE department = 'Engineering'
        EXPLANATION: This query retrieves all engineering employees
        CONFIDENCE: 0.95
        COMPLEXITY: simple
        """
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_llm_class.return_value = mock_llm
        
        mock_collection = Mock()
        mock_collection.add = Mock()
        mock_collection.count.return_value = 0
        mock_collection.query.return_value = {
            "documents": [["Schema info", "Example query"]],
            "metadatas": [[{}, {}]]
        }
        
        mock_client = Mock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_chromadb.return_value = mock_client
        
        from rag.text_to_sql_rag import TextToSQLRAG
        
        # Initialize system
        rag_system = TextToSQLRAG()
        await rag_system.initialize()
        
        # Index schema
        schema_info = {
            "employees": {
                "columns": [{"name": "id", "type": "INTEGER", "nullable": False, "default": None}],
                "sample_data": [{"id": 1}]
            }
        }
        await rag_system.index_database_schema(schema_info)
        
        # Retrieve context
        schema_context, example_context = await rag_system.retrieve_relevant_context(
            "Show engineering employees"
        )
        
        # Generate SQL
        result = await rag_system.generate_sql_with_explanation(
            question="Show engineering employees",
            schema_context=schema_context,
            example_context=example_context
        )
        
        # Verify complete workflow
        assert result["sql_query"] == "SELECT * FROM employees WHERE department = 'Engineering'"
        assert result["confidence_score"] == 0.95
        assert result["complexity"] == "simple"
        
        # Verify all mocks were called appropriately
        mock_embeddings.embed_documents.assert_called()
        mock_collection.add.assert_called()
        mock_embeddings.embed_query.assert_called()
        mock_collection.query.assert_called()
        mock_llm.ainvoke.assert_called()
    
    @pytest.mark.asyncio
    @patch.dict(os.environ, {'CHROMA_PERSIST_DIRECTORY': ''})
    async def test_rag_system_with_temporary_storage(self):
        """Test RAG system with temporary storage directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the environment to use temp directory
            with patch.dict(os.environ, {'CHROMA_PERSIST_DIRECTORY': temp_dir}):
                with patch('rag.text_to_sql_rag.SentenceTransformerEmbeddings') as mock_emb, \
                     patch('rag.text_to_sql_rag.ChatOpenAI') as mock_llm:
                    
                    mock_emb.return_value = Mock()
                    mock_llm.return_value = Mock()
                    
                    from rag.text_to_sql_rag import TextToSQLRAG
                    
                    rag_system = TextToSQLRAG()
                    
                    # Should use the temporary directory
                    assert temp_dir in rag_system.persist_directory