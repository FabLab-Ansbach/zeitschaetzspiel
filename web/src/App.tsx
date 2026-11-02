import { useEffect, useRef, useState } from 'react';
import * as lb from './leaderboard.ts';
import { connect, disconnect, reconnect, sendStart, supported } from './serial.ts';

type Phase = 'disconnected' | 'connecting' | 'idle' | 'armed' | 'waiting' | 'running' | 'result';

const STATUS: Record<Phase, string> = {
  disconnected: 'Nicht verbunden',
  connecting: 'Warte auf den Arduino…',
  idle: 'Spiel bereit',
  armed: 'Spiel wird vorbereitet…',
  waiting: 'Bereit zum Start',
  running: 'Zeitmessung läuft…',
  result: 'Spiel beendet',
};

const HINT: Record<Phase, string> = {
  disconnected: 'Verbinde dich zuerst mit dem Arduino.',
  connecting: 'Der Arduino startet nach dem Verbinden neu – das dauert ein paar Sekunden.',
  idle: "Drücke 'Neues Spiel starten'",
  armed: 'Warte auf Spielstart…',
  waiting: 'Drücke den Taster zum Starten der Zeitmessung',
  running: 'Drücke den Taster erneut zum Stoppen',
  result: 'Trage Namen ein oder starte neu',
};

const sounds = new Map<string, HTMLAudioElement>();
function play(file: string) {
  let sound = sounds.get(file);
  if (!sound) sounds.set(file, (sound = new Audio(`audio/${file}.mp3`)));
  sound.currentTime = 0;
  void sound.play().catch(() => {});
}

const seconds = (ms: number, digits = 3) => (ms / 1000).toFixed(digits);

// Eingefärbt wird nach relativer Abweichung, weil die Rangliste danach sortiert
const accuracy = (relPercent: number) => (relPercent < 2 ? 'good' : relPercent < 5 ? 'warn' : 'bad');

type Dialog = { kind: 'overwrite'; entry: lb.Entry } | { kind: 'clear' } | null;

