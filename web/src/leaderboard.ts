export type Entry = {
  name: string;
  target_time: number;
  elapsed_time: number;
  deviation: number;
};

const KEY = 'zeitschaetzspiel.leaderboard';
export const MAX_ENTRIES = 20;

export const relDeviation = (e: Entry) =>
  e.target_time ? (Math.abs(e.deviation) / e.target_time) * 100 : Infinity;

/** Sortiert nach relativer Abweichung und kappt auf die besten MAX_ENTRIES. */
export const rank = (entries: Entry[]) =>
  [...entries]
    .sort((a, b) => {
      const x = relDeviation(a);
      const y = relDeviation(b);
      return x === y ? 0 : x < y ? -1 : 1;
    })
    .slice(0, MAX_ENTRIES);

export const upsert = (entries: Entry[], entry: Entry) => {
  const i = entries.findIndex((e) => e.name === entry.name);
  const next = [...entries];
  if (i >= 0) next[i] = entry;
  else next.push(entry);
  return rank(next);
};

const isEntry = (e: unknown): e is Entry =>
  typeof e === 'object' &&
  e !== null &&
  (['name', 'target_time', 'elapsed_time', 'deviation'] as const).every((k) => k in e);

export function load(): Entry[] {
  try {
    const raw: unknown = JSON.parse(localStorage.getItem(KEY) ?? '[]');
    return Array.isArray(raw) ? rank(raw.filter(isEntry)) : [];
  } catch {
    return [];
  }
}

export const save = (entries: Entry[]) =>
  localStorage.setItem(KEY, JSON.stringify(entries));
