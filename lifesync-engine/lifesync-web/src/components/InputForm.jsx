import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, ChevronRight } from 'lucide-react';

const InputForm = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);

  const handleNext = () => {
    if (step < 3) setStep(step + 1);
    else navigate('/dashboard');
  };

  return (
    <div className="max-w-2xl mx-auto min-h-screen p-6 pt-12">
      <header className="flex justify-between items-center mb-12">
        <button 
          onClick={() => step > 1 ? setStep(step - 1) : navigate('/')}
          className="flex items-center text-zinc-400 hover:text-white transition-colors text-sm"
        >
          <ChevronLeft size={16} className="mr-1" /> Back
        </button>
        <span className="text-sm font-mono text-zinc-500">Step {step} of 3</span>
      </header>

      <motion.div
        key={step}
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: -20 }}
      >
        {step === 1 && (
          <div className="space-y-8">
            <div>
              <h2 className="text-xs font-bold tracking-widest text-zinc-500 uppercase mb-2">Foundations</h2>
              <h1 className="text-3xl font-bold tracking-tight mb-2">Define Your Rhythm</h1>
              <p className="text-zinc-400 text-sm">Your schedule is the canvas for your AI plan. Let's start with your core daily anchors.</p>
            </div>

            <div className="bg-[#18181b] p-6 rounded-2xl border border-zinc-800">
              <h3 className="font-semibold mb-4">Work & Education</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs text-zinc-500 uppercase font-bold tracking-wider block mb-2">Start Shift</label>
                  <input type="time" defaultValue="09:00" className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-2 text-white" />
                </div>
                <div>
                  <label className="text-xs text-zinc-500 uppercase font-bold tracking-wider block mb-2">End Shift</label>
                  <input type="time" defaultValue="17:00" className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-2 text-white" />
                </div>
              </div>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-8">
             <div>
              <h2 className="text-xs font-bold tracking-widest text-zinc-500 uppercase mb-2">Phase 2: Lifestyle Architecture</h2>
              <h1 className="text-3xl font-bold tracking-tight mb-2">What Defines Your Future?</h1>
            </div>
            {/* Additional Goal Inputs matching PDF design go here */}
            <div className="bg-[#18181b] p-6 rounded-2xl border border-zinc-800">
              <h3 className="font-semibold mb-1">Core Goals</h3>
              <p className="text-xs text-zinc-500 mb-4">High-impact pursuits requiring disciplined blocks.</p>
              <input type="text" placeholder="e.g. Master AI Engineering" className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-3 text-white mb-4" />
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-8">
             <div>
              <h2 className="text-xs font-bold tracking-widest text-zinc-500 uppercase mb-2">Rigid Commitments</h2>
              <h1 className="text-3xl font-bold tracking-tight mb-2">Add Fixed Events</h1>
            </div>
             <div className="bg-[#18181b] p-6 rounded-2xl border border-zinc-800">
              <input type="text" placeholder="e.g. Team Standup, Gym" className="w-full bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-3 text-white mb-4" />
            </div>
          </div>
        )}

        <div className="mt-12 flex justify-end">
          <button 
            onClick={handleNext}
            className="flex items-center gap-2 bg-[#f97316] text-black font-semibold rounded-xl py-3 px-6 hover:bg-orange-600 transition-colors"
          >
            {step === 3 ? 'Generate Plan' : 'Continue'} <ChevronRight size={18} />
          </button>
        </div>
      </motion.div>
    </div>
  );
};

export default InputForm;