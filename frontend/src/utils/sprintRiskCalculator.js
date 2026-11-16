
const clamp = (value) =>
  Math.max(0, Math.min(100, value));

const ratio = (part, total) =>
  total > 0 ? part / total : 0;

export function calculateSprintRisk({
  deliverySummary,
  sprintMetrics,
  velocityData,
  daysRemaining,
}) {
  const scope = deliverySummary?.current_scope;
  const commitment = deliverySummary?.commitment;
  const items = deliverySummary?.work_items;

  if (!scope || !items || !velocityData?.data_complete) {
    return null;
  }

  const totalPoints = Number(scope.total_points ?? 0);
  const remainingPoints = Number(scope.remaining_points ?? 0);
  const originalPoints = Number(commitment?.planned_points ?? 0);

  const totalItems = Number(items.total ?? 0);
  const blocked = Number(items.blocked ?? 0);
  const bugs = Number(items.bugs ?? 0);
  const reopened = Number(items.reopened ?? 0);

  const averageVelocity = Number(
    velocityData.average_velocity ?? 0
  );

  const history = velocityData.sprints ?? [];

  const durations = history.map((sprint) => {
    const start = Date.parse(`${sprint.start_date}T00:00:00Z`);
    const end = Date.parse(`${sprint.end_date}T00:00:00Z`);

    return (end - start) / 86400000 + 1;
  }).filter((days) => Number.isFinite(days) && days > 0);

  const averageDuration = durations.length
    ? durations.reduce((sum, days) => sum + days, 0)
        / durations.length
    : null;

  const expectedCapacity =
    averageDuration && averageVelocity > 0
      ? averageVelocity *
        (Math.max(0, Number(daysRemaining) || 0) / averageDuration)
      : null;

  const deliveryRisk =
    remainingPoints === 0
      ? 0
      : expectedCapacity == null
        ? null
        : clamp(
            100 * (1 - expectedCapacity / remainingPoints)
          );

  const qualityRisk = clamp(
    100 * ratio(bugs + reopened, totalItems)
  );

  const dependencyRisk = clamp(
    100 * ratio(blocked, totalItems)
  );

  const scopeGrowth = originalPoints > 0
    ? Math.max(0, totalPoints - originalPoints) / originalPoints
    : null;

  const scopeRisk = scopeGrowth == null
    ? null
    : clamp(scopeGrowth * 400);

  const capacityRisk = deliveryRisk;

  const categories = {
    delivery: deliveryRisk,
    quality: qualityRisk,
    dependency: dependencyRisk,
    capacity: capacityRisk,
    scope: scopeRisk,
  };

  const weights = {
    delivery: 0.35,
    quality: 0.20,
    dependency: 0.15,
    capacity: 0.15,
    scope: 0.15,
  };

  const available = Object.keys(categories).filter(
    (key) => categories[key] != null
  );

  const weightTotal = available.reduce(
    (sum, key) => sum + weights[key], 0
  );

  const sprintRisk = weightTotal > 0
    ? available.reduce(
        (sum, key) =>
          sum + categories[key] * weights[key], 0
      ) / weightTotal
    : null;

  return {
    sprintRisk: sprintRisk == null
      ? null
      : Math.round(sprintRisk),
    categories,
    indicators: {
      remainingPoints,
      blocked,
      bugs,
      reopened,
      scopeGrowth,
      expectedCapacity,
      averageVelocity,
      daysRemaining,
    },
  };
}
