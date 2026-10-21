export function rescaleWeights(
  current: Record<string, number>,
  changedId: string,
  rawValue: number,
  criterionIds: string[],
): Record<string, number> {
  const value = Math.max(0, Math.min(100, Number(rawValue)));
  const others = criterionIds.filter((id) => id !== changedId);
  const result: Record<string, number> = { ...current, [changedId]: value };

  if (others.length === 0) {
    return { [changedId]: 100 };
  }

  const remaining = 100 - value;
  const otherTotal = others.reduce((sum, id) => sum + Math.max(0, current[id] ?? 0), 0);

  if (otherTotal <= 0) {
    const each = remaining / others.length;
    others.forEach((id) => {
      result[id] = round1(each);
    });
  } else {
    others.forEach((id) => {
      result[id] = round1((Math.max(0, current[id] ?? 0) / otherTotal) * remaining);
    });
  }

  // Correct rounding drift so the displayed sliders always total exactly 100.
  const total = criterionIds.reduce((sum, id) => sum + (result[id] ?? 0), 0);
  const drift = round1(100 - total);
  if (Math.abs(drift) >= 0.1) {
    const lastOther = others[others.length - 1];
    result[lastOther] = round1(Math.max(0, (result[lastOther] ?? 0) + drift));
  }
  result[changedId] = round1(result[changedId]);
  return result;
}

export function round1(value: number): number {
  return Math.round(value * 10) / 10;
}

export function weightsToRecord(
  weights: Array<{ criterionId: string; weightValue: number }>,
  criteriaIds: string[],
): Record<string, number> {
  const record: Record<string, number> = {};
  criteriaIds.forEach((id) => {
    record[id] = 0;
  });
  weights.forEach((weight) => {
    if (id_in(record, weight.criterionId)) {
      record[weight.criterionId] = weight.weightValue;
    }
  });
  return record;
}

function id_in(record: Record<string, number>, id: string): boolean {
  return Object.prototype.hasOwnProperty.call(record, id);
}
