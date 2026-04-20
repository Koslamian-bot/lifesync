import React from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { Activity } from 'lucide-react';

const Login = () => {
  const navigate = useNavigate();

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        <div className="flex justify-center mb-8">
          <div className="bg-zinc-800 p-4 rounded-2xl border border-zinc-700 shadow-[0_0_15px_rgba(255,255,255,0.1)]">
            <Activity size={32} className="text-white" />
          </div>
        </div>

        <div className="text-center mb-10">
          <h1 className="text-3xl font-bold tracking-tight mb-2">System Access</h1>
          <p className="text-zinc-400 text-sm">Authorize your session to synchronize<br/>with your future.</p>
        </div>

        <form className="space-y-6" onSubmit={(e) => { e.preventDefault(); navigate('/setup'); }}>
          <div className="space-y-2">
            <label className="text-xs font-bold text-zinc-500 tracking-wider uppercase">Neural Identity (Email)</label>
            <input 
              type="email" 
              defaultValue="name@lifesync.ai"
              className="w-full bg-zinc-900 border border-zinc-800 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-zinc-500 transition-colors"
            />
          </div>

          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <label className="text-xs font-bold text-zinc-500 tracking-wider uppercase">Access Key</label>
              <span className="text-xs text-zinc-500 cursor-pointer hover:text-white transition-colors">Forgotten?</span>
            </div>
            <input 
              type="password" 
              defaultValue="password123"
              className="w-full bg-zinc-900 border border-zinc-800 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-zinc-500 transition-colors"
            />
          </div>

          <div className="flex items-center gap-2">
            <input type="checkbox" className="w-4 h-4 rounded bg-zinc-900 border-zinc-800" />
            <span className="text-sm text-zinc-400">Maintain connection for 30 days</span>
          </div>

          <button type="submit" className="w-full bg-white text-black font-semibold rounded-xl py-3 mt-4 hover:bg-zinc-200 transition-colors">
            Initialize Sync
          </button>
        </form>

        <div className="mt-8 flex items-center gap-4">
          <div className="h-px bg-zinc-800 flex-1"></div>
          <span className="text-xs text-zinc-500 font-medium tracking-wider uppercase">Or Establish Via</span>
          <div className="h-px bg-zinc-800 flex-1"></div>
        </div>

        <div className="grid grid-cols-2 gap-4 mt-6">
          <button className="flex items-center justify-center gap-2 bg-zinc-900 border border-zinc-800 rounded-xl py-3 hover:bg-zinc-800 transition-colors">
            <span className="text-sm font-medium">Google</span>
          </button>
          <button className="flex items-center justify-center gap-2 bg-zinc-900 border border-zinc-800 rounded-xl py-3 hover:bg-zinc-800 transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.2c3-.3 6-1.5 6-6.5a4.6 4.6 0 0 0-1.3-3.2 4.2 4.2 0 0 0-.1-3.2s-1.1-.3-3.5 1.3a12.3 12.3 0 0 0-6.2 0C6.5 2.8 5.4 3.1 5.4 3.1a4.2 4.2 0 0 0-.1 3.2A4.6 4.6 0 0 0 4 9.5c0 5 3 6.2 6 6.5a4.8 4.8 0 0 0-1 3.2v4"></path>
            </svg>
            <span className="text-sm font-medium">GitHub</span>
          </button>
        </div>
      </motion.div>
    </div>
  );
};

export default Login;