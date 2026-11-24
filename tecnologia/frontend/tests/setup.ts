import '@testing-library/jest-dom';
import { TextDecoder, TextEncoder } from 'util';

// jsdom no define TextEncoder/TextDecoder, que usa React Router.
Object.assign(globalThis, { TextEncoder, TextDecoder });
