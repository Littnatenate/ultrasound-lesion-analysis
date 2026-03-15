import { motion, AnimatePresence } from "framer-motion";
import { GridPattern } from "./ui/GridPattern";

/**
 * SplashScreen — Professional "first impression" loading screen.
 * Features a subtle GridPattern background, scanning ring, and shimmer logo.
 * Uses Framer Motion for smooth entrance/exit transitions.
 */
export default function SplashScreen({ isVisible }) {
  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          key="splash"
          className="splash-screen"
          initial={{ opacity: 1 }}
          exit={{ opacity: 0, scale: 1.02 }}
          transition={{ duration: 0.8, ease: "easeInOut" }}
          style={{ position: "fixed", inset: 0, zIndex: 1000 }}
        >
          {/* Animated grid background */}
          <GridPattern
            width={48}
            height={48}
            squares={[
              [2, 3],
              [5, 1],
              [8, 5],
              [3, 7],
              [10, 3],
              [7, 8],
              [1, 5],
              [12, 6],
            ]}
            className="opacity-60"
          />

          {/* Radial gradient overlay for depth */}
          <div
            style={{
              position: "absolute",
              inset: 0,
              background:
                "radial-gradient(circle at 50% 50%, transparent 0%, var(--bg-primary) 70%)",
              pointerEvents: "none",
            }}
          />

          {/* Content */}
          <motion.div
            style={{
              position: "relative",
              zIndex: 1,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
            }}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            {/* Logo */}
            <div
              className="splash-logo"
              style={{
                background: "transparent",
                boxShadow: "none",
                width: 320,
                height: 120,
              }}
            >
              <img
                src="sc-logo-transparent.png"
                alt="SonoClarity"
                style={{
                  width: "100%",
                  height: "100%",
                  objectFit: "contain",
                }}
              />
            </div>

            {/* Shimmer Title */}
            <h1 className="shimmer-text" style={{ fontSize: "1.6rem", fontWeight: 700, marginBottom: 8 }}>
              SonoClarity
            </h1>

            {/* Subtitle */}
            <p
              style={{
                fontSize: "0.85rem",
                color: "var(--text-muted)",
                marginBottom: 32,
              }}
            >
              Initializing AI model...
            </p>

            {/* Scanning Ring */}
            <div className="scanning-ring" />

            {/* Status */}
            <motion.p
              style={{
                fontSize: "0.8rem",
                color: "var(--text-muted)",
              }}
              animate={{ opacity: [0.4, 1, 0.4] }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              Loading Detectron2 + PointRend
            </motion.p>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
