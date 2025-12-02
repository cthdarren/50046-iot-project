import type { CreateClientConfig } from '@hey-api/client-axios';

export const createClientConfig: CreateClientConfig = (config) => ({
  ...config,
  baseURL: 'http://iot-alb-359304225.ap-southeast-1.elb.amazonaws.com/analytics',
});
