import { cn } from "../../lib/utils";

/**
 * BorderBeam — An animated beam of light that travels along the border.
 * Inspired by MagicUI. Used on key cards to draw subtle attention.
 */
export function BorderBeam({
  size = 200,
  duration = 12,
  delay = 0,
  colorFrom = "#7B5EA7",
  colorTo = "#9CAF88",
  className,
}) {
  return (
    <div
      className={cn("pointer-events-none absolute inset-0 rounded-[inherit]", className)}
      style={{ overflow: "hidden" }}
    >
      <div
        style={{
          position: "absolute",
          inset: 0,
          borderRadius: "inherit",
          mask: "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)",
          WebkitMask: "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)",
          maskComposite: "exclude",
          WebkitMaskComposite: "xor",
          padding: "1px",
        }}
      >
        <div
          style={{
            position: "absolute",
            width: `${size}px`,
            height: `${size}px`,
            top: "50%",
            left: "50%",
            background: `conic-gradient(from 0deg, transparent 0%, ${colorFrom} 10%, ${colorTo} 20%, transparent 30%)`,
            animation: `borderBeamSpin ${duration}s linear infinite`,
            animationDelay: `${delay}s`,
            borderRadius: "50%",
            transform: "translate(-50%, -50%)",
          }}
        />
      </div>
    </div>
  );
}

export default BorderBeam;
