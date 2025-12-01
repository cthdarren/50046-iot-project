import { defineConfig } from '@hey-api/openapi-ts';

export default [
    {
      input: '/home/lingyuan/Downloads/openapi_analytics_service.json',
      output: 'app/services/analytics',
    },
    {
      input: '/home/lingyuan/Downloads/openapi_availability_service.json',
      output: 'app/services/availability',
    },
];
