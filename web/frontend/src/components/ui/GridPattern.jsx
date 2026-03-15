import { useId } from "react";
import { cn } from "../../lib/utils";

/**
 * GridPattern — A subtle animated grid background inspired by MagicUI.
 * Renders an SVG grid with optional highlighted squares that pulse gently.
 */
export function GridPattern({
  width = 40,
  height = 40,
  squares = [],
  strokeDasharray = "0",
  className,
  ...props
}) {
  const id = useId();

  return (
    <svg
      aria-hidden="true"
      className={cn(
        "pointer-events-none absolute inset-0 h-full w-full fill-gray-400/[0.03] stroke-gray-400/[0.07]",
        className
      )}
      {...props}
    >
      <defs>
        <pattern
          id={id}
          width={width}
          height={height}
          patternUnits="userSpaceOnUse"
          x={-1}
          y={-1}
        >
          <path
            d={`M.5 ${height}V.5H${width}`}
            fill="none"
            strokeDasharray={strokeDasharray}
          />
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill={`url(#${id})`} />
      {squares && squares.length > 0 && (
        <svg x={-1} y={-1} className="overflow-visible">
          {squares.map(([x, y], idx) => (
            <rect
              key={`${x}-${y}-${idx}`}
              width={width - 1}
              height={height - 1}
              x={x * width + 1}
              y={y * height + 1}
              strokeWidth="0"
              className="fill-purple-500/[0.06]"
              style={{
                animation: `gridPulse ${3 + idx * 0.5}s ease-in-out infinite`,
                animationDelay: `${idx * 0.8}s`,
              }}
            />
          ))}
        </svg>
      )}
    </svg>
  );
}

export default GridPattern;
