export const apiBaseUrl =
  process.env.API_INTERNAL_URL?.replace(/\/$/, "") ??
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ??
  "http://localhost:8000/api/v1";

export const DEFAULT_PAGE_SIZE = 25;
