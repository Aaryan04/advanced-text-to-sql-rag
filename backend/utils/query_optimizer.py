import re
import logging
from typing import Dict, Any, List, Tuple
import sqlparse
from sqlparse import sql, tokens

logger = logging.getLogger(__name__)

class QueryOptimizer:
    def __init__(self):
        self.optimization_rules = [
            self._optimize_select_star,
            self._optimize_unnecessary_distinct,
            self._optimize_redundant_conditions,
            self._optimize_inefficient_joins,
            self._add_limit_if_missing
        ]
    
    async def optimize_query(self, sql_query: str) -> Dict[str, Any]:
        try:
            original_query = sql_query.strip()
            optimized_query = original_query
            optimizations_applied = []
            
            for rule in self.optimization_rules:
                result = rule(optimized_query)
                if result["modified"]:
                    optimized_query = result["query"]
                    optimizations_applied.append(result["description"])
            
            return {
                "original_query": original_query,
                "optimized_query": optimized_query,
                "optimization_applied": len(optimizations_applied) > 0,
                "optimizations": optimizations_applied
            }
        
        except Exception as e:
            logger.error(f"Query optimization failed: {str(e)}")
            return {
                "original_query": sql_query,
                "optimized_query": sql_query,
                "optimization_applied": False,
                "optimizations": []
            }
    
    def _optimize_select_star(self, query: str) -> Dict[str, Any]:
        if re.search(r'SELECT\s+\*\s+FROM', query, re.IGNORECASE):
            if not re.search(r'LIMIT\s+\d+', query, re.IGNORECASE):
                optimized = re.sub(
                    r'(SELECT\s+\*\s+FROM\s+\w+.*?)(?:\s*;?\s*$)',
                    r'\1 LIMIT 1000',
                    query,
                    flags=re.IGNORECASE | re.DOTALL
                )
                if optimized != query:
                    return {
                        "modified": True,
                        "query": optimized,
                        "description": "Added LIMIT to SELECT * query for performance"
                    }
        
        return {"modified": False, "query": query, "description": ""}
    
    def _optimize_unnecessary_distinct(self, query: str) -> Dict[str, Any]:
        if re.search(r'SELECT\s+DISTINCT\s+\*', query, re.IGNORECASE):
            optimized = re.sub(
                r'SELECT\s+DISTINCT\s+\*',
                'SELECT *',
                query,
                flags=re.IGNORECASE
            )
            if optimized != query:
                return {
                    "modified": True,
                    "query": optimized,
                    "description": "Removed unnecessary DISTINCT with SELECT *"
                }
        
        return {"modified": False, "query": query, "description": ""}
    
    def _optimize_redundant_conditions(self, query: str) -> Dict[str, Any]:
        patterns = [
            (r'WHERE\s+(\w+)\s*=\s*(\w+)\s+AND\s+\1\s*=\s*\2', r'WHERE \1 = \2'),
            (r'WHERE\s+(\w+)\s*IS\s+NOT\s+NULL\s+AND\s+\1\s*IS\s+NOT\s+NULL', r'WHERE \1 IS NOT NULL'),
        ]
        
        optimized = query
        for pattern, replacement in patterns:
            new_query = re.sub(pattern, replacement, optimized, flags=re.IGNORECASE)
            if new_query != optimized:
                return {
                    "modified": True,
                    "query": new_query,
                    "description": "Removed redundant WHERE conditions"
                }
        
        return {"modified": False, "query": query, "description": ""}
    
    def _optimize_inefficient_joins(self, query: str) -> Dict[str, Any]:
        cartesian_join_pattern = r'FROM\s+(\w+)\s*,\s*(\w+)(?!\s+ON|\s+WHERE)'
        
        if re.search(cartesian_join_pattern, query, re.IGNORECASE):
            logger.warning("Detected potential cartesian join - manual review recommended")
            return {
                "modified": False,
                "query": query,
                "description": "Cartesian join detected - manual optimization needed"
            }
        
        return {"modified": False, "query": query, "description": ""}
    
    def _add_limit_if_missing(self, query: str) -> Dict[str, Any]:
        if not re.search(r'LIMIT\s+\d+', query, re.IGNORECASE):
            if not re.search(r'COUNT\s*\(', query, re.IGNORECASE):
                optimized = query.rstrip(';') + ' LIMIT 1000'
                return {
                    "modified": True,
                    "query": optimized,
                    "description": "Added default LIMIT for performance"
                }
        
        return {"modified": False, "query": query, "description": ""}
    
    def analyze_query_complexity(self, query: str) -> Dict[str, Any]:
        try:
            parsed = sqlparse.parse(query)[0]
            
            complexity_score = 0
            factors = []
            
            join_count = len(re.findall(r'\bJOIN\b', query, re.IGNORECASE))
            if join_count > 0:
                complexity_score += join_count * 2
                factors.append(f"{join_count} JOINs")
            
            subquery_count = len(re.findall(r'SELECT.*FROM.*SELECT', query, re.IGNORECASE | re.DOTALL))
            if subquery_count > 0:
                complexity_score += subquery_count * 3
                factors.append(f"{subquery_count} subqueries")
            
            aggregate_count = len(re.findall(r'\b(COUNT|SUM|AVG|MIN|MAX)\s*\(', query, re.IGNORECASE))
            if aggregate_count > 0:
                complexity_score += aggregate_count
                factors.append(f"{aggregate_count} aggregate functions")
            
            group_by = re.search(r'\bGROUP BY\b', query, re.IGNORECASE)
            if group_by:
                complexity_score += 2
                factors.append("GROUP BY clause")
            
            having = re.search(r'\bHAVING\b', query, re.IGNORECASE)
            if having:
                complexity_score += 2
                factors.append("HAVING clause")
            
            union_count = len(re.findall(r'\bUNION\b', query, re.IGNORECASE))
            if union_count > 0:
                complexity_score += union_count * 2
                factors.append(f"{union_count} UNION operations")
            
            if complexity_score <= 3:
                complexity_level = "low"
            elif complexity_score <= 8:
                complexity_level = "medium"
            else:
                complexity_level = "high"
            
            return {
                "complexity_score": complexity_score,
                "complexity_level": complexity_level,
                "complexity_factors": factors
            }
        
        except Exception as e:
            logger.error(f"Query complexity analysis failed: {str(e)}")
            return {
                "complexity_score": 0,
                "complexity_level": "unknown",
                "complexity_factors": []
            }