import { useRef, useState } from 'react';
import axios from 'axios';
import { Activity, ShieldAlert, Cpu, Play, Download, UploadCloud, Zap } from 'lucide-react';
import DataCore3D from './components/DataCore3D';

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

export default function App() {
  const [metrics, setMetrics] = useState(null);
  const [exceptions, setExceptions] = useState([]);
  const [selectedException, setSelectedException] = useState(null);
  const [aiAnalysis, setAiAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [investigating, setInvestigating] = useState(false);
  const [chaosMode, setChaosMode] = useState(false);
  const fileInputRef = useRef(null);
  const investigationRequestRef = useRef(0);

  const clearSelection = () => {
    investigationRequestRef.current += 1;
    setSelectedException(null);
    setAiAnalysis(null);
    setInvestigating(false);
  };

  const handle3DNodeClick = (bankStmtId) => {
    const exc = exceptions.find(e => e.bank_stmt_id === bankStmtId);
    if (exc) {
      setSelectedException(exc);
      runInvestigation(bankStmtId);
    }
  };

  const refreshReconciliationData = async (result) => {
    setMetrics(result.data.metrics);
    const exceptionsResult = await axios.get(`${API_BASE_URL}/exceptions`);
    setExceptions(Array.isArray(exceptionsResult.data) ? exceptionsResult.data : []);
    clearSelection();
  };

  const runReconciliation = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE_URL}/reconcile`);
      await refreshReconciliationData(res);
    } catch (err) {
      console.error("Reconciliation failed", err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelection = async (event) => {
    const file = event.target.files?.[0];
    // Clear the field immediately so the same CSV can be uploaded again.
    event.target.value = '';

    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    clearSelection();
    setUploading(true);
    try {
      const res = await axios.post(`${API_BASE_URL}/reconcile/upload`, formData);
      await refreshReconciliationData(res);
    } catch (err) {
      console.error("CSV upload failed", err);
    } finally {
      setUploading(false);
    }
  };

  const runInvestigation = async (bankStmtId) => {
    const requestId = investigationRequestRef.current + 1;
    investigationRequestRef.current = requestId;
    setInvestigating(true);
    setAiAnalysis(null);
    try {
      const res = await axios.post(`${API_BASE_URL}/investigate/${bankStmtId}?simulate_outage=${chaosMode}`);
      if (requestId === investigationRequestRef.current) {
        setAiAnalysis(res.data.ai_analysis);
      }
    } catch (err) {
      console.error("AI Investigation failed", err);
    } finally {
      if (requestId === investigationRequestRef.current) {
        setInvestigating(false);
      }
    }
  };

  return (
    <div className="min-h-screen bg-aura-bg text-slate-100 p-6">
      {/* Header */}
      <header className="flex justify-between items-center pb-6 border-b border-aura-border">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold tracking-wider text-white">AURA</h1>
            <span className="px-2.5 py-0.5 text-xs font-mono bg-aura-cyan/10 border border-aura-cyan/40 text-aura-cyan rounded-full">
              FINANCE CONTROLLER
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">Autonomous Unified Reconciliation & Exception Resolution</p>
        </div>
        
        {/* New Command Controls */}
        <div className="flex items-center gap-4">
          
          {/* Chaos Monkey Switch */}
          <div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-aura-border bg-aura-panel/50">
            <Zap className={`w-4 h-4 ${chaosMode ? 'text-aura-red drop-shadow-[0_0_8px_rgba(255,51,102,0.8)]' : 'text-slate-500'}`} />
            <span className={`text-[10px] font-mono tracking-wider ${chaosMode ? 'text-aura-red' : 'text-slate-400'}`}>CHAOS MONKEY</span>
            <button 
              onClick={() => setChaosMode(!chaosMode)}
              className={`w-9 h-5 rounded-full relative transition-colors duration-300 ${chaosMode ? 'bg-aura-red/30' : 'bg-slate-700'}`}
            >
              <div className={`w-3.5 h-3.5 rounded-full bg-white absolute top-[3px] transition-transform duration-300 ${chaosMode ? 'translate-x-4 shadow-[0_0_10px_#FF3366]' : 'translate-x-1'}`} />
            </button>
          </div>

          {/* Export Audit Trail */}
          <a
            href={`${API_BASE_URL}/export`}
            download="aura_audit_trail.csv"
            className="flex items-center gap-2 px-4 py-2.5 rounded-lg border border-aura-border bg-aura-panel text-slate-300 hover:text-white hover:bg-aura-border/50 transition text-xs font-semibold uppercase tracking-wide"
          >
            <Download className="w-4 h-4" />
            Export Audit
          </a>

          {/* Bank statement ingestion */}
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,text/csv"
            onChange={handleFileSelection}
            className="hidden"
            aria-label="Upload bank statement CSV"
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={loading || uploading}
            className="flex items-center gap-2 px-4 py-2.5 rounded-lg border border-aura-border bg-aura-panel text-slate-300 hover:text-white hover:bg-aura-border/50 transition text-xs font-semibold uppercase tracking-wide disabled:cursor-not-allowed disabled:opacity-50"
          >
            <UploadCloud className="w-4 h-4" />
            {uploading ? 'Ingesting...' : 'Ingest CSV'}
          </button>

          {/* Execute Button */}
          <button
            onClick={runReconciliation}
            disabled={loading || uploading}
            className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-aura-cyan text-black font-semibold text-sm hover:bg-aura-cyan/90 transition shadow-[0_0_20px_rgba(0,240,255,0.4)] disabled:opacity-50 uppercase tracking-wide"
          >
            <Play className="w-4 h-4 fill-current" />
            {loading ? 'Reconciling...' : 'Execute'}
          </button>
        </div>
      </header>

      {/* Main Grid */}
      <div className="grid grid-cols-12 gap-6 mt-6">
        {/* Left Column: 3D Core + Telemetry */}
        <div className="col-span-12 lg:col-span-7 flex flex-col gap-6">
          <DataCore3D 
            isFocused={investigating || !!aiAnalysis} 
            activeId={selectedException?.bank_stmt_id}
            riskLevel={aiAnalysis?.risk_level}
            onReset={clearSelection}
            totalCount={metrics ? metrics.total_records : 150}
            exceptions={exceptions}
            onNodeClick={handle3DNodeClick}
          />

          {/* Metric Cards */}
          <div className="grid grid-cols-4 gap-4">
            <div className="bg-aura-panel border border-aura-border p-4 rounded-xl">
              <span className="text-xs text-slate-400 font-mono">TOTAL BATCH</span>
              <p className="text-2xl font-bold text-white mt-1">{metrics ? metrics.total_records : '---'}</p>
            </div>
            <div className="bg-aura-panel border border-aura-border p-4 rounded-xl">
              <span className="text-xs text-aura-emerald font-mono">MATCHED</span>
              <p className="text-2xl font-bold text-aura-emerald mt-1">{metrics ? metrics.matched : '---'}</p>
            </div>
            <div className="bg-aura-panel border border-aura-border p-4 rounded-xl">
              <span className="text-xs text-aura-amber font-mono">INSPECTION</span>
              <p className="text-2xl font-bold text-aura-amber mt-1">{metrics ? metrics.reviews + metrics.duplicates : '---'}</p>
            </div>
            <div className="bg-aura-panel border border-aura-border p-4 rounded-xl">
              <span className="text-xs text-aura-cyan font-mono">ACCURACY</span>
              <p className="text-2xl font-bold text-aura-cyan mt-1">{metrics ? `${metrics.accuracy}%` : '---'}</p>
            </div>
          </div>

          {/* Exceptions Table */}
          <div className="bg-aura-panel border border-aura-border rounded-xl p-5 flex-1">
            <h2 className="text-sm font-semibold tracking-wide uppercase font-mono text-slate-300 mb-4 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-aura-amber" /> Exception Resolution Queue
            </h2>
            <div className="overflow-y-auto max-h-64 divide-y divide-aura-border/50 text-xs">
              {exceptions.length === 0 ? (
                <p className="text-slate-500 py-6 text-center">Execute reconciliation to ingest and match records.</p>
              ) : (
                exceptions.map((exc) => (
                  <div 
                    key={exc.bank_stmt_id}
                    onClick={() => { setSelectedException(exc); runInvestigation(exc.bank_stmt_id); }}
                    className={`p-3 flex justify-between items-center cursor-pointer hover:bg-aura-border/30 transition rounded-lg ${selectedException?.bank_stmt_id === exc.bank_stmt_id ? 'bg-aura-border/50 border-l-2 border-aura-cyan' : ''}`}
                  >
                    <div>
                      <span className="font-mono text-slate-300 font-semibold">{exc.bank_stmt_id}</span>
                      <p className="text-slate-400 mt-0.5">{exc.system_reason}</p>
                    </div>
                    <span className={`px-2 py-0.5 rounded font-mono text-[10px] ${exc.system_status === 'REVIEW' ? 'bg-aura-amber/10 text-aura-amber border border-aura-amber/30' : exc.system_status === 'DUPLICATE' ? 'bg-purple-500/10 text-purple-400 border border-purple-500/30' : 'bg-aura-red/10 text-aura-red border border-aura-red/30'}`}>
                      {exc.system_status}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Right Column: AI Exception Cockpit */}
        <div className="col-span-12 lg:col-span-5 bg-aura-panel border border-aura-border rounded-xl p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 pb-4 border-b border-aura-border">
              <Cpu className="w-5 h-5 text-aura-cyan" />
              <h2 className="text-sm font-semibold tracking-wide uppercase font-mono text-slate-200">
                Layer 3 // Autonomous AI Investigation
              </h2>
            </div>

            {selectedException ? (
              <div className="mt-5 space-y-4">
                <div>
                  <span className="text-xs text-slate-400 font-mono">SELECTED RECORD</span>
                  <p className="text-sm font-mono text-white mt-0.5">{selectedException.bank_stmt_id} ({selectedException.invoice_ref})</p>
                </div>
                
                <div className="bg-aura-bg/80 border border-aura-border p-4 rounded-lg">
                  <span className="text-xs text-aura-cyan font-mono">AI ROOT-CAUSE ANALYSIS</span>
                  {investigating ? (
                    <p className="text-xs text-slate-400 mt-2 animate-pulse">Running autonomous reasoning...</p>
                  ) : aiAnalysis ? (
                    <p className="text-xs text-slate-300 mt-2 leading-relaxed">{aiAnalysis.investigation_summary}</p>
                  ) : (
                    <p className="text-xs text-slate-500 mt-2">Waiting for agent invocation...</p>
                  )}
                </div>

                {aiAnalysis && (
                  <div className="grid grid-cols-2 gap-3 pt-2">
                    <div className="bg-aura-bg/60 border border-aura-border p-3 rounded-lg">
                      <span className="text-[10px] text-slate-400 font-mono uppercase">Action</span>
                      <p className="text-xs font-semibold text-aura-emerald mt-1 font-mono">{aiAnalysis.recommended_action}</p>
                    </div>
                    <div className="bg-aura-bg/60 border border-aura-border p-3 rounded-lg">
                      <span className="text-[10px] text-slate-400 font-mono uppercase">Risk Level</span>
                      <p className={`text-xs font-semibold mt-1 font-mono ${aiAnalysis.risk_level === 'LOW' ? 'text-aura-emerald' : 'text-aura-amber'}`}>
                        {aiAnalysis.risk_level}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="h-64 flex flex-col items-center justify-center text-center text-slate-500">
                <Activity className="w-8 h-8 text-slate-600 mb-2 animate-pulse" />
                <p className="text-xs">Select any flagged item from the queue to trigger the AI investigation agent.</p>
              </div>
            )}
          </div>

          <div className="pt-4 border-t border-aura-border/60 flex justify-between items-center text-[11px] font-mono text-slate-500">
            <span>AUDIT TRAIL // ACTIVE</span>
            <span>ZERO-HALLUCINATION DUAL-PASS</span>
          </div>
        </div>
      </div>
    </div>
  );
}
