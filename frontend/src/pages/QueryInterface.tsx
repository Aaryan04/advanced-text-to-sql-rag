import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Paper,
  TextField,
  Button,
  Typography,
  CircularProgress,
  Alert,
  Chip,
  Tabs,
  Tab,
  IconButton,
  Tooltip,
  Card,
  CardContent,
  LinearProgress,
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  ContentCopy,
  Download,
  Share,
  Favorite,
  FavoriteBorder,
  TrendingUp,
  Speed,
  CheckCircle,
  Error,
} from '@mui/icons-material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import Editor from '@monaco-editor/react';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';

import { useQuery, useMutation } from '@tanstack/react-query';
import { executeQuery, QueryRequest, QueryResponse } from '../utils/api';
import { useWebSocket } from '../hooks/useWebSocket';
import ResultsVisualizer from '../components/ResultsVisualizer';
import QuerySuggestions from '../components/QuerySuggestions';

interface QueryProgress {
  step: string;
  progress: number;
  sql_preview?: string;
}

const QueryInterface: React.FC = () => {
  const [question, setQuestion] = useState('');
  const [currentTab, setCurrentTab] = useState(0);
  const [queryResult, setQueryResult] = useState<QueryResponse | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [progress, setProgress] = useState<QueryProgress | null>(null);
  const [isFavorite, setIsFavorite] = useState(false);

  const { sendMessage, lastMessage, connectionStatus } = useWebSocket('/ws/query');

  const queryMutation = useMutation(executeQuery, {
    onSuccess: (data) => {
      setQueryResult(data);
      setIsExecuting(false);
      toast.success('Query executed successfully!');
    },
    onError: (error: any) => {
      setIsExecuting(false);
      toast.error(error.message || 'Query execution failed');
    },
  });

  useEffect(() => {
    if (lastMessage) {
      const data = JSON.parse(lastMessage.data);
      
      switch (data.type) {
        case 'progress':
          setProgress(data);
          break;
        case 'result':
          setQueryResult(data.data);
          setIsExecuting(false);
          setProgress(null);
          toast.success('Query completed!');
          break;
        case 'error':
          setIsExecuting(false);
          setProgress(null);
          toast.error(data.message);
          break;
      }
    }
  }, [lastMessage]);

  const handleExecuteQuery = () => {
    if (!question.trim()) {
      toast.error('Please enter a question');
      return;
    }

    setIsExecuting(true);
    setProgress(null);
    setQueryResult(null);

    const queryRequest: QueryRequest = {
      question: question.trim(),
      include_explanation: true,
      max_results: 100,
    };

    if (connectionStatus === 'Connected') {
      sendMessage(queryRequest);
    } else {
      queryMutation.mutate(queryRequest);
    }
  };

  const handleStopExecution = () => {
    setIsExecuting(false);
    setProgress(null);
    toast.info('Query execution stopped');
  };

  const handleCopySQL = () => {
    if (queryResult?.sql_query) {
      navigator.clipboard.writeText(queryResult.sql_query);
      toast.success('SQL copied to clipboard');
    }
  };

  const handleCopyResults = () => {
    if (queryResult?.results) {
      const csvData = convertToCSV(queryResult.results);
      navigator.clipboard.writeText(csvData);
      toast.success('Results copied to clipboard');
    }
  };

  const convertToCSV = (data: any[]) => {
    if (!data.length) return '';
    
    const headers = Object.keys(data[0]);
    const rows = data.map(row => headers.map(header => JSON.stringify(row[header] || '')).join(','));
    return [headers.join(','), ...rows].join('\n');
  };

  const getGridColumns = (): GridColDef[] => {
    if (!queryResult?.results?.length) return [];
    
    const firstRow = queryResult.results[0];
    return Object.keys(firstRow).map((key) => ({
      field: key,
      headerName: key.toUpperCase(),
      width: 150,
      flex: 1,
    }));
  };

  const exampleQuestions = [
    'Show all employees in the engineering department',
    'What is the average salary by department?',
    'Which projects have the highest budget?',
    'Show sales performance by region',
    'Find employees working on multiple projects',
  ];

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column', p: 2 }}>
      <Grid container spacing={2} sx={{ height: '100%' }}>
        {/* Left Panel - Query Input */}
        <Grid item xs={12} md={5}>
          <Paper sx={{ height: '100%', display: 'flex', flexDirection: 'column', p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Ask a Question
            </Typography>
            
            <TextField
              fullWidth
              multiline
              rows={4}
              variant="outlined"
              placeholder="Ask anything about your data... e.g., 'Show me the top 5 highest paid employees'"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              sx={{ mb: 2 }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && e.ctrlKey) {
                  handleExecuteQuery();
                }
              }}
            />

            <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
              <Button
                variant="contained"
                startIcon={isExecuting ? <Stop /> : <PlayArrow />}
                onClick={isExecuting ? handleStopExecution : handleExecuteQuery}
                disabled={!question.trim()}
                color={isExecuting ? 'secondary' : 'primary'}
              >
                {isExecuting ? 'Stop' : 'Execute'}
              </Button>
              <Tooltip title="Ctrl+Enter">
                <IconButton size="small">
                  <Speed />
                </IconButton>
              </Tooltip>
            </Box>

            {/* Progress Indicator */}
            <AnimatePresence>
              {progress && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                >
                  <Card sx={{ mb: 2, bgcolor: 'primary.dark' }}>
                    <CardContent sx={{ pb: '16px !important' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                        <CircularProgress size={16} sx={{ mr: 1 }} />
                        <Typography variant="body2">{progress.step}</Typography>
                      </Box>
                      <LinearProgress variant="determinate" value={progress.progress} />
                      {progress.sql_preview && (
                        <Box sx={{ mt: 1, p: 1, bgcolor: 'rgba(0,0,0,0.3)', borderRadius: 1 }}>
                          <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
                            {progress.sql_preview}
                          </Typography>
                        </Box>
                      )}
                    </CardContent>
                  </Card>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Example Questions */}
            <Typography variant="subtitle2" gutterBottom>
              Example Questions:
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {exampleQuestions.map((example, index) => (
                <Chip
                  key={index}
                  label={example}
                  variant="outlined"
                  size="small"
                  onClick={() => setQuestion(example)}
                  sx={{ cursor: 'pointer', justifyContent: 'flex-start', height: 'auto', py: 1 }}
                />
              ))}
            </Box>

            <QuerySuggestions onSelectSuggestion={setQuestion} />
          </Paper>
        </Grid>

        {/* Right Panel - Results */}
        <Grid item xs={12} md={7}>
          <Paper sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            {queryResult ? (
              <>
                <Box sx={{ borderBottom: 1, borderColor: 'divider', px: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', py: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Chip
                        icon={<CheckCircle />}
                        label={`${queryResult.results.length} rows`}
                        color="success"
                        size="small"
                      />
                      <Chip
                        icon={<Speed />}
                        label={`${(queryResult.execution_time * 1000).toFixed(0)}ms`}
                        color="info"
                        size="small"
                      />
                      <Chip
                        icon={<TrendingUp />}
                        label={`${Math.round(queryResult.confidence_score * 100)}% confidence`}
                        color="primary"
                        size="small"
                      />
                    </Box>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <IconButton
                        size="small"
                        onClick={() => setIsFavorite(!isFavorite)}
                        color={isFavorite ? 'primary' : 'default'}
                      >
                        {isFavorite ? <Favorite /> : <FavoriteBorder />}
                      </IconButton>
                      <IconButton size="small" onClick={handleCopySQL}>
                        <ContentCopy />
                      </IconButton>
                      <IconButton size="small" onClick={handleCopyResults}>
                        <Download />
                      </IconButton>
                      <IconButton size="small">
                        <Share />
                      </IconButton>
                    </Box>
                  </Box>
                  <Tabs
                    value={currentTab}
                    onChange={(_, newValue) => setCurrentTab(newValue)}
                    sx={{ minHeight: 'auto' }}
                  >
                    <Tab label="Results" />
                    <Tab label="SQL Query" />
                    <Tab label="Visualization" />
                    <Tab label="Explanation" />
                  </Tabs>
                </Box>

                <Box sx={{ flex: 1, overflow: 'hidden' }}>
                  {currentTab === 0 && (
                    <DataGrid
                      rows={queryResult.results.map((row, index) => ({ id: index, ...row }))}
                      columns={getGridColumns()}
                      pageSize={25}
                      rowsPerPageOptions={[25, 50, 100]}
                      disableSelectionOnClick
                      sx={{
                        border: 'none',
                        '& .MuiDataGrid-cell': {
                          borderColor: '#333',
                        },
                        '& .MuiDataGrid-columnHeaders': {
                          backgroundColor: '#2a2a2a',
                          borderColor: '#333',
                        },
                      }}
                    />
                  )}

                  {currentTab === 1 && (
                    <Box sx={{ height: '100%' }}>
                      <Editor
                        height="100%"
                        language="sql"
                        value={queryResult.sql_query}
                        theme="vs-dark"
                        options={{
                          readOnly: true,
                          minimap: { enabled: false },
                          fontSize: 14,
                          wordWrap: 'on',
                        }}
                      />
                    </Box>
                  )}

                  {currentTab === 2 && (
                    <ResultsVisualizer data={queryResult.results} />
                  )}

                  {currentTab === 3 && (
                    <Box sx={{ p: 2, height: '100%', overflow: 'auto' }}>
                      <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
                        {queryResult.explanation}
                      </Typography>
                    </Box>
                  )}
                </Box>
              </>
            ) : (
              <Box sx={{ 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center', 
                height: '100%',
                flexDirection: 'column',
                gap: 2,
                color: 'text.secondary'
              }}>
                <Database sx={{ fontSize: 64, opacity: 0.3 }} />
                <Typography variant="h6">
                  Ask a question to see results
                </Typography>
                <Typography variant="body2" textAlign="center">
                  Use natural language to query your database.<br />
                  AI will convert it to SQL and execute it for you.
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default QueryInterface;