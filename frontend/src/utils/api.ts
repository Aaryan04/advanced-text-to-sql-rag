import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

export interface QueryRequest {
  question: string;
  database_context?: string;
  include_explanation?: boolean;
  max_results?: number;
}

export interface QueryResponse {
  sql_query: string;
  results: any[];
  explanation: string;
  confidence_score: number;
  execution_time: number;
  metadata: {
    complexity: string;
    validation_passed: boolean;
    optimization_applied: boolean;
    retry_count: number;
    schema_context_count: number;
    example_context_count: number;
  };
}

export interface TableSchema {
  columns: {
    name: string;
    type: string;
    nullable: boolean;
    default: string;
  }[];
  sample_data: any[];
}

export interface DatabaseSchema {
  [tableName: string]: TableSchema;
}

export interface QueryHistoryEntry {
  id: number;
  question: string;
  sql_query: string;
  results_count: number;
  execution_time: number;
  confidence_score: number;
  created_at: string;
  success: boolean;
  error_message?: string;
  metadata: any;
}

export interface HealthStatus {
  status: string;
  timestamp: string;
  components: {
    database: boolean;
    rag_system: boolean;
    workflow: boolean;
  };
}

// API Functions
export const executeQuery = async (request: QueryRequest): Promise<QueryResponse> => {
  const response = await api.post('/query', request);
  return response.data;
};

export const getDatabaseSchema = async (tableNames?: string[]): Promise<DatabaseSchema> => {
  const response = await api.get('/schema', {
    params: tableNames ? { table_names: tableNames } : {},
  });
  return response.data.schema;
};

export const getAllTables = async (): Promise<string[]> => {
  const response = await api.get('/tables');
  return response.data.tables;
};

export const getQueryHistory = async (limit: number = 50): Promise<QueryHistoryEntry[]> => {
  const response = await api.get('/query-history', {
    params: { limit },
  });
  return response.data.history;
};

export const getHealthStatus = async (): Promise<HealthStatus> => {
  const response = await api.get('/health');
  return response.data;
};

// Error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.data?.detail) {
      throw new Error(error.response.data.detail);
    }
    throw error;
  }
);

export default api;