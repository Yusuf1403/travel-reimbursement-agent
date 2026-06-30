# Sample curl Commands

## Health Check
```bash
curl -s http://localhost:8000/health | python -m json.tool
```

## Version Info
```bash
curl -s http://localhost:8000/version | python -m json.tool
```

## Metrics
```bash
curl -s http://localhost:8000/metrics | python -m json.tool
```

## Evaluate a Claim (Approved Scenario)
```bash
curl -X POST http://localhost:8000/evaluate \
  -H "Content-Type: application/json" \
  -d @data/claims/claim_001_approved.json | python -m json.tool
```

## Evaluate a Claim (Rejected Scenario)
```bash
curl -X POST http://localhost:8000/evaluate \
  -H "Content-Type: application/json" \
  -d @data/claims/claim_003_rejected.json | python -m json.tool
```

## Evaluate a Claim (Manual Review Scenario)
```bash
curl -X POST http://localhost:8000/evaluate \
  -H "Content-Type: application/json" \
  -d @data/claims/claim_004_manual_review.json | python -m json.tool
```

## Upload a Policy Document
```bash
curl -X POST http://localhost:8000/upload-policy \
  -F "file=@data/policies/travel_policy.md"
```

## Swagger UI
Open in browser: http://localhost:8000/docs

## ReDoc
Open in browser: http://localhost:8000/redoc

## OpenAPI JSON Schema
```bash
curl -s http://localhost:8000/openapi.json | python -m json.tool
```
