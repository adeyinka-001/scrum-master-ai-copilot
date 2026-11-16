
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

async function getJson(path, params) {
  const url = new URL(path, API_BASE_URL);

  Object.entries(params).forEach(([key, value]) => {
    if (value) url.searchParams.set(key, value);
  });

  const response = await fetch(url.toString(), {
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    const body = await response.text();

    throw new Error(
      `API returned ${response.status}: ${body.slice(0, 200)}`
    );
  }

  return response.json();
}

export function getDashboardTeams(organizationId) {
  return getJson("/api/v1/metrics/dashboard/teams", {
    organization_id: organizationId,
  });
}

export function getDashboardSprints(organizationId, teamId) {
  return getJson("/api/v1/metrics/dashboard/sprints", {
    organization_id: organizationId,
    team_id: teamId,
  });
}

export function getDashboardMetrics(organizationId, teamId, sprintId) {
  return getJson("/api/v1/metrics/dashboard", {
    organization_id: organizationId,
    team_id: teamId,
    sprint_id: sprintId,
  });
}
