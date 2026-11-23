import type { Config } from 'jest';

// Jest + ts-jest + jsdom (research §12). Cobertura con umbral del 60 % sobre la lógica,
// la sesión y el cliente de la API (constitución, principio VI).
const config: Config = {
  testEnvironment: 'jsdom',
  roots: ['<rootDir>/tests'],
  transform: {
    '^.+\\.tsx?$': ['ts-jest', { tsconfig: '<rootDir>/tsconfig.jest.json' }],
  },
  setupFilesAfterEnv: ['<rootDir>/tests/setup.ts'],
  moduleNameMapper: {
    // src/config.ts usa import.meta.env, que Jest (CommonJS) no entiende.
    '^(\\.{1,2}/)+(src/)?config$': '<rootDir>/tests/mocks/config.ts',
    '\\.(css)$': 'identity-obj-proxy',
  },
  collectCoverageFrom: [
    'src/logica/**/*.{ts,tsx}',
    'src/auth/**/*.{ts,tsx}',
    'src/api/**/*.{ts,tsx}',
    'src/leerConfig.ts',
  ],
  coverageReporters: ['text', 'lcov', 'html'],
  coverageDirectory: 'coverage',
  coverageThreshold: {
    global: { branches: 60, functions: 60, lines: 60, statements: 60 },
  },
};

export default config;
