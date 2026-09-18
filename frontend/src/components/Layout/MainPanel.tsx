import type { Tab } from '../../types';
import ScoutResults from '../Scout/ScoutResults';
import ReportSuccess from '../Report/ReportSuccess';
import ResourcesList from '../Resources/ResourcesList';

interface Props {
  tab: Tab;
  onExpandSidebar: () => void;
}

export default function MainPanel({ tab, onExpandSidebar }: Props) {
  return (
    <div className="flex flex-col h-full bg-ground-50">
      {/* Mobile header bar with back button */}
      <div className="md:hidden flex items-center gap-2 px-4 py-3 border-b border-ground-200 bg-white">
        <button
          onClick={onExpandSidebar}
          className="p-1.5 rounded-md hover:bg-ground-100 text-ground-800/50"
          aria-label="Back to controls"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M15 18l-6-6 6-6" />
          </svg>
        </button>
        <span className="text-sm font-medium text-ground-800/70">
          {tab === 'scout' && 'Route Advisory'}
          {tab === 'report' && 'Report Status'}
          {tab === 'resources' && 'Nearby Resources'}
          {tab === 'status' && 'Check Status'}
        </span>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto main-scroll">
        {tab === 'scout' && <ScoutResults />}
        {tab === 'report' && <ReportSuccess />}
        {tab === 'resources' && <ResourcesList />}
        {tab === 'status' && (
          <EmptyState
            icon="🔍"
            title="Check a report's status"
            subtitle="Enter your receipt token in the sidebar to look up your report."
          />
        )}
      </div>
    </div>
  );
}

function EmptyState({ icon, title, subtitle }: { icon: string; title: string; subtitle: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center px-8">
      <span className="text-4xl mb-3">{icon}</span>
      <h2 className="font-display text-lg font-semibold text-ground-800/70">{title}</h2>
      <p className="text-sm text-ground-800/40 mt-1 max-w-sm">{subtitle}</p>
    </div>
  );
}
