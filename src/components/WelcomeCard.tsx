import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  Grid,
  Icon,
  alpha,
  useTheme
} from '@mui/material';
import {
  AutoAwesome,
  Security,
  Speed,
  Psychology,
  Code,
  Analytics
} from '@mui/icons-material';

const WelcomeCard: React.FC = () => {
  const theme = useTheme();

  const features = [
    {
      icon: <Psychology />,
      title: 'Natural Language',
      description: 'Ask questions in plain English, get SQL results instantly'
    },
    {
      icon: <AutoAwesome />,
      title: 'AI-Powered',
      description: 'Advanced RAG system with LangChain & LangGraph'
    },
    {
      icon: <Security />,
      title: 'Secure',
      description: 'Built-in SQL injection prevention and validation'
    },
    {
      icon: <Speed />,
      title: 'Real-time',
      description: 'Instant query execution with live results'
    },
    {
      icon: <Code />,
      title: 'SQL Generation',
      description: 'See the generated SQL with syntax highlighting'
    },
    {
      icon: <Analytics />,
      title: 'Analytics',
      description: 'Confidence scores and performance metrics'
    }
  ];

  const examples = [
    "Show me all employees in the Engineering department",
    "What's the average salary by department?", 
    "Find the top 5 highest paid employees",
    "List all active projects with their budgets",
    "Show sales data for the current year",
    "Which departments have the most employees?"
  ];

  return (
    <Card
      sx={{
        mb: 3,
        background: `linear-gradient(135deg, ${alpha(theme.palette.primary.main, 0.1)} 0%, ${alpha(theme.palette.secondary.main, 0.1)} 100%)`,
        border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`,
        borderRadius: 3,
      }}
    >
      <CardContent sx={{ p: 4 }}>
        <Box sx={{ textAlign: 'center', mb: 4 }}>
          <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 2 }}>
            🚀 Welcome to SQL Assistant
          </Typography>
          <Typography variant="h6" color="text.secondary" sx={{ mb: 3 }}>
            Transform natural language into powerful SQL queries with AI
          </Typography>
          <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1, flexWrap: 'wrap' }}>
            <Chip label="LangChain" color="primary" variant="outlined" />
            <Chip label="LangGraph" color="primary" variant="outlined" />
            <Chip label="RAG System" color="secondary" variant="outlined" />
            <Chip label="Real-time" color="success" variant="outlined" />
          </Box>
        </Box>

        <Grid container spacing={3} sx={{ mb: 4 }}>
          {features.map((feature, index) => (
            <Grid item xs={12} sm={6} md={4} key={index}>
              <Box
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 2,
                  p: 2,
                  borderRadius: 2,
                  bgcolor: alpha(theme.palette.background.paper, 0.5),
                  border: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    bgcolor: alpha(theme.palette.primary.main, 0.1),
                    transform: 'translateY(-2px)',
                  }
                }}
              >
                <Icon
                  sx={{
                    color: theme.palette.primary.main,
                    fontSize: 32,
                  }}
                >
                  {feature.icon}
                </Icon>
                <Box>
                  <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                    {feature.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {feature.description}
                  </Typography>
                </Box>
              </Box>
            </Grid>
          ))}
        </Grid>

        <Box sx={{ textAlign: 'center' }}>
          <Typography variant="h6" sx={{ mb: 2, color: 'text.secondary' }}>
            💡 Try these example queries:
          </Typography>
          <Box sx={{ display: 'flex', justifyContent: 'center', flexWrap: 'wrap', gap: 1 }}>
            {examples.map((example, index) => (
              <Chip
                key={index}
                label={example}
                sx={{
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  '&:hover': {
                    bgcolor: theme.palette.primary.main,
                    color: 'white',
                    transform: 'scale(1.05)',
                  },
                }}
              />
            ))}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

export default WelcomeCard;