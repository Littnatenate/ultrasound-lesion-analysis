import { motion } from 'framer-motion'
import { Box, Cpu, Zap, Layout, Layers, Eye, Server, FileText, Download, Target, Ruler, AlertTriangle, Flame, ScrollText } from 'lucide-react'
import GridPattern from './ui/GridPattern'

export default function AboutPanel() {
    const techStack = [
        { icon: <Box size={24} className="text-blue-400 group-hover:scale-110 transition-transform" />, name: 'Detectron2' },
        { icon: <Cpu size={24} className="text-orange-500 group-hover:scale-110 transition-transform" />, name: 'PyTorch' },
        { icon: <Zap size={24} className="text-teal-400 group-hover:scale-110 transition-transform" />, name: 'FastAPI' },
        { icon: <Layout size={24} className="text-cyan-400 group-hover:scale-110 transition-transform" />, name: 'React' },
        { icon: <Layers size={24} className="text-purple-400 group-hover:scale-110 transition-transform" />, name: 'Vite' },
        { icon: <Eye size={24} className="text-green-400 group-hover:scale-110 transition-transform" />, name: 'OpenCV' },
        { icon: <Server size={24} className="text-gray-400 group-hover:scale-110 transition-transform" />, name: 'pywebview' },
        { icon: <FileText size={24} className="text-red-400 group-hover:scale-110 transition-transform" />, name: 'fpdf2' },
    ]

    const features = [
        { icon: <Target size={18} className="text-blue-400" />, label: 'Detection', value: 'Instance segmentation with PointRend' },
        { icon: <Ruler size={18} className="text-purple-400" />, label: 'Measurements', value: 'Height, width, area, circularity' },
        { icon: <AlertTriangle size={18} className="text-yellow-400" />, label: 'Risk Model', value: 'Logistic regression (see doctor probability)' },
        { icon: <ScrollText size={18} className="text-green-400" />, label: 'Reports', value: 'PDF, PNG, CSV export' },
    ]

    const containerVariants = {
        hidden: { opacity: 0 },
        show: {
            opacity: 1,
            transition: { staggerChildren: 0.1 }
        }
    }

    const itemVariants = {
        hidden: { opacity: 0, y: 20 },
        show: { opacity: 1, y: 0, transition: { type: 'spring', stiffness: 300, damping: 24 } }
    }

    return (
        <motion.div 
            className="w-full max-w-4xl mx-auto relative overflow-visible"
            style={{ display: 'flex', flexDirection: 'column', gap: '24px', paddingBottom: '40px', width: '100%', maxWidth: '896px', margin: '0 auto' }}
            variants={containerVariants}
            initial="hidden"
            animate="show"
        >
            <GridPattern className="opacity-10 absolute inset-0 -z-10" />

            <motion.div variants={itemVariants} className="text-center" style={{ padding: '32px 0' }}>
                <div className="w-[300px] h-[100px] mx-auto mb-6 relative">
                    <img src="sc-icon-transparent.png" alt="SonoClarity" className="w-full h-full object-contain filter drop-shadow-[0_0_15px_rgba(168,85,247,0.4)]" />
                </div>
                <h2 className="text-4xl font-extrabold tracking-tight text-white mb-2">SonoClarity</h2>
                <p className="text-lg text-purple-300/80 font-medium">Empowering Patients with Instant Clarity</p>
            </motion.div>

            <motion.div variants={itemVariants} className="card card-glass card-accent relative overflow-hidden border border-purple-500/20" style={{ padding: '32px' }}>
                <div className="absolute top-0 right-0 w-64 h-64 bg-purple-500/10 blur-[100px] rounded-full pointer-events-none" />
                <h3 className="text-2xl font-bold text-white mb-4">Our Mission</h3>
                <div className="space-y-4 text-gray-300 leading-relaxed text-[15px]">
                    <p>
                        Waiting for medical results can be one of the most stressful experiences a person can endure. At <strong className="text-purple-300">SonoClarity</strong>, our mission is to dramatically reduce the crushing anxiety and painful waiting times associated with breast cancer screenings.
                    </p>
                    <p>
                        By leveraging state-of-the-art Artificial Intelligence, we aim to provide patients with instantaneous, easy-to-understand insights about their ultrasound scans. Whether you are tracking progressive changes during annual checkups or seeking immediate second-reader confidence, this tool is designed to save you time and bring you peace of mind.
                    </p>
                </div>
            </motion.div>

            <div className="grid grid-cols-1 md:grid-cols-2" style={{ gap: '24px' }}>
                <motion.div variants={itemVariants} className="card card-glass border border-white/5 flex flex-col h-full" style={{ padding: '24px' }}>
                    <h3 className="text-xl font-bold text-white mb-2">Key Features</h3>
                    <div className="flex-1 flex flex-col justify-center space-y-4 mt-4">
                        {features.map((f, i) => (
                            <div key={i} className="flex items-center justify-between border-b border-white/5 pb-3 last:border-0 last:pb-0">
                                <div className="flex items-center gap-3 text-sm font-semibold text-gray-200">
                                    <div className="p-2 bg-black/30 rounded-lg">{f.icon}</div>
                                    {f.label}
                                </div>
                                <div className="text-xs text-right text-gray-400 max-w-[50%]">{f.value}</div>
                            </div>
                        ))}
                    </div>
                </motion.div>

                <motion.div variants={itemVariants} className="card card-glass border border-white/5 flex flex-col h-full" style={{ padding: '24px' }}>
                    <h3 className="text-xl font-bold text-white mb-3">Download Desktop App</h3>
                    <p className="text-sm text-gray-400 mb-6 leading-relaxed">
                        Want to run our advanced AI models directly on your hospital computer with built-in patient registry tracking? Download our native Windows software.
                    </p>
                    <div className="mt-auto">
                        <button 
                            className="w-full btn btn-primary py-4 rounded-xl flex items-center justify-center gap-3 hover:scale-[1.02] transition-transform shadow-[0_0_20px_rgba(168,85,247,0.3)] border border-purple-500/50" 
                            onClick={() => alert("The Desktop executable (.exe) is still compiling. Please check our GitHub repository for the latest release!")}
                        >
                            <Download size={20} /> Download SonoClarity (.exe)
                        </button>
                    </div>
                </motion.div>
            </div>

            <motion.div variants={itemVariants} className="card card-glass border border-white/5 relative overflow-hidden" style={{ padding: '32px', marginTop: '24px' }}>
                <h3 className="text-xl font-bold text-white mb-6 text-center">Powered By</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {techStack.map(({ icon, name }) => (
                        <div className="bg-black/20 hover:bg-black/40 border border-white/5 hover:border-white/10 rounded-xl p-4 flex flex-col items-center justify-center gap-3 transition-colors group cursor-default" key={name}>
                            {icon}
                            <span className="text-sm font-medium text-gray-300 group-hover:text-white transition-colors">{name}</span>
                        </div>
                    ))}
                </div>
            </motion.div>
        </motion.div>
    )
}