export function App() {
  const [phase, setPhase] = useState<Phase>('disconnected');
  const [connected, setConnected] = useState(false);
  const [target, setTarget] = useState<number | null>(null);
  const [elapsed, setElapsed] = useState<number | null>(null);
  const [deviation, setDeviation] = useState<number | null>(null);
  const [name, setName] = useState('');
  const [savedName, setSavedName] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [dialog, setDialog] = useState<Dialog>(null);
  const [board, setBoard] = useState<lb.Entry[]>(() => lb.load());
  const port = useRef<SerialPort | null>(null);

  const value = (line: string) => Number(line.split(':')[1]!.trim());

  const handlers = {
    onLine(line: string) {
      if (line === 'PC_READY') return setPhase('idle');
      if (line === 'WAITING_FOR_BUTTON') return setPhase('waiting');
      if (line === 'TIME_STARTED') {
        play('start');
        return setPhase('running');
      }
      if (line.startsWith('TARGET_TIME:')) return setTarget(value(line));
      if (line.startsWith('ELAPSED_TIME:')) return setElapsed(value(line));
      if (line.startsWith('DEVIATION:')) {
        const dev = value(line);
        const abs = Math.abs(dev);
        play(abs >= 10000 ? 'fail' : abs === 0 ? 'winner' : 'good');
        setDeviation(dev);
        return setPhase('result');
      }
      // GAME_ENDED und die Debug-Zeilen des Sketches brauchen keine Reaktion
    },
    onClose() {
      if (!port.current) return;
      port.current = null;
      setConnected(false);
      setPhase('disconnected');
      setNotice('Verbindung zum Arduino verloren!');
    },
  };

  useEffect(() => {
    if (supported()) {
      void reconnect(handlers).then((p) => {
        port.current = p;
        if (p) {
          setConnected(true);
          setPhase('connecting');
        }
      });
    }
  }, []);

  async function onConnect() {
    setNotice(null);
    try {
      port.current = await connect(handlers);
      setConnected(true);
      setPhase('connecting');
    } catch {
      setNotice('Konnte den Port nicht öffnen.');
    }
  }

  async function onDisconnect() {
    const open = port.current;
    port.current = null;
    setConnected(false);
    setPhase('disconnected');
    if (open) await disconnect(open);
  }

  async function startGame() {
    if (!port.current) return setNotice('Keine Verbindung zum Arduino!');
    setTarget(null);
    setElapsed(null);
    setDeviation(null);
    setName('');
    setSavedName(null);
    setNotice(null);
    setDialog(null);
    setPhase('armed');
    try {
      await sendStart(port.current);
    } catch {
      setNotice('Fehler beim Senden an Arduino. Verbindung wird getrennt.');
      void onDisconnect();
    }
  }

  function commit(entry: lb.Entry) {
    const next = lb.upsert(board, entry);
    setBoard(next);
    lb.save(next);
    setSavedName(entry.name);
    setDialog(null);
    setNotice(`'${entry.name}' zur Rangliste hinzugefügt!`);
  }

  function submit() {
    const trimmed = name.trim();
    if (!trimmed) return setNotice('Bitte gib einen Namen ein!');
    if (target === null || elapsed === null || deviation === null) {
      return setNotice('Keine gültigen Spieldaten zum Speichern vorhanden.');
    }
    const entry: lb.Entry = {
      name: trimmed,
      target_time: target,
      elapsed_time: elapsed,
      deviation,
    };
    if (board.some((e) => e.name === trimmed)) return setDialog({ kind: 'overwrite', entry });
    commit(entry);
  }

  function skip() {
    setTarget(null);
    setElapsed(null);
    setDeviation(null);
    setName('');
    setNotice(null);
    setPhase('idle');
  }

  function replace(entries: lb.Entry[]) {
    setBoard(entries);
    lb.save(entries);
    setDialog(null);
  }

  const canSubmit = phase === 'result' && savedName === null;

  if (!supported()) {
    return (
      <div className="app">
        <Header />
        <section className="card unsupported">
          <h2>Web Serial nicht verfügbar</h2>
          <p>
            Dieses Spiel spricht den Arduino direkt über die Web-Serial-Schnittstelle an. Die
            unterstützen <strong>Chrome, Edge, Opera und neuere Firefox-Versionen</strong> auf dem
            Desktop – und nur über HTTPS oder localhost.
          </p>
          <p className="muted">
            Alternativ lässt sich das Spiel weiterhin lokal mit <code>python3 game.py</code> starten.
          </p>
        </section>
      </div>
    );
  }

  return (
    <div className="app">
      <Header>
        <span className={`pill ${connected ? 'on' : 'off'}`}>
          {connected ? 'Verbunden' : 'Nicht verbunden'}
        </span>
        {connected ? (
          <button className="ghost" onClick={onDisconnect}>
            Trennen
          </button>
        ) : (
          <button className="ghost" onClick={onConnect}>
            Arduino verbinden
          </button>
        )}
      </Header>

      <main>
        <section className={`card stage phase-${phase}`}>
          <p className="status" aria-live="polite">
            {STATUS[phase]}
          </p>

          <div className="target">
            <span className="caption">Zielzeit</span>
            {target === null ? (
              <span className="hero placeholder">{phase === 'armed' ? '…' : '–'}</span>
            ) : (
              <span className="hero">
                {seconds(target, 1)}
                <span className="unit">s</span>
              </span>
            )}
          </div>

          <p className="hint">{HINT[phase]}</p>

          {elapsed !== null && deviation !== null && target !== null && (
            <div className="result">
              <div className="stat">
                <span className="caption">Deine Zeit</span>
                <strong>
                  {seconds(elapsed)}
                  <span className="unit">s</span>
                </strong>
              </div>
              <div className={`stat ${accuracy((Math.abs(deviation) / target) * 100)}`}>
                <span className="caption">Abweichung</span>
                <strong>
                  {seconds(Math.abs(deviation))}
                  <span className="unit">s</span>
                </strong>
                <span className="sub">
                  {((Math.abs(deviation) / target) * 100).toFixed(1)} %
                </span>
              </div>
            </div>
          )}

          <div className="controls">
            <button className="primary" onClick={startGame} disabled={!connected}>
              Neues Spiel starten
            </button>
          </div>

          <div className="save">
            <input
              type="text"
              placeholder="Spielername"
              value={name}
              maxLength={24}
              disabled={!canSubmit}
              onChange={(e) => setName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && submit()}
            />
            <button className="accent" onClick={submit} disabled={!canSubmit}>
              Zur Rangliste hinzufügen
            </button>
            <button className="ghost" onClick={skip} disabled={phase !== 'result'}>
              Überspringen
            </button>
          </div>

          {dialog?.kind === 'overwrite' && (
            <div className="prompt">
              <p>Der Name ist bereits in der Rangliste vorhanden. Möchtest du ihn überschreiben?</p>
              <div>
                <button className="accent" onClick={() => commit(dialog.entry)}>
                  Überschreiben
                </button>
                <button className="ghost" onClick={() => setDialog(null)}>
                  Abbrechen
                </button>
              </div>
            </div>
          )}

          {notice && (
            <p className="notice" onClick={() => setNotice(null)}>
              {notice}
            </p>
          )}
        </section>

        <aside className="card board">
          <header>
            <h2>Rangliste</h2>
            <button
              className="ghost small"
              onClick={() => setDialog({ kind: 'clear' })}
              disabled={board.length === 0}
            >
              Zurücksetzen
            </button>
          </header>

          {dialog?.kind === 'clear' && (
            <div className="prompt">
              <p>Möchtest du wirklich die gesamte Rangliste löschen? Das kann nicht rückgängig gemacht werden.</p>
              <div>
                <button className="danger" onClick={() => replace([])}>
                  Alles löschen
                </button>
                <button className="ghost" onClick={() => setDialog(null)}>
                  Abbrechen
                </button>
              </div>
            </div>
          )}

          <ol className="rows">
            {board.map((entry, i) => (
              <li key={entry.name} className={entry.name === savedName ? 'fresh' : undefined}>
                <span className="rank">{i + 1}</span>
                <span className="who">
                  <strong>{entry.name}</strong>
                  <span className="trace">
                    {seconds(entry.target_time, 1)} s → {seconds(entry.elapsed_time)} s
                  </span>
                </span>
                <span className="score">
                  <strong className={accuracy(lb.relDeviation(entry))}>
                    {lb.relDeviation(entry).toFixed(2)} %
                  </strong>
                  <span className="trace">{seconds(Math.abs(entry.deviation))} s</span>
                </span>
                <button
                  className="remove"
                  title={`${entry.name} löschen`}
                  onClick={() => replace(board.filter((e) => e.name !== entry.name))}
                >
                  ✕
                </button>
              </li>
            ))}
          </ol>
          {board.length === 0 && <p className="empty">Noch keine Messungen gespeichert.</p>}
          <p className="muted small">
            Die besten {lb.MAX_ENTRIES} Messungen, sortiert nach relativer Abweichung. Gespeichert
            nur in diesem Browser.
          </p>
        </aside>
      </main>
    </div>
  );
}

function Header({ children }: { children?: React.ReactNode }) {
  return (
    <header className="top">
      <h1>
        Zeit<span>-Schätz-</span>Spiel
      </h1>
      <div className="conn">{children}</div>
    </header>
  );
}
