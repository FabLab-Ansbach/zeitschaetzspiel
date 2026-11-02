import { MAX_ENTRIES, rank, relDeviation, upsert, type Entry } from './leaderboard.ts';

const ok = (cond: boolean, what: string) => {
  if (!cond) throw new Error(`Check fehlgeschlagen: ${what}`);
};

const entry = (name: string, target: number, deviation: number): Entry => ({
  name,
  target_time: target,
  elapsed_time: target + deviation,
  deviation,
});

// Relative Abweichung schlägt absolute: 1 s auf 30 s ist besser als 0,9 s auf 5 s.
const ranked = rank([entry('absolut', 5000, -900), entry('relativ', 30000, 1000)]);
ok(ranked[0]!.name === 'relativ', 'Sortierung nach relativer Abweichung');
ok(relDeviation(entry('x', 20000, -500)) === 2.5, 'relDeviation in Prozent');

// target_time 0 landet hinten statt die Sortierung über NaN-Vergleiche zu zerstören.
ok(rank([entry('kaputt', 0, 0), entry('ok', 10000, 5000)])[0]!.name === 'ok', 'target_time 0');

// Kappung auf die besten 20
const many = Array.from({ length: 25 }, (_, i) => entry(`p${i}`, 10000, (i + 1) * 100));
ok(rank(many).length === MAX_ENTRIES, 'Kappung bei 20');
ok(rank(many).at(-1)!.name === 'p19', 'die schlechtesten fallen raus');

// upsert überschreibt denselben Namen statt zu duplizieren
const once = upsert(many, entry('p0', 10000, 50));
ok(once.filter((e) => e.name === 'p0').length === 1, 'kein Duplikat bei gleichem Namen');
ok(once[0]!.deviation === 50, 'alter Datensatz überschrieben');

// ein besserer Neueintrag drängt sich in eine volle Liste
const pushed = upsert(rank(many), entry('neu', 10000, 1));
ok(pushed[0]!.name === 'neu' && pushed.length === MAX_ENTRIES, 'Neueintrag in voller Liste');

console.log('leaderboard.ts: alle Checks ok');
