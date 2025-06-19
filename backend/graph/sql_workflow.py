import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import time
import json
from langgraph.graph import StateGraph, END
from pydantic import BaseModel
from typing_extensions import TypedDict

from database.connection import DatabaseManager
from rag.text_to_sql_rag import TextToSQLRAG
from utils.sql_validator import SQLValidator
from utils.query_optimizer import QueryOptimizer

logger = logging.getLogger(__name__)

class WorkflowState(TypedDict):
    question: str
    database_context: Optional[str]
    include_explanation: bool
    max_results: int
    
    schema_context: List[str]
    example_context: List[str]
    
    sql_query: str
    explanation: str
    confidence_score: float
    complexity: str
    
    validation_passed: bool
    validation_errors: List[str]
    
    optimized_query: str
    optimization_applied: bool
    
    results: List[Dict[str, Any]]
    execution_time: float
    
    error_message: Optional[str]
    retry_count: int
    max_retries: int

class SQLWorkflowGraph:
    def __init__(self, rag_system: TextToSQLRAG, db_manager: DatabaseManager):
        self.rag_system = rag_system
        self.db_manager = db_manager
        self.sql_validator = SQLValidator()
        self.query_optimizer = QueryOptimizer()
        self.workflow = self._build_workflow()
        
    def _build_workflow(self):
        workflow = StateGraph(WorkflowState)
        
        workflow.add_node("retrieve_context", self._retrieve_context)
        workflow.add_node("generate_sql", self._generate_sql)
        workflow.add_node("validate_sql", self._validate_sql)
        workflow.add_node("optimize_query", self._optimize_query)
        workflow.add_node("execute_query", self._execute_query)
        workflow.add_node("handle_error", self._handle_error)
        workflow.add_node("finalize_result", self._finalize_result)
        
        workflow.set_entry_point("retrieve_context")
        
        workflow.add_edge("retrieve_context", "generate_sql")
        workflow.add_edge("generate_sql", "validate_sql")
        
        workflow.add_conditional_edges(
            "validate_sql",
            self._should_retry_or_optimize,
            {
                "optimize": "optimize_query",
                "retry": "generate_sql",
                "error": "handle_error"
            }
        )
        
        workflow.add_edge("optimize_query", "execute_query")
        
        workflow.add_conditional_edges(
            "execute_query",
            self._should_finalize_or_retry,
            {
                "finalize": "finalize_result",
                "retry": "generate_sql",
                "error": "handle_error"
            }
        )
        
        workflow.add_edge("handle_error", END)
        workflow.add_edge("finalize_result", END)
        
        return workflow.compile()
    
    async def _retrieve_context(self, state: WorkflowState) -> Dict[str, Any]:
        try:
            logger.info(f"Retrieving context for question: {state['question']}")
            
            schema_context, example_context = await self.rag_system.retrieve_relevant_context(
                state["question"], k=8
            )
            
            return {
                **state,
                "schema_context": schema_context,
                "example_context": example_context
            }
        
        except Exception as e:
            logger.error(f"Context retrieval failed: {str(e)}")
            return {
                **state,
                "schema_context": [],
                "example_context": [],
                "error_message": f"Context retrieval failed: {str(e)}"
            }
    
    async def _generate_sql(self, state: WorkflowState) -> Dict[str, Any]:
        try:
            logger.info("Generating SQL query")
            
            if state.get("retry_count", 0) > 0:
                logger.info(f"Retry attempt {state['retry_count']}")
            
            result = await self.rag_system.generate_sql_with_explanation(
                state["question"],
                state["schema_context"],
                state["example_context"]
            )
            
            return {
                **state,
                "sql_query": result["sql_query"],
                "explanation": result["explanation"],
                "confidence_score": result["confidence_score"],
                "complexity": result["complexity"]
            }
        
        except Exception as e:
            logger.error(f"SQL generation failed: {str(e)}")
            return {
                **state,
                "sql_query": "",
                "explanation": "",
                "confidence_score": 0.0,
                "complexity": "error",
                "error_message": f"SQL generation failed: {str(e)}"
            }
    
    async def _validate_sql(self, state: WorkflowState) -> Dict[str, Any]:
        try:
            logger.info("Validating SQL query")
            
            validation_result = await self.sql_validator.validate_query(
                state["sql_query"],
                await self.db_manager.get_all_tables()
            )
            
            return {
                **state,
                "validation_passed": validation_result["is_valid"],
                "validation_errors": validation_result["errors"]
            }
        
        except Exception as e:
            logger.error(f"SQL validation failed: {str(e)}")
            return {
                **state,
                "validation_passed": False,
                "validation_errors": [f"Validation error: {str(e)}"]
            }
    
    async def _optimize_query(self, state: WorkflowState) -> Dict[str, Any]:
        try:
            logger.info("Optimizing SQL query")
            
            optimization_result = await self.query_optimizer.optimize_query(
                state["sql_query"]
            )
            
            return {
                **state,
                "optimized_query": optimization_result["optimized_query"],
                "optimization_applied": optimization_result["optimization_applied"]
            }
        
        except Exception as e:
            logger.error(f"Query optimization failed: {str(e)}")
            return {
                **state,
                "optimized_query": state["sql_query"],
                "optimization_applied": False
            }
    
    async def _execute_query(self, state: WorkflowState) -> Dict[str, Any]:
        try:
            logger.info("Executing SQL query")
            
            start_time = time.time()
            
            query_to_execute = state.get("optimized_query", state["sql_query"])
            if not query_to_execute:
                query_to_execute = state["sql_query"]
            
            results = await self.db_manager.execute_query(
                query_to_execute,
                state["max_results"]
            )
            
            execution_time = time.time() - start_time
            
            await self.db_manager.save_query_history(
                question=state["question"],
                sql_query=query_to_execute,
                results_count=len(results),
                execution_time=execution_time,
                confidence_score=state["confidence_score"],
                success=True
            )
            
            return {
                **state,
                "results": results,
                "execution_time": execution_time
            }
        
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            
            await self.db_manager.save_query_history(
                question=state["question"],
                sql_query=state.get("sql_query", ""),
                results_count=0,
                execution_time=0.0,
                confidence_score=state.get("confidence_score", 0.0),
                success=False,
                error_message=str(e)
            )
            
            return {
                **state,
                "results": [],
                "execution_time": 0.0,
                "error_message": f"Query execution failed: {str(e)}"
            }
    
    async def _handle_error(self, state: WorkflowState) -> Dict[str, Any]:
        logger.error(f"Handling workflow error: {state.get('error_message', 'Unknown error')}")
        
        return {
            **state,
            "results": [],
            "execution_time": 0.0,
            "sql_query": state.get("sql_query", ""),
            "explanation": f"Error: {state.get('error_message', 'Unknown error occurred')}"
        }
    
    async def _finalize_result(self, state: WorkflowState) -> Dict[str, Any]:
        logger.info("Finalizing workflow result")
        
        final_query = state.get("optimized_query") or state.get("sql_query", "")
        
        metadata = {
            "complexity": state.get("complexity", "unknown"),
            "validation_passed": state.get("validation_passed", False),
            "optimization_applied": state.get("optimization_applied", False),
            "retry_count": state.get("retry_count", 0),
            "schema_context_count": len(state.get("schema_context", [])),
            "example_context_count": len(state.get("example_context", []))
        }
        
        return {
            **state,
            "sql_query": final_query,
            "metadata": metadata
        }
    
    def _should_retry_or_optimize(self, state: WorkflowState) -> str:
        if state.get("error_message"):
            return "error"
        
        if not state.get("validation_passed", False):
            retry_count = state.get("retry_count", 0)
            max_retries = state.get("max_retries", 2)
            
            if retry_count < max_retries:
                return "retry"
            else:
                return "error"
        
        return "optimize"
    
    def _should_finalize_or_retry(self, state: WorkflowState) -> str:
        if state.get("error_message"):
            retry_count = state.get("retry_count", 0)
            max_retries = state.get("max_retries", 2)
            
            if retry_count < max_retries:
                return "retry"
            else:
                return "error"
        
        return "finalize"
    
    async def execute_workflow(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            initial_state = WorkflowState(
                question=input_data["question"],
                database_context=input_data.get("database_context"),
                include_explanation=input_data.get("include_explanation", True),
                max_results=input_data.get("max_results", 100),
                
                schema_context=[],
                example_context=[],
                
                sql_query="",
                explanation="",
                confidence_score=0.0,
                complexity="unknown",
                
                validation_passed=False,
                validation_errors=[],
                
                optimized_query="",
                optimization_applied=False,
                
                results=[],
                execution_time=0.0,
                
                error_message=None,
                retry_count=0,
                max_retries=2
            )
            
            result = await self.workflow.ainvoke(initial_state)
            
            return {
                "sql_query": result.get("sql_query", ""),
                "results": result.get("results", []),
                "explanation": result.get("explanation", ""),
                "confidence_score": result.get("confidence_score", 0.0),
                "execution_time": result.get("execution_time", 0.0),
                "metadata": result.get("metadata", {})
            }
        
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            return {
                "sql_query": "",
                "results": [],
                "explanation": f"Workflow failed: {str(e)}",
                "confidence_score": 0.0,
                "execution_time": 0.0,
                "metadata": {"error": True}
            }
    
    async def execute_workflow_streaming(self, input_data: Dict[str, Any], 
                                       websocket, connection_manager) -> Dict[str, Any]:
        try:
            await connection_manager.send_personal_message(
                {"type": "progress", "step": "Retrieving context", "progress": 20}, websocket
            )
            
            initial_state = WorkflowState(
                question=input_data["question"],
                database_context=input_data.get("database_context"),
                include_explanation=input_data.get("include_explanation", True),
                max_results=input_data.get("max_results", 100),
                schema_context=[],
                example_context=[],
                sql_query="",
                explanation="",
                confidence_score=0.0,
                complexity="unknown",
                validation_passed=False,
                validation_errors=[],
                optimized_query="",
                optimization_applied=False,
                results=[],
                execution_time=0.0,
                error_message=None,
                retry_count=0,
                max_retries=2
            )
            
            step_progress = {
                "retrieve_context": 20,
                "generate_sql": 40,
                "validate_sql": 60,
                "optimize_query": 70,
                "execute_query": 90,
                "finalize_result": 100
            }
            
            async for step_name, step_state in self.workflow.astream(initial_state):
                if step_name in step_progress:
                    await connection_manager.send_personal_message({
                        "type": "progress",
                        "step": step_name.replace("_", " ").title(),
                        "progress": step_progress[step_name],
                        "sql_preview": step_state.get("sql_query", "") if step_name == "generate_sql" else None
                    }, websocket)
            
            result = await self.workflow.ainvoke(initial_state)
            
            return {
                "sql_query": result.get("sql_query", ""),
                "results": result.get("results", []),
                "explanation": result.get("explanation", ""),
                "confidence_score": result.get("confidence_score", 0.0),
                "execution_time": result.get("execution_time", 0.0),
                "metadata": result.get("metadata", {})
            }
        
        except Exception as e:
            logger.error(f"Streaming workflow execution failed: {str(e)}")
            await connection_manager.send_personal_message(
                {"type": "error", "message": str(e)}, websocket
            )
            return {
                "sql_query": "",
                "results": [],
                "explanation": f"Workflow failed: {str(e)}",
                "confidence_score": 0.0,
                "execution_time": 0.0,
                "metadata": {"error": True}
            }
    
    def health_check(self) -> bool:
        try:
            return self.workflow is not None
        except Exception:
            return False