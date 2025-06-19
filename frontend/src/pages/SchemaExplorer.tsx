import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Grid,
  IconButton,
  Tooltip,
  Alert,
} from '@mui/material';
import {
  ExpandMore,
  TableChart,
  Key,
  DataArray,
  Visibility,
  ContentCopy,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { getDatabaseSchema, getAllTables, DatabaseSchema } from '../utils/api';
import toast from 'react-hot-toast';

const SchemaExplorer: React.FC = () => {
  const [selectedTable, setSelectedTable] = useState<string | null>(null);

  const {
    data: tables,
    isLoading: tablesLoading,
    error: tablesError,
  } = useQuery('tables', getAllTables);

  const {
    data: schema,
    isLoading: schemaLoading,
    error: schemaError,
  } = useQuery(['schema', selectedTable], 
    () => getDatabaseSchema(selectedTable ? [selectedTable] : undefined),
    { enabled: !!selectedTable }
  );

  const {
    data: fullSchema,
    isLoading: fullSchemaLoading,
  } = useQuery('fullSchema', () => getDatabaseSchema());

  const handleCopyTableName = (tableName: string) => {
    navigator.clipboard.writeText(tableName);
    toast.success(`Table name "${tableName}" copied to clipboard`);
  };

  const handleCopyColumnName = (columnName: string) => {
    navigator.clipboard.writeText(columnName);
    toast.success(`Column name "${columnName}" copied to clipboard`);
  };

  const getTypeColor = (type: string) => {
    const lowerType = type.toLowerCase();
    if (lowerType.includes('int') || lowerType.includes('number') || lowerType.includes('decimal')) {
      return 'primary';
    }
    if (lowerType.includes('varchar') || lowerType.includes('text') || lowerType.includes('char')) {
      return 'secondary';
    }
    if (lowerType.includes('date') || lowerType.includes('time')) {
      return 'warning';
    }
    if (lowerType.includes('bool')) {
      return 'success';
    }
    return 'default';
  };

  if (tablesError) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          Failed to load database tables: {(tablesError as Error).message}
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column', p: 2 }}>
      <Typography variant="h4" gutterBottom>
        Database Schema Explorer
      </Typography>

      <Grid container spacing={2} sx={{ flex: 1, overflow: 'hidden' }}>
        {/* Left Panel - Tables List */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ height: '100%', display: 'flex', flexDirection: 'column', p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Tables ({tables?.length || 0})
            </Typography>
            
            <Box sx={{ flex: 1, overflow: 'auto' }}>
              {tablesLoading ? (
                <Typography>Loading tables...</Typography>
              ) : (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  {tables?.map((tableName) => (
                    <Card
                      key={tableName}
                      sx={{
                        cursor: 'pointer',
                        border: selectedTable === tableName ? '2px solid' : '1px solid #333',
                        borderColor: selectedTable === tableName ? 'primary.main' : '#333',
                        '&:hover': {
                          backgroundColor: 'action.hover',
                        },
                      }}
                      onClick={() => setSelectedTable(tableName)}
                    >
                      <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <TableChart sx={{ mr: 1, fontSize: 20 }} />
                            <Typography variant="body1" fontWeight="medium">
                              {tableName}
                            </Typography>
                          </Box>
                          <Tooltip title="Copy table name">
                            <IconButton
                              size="small"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleCopyTableName(tableName);
                              }}
                            >
                              <ContentCopy fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </Box>
                        {fullSchema?.[tableName] && (
                          <Typography variant="caption" color="text.secondary">
                            {fullSchema[tableName].columns.length} columns
                          </Typography>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </Box>
              )}
            </Box>
          </Paper>
        </Grid>

        {/* Right Panel - Table Details */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ height: '100%', display: 'flex', flexDirection: 'column', p: 2 }}>
            {selectedTable ? (
              <>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <TableChart sx={{ mr: 1 }} />
                  <Typography variant="h6">
                    {selectedTable}
                  </Typography>
                </Box>

                {schemaLoading || fullSchemaLoading ? (
                  <Typography>Loading schema...</Typography>
                ) : schemaError ? (
                  <Alert severity="error">
                    Failed to load schema: {(schemaError as Error).message}
                  </Alert>
                ) : (
                  <Box sx={{ flex: 1, overflow: 'auto' }}>
                    {/* Columns Table */}
                    <Accordion defaultExpanded>
                      <AccordionSummary expandIcon={<ExpandMore />}>
                        <Typography variant="h6">
                          Columns ({fullSchema?.[selectedTable]?.columns.length || 0})
                        </Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <TableContainer>
                          <Table size="small">
                            <TableHead>
                              <TableRow>
                                <TableCell>Name</TableCell>
                                <TableCell>Type</TableCell>
                                <TableCell>Nullable</TableCell>
                                <TableCell>Default</TableCell>
                                <TableCell>Actions</TableCell>
                              </TableRow>
                            </TableHead>
                            <TableBody>
                              {fullSchema?.[selectedTable]?.columns.map((column) => (
                                <TableRow key={column.name}>
                                  <TableCell>
                                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                      {column.name === 'id' && <Key sx={{ mr: 0.5, fontSize: 16, color: 'warning.main' }} />}
                                      <Typography variant="body2" fontFamily="monospace">
                                        {column.name}
                                      </Typography>
                                    </Box>
                                  </TableCell>
                                  <TableCell>
                                    <Chip
                                      label={column.type}
                                      size="small"
                                      color={getTypeColor(column.type) as any}
                                      variant="outlined"
                                    />
                                  </TableCell>
                                  <TableCell>
                                    <Chip
                                      label={column.nullable ? 'Yes' : 'No'}
                                      size="small"
                                      color={column.nullable ? 'warning' : 'success'}
                                      variant="outlined"
                                    />
                                  </TableCell>
                                  <TableCell>
                                    <Typography variant="body2" fontFamily="monospace">
                                      {column.default || '—'}
                                    </Typography>
                                  </TableCell>
                                  <TableCell>
                                    <Tooltip title="Copy column name">
                                      <IconButton
                                        size="small"
                                        onClick={() => handleCopyColumnName(column.name)}
                                      >
                                        <ContentCopy fontSize="small" />
                                      </IconButton>
                                    </Tooltip>
                                  </TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </TableContainer>
                      </AccordionDetails>
                    </Accordion>

                    {/* Sample Data */}
                    {fullSchema?.[selectedTable]?.sample_data?.length > 0 && (
                      <Accordion>
                        <AccordionSummary expandIcon={<ExpandMore />}>
                          <Typography variant="h6">
                            Sample Data ({fullSchema[selectedTable].sample_data.length} rows)
                          </Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                          <TableContainer>
                            <Table size="small">
                              <TableHead>
                                <TableRow>
                                  {fullSchema[selectedTable].columns.map((column) => (
                                    <TableCell key={column.name}>
                                      {column.name}
                                    </TableCell>
                                  ))}
                                </TableRow>
                              </TableHead>
                              <TableBody>
                                {fullSchema[selectedTable].sample_data.map((row, index) => (
                                  <TableRow key={index}>
                                    {fullSchema[selectedTable].columns.map((column) => (
                                      <TableCell key={column.name}>
                                        <Typography variant="body2" fontFamily="monospace">
                                          {row[column.name]?.toString() || '—'}
                                        </Typography>
                                      </TableCell>
                                    ))}
                                  </TableRow>
                                ))}
                              </TableBody>
                            </Table>
                          </TableContainer>
                        </AccordionDetails>
                      </Accordion>
                    )}
                  </Box>
                )}
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
                <DataArray sx={{ fontSize: 64, opacity: 0.3 }} />
                <Typography variant="h6">
                  Select a table to explore its schema
                </Typography>
                <Typography variant="body2" textAlign="center">
                  Choose a table from the left panel to view its<br />
                  columns, data types, and sample data.
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default SchemaExplorer;