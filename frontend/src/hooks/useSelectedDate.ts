import { useState } from "react";
import { formatDate } from "../studyCore";

export function getInitialSelectedDate(): string {
  return formatDate();
}

export function useSelectedDate(): [string, React.Dispatch<React.SetStateAction<string>>] {
  return useState(getInitialSelectedDate);
}
