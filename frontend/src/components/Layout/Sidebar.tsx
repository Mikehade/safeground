import type { Tab } from '../../types';
import ScoutInputs from '../Scout/ScoutInputs';
import ReportForm from '../Report/ReportForm';
import ResourcesInputs from '../Resources/ResourcesInputs';
import StatusPanel from '../Report/StatusPanel';

const tabs: { id: Tab; label: string; icon: string }[] = [
  { id: 'scout', label: 'Scout', icon: '🛡️' },
  { id: 'report', label: 'Report', icon: '📢' },
  { id: 'resources', label: 'Resources', icon: '🆘' },
  { id: 'status', label: 'Status', icon: '🔍' },
];

interface Props {
  tab: Tab;
  onTabChange: (t: Tab) => void;
  onCollapse: () => void;
}

export default function Sidebar({ tab, onTabChange, onCollapse }: Props) {
  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-5 pt-5 pb-3 border-b border-ground-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl">🛡️</span>
            <h1 className="font-display text-xl font-bold tracking-tight text-ground-900">
              SafeGround
            </h1>
          </div>
          <button
            onClick={onCollapse}
            className="md:hidden p-1.5 rounded-md hover:bg-ground-100 text-ground-800/50"
            aria-label="Show results"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 18l6-6-6-6" />
            </svg>
          </button>
        </div>
        <p className="text-xs text-ground-800/50 mt-1">
          Community safety intelligence — zero identity, zero tracking.
        </p>
      </div>

      {/* Tab switcher — hidden on mobile (use bottom nav instead) */}
      <div className="hidden md:flex border-b border-ground-200">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => onTabChange(t.id)}
            className={`flex-1 py-2.5 text-xs font-medium transition-colors border-b-2 ${
              tab === t.id
                ? 'border-ground-900 text-ground-900'
                : 'border-transparent text-ground-800/40 hover:text-ground-800/70'
            }`}
          >
            <span className="mr-1">{t.icon}</span>
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab content — scrollable */}
      <div className="flex-1 overflow-y-auto sidebar-scroll">
        {tab === 'scout' && <ScoutInputs />}
        {tab === 'report' && <ReportForm />}
        {tab === 'resources' && <ResourcesInputs />}
        {tab === 'status' && <StatusPanel />}
      </div>
    </div>
  );
}
