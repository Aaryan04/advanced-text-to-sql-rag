import React from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box, Typography, Button } from '@mui/material';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#2196f3',
    },
    secondary: {
      main: '#f50057',
    },
    background: {
      default: '#0a0a0a',
      paper: '#1a1a1a',
    },
  },
});

function SimpleApp() {
  const handleTestAPI = async () => {
    try {
      const response = await fetch('http://localhost:8001/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: 'Show all employees in engineering'
        })
      });
      const data = await response.json();
      console.log('API Response:', data);
      alert('Check console for API response!');
    } catch (error) {
      console.error('API Error:', error);
      alert('API Error - check console');
    }
  };

  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Box sx={{ 
        minHeight: '100vh', 
        display: 'flex', 
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 3,
        p: 3
      }}>
        <Typography variant="h2" component="h1" textAlign="center">
          🧠 Advanced Text-to-SQL RAG System
        </Typography>
        
        <Typography variant="h5" color="text.secondary" textAlign="center">
          Powered by LangChain, LangGraph & Modern React
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center' }}>
          <Button 
            variant="contained" 
            size="large"
            onClick={handleTestAPI}
          >
            Test API Connection
          </Button>
          
          <Button 
            variant="outlined" 
            size="large"
            onClick={() => window.open('http://localhost:8001/health', '_blank')}
          >
            Backend Health
          </Button>
          
          <Button 
            variant="outlined" 
            size="large"
            onClick={() => window.open('http://localhost:8001/schema', '_blank')}
          >
            View Schema
          </Button>
        </Box>
        
        <Box sx={{ 
          mt: 4, 
          p: 3, 
          bgcolor: 'background.paper', 
          borderRadius: 2,
          maxWidth: 600,
          textAlign: 'center'
        }}>
          <Typography variant="h6" gutterBottom>
            ✅ System Status
          </Typography>
          <Typography variant="body1">
            • Backend API: Running on port 8001<br/>
            • Frontend UI: Running on port 3000<br/>
            • Database: SQLite with sample data<br/>
            • Mock AI: Intelligent query processing
          </Typography>
        </Box>
        
        <Box sx={{ 
          mt: 2, 
          p: 3, 
          bgcolor: 'primary.dark', 
          borderRadius: 2,
          maxWidth: 800,
          textAlign: 'center'
        }}>
          <Typography variant="h6" gutterBottom>
            🎯 Try These Sample Queries
          </Typography>
          <Typography variant="body2" component="div">
            • "Show all employees in engineering"<br/>
            • "What is the average salary by department?"<br/>
            • "Find the top 5 highest paid employees"<br/>
            • "List all departments with their budgets"
          </Typography>
        </Box>
      </Box>
    </ThemeProvider>
  );
}

export default SimpleApp;