const BAUD = 9600;

export type Handlers = {
  onLine: (line: string) => void;
  onClose: () => void;
};

export const supported = () => 'serial' in navigator;

let reader: ReadableStreamDefaultReader<Uint8Array> | null = null;

async function readLoop(port: SerialPort, h: Handlers) {
  reader = port.readable!.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  try {
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split(/\r?\n/);
      buffer = lines.pop()!;
      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed) h.onLine(trimmed);
      }
    }
  } catch {
    // Port abgezogen oder geschlossen
  }
  reader = null;
  h.onClose();
}

async function attach(port: SerialPort, h: Handlers) {
  await port.open({ baudRate: BAUD });
  port.addEventListener('disconnect', h.onClose);
  void readLoop(port, h);
  return port;
}

export async function connect(h: Handlers) {
  return attach(await navigator.serial.requestPort(), h);
}

/** Bereits freigegebener Port: öffnet ohne User-Gesture (Kiosk nach Reboot). */
export async function reconnect(h: Handlers) {
  const [port] = await navigator.serial.getPorts();
  if (!port) return null;
  try {
    return await attach(port, h);
  } catch {
    return null;
  }
}

export async function sendStart(port: SerialPort) {
  const writer = port.writable!.getWriter();
  try {
    await writer.write(new TextEncoder().encode('START_GAME\n'));
  } finally {
    writer.releaseLock();
  }
}

export async function disconnect(port: SerialPort) {
  await reader?.cancel().catch(() => {});
  await port.close().catch(() => {});
}
