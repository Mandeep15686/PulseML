import { Link, useLocation } from 'react-router-dom'
import { Activity, BarChart3, Bell, Database, Upload } from 'lucide-react'

const links = [
  { to: '/',        label: 'Dashboard', icon: Activity },
  { to: '/models',  label: 'Models',    icon: Database },
  { to: '/alerts',  label: 'Alerts',    icon: Bell },
  { to: '/upload',  label: 'Upload',    icon: Upload },
]

export function Navbar() {
  const { pathname } = useLocation()
  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-gray-950/95 backdrop-blur border-b border-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center h-14">
        <Link to="/" className="flex items-center gap-2 mr-8">
          <div className="w-7 h-7 rounded-lg bg-blue-500 flex items-center justify-center">
            <BarChart3 size={15} className="text-white" />
          </div>
          <span className="font-bold text-white text-sm">PulseML</span>
        </Link>
        <div className="flex gap-1">
          {links.map(({ to, label, icon: Icon }) => {
            const active = pathname === to || (to !== '/' && pathname.startsWith(to))
            return (
              <Link
                key={to}
                to={to}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors
                  ${active
                    ? 'bg-blue-500/15 text-blue-400'
                    : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
                  }`}
              >
                <Icon size={14} />
                {label}
              </Link>
            )
          })}
        </div>
      </div>
    </nav>
  )
}
