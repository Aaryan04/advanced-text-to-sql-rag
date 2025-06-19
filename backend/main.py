from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import asyncio
import json
from datetime import datetime

from database.connection import DatabaseManager
from rag.text_to_sql_rag import TextToSQLRAG
from graph.sql_workflow import SQLWorkflowGraph
from utils.websocket_manager import ConnectionManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Text-to-SQL RAG System")
    
    app.state.db_manager = DatabaseManager()
    await app.state.db_manager.initialize()
    
    app.state.rag_system = TextToSQLRAG()
    await app.state.rag_system.initialize()
    
    app.state.workflow_graph = SQLWorkflowGraph(
        rag_system=app.state.rag_system,
        db_manager=app.state.db_manager
    )
    
    app.state.connection_manager = ConnectionManager()
    
    yield
    
    logger.info("Shutting down Text-to-SQL RAG System")
    await app.state.db_manager.close()

app = FastAPI(
    title="Advanced Text-to-SQL RAG System",
    description="An intelligent system that converts natural language to SQL using RAG and LangGraph",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str
    database_context: Optional[str] = None
    include_explanation: bool = True
    max_results: int = 100

class QueryResponse(BaseModel):
    sql_query: str
    results: List[Dict[str, Any]]
    explanation: str
    confidence_score: float
    execution_time: float
    metadata: Dict[str, Any]

class SchemaRequest(BaseModel):
    table_names: Optional[List[str]] = None

@app.get("/")
async def root():
    return {"message": "Advanced Text-to-SQL RAG System is running"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "database": await app.state.db_manager.health_check(),
            "rag_system": app.state.rag_system.health_check(),
            "workflow": app.state.workflow_graph.health_check()
        }
    }

@app.post("/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    try:
        result = await app.state.workflow_graph.execute_workflow({
            "question": request.question,
            "database_context": request.database_context,
            "include_explanation": request.include_explanation,
            "max_results": request.max_results
        })
        
        return QueryResponse(**result)
    
    except Exception as e:
        logger.error(f"Query execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/schema")
async def get_database_schema(request: Optional[SchemaRequest] = None):
    try:
        schema = await app.state.db_manager.get_schema_info(
            table_names=request.table_names if request else None
        )
        return {"schema": schema}
    
    except Exception as e:
        logger.error(f"Schema retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tables")
async def get_tables():
    try:
        tables = await app.state.db_manager.get_all_tables()
        return {"tables": tables}
    
    except Exception as e:
        logger.error(f"Table listing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/query-history")
async def get_query_history(limit: int = 50):
    try:
        history = await app.state.db_manager.get_query_history(limit)
        return {"history": history}
    
    except Exception as e:
        logger.error(f"Query history retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/query")
async def websocket_query_endpoint(websocket: WebSocket):
    await app.state.connection_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            request_data = json.loads(data)
            
            await app.state.connection_manager.send_personal_message(
                {"type": "status", "message": "Processing query..."}, websocket
            )
            
            try:
                result = await app.state.workflow_graph.execute_workflow_streaming(
                    request_data, websocket, app.state.connection_manager
                )
                
                await app.state.connection_manager.send_personal_message(
                    {"type": "result", "data": result}, websocket
                )
            
            except Exception as e:
                await app.state.connection_manager.send_personal_message(
                    {"type": "error", "message": str(e)}, websocket
                )
    
    except WebSocketDisconnect:
        app.state.connection_manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)