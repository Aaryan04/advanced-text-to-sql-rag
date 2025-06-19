import React, { useMemo } from 'react';
import { Box, Typography, Paper, Grid } from '@mui/material';
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
  ScatterChart,
  Scatter,
  ResponsiveContainer,
} from 'recharts';

interface ResultsVisualizerProps {
  data: any[];
}

const COLORS = ['#2196f3', '#f50057', '#4caf50', '#ff9800', '#9c27b0', '#00bcd4', '#cddc39', '#795548'];

const ResultsVisualizer: React.FC<ResultsVisualizerProps> = ({ data }) => {
  const analysisResult = useMemo(() => {
    if (!data || data.length === 0) {
      return { chartType: 'none', chartData: [], numericColumns: [], categoricalColumns: [] };
    }

    const firstRow = data[0];
    const columns = Object.keys(firstRow);
    
    const numericColumns = columns.filter(col => {
      const sampleValues = data.slice(0, 10).map(row => row[col]);
      return sampleValues.every(val => val !== null && val !== undefined && !isNaN(Number(val)));
    });

    const categoricalColumns = columns.filter(col => {
      const uniqueValues = new Set(data.map(row => row[col]));
      return uniqueValues.size <= Math.min(20, data.length * 0.8) && uniqueValues.size > 1;
    });

    let chartType = 'table';
    let chartData = data;

    // Determine best chart type based on data structure
    if (numericColumns.length >= 1 && categoricalColumns.length >= 1) {
      // Bar chart for categorical vs numeric
      chartType = 'bar';
      const categoryCol = categoricalColumns[0];
      const numericCol = numericColumns[0];
      
      const aggregated = data.reduce((acc, row) => {
        const key = row[categoryCol];
        if (!acc[key]) {
          acc[key] = { name: key, [numericCol]: 0, count: 0 };
        }
        acc[key][numericCol] += Number(row[numericCol]) || 0;
        acc[key].count += 1;
        return acc;
      }, {} as any);

      chartData = Object.values(aggregated).map((item: any) => ({
        ...item,
        [numericCol]: item[numericCol] / item.count, // Average
      }));
    } else if (numericColumns.length >= 2) {
      // Scatter plot for numeric vs numeric
      chartType = 'scatter';
      chartData = data.map((row, index) => ({
        x: Number(row[numericColumns[0]]) || 0,
        y: Number(row[numericColumns[1]]) || 0,
        id: index,
      }));
    } else if (categoricalColumns.length === 1 && data.length <= 20) {
      // Pie chart for single categorical with small dataset
      chartType = 'pie';
      const categoryCol = categoricalColumns[0];
      const counts = data.reduce((acc, row) => {
        const key = row[categoryCol];
        acc[key] = (acc[key] || 0) + 1;
        return acc;
      }, {} as any);

      chartData = Object.entries(counts).map(([name, value]) => ({
        name,
        value: value as number,
      }));
    } else if (numericColumns.length >= 1 && data.length > 5) {
      // Line chart for time series or ordered data
      chartType = 'line';
      chartData = data.map((row, index) => ({
        index,
        value: Number(row[numericColumns[0]]) || 0,
        name: row[columns[0]] || `Row ${index + 1}`,
      }));
    }

    return { chartType, chartData, numericColumns, categoricalColumns };
  }, [data]);

  const renderChart = () => {
    const { chartType, chartData, numericColumns, categoricalColumns } = analysisResult;

    switch (chartType) {
      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="name" stroke="#ccc" />
              <YAxis stroke="#ccc" />
              <Tooltip
                contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
              />
              <Legend />
              <Bar dataKey={numericColumns[0]} fill={COLORS[0]} />
            </BarChart>
          </ResponsiveContainer>
        );

      case 'line':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="index" stroke="#ccc" />
              <YAxis stroke="#ccc" />
              <Tooltip
                contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
              />
              <Legend />
              <Line type="monotone" dataKey="value" stroke={COLORS[0]} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        );

      case 'pie':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={120}
                fill="#8884d8"
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
              />
            </PieChart>
          </ResponsiveContainer>
        );

      case 'scatter':
        return (
          <ResponsiveContainer width="100%" height={400}>
            <ScatterChart margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="x" stroke="#ccc" name={numericColumns[0]} />
              <YAxis dataKey="y" stroke="#ccc" name={numericColumns[1]} />
              <Tooltip
                cursor={{ strokeDasharray: '3 3' }}
                contentStyle={{ backgroundColor: '#1a1a1a', border: '1px solid #333' }}
              />
              <Scatter data={chartData} fill={COLORS[0]} />
            </ScatterChart>
          </ResponsiveContainer>
        );

      default:
        return (
          <Box sx={{ p: 3, textAlign: 'center', color: 'text.secondary' }}>
            <Typography variant="h6" gutterBottom>
              No suitable visualization found
            </Typography>
            <Typography variant="body2">
              The data structure doesn't match common visualization patterns.
              Try the Results tab to view the raw data.
            </Typography>
          </Box>
        );
    }
  };

  const getDataInsights = () => {
    if (!data || data.length === 0) return null;

    const { numericColumns, categoricalColumns } = analysisResult;
    const insights = [];

    insights.push(`${data.length} rows of data`);
    
    if (numericColumns.length > 0) {
      insights.push(`${numericColumns.length} numeric columns`);
    }
    
    if (categoricalColumns.length > 0) {
      insights.push(`${categoricalColumns.length} categorical columns`);
    }

    return insights;
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ p: 2, borderBottom: '1px solid #333' }}>
        <Typography variant="h6" gutterBottom>
          Data Visualization
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          {getDataInsights()?.map((insight, index) => (
            <Typography
              key={index}
              variant="caption"
              sx={{
                bgcolor: 'primary.dark',
                px: 1,
                py: 0.5,
                borderRadius: 1,
                fontSize: '0.75rem',
              }}
            >
              {insight}
            </Typography>
          ))}
        </Box>
      </Box>
      
      <Box sx={{ flex: 1, p: 2 }}>
        {renderChart()}
      </Box>
    </Box>
  );
};

export default ResultsVisualizer;