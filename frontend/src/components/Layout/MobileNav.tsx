import { Shield, Megaphone, LifeBuoy, Search } from 'lucide-react';
import type { Tab } from '../../types';

const tabs: { id: Tab; label: string; Icon: any }[] = [
  { id: 'scout', label: 'Scout', Icon: Shield },
  { id: 'report', label: 'Report', Icon: Megaphone },
  { id: 'resources', label: 'Resources', Icon: LifeBuoy },
  { id: 'status', label: 'Status', Icon: Search },
];

interface Props { active: Tab; onChange: (t: Tab) => void; showMain: boolean; onToggle: () => void; }

export default function MobileNav({ active, onChange }: Props) {
  return (
    <nav className="md:hidden border-t border-[#e8e6e1] bg-white px-1 pb-[env(safe-area-inset-bottom)]">
      <div className="flex justify-around">
        {tabs.map((t) => (
          <button key={t.id} onClick={() => onChange(t.id)}
            className={`flex flex-col items-center py-2 px-2 text-[10px] transition-colors ${
              active === t.id ? 'text-[#2d2a24] font-semibold' : 'text-[#c5c0ba]'
            }`}>
            <t.Icon size={18} strokeWidth={active === t.id ? 2 : 1.5} />
            <span className="mt-0.5">{t.label}</span>
          </button>
        ))}
      </div>
    </nav>
  );
}
