
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";

// ==========================================
// SHARED API REQUEST FUNCTION
// ==========================================

async function getJson(path, params = {}) {
  const url = new URL(path, API_BASE_URL);

  Object.entries(params).forEach(([key, value]) => {
    if (value != null && value !== "") {
      url.searchParams.set(key, value);
    }
  });

  const response = await fetch(url.toString(), {
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    const body = await response.text();

    throw new Error(
      `API returned ${response.status}: ${body.slice(0, 200)}`
    );
  }

  return response.json();
}

// ==========================================
// 1. DASHBOARD TEAMS
// ==========================================

export function getDashboardTeams(organizationId) {
  return getJson("/api/v1/metrics/dashboard/teams", {
    organization_id: organizationId,
  });
}

// ==========================================
// 2. DASHBOARD SPRINTS
// ==========================================

export function getDashboardSprints(organizationId, teamId) {
  return getJson("/api/v1/metrics/dashboard/sprints", {
    organization_id: organizationId,
    team_id: teamId,
  });
}

// ==========================================
// 3. DASHBOARD METRICS
// ==========================================

export function getDashboardMetrics(
  organizationId,
  teamId,
  sprintId
) {
  return getJson("/api/v1/metrics/dashboard", {
    organization_id: organizationId,
    team_id: teamId,
    sprint_id: sprintId,
  });
}

// ==========================================
// 4. SPRINT METRICS
// ==========================================

export function getSprintMetrics(sprintId) {
  return getJson(
    `/api/v1/metrics/sprints/${encodeURIComponent(sprintId)}`
  );
}

// ==========================================
// 5. PROJECT VELOCITY
// ==========================================

export function getProjectVelocity(projectId) {
  return getJson(
    `/api/v1/metrics/projects/${encodeURIComponent(projectId)}/velocity`
  );
}

// ==========================================
// 6. DELIVERY SUMMARY
// ==========================================

export function getDeliverySummary(
  organizationId,
  teamId,
  sprintId
) {
  return getJson("/api/v1/metrics/delivery/summary", {
    organization_id: organizationId,
    team_id: teamId,
    sprint_id: sprintId,
  });
}

// ==========================================
// 7. HISTORICAL DELIVERY VELOCITY
// ==========================================

export function getDeliveryVelocity(
  organizationId,
  projectId,
  teamId = null
) {
  return getJson("/api/v1/metrics/delivery/velocity", {
    organization_id: organizationId,
    project_id: projectId,
    team_id: teamId,
  });
}
