export function calculateDateRangeDuration(start: Date, end: Date): string {
  const ms = Math.abs(end.getTime() - start.getTime());

  const totalMinutes = Math.floor(ms / (1000 * 60));
  const totalHours = Math.floor(ms / (1000 * 60 * 60));
  const days = Math.floor(totalHours / 24);
  const hours = totalHours % 24;
  const minutes = totalMinutes % 60;

  // Format cleanly:
  const parts: string[] = [];

  if (days > 0) parts.push(`${days} day${days !== 1 ? "s" : ""}`);
  if (hours > 0) parts.push(`${hours} hour${hours !== 1 ? "s" : ""}`);
  if (minutes > 0 && days === 0) {
    // only show minutes if duration < 1 day (cleaner)
    parts.push(`${minutes} min`);
  }

  return parts.join(" ");
}
