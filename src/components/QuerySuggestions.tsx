import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  IconButton,
  Collapse,
  Chip,
} from '@mui/material';
import {
  ExpandMore,
  ExpandLess,
  TrendingUp,
  Speed,
  Analytics,
  Group,
} from '@mui/icons-material';

interface QuerySuggestionsProps {
  onSelectSuggestion: (suggestion: string) => void;
}

const QuerySuggestions: React.FC<QuerySuggestionsProps> = ({ onSelectSuggestion }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const suggestionCategories = [
    {
      category: 'Basic Queries',
      icon: <Speed />,
      color: 'primary',
      suggestions: [
        'Show all employees',
        'List all departments',
        'Count total number of projects',
        'Show active projects only',
      ],
    },
    {
      category: 'Analytics',
      icon: <Analytics />,
      color: 'secondary',
      suggestions: [
        'Average salary by department',
        'Total sales by region',
        'Employee count per department',
        'Project budget distribution',
      ],
    },
    {
      category: 'Complex Queries',
      icon: <TrendingUp />,
      color: 'warning',
      suggestions: [
        'Top 5 highest paid employees with their departments',
        'Employees working on multiple active projects',
        'Departments with budget over average',
        'Sales performance compared to last year',
      ],
    },
    {
      category: 'Relationships',
      icon: <Group />,
      color: 'success',
      suggestions: [
        'Employees and their managers',
        'Projects assigned to each employee',
        'Department managers and their team sizes',
        'Sales representatives and their territories',
      ],
    },
  ];

  return (
    <Box sx={{ mt: 2 }}>
      <Box
        sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          cursor: 'pointer',
          mb: 1,
        }}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <Typography variant="subtitle2">
          Smart Suggestions
        </Typography>
        <IconButton size="small">
          {isExpanded ? <ExpandLess /> : <ExpandMore />}
        </IconButton>
      </Box>

      <Collapse in={isExpanded}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
          {suggestionCategories.map((category, categoryIndex) => (
            <Card
              key={categoryIndex}
              sx={{
                bgcolor: 'background.paper',
                border: '1px solid #333',
              }}
            >
              <CardContent sx={{ pb: '16px !important' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  {React.cloneElement(category.icon, { 
                    sx: { mr: 1, fontSize: 18 } 
                  })}
                  <Typography variant="body2" fontWeight="bold">
                    {category.category}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                  {category.suggestions.map((suggestion, suggestionIndex) => (
                    <Chip
                      key={suggestionIndex}
                      label={suggestion}
                      variant="outlined"
                      size="small"
                      color={category.color as any}
                      onClick={() => onSelectSuggestion(suggestion)}
                      sx={{
                        cursor: 'pointer',
                        justifyContent: 'flex-start',
                        height: 'auto',
                        py: 0.5,
                        '&:hover': {
                          backgroundColor: `${category.color}.dark`,
                          opacity: 0.8,
                        },
                      }}
                    />
                  ))}
                </Box>
              </CardContent>
            </Card>
          ))}
        </Box>
      </Collapse>
    </Box>
  );
};

export default QuerySuggestions;