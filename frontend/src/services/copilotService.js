
const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || ""
).replace(/\/$/, "");

export async function sendCopilotMessage({
  message,
  history = [],
  organizationId
}) {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/copilot/chat`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        message,
        history,
        organization_id: organizationId || null
      })
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : "Unable to get a response from AI Copilot."
    );
  }

  return data.answer;
}
