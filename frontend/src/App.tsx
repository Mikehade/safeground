import { useState, useEffect } from 'react';
import type { Tab } from './types';
import Sidebar from './components/Layout/Sidebar';
import MainPanel from './components/Layout/MainPanel';
import QuickExit from './components/Layout/QuickExit';
import MobileNav from './components/Layout/MobileNav';
import { useScoutStore } from './store/useScoutStore';
import { useReportStore } from './store/useReportStore';

export default function App() {
  const [tab, setTab] = useState<Tab>('scout');
  const [showMain, setShowMain] = useState(false); // mobile: which panel is visible

  // Auto-switch to main panel when results arrive (mobile fix)
  const advisory = useScoutStore((s) => s.advisory);
  const scoutLoading = useScoutStore((s) => s.loading);
  const receiptToken = useReportStore((s) => s.receiptToken);

  useEffect(() => {
    // When scout starts loading, show main panel on mobile so user sees progress
    if (scoutLoading) setShowMain(true);
  }, [scoutLoading]);

  useEffect(() => {
    if (receiptToken) setShowMain(true);
  }, [receiptToken]);

  return (
    <div className="h-screen flex flex-col bg-[#faf9f7]">
      <QuickExit />

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <div className={`
          ${!showMain ? 'flex' : 'hidden'} md:flex
          flex-col border-r border-[#e8e6e1] bg-white
          w-full md:w-[360px] lg:w-[400px] shrink-0
        `}>
          <Sidebar tab={tab} onTabChange={setTab} onShowMain={() => setShowMain(true)} />
        </div>

        {/* Main */}
        <div className={`
          ${showMain ? 'flex' : 'hidden'} md:flex
          flex-col flex-1 min-w-0
        `}>
          <MainPanel tab={tab} onShowSidebar={() => setShowMain(false)} />
        </div>
      </div>

      <MobileNav
        active={tab}
        onChange={(t) => { setTab(t); setShowMain(false); }}
        showMain={showMain}
        onToggle={() => setShowMain(!showMain)}
      />
    </div>
  );
}
