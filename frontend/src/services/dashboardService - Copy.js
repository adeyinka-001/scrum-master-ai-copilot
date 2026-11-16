
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";

export async function getDashboardMetrics(organizationId) {
  const url = new URL(
    "/api/v1/metrics/dashboard",
    API_BASE_URL
  );

  url.searchParams.set(
    "organization_id",
    organizationId
  );

  const response = await fetch(url, {
    headers: {
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(
      `Dashboard request failed: ${response.status}`
    );
  }

  return response.json();
}
