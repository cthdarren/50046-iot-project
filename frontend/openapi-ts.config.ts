import { defineConfig } from '@hey-api/openapi-ts';

export default [
    {
      input: '/home/lingyuan/Downloads/openapi_analytics_service.json',
      output: 'app/services/analytics',
        plugins: [
        {
          name: '@hey-api/client-axios',
          runtimeConfigPath: '../../hey-api.ts', 
        },
      ],
    },
    {
      input: '/home/lingyuan/Downloads/openapi_availability_service.json',
      output: 'app/services/availability',
        plugins: [
        {
          name: '@hey-api/client-axios',
          runtimeConfigPath: '../../hey-api.ts', 
        },
      ],
    },
];
