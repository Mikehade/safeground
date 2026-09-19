import { Shield, Megaphone, LifeBuoy, Search } from 'lucide-react';
import type { Tab } from '../../types';
import ScoutInputs from '../Scout/ScoutInputs';
import ReportForm from '../Report/ReportForm';
import ResourcesInputs from '../Resources/ResourcesInputs';
import StatusPanel from '../Report/StatusPanel';

const tabs: { id: Tab; label: string; Icon: any }[] = [
  { id: 'scout', label: 'Scout', Icon: Shield },
  { id: 'report', label: 'Report', Icon: Megaphone },
  { id: 'resources', label: 'Resources', Icon: LifeBuoy },
  { id: 'status', label: 'Status', Icon: Search },
];

interface Props { tab: Tab; onTabChange: (t: Tab) => void; onShowMain: () => void; }

export default function Sidebar({ tab, onTabChange, onShowMain }: Props) {
  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-5 pt-5 pb-3 border-b border-[#e8e6e1]">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Shield size={22} strokeWidth={2} className="text-[#2d2a24]" />
            <h1 className="font-display text-lg font-bold tracking-tight text-[#2d2a24]">SafeGround</h1>
          </div>
          <button onClick={onShowMain} className="md:hidden p-1.5 rounded-md hover:bg-[#f5f4f1] text-[#9b9590]">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 18l6-6-6-6"/></svg>
          </button>
        </div>
        <p className="text-[11px] text-[#9b9590] mt-1">Community safety intelligence — zero identity.</p>
      </div>

      {/* Tabs — desktop only */}
      <div className="hidden md:flex border-b border-[#e8e6e1]">
        {tabs.map((t) => (
          <button key={t.id} onClick={() => onTabChange(t.id)}
            className={`flex-1 flex items-center justify-center gap-1.5 py-2.5 text-[11px] font-medium transition-colors border-b-2 ${
              tab === t.id ? 'border-[#2d2a24] text-[#2d2a24]' : 'border-transparent text-[#b5b0aa] hover:text-[#6b6560]'
            }`}>
            <t.Icon size={13} /> {t.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto sidebar-scroll">
        {tab === 'scout' && <ScoutInputs onShowMain={onShowMain} />}
        {tab === 'report' && <ReportForm />}
        {tab === 'resources' && <ResourcesInputs />}
        {tab === 'status' && <StatusPanel />}
      </div>
    </div>
  );
}
