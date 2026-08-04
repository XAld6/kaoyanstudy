import { beforeEach, describe, expect, it, vi } from "vitest";

const { formatDateMock, setSelectedDateMock, useStateMock } = vi.hoisted(() => {
  const setSelectedDateMock = vi.fn();
  return {
    formatDateMock: vi.fn(() => "2042-05-06"),
    setSelectedDateMock,
    useStateMock: vi.fn(() => ["2042-05-06", setSelectedDateMock])
  };
});

vi.mock("react", () => ({
  useState: useStateMock
}));

vi.mock("../studyCore", () => ({
  formatDate: formatDateMock
}));

import { getInitialSelectedDate, useSelectedDate } from "./useSelectedDate";

describe("useSelectedDate", () => {
  beforeEach(() => {
    formatDateMock.mockClear();
    setSelectedDateMock.mockClear();
    useStateMock.mockClear();
  });

  it("gets the default date from studyCore.formatDate", () => {
    expect(getInitialSelectedDate()).toBe("2042-05-06");
    expect(formatDateMock).toHaveBeenCalledOnce();
    expect(formatDateMock).toHaveBeenCalledWith();
  });

  it("passes getInitialSelectedDate to useState for lazy initialization", () => {
    expect(useSelectedDate()).toEqual(["2042-05-06", setSelectedDateMock]);
    expect(useStateMock).toHaveBeenCalledOnce();
    expect(useStateMock).toHaveBeenCalledWith(getInitialSelectedDate);
    expect(formatDateMock).not.toHaveBeenCalled();
  });
});
