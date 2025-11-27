## For dev

### Pre reqs
You need docker


### Running local env

```make docker-build```

```make docker-run```

### To generate openapi schema

- Ensure backend is running at localhost:8000
- Alternatively, if you can't get backend running, replace the link in openapi-config.ts to the local file location
Then run 
```npm run openapi-ts```
