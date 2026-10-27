import {EventEmitter} from 'node:events';

// Minimal TTY streams for driving Ink (the same shape ink-testing-library uses).
export class FakeStdin extends EventEmitter {
  isTTY = true;
  data: string | null = null;
  write = (data: string) => {
    this.data = data;
    this.emit('readable');
    this.emit('data', data);
  };
  read = () => {
    const {data} = this;
    this.data = null;
    return data;
  };
  setEncoding() {}
  setRawMode() {}
  resume() {}
  pause() {}
  ref() {}
  unref() {}
}

export class FakeStdout extends EventEmitter {
  columns = 100;
  frames: string[] = [];
  write = (frame: string, callback?: () => void) => {
    this.frames.push(frame);
    callback?.();
    return true;
  };
}
