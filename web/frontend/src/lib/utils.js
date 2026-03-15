import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge Tailwind classes with clsx for conditional styling.
 * Usage: cn("base-class", condition && "conditional-class", "override-class")
 */
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}
