import { ChevronLeft, Map, FileText, LifeBuoy, Search } from 'lucide-react';
import type { Tab } from '../../types';
import ScoutResults from '../Scout/ScoutResults';
import ReportSuccess from '../Report/ReportSuccess';
import ResourcesList from '../Resources/ResourcesList';

interface Props { tab: Tab; onShowSidebar: () => void; }

export default function MainPanel({ tab, onShowSidebar }: Props) {
  const titles: Record<Tab, string> = {
    scout: 'Route Advisory', report: 'Report Confirmation',
    resources: 'Nearby Resources', status: 'Status Check',
  };

  return (
    <div className="flex flex-col h-full bg-[#faf9f7]">
      {/* Mobile back bar */}
      <div className="md:hidden flex items-center gap-2 px-4 py-2.5 border-b border-[#e8e6e1] bg-white">
        <button onClick={onShowSidebar} className="p-1 rounded-md hover:bg-[#f5f4f1] text-[#9b9590]">
          <ChevronLeft size={18} />
        </button>
        <span className="text-sm font-medium text-[#6b6560]">{titles[tab]}</span>
      </div>

      <div className="flex-1 overflow-y-auto main-scroll">
        {tab === 'scout' && <ScoutResults />}
        {tab === 'report' && <ReportSuccess />}
        {tab === 'resources' && <ResourcesList />}
        {tab === 'status' && (
          <div className="flex flex-col items-center justify-center h-full text-center px-8">
            <Search size={40} strokeWidth={1.2} className="text-[#d1cec8] mb-3" />
            <h2 className="font-display text-base font-semibold text-[#6b6560]">Check a report</h2>
            <p className="text-xs text-[#b5b0aa] mt-1 max-w-xs">Enter your receipt token in the panel to look up your report status.</p>
          </div>
        )}
      </div>
    </div>
  );
}
