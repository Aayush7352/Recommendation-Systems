import clsx, { type ClassValue } from "clsx";

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatNumber(n: number, opts?: Intl.NumberFormatOptions) {
  return new Intl.NumberFormat("en-US", opts).format(n);
}

export function formatPercent(n: number, digits = 2) {
  return `${(n * 100).toFixed(digits)}%`;
}

export function formatScore(n: number, digits = 4) {
  return n.toFixed(digits);
}
