import { cn } from "../../lib/utils";

/**
 * AnimatedBeam — Simulates a glowing data packet traveling along an SVG path.
 * Inspired by MagicUI.
 */
export function AnimatedBeam({
  className,
  containerRef,
  fromRef,
  toRef,
  pathColor = "rgba(123, 94, 167, 0.2)",
  pathWidth = 2,
  pathOpacity = 0.4,
  gradientStartColor = "#7B5EA7",
  gradientStopColor = "#a855f7",
  gradientId = "animated-beam-grad",
  delay = 0,
  duration = 3,
  reverse = false,
  pathData,
}) {
  return (
    <svg
      fill="none"
      width="100%"
      height="100%"
      xmlns="http://www.w3.org/2000/svg"
      className={cn("pointer-events-none absolute left-0 top-0 w-full h-full", className)}
    >
      <path
        d={pathData}
        stroke={pathColor}
        strokeWidth={pathWidth}
        strokeOpacity={pathOpacity}
        strokeLinecap="round"
      />
      <path
        d={pathData}
        stroke={`url(#${gradientId})`}
        strokeWidth={pathWidth + 1}
        strokeLinecap="round"
        style={{
          strokeDasharray: "15 100",
          animation: `beamSpin ${duration}s linear infinite`,
          animationDelay: `${delay}s`,
          animationDirection: reverse ? "reverse" : "normal",
        }}
      />
      <defs>
        <linearGradient
          id={gradientId}
          x1="0"
          y1="0"
          x2="0"
          y2="100%"
          gradientUnits="userSpaceOnUse"
        >
          <stop stopColor={gradientStartColor} stopOpacity="0"></stop>
          <stop stopColor={gradientStopColor}></stop>
        </linearGradient>
      </defs>
    </svg>
  );
}

export default AnimatedBeam;
