# Deployment Checklist

## Pre-Deployment

- [ ] Set up PostgreSQL database (production)
- [ ] Set environment variables:
  - `DATABASE_URL=postgresql://user:password@host:5432/dbname`
  - `SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))"`>
  - `FLASK_ENV=production`
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Run database seeder: `python scripts/seed.py`
- [ ] Verify 2026 profiles loaded successfully

## Testing

- [ ] Test GET /api/profiles endpoint
- [ ] Test GET /api/profiles/search endpoint
- [ ] Verify CORS headers present on all responses
- [ ] Test from multiple networks/browsers
- [ ] Verify pagination works (page 1, page 2, etc.)
- [ ] Test error cases (invalid params, limit > 50, etc.)

## Example Test Commands

```bash
# Test profiles endpoint
curl "https://yourapp.domain.app/api/profiles?limit=5"

# Test search endpoint
curl "https://yourapp.domain.app/api/profiles/search?q=young+males+from+nigeria"

# Test CORS
curl -H "Origin: https://example.com" -I "https://yourapp.domain.app/api/profiles"

# Test pagination
curl "https://yourapp.domain.app/api/profiles?page=1&limit=10"
curl "https://yourapp.domain.app/api/profiles?page=2&limit=10"

# Test filtering
curl "https://yourapp.domain.app/api/profiles?gender=male&country_id=NG&min_age=25"

# Test sorting
curl "https://yourapp.domain.app/api/profiles?sort_by=age&order=asc&limit=5"

# Test error cases
curl "https://yourapp.domain.app/api/profiles?limit=51"  # Should return 400
curl "https://yourapp.domain.app/api/profiles?min_age=abc"  # Should return 422
curl "https://yourapp.domain.app/api/profiles/search?q="  # Should return 400
```

## Submission

- [ ] Confirm server is live and accessible
- [ ] Test from multiple networks
- [ ] Submit API base URL: `https://yourapp.domain.app`
- [ ] Submit GitHub repo link
- [ ] Check Thanos bot for success/error message

## Supported Platforms

✅ Vercel, Railway, Heroku, AWS, PXXL App
❌ Render (not accepted per requirements)

## Common Issues

### Database Connection Errors
- Verify DATABASE_URL is correct
- Check PostgreSQL is running and accessible
- Verify firewall rules allow connections

### CORS Issues
- Verify `Access-Control-Allow-Origin: *` header is present
- Check flask-cors is installed and configured

### Seeder Issues
- Verify data/profiles.json exists
- Check DATABASE_URL is set
- Verify PostgreSQL user has CREATE/INSERT permissions

### Import Errors
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check Python version is 3.10+
