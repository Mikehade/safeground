import type { Tab } from '../../types';

const tabs: { id: Tab; label: string; icon: string }[] = [
  { id: 'scout', label: 'Scout', icon: '🛡️' },
  { id: 'report', label: 'Report', icon: '📢' },
  { id: 'resources', label: 'Resources', icon: '🆘' },
  { id: 'status', label: 'Status', icon: '🔍' },
];

interface Props {
  active: Tab;
  onChange: (tab: Tab) => void;
  sidebarOpen: boolean;
  onToggleSidebar: () => void;
}

export default function MobileNav({ active, onChange, sidebarOpen, onToggleSidebar }: Props) {
  return (
    <nav className="md:hidden border-t border-ground-200 bg-white px-1 pb-[env(safe-area-inset-bottom)]">
      <div className="flex justify-around">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => {
              onChange(tab.id);
              if (!sidebarOpen) onToggleSidebar();
            }}
            className={`flex flex-col items-center py-2 px-2 text-[10px] transition-colors ${
              active === tab.id
                ? 'text-ground-900 font-semibold'
                : 'text-ground-800/30 hover:text-ground-800/60'
            }`}
          >
            <span className="text-base mb-0.5">{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>
    </nav>
  );
}
