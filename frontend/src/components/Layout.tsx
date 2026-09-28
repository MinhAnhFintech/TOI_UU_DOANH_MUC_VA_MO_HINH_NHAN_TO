import { NavLink, Outlet } from 'react-router-dom';
import { Database, LineChart, TrendingUp, Cpu, PieChart, Activity, Target, Sliders, Briefcase, FileText } from 'lucide-react';
import { cn } from '../lib/utils';
import { useGlobalStore } from '../hooks/useGlobalStore';
import { MODELS } from '../lib/constants';

const navItems = [
  { to: '/data', icon: Database, label: 'Chất lượng Dữ liệu' },
  { to: '/factors', icon: Activity, label: 'Phân tích Nhân tố' },
  { to: '/regression', icon: TrendingUp, label: 'Hồi quy Chuỗi thời gian' },
  { to: '/models', icon: Cpu, label: 'So sánh Mô hình' },
  { to: '/quantile', icon: LineChart, label: 'Hồi quy Phân vị' },
  { to: '/frontier', icon: Target, label: 'Đường biên Hiệu quả' },
  { to: '/weights', icon: PieChart, label: 'Tỷ trọng Danh mục' },
  { to: '/backtest', icon: Briefcase, label: 'Kiểm định (Backtest)' },
  { to: '/sensitivity', icon: Sliders, label: 'Phân tích Độ nhạy' },
  { to: '/conclusion', icon: FileText, label: 'Kết luận' },
];

export default function Layout() {
  const { selectedModel, setSelectedModel } = useGlobalStore();

  return (
    <div className="flex h-screen bg-slate-50">
      <aside className="w-64 bg-navy-900 text-white flex flex-col">
        <div className="p-4 border-b border-navy-700">
          <h1 className="text-xl font-bold text-gold-500">VN30 Optimizer</h1>
        </div>
        <nav className="flex-1 overflow-y-auto py-4 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  'flex items-center px-4 py-3 text-sm font-medium transition-colors',
                  isActive ? 'bg-navy-800 text-gold-400 border-r-4 border-gold-500' : 'text-slate-300 hover:bg-navy-800 hover:text-white'
                )
              }
            >
              <item.icon className="mr-3 h-5 w-5" />
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="flex-1 flex flex-col overflow-hidden">
        <header className="bg-white border-b border-slate-200 p-4 flex items-center justify-between z-10 shadow-sm">
          <div className="flex items-center space-x-4">
            <h2 className="text-lg font-semibold text-slate-800">Mô hình Nhân tố VN30</h2>
          </div>
          <div className="flex items-center space-x-4">
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="border-slate-300 rounded-md shadow-sm focus:border-gold-500 focus:ring-gold-500 text-sm"
            >
              {MODELS.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>
        </header>
        <div className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
