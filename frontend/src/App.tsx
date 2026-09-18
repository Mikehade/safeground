import { useState } from 'react';
import type { Tab } from './types';
import Sidebar from './components/Layout/Sidebar';
import MainPanel from './components/Layout/MainPanel';
import QuickExit from './components/Layout/QuickExit';
import MobileNav from './components/Layout/MobileNav';

export default function App() {
  const [tab, setTab] = useState<Tab>('scout');
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div className="h-screen flex flex-col bg-ground-50">
      <QuickExit />

      {/* Desktop: side-by-side. Mobile: toggle between sidebar and main. */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <div
          className={`
            ${sidebarOpen ? 'flex' : 'hidden'}
            md:flex flex-col border-r border-ground-200 bg-white
            w-full md:w-[380px] lg:w-[420px] shrink-0
          `}
        >
          <Sidebar tab={tab} onTabChange={setTab} onCollapse={() => setSidebarOpen(false)} />
        </div>

        {/* Main content area */}
        <div
          className={`
            ${!sidebarOpen ? 'flex' : 'hidden'}
            md:flex flex-col flex-1 min-w-0
          `}
        >
          <MainPanel tab={tab} onExpandSidebar={() => setSidebarOpen(true)} />
        </div>
      </div>

      {/* Mobile bottom nav — only on small screens */}
      <MobileNav
        active={tab}
        onChange={setTab}
        sidebarOpen={sidebarOpen}
        onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
      />
    </div>
  );
}
