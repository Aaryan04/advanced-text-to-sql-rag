import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  Avatar,
  Chip,
  Divider,
  CircularProgress,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Card,
  CardContent,
  Tooltip,
  Fade,
  useTheme
} from '@mui/material';
import {
  Send as SendIcon,
  Person as PersonIcon,
  SmartToy as BotIcon,
  ExpandMore as ExpandMoreIcon,
  ContentCopy as CopyIcon,
  PlayArrow as RunIcon,
  Code as CodeIcon,
  Assessment as AssessmentIcon,
  Schedule as ScheduleIcon,
  Security as SecurityIcon
} from '@mui/icons-material';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import WelcomeCard from '../components/WelcomeCard';

interface ChatMessage {
  id: string;
  type: 'user' | 'bot';
  content: string;
  timestamp: Date;
  sqlQuery?: string;
  results?: any[];
  metadata?: {
    confidence_score?: number;
    execution_time?: number;
    complexity?: string;
    validation_passed?: boolean;
  };
  isLoading?: boolean;
  error?: string;
}

const ChatInterface: React.FC = () => {
  const theme = useTheme();
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      type: 'bot',
      content: "Hello! I'm your Text-to-SQL assistant. Ask me anything about the database - I can help you find employees, analyze sales data, explore projects, or generate any SQL query you need. Try asking something like 'Show me all employees in Engineering' or 'What's the average salary by department?'",
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
      const response = await fetch('http://localhost:8001/query', {
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
        content: data.explanation || 'Here are the results for your query:',
        timestamp: new Date(),
        sqlQuery: data.sql_query,
        results: data.results,
        metadata: data.metadata || {
          confidence_score: data.confidence_score,
          execution_time: data.execution_time,
        },
      };

      setMessages(prev => prev.slice(0, -1).concat([botResponse]));
    } catch (error) {
      const errorMessage: ChatMessage = {
        id: (Date.now() + 2).toString(),
        type: 'bot',
        content: 'I apologize, but I encountered an error processing your request.',
        timestamp: new Date(),
        error: error instanceof Error ? error.message : 'Unknown error occurred',
      };

      setMessages(prev => prev.slice(0, -1).concat([errorMessage]));
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

  const renderMessage = (message: ChatMessage) => {
    const isUser = message.type === 'user';

    return (
      <Fade in timeout={500} key={message.id}>
        <Box
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
              bgcolor: isUser ? theme.palette.primary.main : theme.palette.secondary.main,
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
                bgcolor: isUser 
                  ? theme.palette.primary.dark 
                  : theme.palette.background.paper,
                color: isUser ? 'white' : 'inherit',
                borderRadius: 2,
                position: 'relative',
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

                  {message.error && (
                    <Alert severity="error" sx={{ mt: 1 }}>
                      {message.error}
                    </Alert>
                  )}

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
                            <Tooltip title="Copy SQL">
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
                            </Tooltip>
                            <SyntaxHighlighter
                              language="sql"
                              style={oneDark}
                              customStyle={{
                                margin: 0,
                                borderRadius: 8,
                                fontSize: '14px'
                              }}
                            >
                              {message.sqlQuery}
                            </SyntaxHighlighter>
                          </Box>
                        </AccordionDetails>
                      </Accordion>
                    </Box>
                  )}

                  {message.metadata && (
                    <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      {message.metadata.confidence_score && (
                        <Chip
                          icon={<AssessmentIcon />}
                          label={`Confidence: ${(message.metadata.confidence_score * 100).toFixed(0)}%`}
                          size="small"
                          color={message.metadata.confidence_score > 0.8 ? 'success' : 'warning'}
                        />
                      )}
                      {message.metadata.execution_time && (
                        <Chip
                          icon={<ScheduleIcon />}
                          label={`${(message.metadata.execution_time * 1000).toFixed(1)}ms`}
                          size="small"
                        />
                      )}
                      {message.metadata.complexity && (
                        <Chip
                          label={message.metadata.complexity}
                          size="small"
                          variant="outlined"
                        />
                      )}
                      {message.metadata.validation_passed && (
                        <Chip
                          icon={<SecurityIcon />}
                          label="Validated"
                          size="small"
                          color="success"
                        />
                      )}
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
                                    <TableCell key={column} sx={{ fontWeight: 'bold' }}>
                                      {column}
                                    </TableCell>
                                  ))}
                                </TableRow>
                              </TableHead>
                              <TableBody>
                                {message.results.slice(0, 20).map((row, index) => (
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
                          {message.results.length > 20 && (
                            <Typography variant="caption" sx={{ mt: 1, display: 'block' }}>
                              Showing first 20 of {message.results.length} results
                            </Typography>
                          )}
                        </AccordionDetails>
                      </Accordion>
                    </Box>
                  )}
                </>
              )}

              <Typography
                variant="caption"
                sx={{
                  position: 'absolute',
                  bottom: -20,
                  [isUser ? 'right' : 'left']: 8,
                  color: 'text.secondary',
                }}
              >
                {message.timestamp.toLocaleTimeString()}
              </Typography>
            </Paper>
          </Box>
        </Box>
      </Fade>
    );
  };

  const quickSuggestions = [
    "Show all employees in Engineering",
    "What's the average salary by department?",
    "List all active projects",
    "Find top 5 highest paid employees",
    "Show sales data for this year",
    "Which departments have the most employees?"
  ];

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Paper
        elevation={2}
        sx={{
          p: 2,
          borderRadius: 0,
          borderBottom: `1px solid ${theme.palette.divider}`,
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
          bgcolor: theme.palette.background.default,
        }}
      >
        {/* Welcome Card (shown only initially) */}
        {messages.length === 1 && <WelcomeCard />}

        {messages.map(renderMessage)}

        {/* Quick Suggestions (shown when no user messages yet) */}
        {messages.length === 1 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="h6" sx={{ mb: 2, color: 'text.secondary', textAlign: 'center' }}>
              🚀 Start a conversation:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, justifyContent: 'center' }}>
              {quickSuggestions.map((suggestion, index) => (
                <Chip
                  key={index}
                  label={suggestion}
                  onClick={() => setInputValue(suggestion)}
                  size="medium"
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
        )}

        <div ref={messagesEndRef} />
      </Box>

      {/* Input */}
      <Paper
        elevation={3}
        sx={{
          p: 2,
          borderRadius: 0,
          borderTop: `1px solid ${theme.palette.divider}`,
          bgcolor: theme.palette.background.paper,
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
                bgcolor: theme.palette.background.default,
                '&:hover': {
                  bgcolor: theme.palette.background.default,
                },
                '&.Mui-focused': {
                  bgcolor: theme.palette.background.default,
                },
              },
            }}
          />
          <Tooltip title={isLoading ? "Processing..." : "Send message (Enter)"}>
            <span>
              <IconButton
                color="primary"
                onClick={handleSendMessage}
                disabled={!inputValue.trim() || isLoading}
                sx={{
                  bgcolor: inputValue.trim() && !isLoading ? theme.palette.primary.main : theme.palette.action.disabled,
                  color: 'white',
                  '&:hover': {
                    bgcolor: inputValue.trim() && !isLoading ? theme.palette.primary.dark : theme.palette.action.disabled,
                  },
                  borderRadius: 3,
                  width: 48,
                  height: 48,
                  transition: 'all 0.2s ease',
                }}
              >
                {isLoading ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
              </IconButton>
            </span>
          </Tooltip>
        </Box>
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          Press Enter to send • Shift+Enter for new line
        </Typography>
      </Paper>
    </Box>
  );
};

export default ChatInterface;