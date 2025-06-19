import React from 'react';
import { 
  AppBar, 
  Toolbar, 
  Typography, 
  Button, 
  Box,
  IconButton,
  Chip
} from '@mui/material';
import { 
  Storage,
  History,
  Analytics,
  Search,
  GitHub,
  Chat
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';

const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Chat', icon: <Chat /> },
    { path: '/query', label: 'Query', icon: <Search /> },
    { path: '/schema', label: 'Schema', icon: <Storage /> },
    { path: '/history', label: 'History', icon: <History /> },
    { path: '/analytics', label: 'Analytics', icon: <Analytics /> },
  ];

  return (
    <AppBar position="static" sx={{ backgroundColor: '#1a1a1a', borderBottom: '1px solid #333' }}>
      <Toolbar>
        <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
          <Typography variant="h6" component="div" sx={{ mr: 4, fontWeight: 'bold' }}>
            🧠 Text-to-SQL RAG
          </Typography>
          <Chip 
            label="Advanced" 
            size="small" 
            color="primary" 
            variant="outlined"
            sx={{ mr: 3 }}
          />
        </Box>

        <Box sx={{ display: 'flex', gap: 1 }}>
          {navItems.map((item) => (
            <Button
              key={item.path}
              startIcon={item.icon}
              onClick={() => navigate(item.path)}
              variant={location.pathname === item.path ? 'contained' : 'text'}
              sx={{
                color: location.pathname === item.path ? 'white' : '#aaa',
                '&:hover': {
                  backgroundColor: location.pathname === item.path ? 'primary.dark' : 'rgba(255,255,255,0.1)',
                },
              }}
            >
              {item.label}
            </Button>
          ))}
        </Box>

        <IconButton
          sx={{ ml: 2, color: 'inherit' }}
          onClick={() => window.open('https://github.com/Aaryan04/advanced-text-to-sql-rag', '_blank')}
        >
          <GitHub />
        </IconButton>
      </Toolbar>
    </AppBar>
  );
};

export default Navbar;