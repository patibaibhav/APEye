import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';
import setupMockAdapter from './mocks/mockAdapter';

// Initialize mocks if VITE_USE_MOCKS=true
setupMockAdapter();

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
