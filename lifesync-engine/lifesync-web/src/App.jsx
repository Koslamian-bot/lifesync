import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Login from './components/Login';
import InputForm from './components/InputForm';
import Dashboard from './components/Dashboard';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-[#09090b] text-white font-sans">
        <Routes>
          <Route path="/" element={<Login />} />
          <Route path="/setup" element={<InputForm />} />
          <Route path="/dashboard" element={<Dashboard />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;