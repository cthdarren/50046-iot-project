import type { CreateClientConfig } from '@hey-api/client-axios';

export const createClientConfig: CreateClientConfig = (config) => ({
  ...config,
  baseURL: 'http://iot-backend-alb-227826614.ap-southeast-1.elb.amazonaws.com',
});
