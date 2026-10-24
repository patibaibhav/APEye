import apiClient from '../api/client';
import alertsPageFixture from './fixtures/alerts-page.json';
import alertDetailFixture from './fixtures/alert-detail.json';
import alertSeverityFixture from './fixtures/alert-severity.json';
import dashboardSummaryFixture from './fixtures/dashboard-summary.json';
import loginResponseFixture from './fixtures/login-response.json';
import logsPageFixture from './fixtures/logs-page.json';
import reportsPageFixture from './fixtures/reports-page.json';
import reportsSummaryFixture from './fixtures/reports-summary.json';
import responseTimesFixture from './fixtures/response-times.json';
import statusDistributionFixture from './fixtures/status-distribution.json';
import suspiciousIpsPageFixture from './fixtures/suspicious-ips-page.json';
import suspiciousIpDetailFixture from './fixtures/suspicious-ip-detail.json';
import topEndpointsFixture from './fixtures/top-endpoints.json';
import usersPageFixture from './fixtures/users-page.json';

export function setupMockAdapter() {
  if (import.meta.env.VITE_USE_MOCKS !== 'true') {
    return;
  }

  // Clone fixtures to allow local mutations during demo / test runs
  let alertsData = JSON.parse(JSON.stringify(alertsPageFixture));
  let alertDetailData = JSON.parse(JSON.stringify(alertDetailFixture));
  let suspiciousIpsData = JSON.parse(JSON.stringify(suspiciousIpsPageFixture));
  let suspiciousIpDetailData = JSON.parse(JSON.stringify(suspiciousIpDetailFixture));
  let usersData = JSON.parse(JSON.stringify(usersPageFixture));
  let reportsData = JSON.parse(JSON.stringify(reportsPageFixture));

  // Override apiClient adapter with our custom mock router
  apiClient.defaults.adapter = async (config) => {
    const url = (config.url || '').replace(/^\/api/, '');
    const method = (config.method || 'get').toLowerCase();

    // Helper to simulate network latency
    await new Promise((resolve) => setTimeout(resolve, 60));

    // Route matching
    // 1. Auth routes
    if (url === '/auth/login' && method === 'post') {
      const body = typeof config.data === 'string' ? JSON.parse(config.data || '{}') : config.data;
      if (body.username && body.password) {
        return {
          data: loginResponseFixture,
          status: 200,
          statusText: 'OK',
          headers: {},
          config,
        };
      }
      return Promise.reject({
        response: {
          status: 401,
          data: {
            error: {
              code: 'INVALID_CREDENTIALS',
              message: 'Invalid username or password',
              details: null,
              request_id: 'mock-req-auth-fail',
            },
          },
        },
      });
    }

    if (url === '/auth/logout' && method === 'post') {
      return { data: null, status: 204, statusText: 'No Content', headers: {}, config };
    }

    if (url === '/auth/me' && method === 'get') {
      return {
        data: loginResponseFixture.user,
        status: 200,
        statusText: 'OK',
        headers: {},
        config,
      };
    }

    // 2. Dashboard routes
    if (url === '/dashboard/summary' && method === 'get') {
      return { data: dashboardSummaryFixture, status: 200, statusText: 'OK', headers: {}, config };
    }
    if (url === '/dashboard/traffic' && method === 'get') {
      const trafficFixture = (await import('./fixtures/traffic.json')).default;
      return { data: trafficFixture, status: 200, statusText: 'OK', headers: {}, config };
    }
    if (url === '/dashboard/status-distribution' && method === 'get') {
      return { data: statusDistributionFixture, status: 200, statusText: 'OK', headers: {}, config };
    }
    if (url === '/dashboard/top-endpoints' && method === 'get') {
      return { data: topEndpointsFixture, status: 200, statusText: 'OK', headers: {}, config };
    }
    if (url === '/dashboard/response-times' && method === 'get') {
      return { data: responseTimesFixture, status: 200, statusText: 'OK', headers: {}, config };
    }
    if (url === '/dashboard/alert-severity' && method === 'get') {
      return { data: alertSeverityFixture, status: 200, statusText: 'OK', headers: {}, config };
    }

    // 3. Logs routes
    if (url.startsWith('/logs') && method === 'get') {
      if (url === '/logs') {
        return { data: logsPageFixture, status: 200, statusText: 'OK', headers: {}, config };
      }
      const logId = url.split('/')[2];
      const found = logsPageFixture.items.find((item) => String(item.id) === String(logId));
      if (found) {
        return { data: found, status: 200, statusText: 'OK', headers: {}, config };
      }
      return { data: logsPageFixture.items[0], status: 200, statusText: 'OK', headers: {}, config };
    }

    // 4. Alerts routes
    if (url === '/alerts' && method === 'get') {
      return { data: alertsData, status: 200, statusText: 'OK', headers: {}, config };
    }

    if (url.match(/^\/alerts\/\d+\/status$/) && method === 'patch') {
      const body = typeof config.data === 'string' ? JSON.parse(config.data || '{}') : config.data;
      alertDetailData.status = body.status;
      const item = alertsData.items.find((a) => a.id === alertDetailData.id);
      if (item) item.status = body.status;
      return { data: alertDetailData, status: 200, statusText: 'OK', headers: {}, config };
    }

    if (url.match(/^\/alerts\/\d+\/notes$/) && method === 'post') {
      const body = typeof config.data === 'string' ? JSON.parse(config.data || '{}') : config.data;
      const newNote = {
        id: alertDetailData.notes.length + 1,
        alert_id: alertDetailData.id,
        author_id: 1,
        author_username: 'admin',
        note: body.note,
        created_at: new Date().toISOString(),
      };
      alertDetailData.notes.push(newNote);
      return { data: newNote, status: 201, statusText: 'Created', headers: {}, config };
    }

    if (url.match(/^\/alerts\/\d+$/) && method === 'get') {
      return { data: alertDetailData, status: 200, statusText: 'OK', headers: {}, config };
    }

    // 5. Suspicious IPs routes
    if (url === '/suspicious-ips' && method === 'get') {
      return { data: suspiciousIpsData, status: 200, statusText: 'OK', headers: {}, config };
    }

    if (url.match(/^\/suspicious-ips\/[^/]+\/investigation$/) && method === 'patch') {
      const body = typeof config.data === 'string' ? JSON.parse(config.data || '{}') : config.data;
      suspiciousIpDetailData.investigation_status = body.status;
      if (body.note) suspiciousIpDetailData.investigation_note = body.note;
      return { data: suspiciousIpDetailData, status: 200, statusText: 'OK', headers: {}, config };
    }

    if (url.startsWith('/suspicious-ips/') && method === 'get') {
      return { data: suspiciousIpDetailData, status: 200, statusText: 'OK', headers: {}, config };
    }

    // 6. Reports & Exports
    if (url === '/reports/summary' && method === 'get') {
      return { data: reportsSummaryFixture, status: 200, statusText: 'OK', headers: {}, config };
    }

    if (url === '/reports/archive' && method === 'post') {
      const body = typeof config.data === 'string' ? JSON.parse(config.data || '{}') : config.data;
      const newArchive = {
        id: reportsData.items.length + 1,
        report_type: body.report_type,
        object_key: `dev/${body.report_type.toLowerCase()}/mock-key.csv`,
        storage_backend: 'local',
        size_bytes: 512,
        created_at: new Date().toISOString(),
        range: { from: body.from, to: body.to },
      };
      reportsData.items.unshift(newArchive);
      return { data: newArchive, status: 201, statusText: 'Created', headers: {}, config };
    }

    if (url === '/reports' && method === 'get') {
      return { data: reportsData, status: 200, statusText: 'OK', headers: {}, config };
    }

    if (url.match(/^\/reports\/\d+\/download$/) && method === 'get') {
      return {
        data: {
          url: 'data:text/plain;charset=utf-8,Mock%20Export%20Data',
          expires_at: new Date(Date.now() + 300000).toISOString(),
        },
        status: 200,
        statusText: 'OK',
        headers: {},
        config,
      };
    }

    if (url.startsWith('/exports/') && method === 'get') {
      return {
        data: new Blob(['time,ip,path,status\n2026-01-15T10:30:00Z,203.0.113.10,/api/logs,200'], { type: 'text/csv' }),
        status: 200,
        statusText: 'OK',
        headers: { 'content-type': 'text/csv' },
        config,
      };
    }

    // 7. Users
    if (url === '/users' && method === 'get') {
      return { data: usersData, status: 200, statusText: 'OK', headers: {}, config };
    }

    if (url === '/users' && method === 'post') {
      const body = typeof config.data === 'string' ? JSON.parse(config.data || '{}') : config.data;
      const newUser = {
        id: usersData.items.length + 1,
        username: body.username,
        role: body.role,
        is_active: true,
        created_at: new Date().toISOString(),
        last_login_at: null,
      };
      usersData.items.push(newUser);
      return { data: newUser, status: 201, statusText: 'Created', headers: {}, config };
    }

    if (url.match(/^\/users\/\d+$/) && method === 'patch') {
      const body = typeof config.data === 'string' ? JSON.parse(config.data || '{}') : config.data;
      const userId = Number(url.split('/')[2]);
      const user = usersData.items.find((u) => u.id === userId);
      if (user) {
        if (body.is_active !== undefined) user.is_active = body.is_active;
        if (body.role !== undefined) user.role = body.role;
        return { data: user, status: 200, statusText: 'OK', headers: {}, config };
      }
    }

    // Default fallback: 404
    return Promise.reject({
      response: {
        status: 404,
        data: {
          error: {
            code: 'NOT_FOUND',
            message: `Mock not found for ${method.toUpperCase()} ${url}`,
            details: null,
            request_id: 'mock-404',
          },
        },
      },
    });
  };
}

export default setupMockAdapter;
