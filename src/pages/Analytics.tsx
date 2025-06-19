import React from 'react';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  Alert,
} from '@mui/material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
} from 'recharts';
import { useQuery } from '@tanstack/react-query';
import { getQueryHistory, QueryHistoryEntry } from '../utils/api';

const COLORS = ['#2196f3', '#f50057', '#4caf50', '#ff9800', '#9c27b0'];

const Analytics: React.FC = () => {
  const {
    data: history,
    isLoading,
    error,
  } = useQuery('queryHistory', () => getQueryHistory(500));

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          Failed to load analytics data: {(error as Error).message}
        </Alert>
      </Box>
    );
  }

  if (isLoading) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography>Loading analytics...</Typography>
      </Box>
    );
  }

  // Process data for analytics
  const processAnalyticsData = (history: QueryHistoryEntry[]) => {
    // Query success rate over time
    const dailyStats = history.reduce((acc, query) => {
      const date = new Date(query.created_at).toDateString();
      if (!acc[date]) {
        acc[date] = { date, total: 0, successful: 0, failed: 0 };
      }
      acc[date].total++;
      if (query.success) {
        acc[date].successful++;
      } else {
        acc[date].failed++;
      }
      return acc;
    }, {} as any);

    const timeSeriesData = Object.values(dailyStats)
      .sort((a: any, b: any) => new Date(a.date).getTime() - new Date(b.date).getTime())
      .slice(-30); // Last 30 days

    // Complexity distribution
    const complexityStats = history.reduce((acc, query) => {
      const complexity = query.metadata?.complexity || 'unknown';
      acc[complexity] = (acc[complexity] || 0) + 1;
      return acc;
    }, {} as any);

    const complexityData = Object.entries(complexityStats).map(([name, value]) => ({
      name: name.charAt(0).toUpperCase() + name.slice(1),
      value: value as number,
    }));

    // Performance metrics
    const performanceData = history
      .filter(q => q.success)
      .slice(-50)
      .map((query, index) => ({
        index,
        executionTime: query.execution_time * 1000,
        confidence: query.confidence_score * 100,
        resultsCount: query.results_count,
      }));

    // Error analysis
    const errorStats = history
      .filter(q => !q.success)
      .reduce((acc, query) => {
        const errorType = query.error_message?.split(':')[0] || 'Unknown Error';
        acc[errorType] = (acc[errorType] || 0) + 1;
        return acc;
      }, {} as any);

    const errorData = Object.entries(errorStats)
      .map(([name, value]) => ({ name, value: value as number }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 5);

    return {
      timeSeriesData,
      complexityData,
      performanceData,
      errorData,
      totalQueries: history.length,
      successRate: history.length ? (history.filter(q => q.success).length / history.length) * 100 : 0,
      avgExecutionTime: history.length ? history.reduce((sum, q) => sum + q.execution_time, 0) / history.length * 1000 : 0,
      avgConfidence: history.length ? history.reduce((sum, q) => sum + q.confidence_score, 0) / history.length * 100 : 0,
    };
  };

  const analytics = processAnalyticsData(history || []);

  return (
    <Box sx={{ height: '100vh', overflow: 'auto', p: 2 }}>
      <Typography variant="h4" gutterBottom>
        Query Analytics Dashboard
      </Typography>

      {/* Summary Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h4" color="primary">
                {analytics.totalQueries}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Queries
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h4" color="success.main">
                {analytics.successRate.toFixed(1)}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Success Rate
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h4" color="info.main">
                {analytics.avgExecutionTime.toFixed(0)}ms
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Avg Execution Time
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h4" color="secondary.main">
                {analytics.avgConfidence.toFixed(0)}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Avg Confidence
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={2}>
        {/* Query Trends */}
        <Grid item xs={12} lg={8}>
          <Card sx={{ height: 400 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Query Trends (Last 30 Days)
              </Typography>
              <ResponsiveContainer width="100%" height={320}>
                <LineChart data={analytics.timeSeriesData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis 
                    dataKey="date" 
                    stroke="#ccc"
                    tickFormatter={(value) => new Date(value).toLocaleDateString()}
                  />
                  <YAxis stroke="#ccc" />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
                    labelFormatter={(value) => new Date(value).toLocaleDateString()}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="successful"
                    stroke={COLORS[2]}
                    strokeWidth={2}
                    name="Successful"
                  />
                  <Line
                    type="monotone"
                    dataKey="failed"
                    stroke={COLORS[1]}
                    strokeWidth={2}
                    name="Failed"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Complexity Distribution */}
        <Grid item xs={12} lg={4}>
          <Card sx={{ height: 400 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Query Complexity Distribution
              </Typography>
              <ResponsiveContainer width="100%" height={320}>
                <PieChart>
                  <Pie
                    data={analytics.complexityData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {analytics.complexityData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Performance Metrics */}
        <Grid item xs={12} lg={8}>
          <Card sx={{ height: 400 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Performance Metrics (Last 50 Successful Queries)
              </Typography>
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={analytics.performanceData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                  <XAxis dataKey="index" stroke="#ccc" />
                  <YAxis stroke="#ccc" />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
                  />
                  <Legend />
                  <Bar dataKey="executionTime" fill={COLORS[0]} name="Execution Time (ms)" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Error Analysis */}
        <Grid item xs={12} lg={4}>
          <Card sx={{ height: 400 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Common Error Types
              </Typography>
              {analytics.errorData.length > 0 ? (
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart data={analytics.errorData} layout="horizontal">
                    <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                    <XAxis type="number" stroke="#ccc" />
                    <YAxis dataKey="name" type="category" stroke="#ccc" width={100} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
                    />
                    <Bar dataKey="value" fill={COLORS[1]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <Box sx={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center', 
                  height: 320,
                  color: 'text.secondary'
                }}>
                  <Typography>No errors to analyze</Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Analytics;