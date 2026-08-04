export function minutesLabel(minutes: number) {
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  if (!hours) return `${rest} 分钟`;
  if (!rest) return `${hours} 小时`;
  return `${hours} 小时 ${rest} 分钟`;
}

export function daysLeft(examDate: string, today = new Date()) {
  if (!examDate) return 0;
  const start = new Date(`${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`);
  const exam = new Date(examDate);
  return Math.max(0, Math.ceil((exam.getTime() - start.getTime()) / 86400000));
}
