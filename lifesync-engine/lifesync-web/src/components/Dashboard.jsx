import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { BarChart, Bar, XAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { Zap, Download, Share2 } from 'lucide-react';
import { fetchTwoWeekPlan } from '../services/api';

const Dashboard = () => {
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadPlan = async () => {
      const data = await fetchTwoWeekPlan();
      setPlan(data);
      setLoading(false);
    };
    loadPlan();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center">
        <div className="w-16 h-16 border-4 border-zinc-800 border-t-[#a855f7] rounded-full animate-spin"></div>
        <p className="mt-4 text-zinc-500 font-mono text-sm tracking-widest">ARCHITECTING PLAN...</p>
      </div>
    );
  }

  // Mocked chart data for the Focus Intensity widget
  const chartData = [
    { day: 'M', focus: 8, rest: 2 },
    { day: 'T', focus: 6, rest: 3 },
    { day: 'W', focus: 9, rest: 1 },
    { day: 'T', focus: 7, rest: 2 },
    { day: 'F', focus: 5, rest: 4 },
    { day: 'S', focus: 3, rest: 6 },
    { day: 'S', focus: 4, rest: 5 },
  ];

  return (
    <div className="max-w-7xl mx-auto p-6 pt-8 min-h-screen">
      <header className="flex justify-between items-end mb-8 border-b border-zinc-800 pb-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">{plan.plan_title}</h1>
          <p className="text-sm text-zinc-400 mt-1 font-mono">{plan.sprint_start} ➔ {plan.sprint_end}</p>
        </div>
        <div className="flex gap-4">
          <button className="flex items-center gap-2 bg-zinc-900 border border-zinc-800 hover:bg-zinc-800 px-4 py-2 rounded-lg text-sm transition-colors">
            <Share2 size={16} /> Share Link
          </button>
          <button className="flex items-center gap-2 bg-zinc-100 hover:bg-white text-black font-semibold px-4 py-2 rounded-lg text-sm transition-colors">
            <Download size={16} /> Export ICS
          </button>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        
        {/* Left Sidebar: Active Goals & Milestones */}
        <div className="space-y-6">
          <h2 className="text-xs font-bold tracking-widest text-zinc-500 uppercase">Active Milestones</h2>
          {plan.milestones.map((m, idx) => (
            <motion.div 
              initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: idx * 0.1 }}
              key={idx} 
              className="bg-[#18181b] p-4 rounded-xl border border-zinc-800"
            >
              <h3 className="font-semibold text-white mb-3">{m.goal_name}</h3>
              <div className="space-y-2">
                <div className="flex items-start gap-2 text-sm">
                  <span className="text-zinc-500 font-mono">W1</span>
                  <span className="text-zinc-300">{m.week_1_target}</span>
                </div>
                <div className="flex items-start gap-2 text-sm">
                  <span className="text-zinc-500 font-mono">W2</span>
                  <span className="text-zinc-300">{m.week_2_target}</span>
                </div>
              </div>
            </motion.div>
          ))}

          <div className="bg-gradient-to-br from-[#18181b] to-zinc-900 p-4 rounded-xl border border-zinc-800 mt-6">
            <div className="flex items-center gap-2 mb-2 text-yellow-500">
              <Zap size={18} /> <span className="font-bold">System Status</span>
            </div>
            <p className="text-xs text-zinc-400">Neural load at 42%. Entropy low. Schedule optimized for peak performance.</p>
          </div>
        </div>

        {/* Center: 14-Day Grid */}
        <div className="col-span-2">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xs font-bold tracking-widest text-zinc-500 uppercase">14-Day Outlook</h2>
            <div className="flex gap-2 text-xs font-mono">
              <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-white"></div> Work</span>
              <span className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-[#a855f7]"></div> Hobby</span>
            </div>
          </div>
          
          <div className="grid grid-cols-7 gap-3">
            {[...Array(14)].map((_, i) => {
              const isToday = i === 0; // Simplified for UI demonstration
              return (
                <div 
                  key={i} 
                  className={`bg-[#18181b] rounded-xl p-3 h-36 border flex flex-col justify-between ${isToday ? 'border-zinc-500' : 'border-zinc-800 hover:border-zinc-700'} transition-colors cursor-pointer`}
                >
                  <div className="flex justify-between items-start">
                    <span className={`text-xs font-mono ${isToday ? 'text-white' : 'text-zinc-500'}`}>OCT {14 + i}</span>
                    {isToday && <span className="text-[10px] bg-zinc-800 px-2 py-0.5 rounded-full">Today</span>}
                  </div>
                  <div className="space-y-1">
                    <div className="h-1 w-full bg-zinc-800 rounded-full overflow-hidden">
                      <div className="h-full bg-white w-3/4"></div>
                    </div>
                    <div className="h-1 w-full bg-zinc-800 rounded-full overflow-hidden">
                      <div className="h-full bg-[#a855f7] w-1/3"></div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Sidebar: Analytics & Charts */}
        <div className="space-y-6">
          <div className="bg-[#18181b] p-4 rounded-xl border border-zinc-800 h-64">
             <h2 className="text-xs font-bold tracking-widest text-zinc-500 uppercase mb-6">Focus Intensity</h2>
             <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData}>
                <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fill: '#71717a', fontSize: 12 }} />
                <Tooltip cursor={{ fill: '#27272a' }} contentStyle={{ backgroundColor: '#09090b', border: '1px solid #27272a' }} />
                <Bar dataKey="focus" fill="#ffffff" radius={[2, 2, 0, 0]} />
                <Bar dataKey="rest" fill="#3f3f46" radius={[2, 2, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="bg-[#18181b] p-4 rounded-xl border border-zinc-800">
              <span className="text-xs text-zinc-500 font-mono block mb-1">UPTIME</span>
              <span className="text-2xl font-bold">92%</span>
            </div>
            <div className="bg-[#18181b] p-4 rounded-xl border border-zinc-800">
              <span className="text-xs text-zinc-500 font-mono block mb-1">TREND</span>
              <span className="text-2xl font-bold text-green-400">+14%</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

export default Dashboard;