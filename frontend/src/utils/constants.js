export const ThreatCategory = {
  BRUTE_FORCE: 'BRUTE_FORCE',
  EXCESSIVE_REQUESTS: 'EXCESSIVE_REQUESTS',
  RECONNAISSANCE: 'RECONNAISSANCE',
  UNAUTHORIZED_ACCESS: 'UNAUTHORIZED_ACCESS',
};

export const ThreatCategoryLabels = {
  BRUTE_FORCE: 'Brute Force',
  EXCESSIVE_REQUESTS: 'Excessive Requests',
  RECONNAISSANCE: 'Reconnaissance',
  UNAUTHORIZED_ACCESS: 'Unauthorized Access',
};

export const Severity = {
  LOW: 'LOW',
  MEDIUM: 'MEDIUM',
  HIGH: 'HIGH',
};

export const AlertStatus = {
  ACTIVE: 'ACTIVE',
  INVESTIGATING: 'INVESTIGATING',
  RESOLVED: 'RESOLVED',
};

export const InvestigationStatus = {
  NEW: 'NEW',
  INVESTIGATING: 'INVESTIGATING',
  RESOLVED: 'RESOLVED',
};

export const AuthOutcome = {
  NONE: 'NONE',
  AUTHENTICATED: 'AUTHENTICATED',
  LOGIN_SUCCESS: 'LOGIN_SUCCESS',
  LOGIN_FAILED: 'LOGIN_FAILED',
  TOKEN_INVALID: 'TOKEN_INVALID',
  TOKEN_EXPIRED: 'TOKEN_EXPIRED',
  FORBIDDEN: 'FORBIDDEN',
};

export const Role = {
  ADMIN: 'ADMIN',
  ANALYST: 'ANALYST',
};

export const ReportType = {
  SUMMARY: 'SUMMARY',
  LOGS_CSV: 'LOGS_CSV',
  ALERTS_CSV: 'ALERTS_CSV',
};

export const ReportTypeLabels = {
  SUMMARY: 'Security Summary (Markdown)',
  LOGS_CSV: 'API Request Logs (CSV)',
  ALERTS_CSV: 'Security Alerts (CSV)',
};

export const HTTP_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS', 'HEAD'];
export const STATUS_CLASSES = ['2xx', '3xx', '4xx', '5xx'];
