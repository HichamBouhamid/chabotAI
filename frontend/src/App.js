import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'; // Import Routes
import 'bootstrap/dist/css/bootstrap.min.css';
import ChatPdf from './pages/ChatPdf';
import Register from './pages/Register';
import Login from './pages/Login';
import Upload from './pages/Upload';

function App() {
  return (
    <Router>
      <Routes> {/* Use Routes instead of Route */}
        <Route path="/" element={<Login />} /> {/* Use 'element' prop to specify component */}
        <Route path="/register" element={<Register />} />
        <Route path="/chat" element={<ChatPdf />} />
        <Route path="/upload" element={<Upload />} />
      </Routes>
    </Router>
  );
}

export default App;
