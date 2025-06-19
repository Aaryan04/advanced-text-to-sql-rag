import asyncio
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, JSON
from sqlalchemy import text, inspect
from datetime import datetime
import os
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

class QueryHistory(Base):
    __tablename__ = "query_history"
    
    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    sql_query = Column(Text, nullable=False)
    results_count = Column(Integer, default=0)
    execution_time = Column(Float, default=0.0)
    confidence_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    query_metadata = Column(JSON, default={})
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)

class DatabaseManager:
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./texttosql.db")
        self.engine = None
        self.session_factory = None
        self._sample_data_loaded = False
    
    async def initialize(self):
        self.engine = create_async_engine(
            self.database_url,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=3600,
            echo=False
        )
        
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        await self._create_sample_database()
        logger.info("Database initialized successfully")
    
    async def _create_sample_database(self):
        if self._sample_data_loaded:
            return
            
        sample_tables = [
            """
            CREATE TABLE IF NOT EXISTS employees (
                id SERIAL PRIMARY KEY,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                department VARCHAR(50),
                salary DECIMAL(10,2),
                hire_date DATE,
                manager_id INTEGER REFERENCES employees(id),
                is_active BOOLEAN DEFAULT TRUE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS departments (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) UNIQUE NOT NULL,
                budget DECIMAL(12,2),
                location VARCHAR(100),
                manager_id INTEGER REFERENCES employees(id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS projects (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                start_date DATE,
                end_date DATE,
                budget DECIMAL(12,2),
                department_id INTEGER REFERENCES departments(id),
                status VARCHAR(20) DEFAULT 'active'
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS employee_projects (
                employee_id INTEGER REFERENCES employees(id),
                project_id INTEGER REFERENCES projects(id),
                role VARCHAR(50),
                hours_allocated INTEGER,
                PRIMARY KEY (employee_id, project_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS sales (
                id SERIAL PRIMARY KEY,
                employee_id INTEGER REFERENCES employees(id),
                product_name VARCHAR(100),
                sale_amount DECIMAL(10,2),
                sale_date DATE,
                customer_name VARCHAR(100),
                region VARCHAR(50)
            )
            """
        ]
        
        sample_data = [
            """
            INSERT INTO departments (name, budget, location) VALUES
            ('Engineering', 500000.00, 'San Francisco'),
            ('Sales', 300000.00, 'New York'),
            ('Marketing', 200000.00, 'Los Angeles'),
            ('HR', 150000.00, 'Chicago'),
            ('Finance', 250000.00, 'Boston')
            ON CONFLICT (name) DO NOTHING
            """,
            """
            INSERT INTO employees (first_name, last_name, email, department, salary, hire_date, is_active) VALUES
            ('John', 'Doe', 'john.doe@company.com', 'Engineering', 95000.00, '2022-01-15', TRUE),
            ('Jane', 'Smith', 'jane.smith@company.com', 'Sales', 75000.00, '2021-03-20', TRUE),
            ('Bob', 'Johnson', 'bob.johnson@company.com', 'Engineering', 105000.00, '2020-06-10', TRUE),
            ('Alice', 'Williams', 'alice.williams@company.com', 'Marketing', 65000.00, '2023-02-01', TRUE),
            ('Charlie', 'Brown', 'charlie.brown@company.com', 'HR', 70000.00, '2021-11-30', TRUE),
            ('Eva', 'Davis', 'eva.davis@company.com', 'Finance', 80000.00, '2022-09-15', TRUE),
            ('Frank', 'Miller', 'frank.miller@company.com', 'Sales', 78000.00, '2023-01-10', TRUE),
            ('Grace', 'Wilson', 'grace.wilson@company.com', 'Engineering', 98000.00, '2021-08-25', TRUE)
            ON CONFLICT (email) DO NOTHING
            """,
            """
            INSERT INTO projects (name, description, start_date, end_date, budget, status) VALUES
            ('Website Redesign', 'Complete overhaul of company website', '2023-01-01', '2023-06-30', 75000.00, 'completed'),
            ('Mobile App Development', 'Native iOS and Android app', '2023-03-01', '2023-12-31', 150000.00, 'active'),
            ('Customer Analytics Platform', 'Data analytics dashboard for sales team', '2023-06-01', '2024-03-31', 100000.00, 'active'),
            ('Marketing Campaign Q4', 'Holiday season marketing push', '2023-10-01', '2023-12-31', 50000.00, 'active'),
            ('HR System Upgrade', 'Modernize HR management system', '2023-05-01', '2023-11-30', 80000.00, 'active')
            """,
            """
            INSERT INTO sales (employee_id, product_name, sale_amount, sale_date, customer_name, region) VALUES
            (2, 'Enterprise Software License', 25000.00, '2023-01-15', 'TechCorp Inc', 'West'),
            (2, 'Consulting Services', 15000.00, '2023-02-20', 'StartupXYZ', 'West'),
            (7, 'Software Maintenance', 8000.00, '2023-01-30', 'BigCorp Ltd', 'East'),
            (7, 'Training Package', 12000.00, '2023-03-10', 'MediumBiz Co', 'East'),
            (2, 'Custom Development', 35000.00, '2023-04-05', 'Enterprise Solutions Inc', 'West')
            """
        ]
        
        try:
            async with self.session_factory() as session:
                for table_sql in sample_tables:
                    await session.execute(text(table_sql))
                
                for data_sql in sample_data:
                    await session.execute(text(data_sql))
                
                await session.commit()
                self._sample_data_loaded = True
                logger.info("Sample database created successfully")
        
        except Exception as e:
            logger.error(f"Failed to create sample database: {str(e)}")
    
    @asynccontextmanager
    async def get_session(self):
        async with self.session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def execute_query(self, sql_query: str, max_results: int = 100) -> List[Dict[str, Any]]:
        async with self.get_session() as session:
            result = await session.execute(text(f"SELECT * FROM ({sql_query}) subquery LIMIT {max_results}"))
            columns = result.keys()
            rows = result.fetchall()
            
            return [dict(zip(columns, row)) for row in rows]
    
    async def get_schema_info(self, table_names: Optional[List[str]] = None) -> Dict[str, Any]:
        schema_info = {}
        
        async with self.get_session() as session:
            if table_names is None:
                # SQLite-compatible query to get table names
                table_result = await session.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                """))
                table_names = [row[0] for row in table_result.fetchall()]
            
            for table_name in table_names:
                try:
                    # SQLite-compatible query to get column info
                    column_result = await session.execute(text(f"PRAGMA table_info({table_name})"))
                    
                    columns = []
                    for row in column_result.fetchall():
                        # SQLite PRAGMA table_info returns: cid, name, type, notnull, dflt_value, pk
                        columns.append({
                            "name": row[1],        # name
                            "type": row[2],        # type
                            "nullable": row[3] == 0,  # notnull (0 = nullable, 1 = not null)
                            "default": row[4]      # dflt_value
                        })
                    
                    sample_data_result = await session.execute(text(f"SELECT * FROM {table_name} LIMIT 3"))
                    sample_data = [dict(zip(sample_data_result.keys(), row)) for row in sample_data_result.fetchall()]
                    
                    schema_info[table_name] = {
                        "columns": columns,
                        "sample_data": sample_data
                    }
                
                except Exception as e:
                    logger.warning(f"Failed to get schema for table {table_name}: {str(e)}")
        
        return schema_info
    
    async def get_all_tables(self) -> List[str]:
        async with self.get_session() as session:
            # SQLite-compatible query to get table names
            result = await session.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """))
            return [row[0] for row in result.fetchall()]
    
    async def save_query_history(self, question: str, sql_query: str, results_count: int, 
                               execution_time: float, confidence_score: float, 
                               success: bool = True, error_message: str = None, 
                               query_metadata: Dict[str, Any] = None):
        async with self.get_session() as session:
            history_entry = QueryHistory(
                question=question,
                sql_query=sql_query,
                results_count=results_count,
                execution_time=execution_time,
                confidence_score=confidence_score,
                success=success,
                error_message=error_message,
                query_metadata=query_metadata or {}
            )
            session.add(history_entry)
            await session.commit()
    
    async def get_query_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        async with self.get_session() as session:
            result = await session.execute(
                text("SELECT * FROM query_history ORDER BY created_at DESC LIMIT :limit"),
                {"limit": limit}
            )
            columns = result.keys()
            rows = result.fetchall()
            
            return [dict(zip(columns, row)) for row in rows]
    
    async def health_check(self) -> bool:
        try:
            async with self.get_session() as session:
                await session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False
    
    async def close(self):
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connection closed")