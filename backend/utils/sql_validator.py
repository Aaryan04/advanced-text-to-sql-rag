import re
import logging
from typing import Dict, Any, List
import sqlparse
from sqlparse import sql, tokens

logger = logging.getLogger(__name__)

class SQLValidator:
    def __init__(self):
        self.forbidden_keywords = {
            'DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'INSERT', 'UPDATE',
            'GRANT', 'REVOKE', 'EXEC', 'EXECUTE', 'sp_', 'xp_'
        }
        
        self.allowed_functions = {
            'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'DISTINCT', 'GROUP_CONCAT',
            'CONCAT', 'SUBSTR', 'LENGTH', 'UPPER', 'LOWER', 'TRIM',
            'COALESCE', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END',
            'CAST', 'CONVERT', 'DATE', 'DATETIME', 'YEAR', 'MONTH', 'DAY',
            'EXTRACT', 'NOW', 'CURRENT_DATE', 'CURRENT_TIME', 'CURRENT_TIMESTAMP'
        }
    
    async def validate_query(self, sql_query: str, available_tables: List[str]) -> Dict[str, Any]:
        try:
            errors = []
            warnings = []
            
            if not sql_query or not sql_query.strip():
                return {
                    "is_valid": False,
                    "errors": ["Empty SQL query"],
                    "warnings": []
                }
            
            sql_query = sql_query.strip()
            
            if not sql_query.upper().startswith('SELECT'):
                errors.append("Only SELECT queries are allowed")
            
            security_errors = self._check_security_violations(sql_query)
            errors.extend(security_errors)
            
            syntax_errors = self._check_syntax(sql_query)
            errors.extend(syntax_errors)
            
            table_errors = self._check_table_references(sql_query, available_tables)
            errors.extend(table_errors)
            
            complexity_warnings = self._check_complexity(sql_query)
            warnings.extend(complexity_warnings)
            
            return {
                "is_valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings
            }
        
        except Exception as e:
            logger.error(f"SQL validation failed: {str(e)}")
            return {
                "is_valid": False,
                "errors": [f"Validation error: {str(e)}"],
                "warnings": []
            }
    
    def _check_security_violations(self, sql_query: str) -> List[str]:
        errors = []
        upper_query = sql_query.upper()
        
        for keyword in self.forbidden_keywords:
            if keyword in upper_query:
                if keyword.endswith('_'):
                    if re.search(rf'\b{re.escape(keyword)}\w*', upper_query):
                        errors.append(f"Forbidden keyword/function: {keyword}")
                else:
                    if re.search(rf'\b{re.escape(keyword)}\b', upper_query):
                        errors.append(f"Forbidden keyword: {keyword}")
        
        comment_patterns = [
            r'--.*',
            r'/\*.*?\*/',
            r'#.*'
        ]
        
        for pattern in comment_patterns:
            if re.search(pattern, sql_query, re.DOTALL):
                errors.append("Comments are not allowed in SQL queries")
                break
        
        if re.search(r';\s*\w', sql_query):
            errors.append("Multiple statements are not allowed")
        
        return errors
    
    def _check_syntax(self, sql_query: str) -> List[str]:
        errors = []
        
        try:
            parsed = sqlparse.parse(sql_query)
            
            if not parsed:
                errors.append("Failed to parse SQL query")
                return errors
            
            statement = parsed[0]
            
            if statement.get_type() != 'SELECT':
                errors.append("Only SELECT statements are allowed")
            
            paren_count = sql_query.count('(') - sql_query.count(')')
            if paren_count != 0:
                errors.append("Unmatched parentheses in SQL query")
            
            quote_patterns = [
                (r"'", "single quotes"),
                (r'"', "double quotes")
            ]
            
            for pattern, quote_type in quote_patterns:
                if sql_query.count(pattern) % 2 != 0:
                    errors.append(f"Unmatched {quote_type} in SQL query")
        
        except Exception as e:
            errors.append(f"Syntax parsing error: {str(e)}")
        
        return errors
    
    def _check_table_references(self, sql_query: str, available_tables: List[str]) -> List[str]:
        errors = []
        
        try:
            parsed = sqlparse.parse(sql_query)[0]
            
            from_tables = self._extract_table_names(parsed)
            
            unavailable_tables = [table for table in from_tables if table not in available_tables]
            
            if unavailable_tables:
                errors.append(f"Referenced tables not found in database: {', '.join(unavailable_tables)}")
        
        except Exception as e:
            logger.warning(f"Table reference check failed: {str(e)}")
        
        return errors
    
    def _extract_table_names(self, parsed_query) -> List[str]:
        table_names = []
        
        def extract_from_token(token):
            if token.ttype is tokens.Keyword and token.value.upper() == 'FROM':
                return True
            return False
        
        def extract_table_name(tokens):
            for token in tokens:
                if hasattr(token, 'tokens'):
                    extract_table_name(token.tokens)
                elif token.ttype is None and not token.is_keyword:
                    table_name = token.value.strip()
                    if table_name and not table_name.startswith('('):
                        table_names.append(table_name.split('.')[0])
        
        tokens = list(parsed_query.flatten())
        from_found = False
        
        for i, token in enumerate(tokens):
            if extract_from_token(token):
                from_found = True
                continue
            
            if from_found and token.ttype is None and not token.is_keyword:
                table_name = token.value.strip()
                if table_name and not table_name.startswith('(') and table_name != ',':
                    table_names.append(table_name.split('.')[0])
        
        return list(set(table_names))
    
    def _check_complexity(self, sql_query: str) -> List[str]:
        warnings = []
        
        join_count = len(re.findall(r'\bJOIN\b', sql_query, re.IGNORECASE))
        if join_count > 5:
            warnings.append(f"Query has {join_count} JOINs, which may impact performance")
        
        subquery_count = sql_query.count('(') 
        if subquery_count > 3:
            warnings.append(f"Query has multiple nested subqueries, which may impact performance")
        
        union_count = len(re.findall(r'\bUNION\b', sql_query, re.IGNORECASE))
        if union_count > 2:
            warnings.append(f"Query has {union_count} UNIONs, which may impact performance")
        
        having_clause = re.search(r'\bHAVING\b', sql_query, re.IGNORECASE)
        group_by_clause = re.search(r'\bGROUP BY\b', sql_query, re.IGNORECASE)
        if having_clause and not group_by_clause:
            warnings.append("HAVING clause without GROUP BY may not work as expected")
        
        return warnings