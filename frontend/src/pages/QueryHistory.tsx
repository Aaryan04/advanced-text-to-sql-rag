import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Alert,
  Card,
  CardContent,
  Grid,
} from '@mui/material';
import {
  Visibility,
  ContentCopy,
  Delete,
  CheckCircle,
  Error,
  Speed,
  TrendingUp,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { format, formatDistanceToNow } from 'date-fns';
import Editor from '@monaco-editor/react';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import toast from 'react-hot-toast';

import { getQueryHistory, QueryHistoryEntry } from '../utils/api';

const QueryHistory: React.FC = () => {
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [selectedQuery, setSelectedQuery] = useState<QueryHistoryEntry | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  const {
    data: history,
    isLoading,
    error,
    refetch,
  } = useQuery('queryHistory', () => getQueryHistory(100));

  const handleViewQuery = (query: QueryHistoryEntry) => {
    setSelectedQuery(query);
    setDialogOpen(true);
  };

  const handleCopySQL = (sql: string) => {
    navigator.clipboard.writeText(sql);
    toast.success('SQL copied to clipboard');
  };

  const handleCopyQuestion = (question: string) => {
    navigator.clipboard.writeText(question);
    toast.success('Question copied to clipboard');
  };

  const getStatusColor = (success: boolean) => {
    return success ? 'success' : 'error';
  };

  const getComplexityColor = (complexity: string) => {
    switch (complexity?.toLowerCase()) {
      case 'simple':
        return 'success';
      case 'medium':
        return 'warning';
      case 'complex':
        return 'error';
      default:
        return 'default';
    }
  };

  const columns: GridColDef[] = [
    {
      field: 'created_at',
      headerName: 'Time',
      width: 120,
      valueFormatter: (params) => {
        return formatDistanceToNow(new Date(params.value), { addSuffix: true });
      },
    },
    {
      field: 'question',
      headerName: 'Question',
      flex: 1,
      minWidth: 200,
      renderCell: (params) => (
        <Tooltip title={params.value}>
          <Typography
            variant="body2"
            sx={{
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              maxWidth: '100%',
            }}
          >
            {params.value}
          </Typography>
        </Tooltip>
      ),
    },
    {
      field: 'success',
      headerName: 'Status',
      width: 100,
      renderCell: (params) => (
        <Chip
          icon={params.value ? <CheckCircle /> : <Error />}
          label={params.value ? 'Success' : 'Failed'}
          color={getStatusColor(params.value)}
          size="small"
        />
      ),
    },
    {
      field: 'results_count',
      headerName: 'Rows',
      width: 80,
      type: 'number',
    },
    {
      field: 'execution_time',
      headerName: 'Time (ms)',
      width: 100,
      valueFormatter: (params) => {
        return `${(params.value * 1000).toFixed(0)}ms`;
      },
    },
    {
      field: 'confidence_score',
      headerName: 'Confidence',
      width: 120,
      renderCell: (params) => (
        <Chip
          label={`${Math.round(params.value * 100)}%`}
          color={params.value > 0.8 ? 'success' : params.value > 0.6 ? 'warning' : 'error'}
          size="small"
        />
      ),
    },
    {
      field: 'metadata',
      headerName: 'Complexity',
      width: 120,
      renderCell: (params) => {
        const complexity = params.value?.complexity || 'unknown';
        return (
          <Chip
            label={complexity}
            color={getComplexityColor(complexity)}
            size="small"
            variant="outlined"
          />
        );
      },
    },
    {
      field: 'actions',
      headerName: 'Actions',
      width: 120,
      renderCell: (params) => (
        <Box>
          <Tooltip title="View details">
            <IconButton
              size="small"
              onClick={() => handleViewQuery(params.row)}
            >
              <Visibility />
            </IconButton>
          </Tooltip>
          <Tooltip title="Copy SQL">
            <IconButton
              size="small"
              onClick={() => handleCopySQL(params.row.sql_query)}
            >
              <ContentCopy />
            </IconButton>
          </Tooltip>
        </Box>
      ),
    },
  ];

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          Failed to load query history: {(error as Error).message}
        </Alert>
      </Box>
    );
  }

  const successfulQueries = history?.filter(q => q.success).length || 0;
  const failedQueries = history?.filter(q => !q.success).length || 0;
  const avgExecutionTime = history?.length ? 
    history.reduce((sum, q) => sum + q.execution_time, 0) / history.length * 1000 : 0;
  const avgConfidence = history?.length ?
    history.reduce((sum, q) => sum + q.confidence_score, 0) / history.length * 100 : 0;

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column', p: 2 }}>
      <Typography variant="h4" gutterBottom>
        Query History
      </Typography>

      {/* Statistics Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <CheckCircle color="success" sx={{ mr: 1 }} />
                <Box>
                  <Typography variant="h6">{successfulQueries}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Successful Queries
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Error color="error" sx={{ mr: 1 }} />
                <Box>
                  <Typography variant="h6">{failedQueries}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Failed Queries
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Speed color="primary" sx={{ mr: 1 }} />
                <Box>
                  <Typography variant="h6">{avgExecutionTime.toFixed(0)}ms</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Avg Execution Time
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <TrendingUp color="secondary" sx={{ mr: 1 }} />
                <Box>
                  <Typography variant="h6">{avgConfidence.toFixed(0)}%</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Avg Confidence
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* History Table */}
      <Paper sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        <DataGrid
          rows={history || []}
          columns={columns}
          pageSize={rowsPerPage}
          rowsPerPageOptions={[10, 25, 50, 100]}
          onPageSizeChange={(newSize) => setRowsPerPage(newSize)}
          disableSelectionOnClick
          loading={isLoading}
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
      </Paper>

      {/* Query Detail Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            Query Details
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Chip
                icon={selectedQuery?.success ? <CheckCircle /> : <Error />}
                label={selectedQuery?.success ? 'Success' : 'Failed'}
                color={selectedQuery?.success ? 'success' : 'error'}
                size="small"
              />
              {selectedQuery?.metadata?.complexity && (
                <Chip
                  label={selectedQuery.metadata.complexity}
                  color={getComplexityColor(selectedQuery.metadata.complexity)}
                  size="small"
                  variant="outlined"
                />
              )}
            </Box>
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedQuery && (
            <Box>
              <Typography variant="h6" gutterBottom>
                Question
              </Typography>
              <Paper sx={{ p: 2, mb: 2, bgcolor: 'background.default' }}>
                <Typography variant="body1">
                  {selectedQuery.question}
                </Typography>
                <IconButton
                  size="small"
                  onClick={() => handleCopyQuestion(selectedQuery.question)}
                  sx={{ float: 'right' }}
                >
                  <ContentCopy />
                </IconButton>
              </Paper>

              <Typography variant="h6" gutterBottom>
                Generated SQL
              </Typography>
              <Box sx={{ height: 200, mb: 2, border: '1px solid #333', borderRadius: 1 }}>
                <Editor
                  height="100%"
                  language="sql"
                  value={selectedQuery.sql_query}
                  theme="vs-dark"
                  options={{
                    readOnly: true,
                    minimap: { enabled: false },
                    fontSize: 12,
                  }}
                />
              </Box>

              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Execution Time: {(selectedQuery.execution_time * 1000).toFixed(0)}ms
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Results: {selectedQuery.results_count} rows
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Confidence: {Math.round(selectedQuery.confidence_score * 100)}%
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="text.secondary">
                    Created: {format(new Date(selectedQuery.created_at), 'PPpp')}
                  </Typography>
                </Grid>
              </Grid>

              {selectedQuery.error_message && (
                <>
                  <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                    Error Message
                  </Typography>
                  <Alert severity="error">
                    {selectedQuery.error_message}
                  </Alert>
                </>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Close</Button>
          {selectedQuery && (
            <Button
              onClick={() => handleCopySQL(selectedQuery.sql_query)}
              startIcon={<ContentCopy />}
            >
              Copy SQL
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default QueryHistory;