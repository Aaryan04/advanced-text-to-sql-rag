import React, { useState, useRef, useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline, Box, Paper, TextField, IconButton, Typography, Avatar, CircularProgress, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Accordion, AccordionSummary, AccordionDetails, Chip } from '@mui/material';
import { Send as SendIcon, Person as PersonIcon, SmartToy as BotIcon, ExpandMore as ExpandMoreIcon, Code as CodeIcon, PlayArrow as RunIcon, ContentCopy as CopyIcon } from '@mui/icons-material';
import { Toaster } from 'react-hot-toast';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      refetchOnWindowFocus: false,
    },
  },
});

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
  typography: {
    fontFamily: '"JetBrains Mono", "Roboto Mono", monospace',
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
  },
});

interface ChatMessage {
  id: string;
  type: 'user' | 'bot';
  content: string;
  timestamp: Date;
  isLoading?: boolean;
  sqlQuery?: string;
  results?: any[];
}

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      type: 'bot',
      content: "Hello! I'm your Text-to-SQL assistant. Ask me anything about the database - I can help you find employees, analyze sales data, or generate any SQL query you need.",
      timestamp: new Date(),
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue,
      timestamp: new Date(),
    };

    const loadingMessage: ChatMessage = {
      id: (Date.now() + 1).toString(),
      type: 'bot',
      content: 'Analyzing your query and generating SQL...',
      timestamp: new Date(),
      isLoading: true,
    };

    setMessages(prev => [...prev, userMessage, loadingMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: inputValue,
          include_explanation: true,
          max_results: 50,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      const botResponse: ChatMessage = {
        id: (Date.now() + 2).toString(),
        type: 'bot',
        content: data.explanation || 'Here are the results for your query.',
        timestamp: new Date(),
        sqlQuery: data.sql_query,
        results: data.results,
      };

      setMessages(prev => prev.slice(0, -1).concat([botResponse]));
    } catch (error) {
      // Mock response for demo purposes when backend is not available
      const mockResponses = [
        "I'd be happy to help you with that query! Here's what I found: Based on your request, I would generate a SQL query like `SELECT * FROM employees WHERE department = 'Sales'` to fetch the relevant data from your database.",
        "Great question! For that type of analysis, I would use an aggregate query such as `SELECT department, AVG(salary) FROM employees GROUP BY department` to calculate the average salary by department.",
        "To find the top performers, I would recommend using `SELECT * FROM employees ORDER BY salary DESC LIMIT 5` which will show you the highest paid employees in your organization.",
        "For that data, I would query the projects table with something like `SELECT * FROM projects WHERE status = 'active'` to get all currently active projects.",
        "That's an interesting analysis! I would use `SELECT COUNT(*) as employee_count, department FROM employees GROUP BY department ORDER BY employee_count DESC` to see department sizes."
      ];
      
      const randomResponse = mockResponses[Math.floor(Math.random() * mockResponses.length)];
      
      const mockResponse: ChatMessage = {
        id: (Date.now() + 2).toString(),
        type: 'bot',
        content: randomResponse,
        timestamp: new Date(),
      };

      setMessages(prev => prev.slice(0, -1).concat([mockResponse]));
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Paper
        elevation={2}
        sx={{
          p: 2,
          borderRadius: 0,
          borderBottom: '1px solid #333',
        }}
      >
        <Typography variant="h5" sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: 1 }}>
          <BotIcon color="primary" />
          SQL Assistant
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Ask me anything about your database in natural language
        </Typography>
      </Paper>

      {/* Messages */}
      <Box
        sx={{
          flex: 1,
          overflow: 'auto',
          p: 2,
          bgcolor: '#0a0a0a',
        }}
      >
        {messages.map((message) => {
          const isUser = message.type === 'user';
          return (
            <Box
              key={message.id}
              sx={{
                display: 'flex',
                flexDirection: isUser ? 'row-reverse' : 'row',
                alignItems: 'flex-start',
                mb: 3,
                gap: 2,
              }}
            >
              <Avatar
                sx={{
                  bgcolor: isUser ? '#2196f3' : '#f50057',
                  width: 40,
                  height: 40,
                }}
              >
                {isUser ? <PersonIcon /> : <BotIcon />}
              </Avatar>

              <Box sx={{ flex: 1, maxWidth: '80%' }}>
                <Paper
                  elevation={1}
                  sx={{
                    p: 2,
                    bgcolor: isUser ? '#2196f3' : '#1a1a1a',
                    color: isUser ? 'white' : 'inherit',
                    borderRadius: 2,
                  }}
                >
                  {message.isLoading ? (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <CircularProgress size={20} />
                      <Typography variant="body1">{message.content}</Typography>
                    </Box>
                  ) : (
                    <>
                      <Typography variant="body1" sx={{ mb: message.sqlQuery ? 1 : 0 }}>
                        {message.content}
                      </Typography>

                      {message.sqlQuery && (
                        <Box sx={{ mt: 2 }}>
                          <Accordion defaultExpanded>
                            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <CodeIcon fontSize="small" />
                                <Typography variant="subtitle2">Generated SQL</Typography>
                              </Box>
                            </AccordionSummary>
                            <AccordionDetails>
                              <Box sx={{ position: 'relative' }}>
                                <IconButton
                                  size="small"
                                  onClick={() => copyToClipboard(message.sqlQuery!)}
                                  sx={{
                                    position: 'absolute',
                                    top: 8,
                                    right: 8,
                                    zIndex: 1,
                                    bgcolor: 'rgba(0,0,0,0.5)',
                                    color: 'white',
                                    '&:hover': { bgcolor: 'rgba(0,0,0,0.7)' }
                                  }}
                                >
                                  <CopyIcon fontSize="small" />
                                </IconButton>
                                <Paper sx={{ p: 2, bgcolor: '#1e1e1e', borderRadius: 1 }}>
                                  <Typography 
                                    component="pre" 
                                    sx={{ 
                                      fontFamily: 'monospace', 
                                      fontSize: '0.875rem',
                                      color: '#61dafb',
                                      whiteSpace: 'pre-wrap',
                                      margin: 0
                                    }}
                                  >
                                    {message.sqlQuery}
                                  </Typography>
                                </Paper>
                              </Box>
                            </AccordionDetails>
                          </Accordion>
                        </Box>
                      )}

                      {message.results && message.results.length > 0 && (
                        <Box sx={{ mt: 2 }}>
                          <Accordion>
                            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <RunIcon fontSize="small" />
                                <Typography variant="subtitle2">
                                  Query Results ({message.results.length} rows)
                                </Typography>
                              </Box>
                            </AccordionSummary>
                            <AccordionDetails>
                              <TableContainer component={Paper} sx={{ maxHeight: 400 }}>
                                <Table stickyHeader size="small">
                                  <TableHead>
                                    <TableRow>
                                      {Object.keys(message.results[0]).map((column) => (
                                        <TableCell key={column} sx={{ fontWeight: 'bold', bgcolor: '#333' }}>
                                          {column}
                                        </TableCell>
                                      ))}
                                    </TableRow>
                                  </TableHead>
                                  <TableBody>
                                    {message.results.slice(0, 10).map((row, index) => (
                                      <TableRow key={index} hover>
                                        {Object.values(row).map((value, cellIndex) => (
                                          <TableCell key={cellIndex}>
                                            {typeof value === 'number' 
                                              ? value.toLocaleString() 
                                              : String(value)
                                            }
                                          </TableCell>
                                        ))}
                                      </TableRow>
                                    ))}
                                  </TableBody>
                                </Table>
                              </TableContainer>
                              {message.results.length > 10 && (
                                <Typography variant="caption" sx={{ mt: 1, display: 'block' }}>
                                  Showing first 10 of {message.results.length} results
                                </Typography>
                              )}
                            </AccordionDetails>
                          </Accordion>
                        </Box>
                      )}
                    </>
                  )}
                </Paper>
              </Box>
            </Box>
          );
        })}
        <div ref={messagesEndRef} />
      </Box>

      {/* Input */}
      <Paper
        elevation={3}
        sx={{
          p: 2,
          borderRadius: 0,
          borderTop: '1px solid #333',
          bgcolor: '#1a1a1a',
        }}
      >
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
          <TextField
            fullWidth
            multiline
            maxRows={4}
            placeholder="Ask me about your database... (e.g., 'Show all employees in Sales')"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={isLoading}
            variant="outlined"
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 3,
                bgcolor: '#0a0a0a',
              },
            }}
          />
          <IconButton
            color="primary"
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isLoading}
            sx={{
              bgcolor: inputValue.trim() && !isLoading ? '#2196f3' : 'rgba(255,255,255,0.1)',
              color: 'white',
              borderRadius: 3,
              width: 48,
              height: 48,
            }}
          >
            {isLoading ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
          </IconButton>
        </Box>
      </Paper>
    </Box>
  );
};

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={darkTheme}>
        <CssBaseline />
        <ChatInterface />
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: '#1a1a1a',
              color: '#fff',
              border: '1px solid #333',
            },
          }}
        />
      </ThemeProvider>
    </QueryClientProvider>
  </React.StrictMode>
);