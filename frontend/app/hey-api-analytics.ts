import type { CreateClientConfig } from '@hey-api/client-axios';

export const createClientConfig: CreateClientConfig = (config) => ({
  ...config,
  baseURL: 'https://tingtangwalawalabingbang.com/analytics',
});
