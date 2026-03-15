import { motion } from 'framer-motion'
import { Settings as SettingsIcon, HelpCircle } from 'lucide-react'
import BorderBeam from './ui/BorderBeam'

export default function SettingsPanel({ settings, onChange }) {
    const toggleTheme = () => {
        onChange({ ...settings, theme: settings.theme === 'dark' ? 'light' : 'dark' })
    }

    return (
        <motion.div 
            className="w-full max-w-2xl mx-auto"
            initial={{ opacity: 0, scale: 0.98, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.98, y: 10 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
        >
            <div className="card card-glass relative overflow-hidden border border-white/10 shadow-2xl" style={{ padding: '32px' }}>
                <BorderBeam duration={12} size={400} className="opacity-30" />
                <div className="relative z-10">
                    <div className="flex items-center" style={{ gap: '16px', marginBottom: '12px' }}>
                        <div className="bg-purple-500/20 rounded-xl border border-purple-500/30" style={{ padding: '12px' }}>
                            <SettingsIcon size={28} className="text-purple-400" />
                        </div>
                        <h2 className="text-3xl font-bold tracking-tight text-white m-0 border-none bg-none">Settings</h2>
                    </div>
                    <p className="text-gray-400 text-sm mb-8 pl-1">
                        Configure the visual overlays on the results page.
                    </p>

                    <div className="flex justify-between items-center bg-black/40 rounded-2xl border border-white/5 hover:bg-white/5 transition-colors group" style={{ padding: '20px' }}>
                        <div>
                            <div className="flex items-center gap-2 text-base font-semibold text-gray-200">
                                App Theme
                                <HelpCircle size={16} className="text-purple-400/70 cursor-help" title="Toggle between the dark glassmorphic V3 interface and experimental light mode." />
                            </div>
                            <div className="text-sm text-gray-500 mt-1">
                                Default is Dark Mode (Recommended)
                            </div>
                        </div>
                        <label className="toggle-switch">
                            <input
                                type="checkbox"
                                checked={settings.theme === 'light'}
                                onChange={toggleTheme}
                            />
                            <span className="toggle-slider"></span>
                        </label>
                    </div>
                </div>
            </div>
        </motion.div>
    )
}
