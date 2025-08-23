# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Facebook Leads to MySQL integration system that captures leads from Facebook forms and consolidates them into the expokossodo_registros table for event management.

## Commands

### Development
```bash
# Run the webhook server locally
python app.py

# Test with ngrok for local development
ngrok http 8000

# Install dependencies
pip install -r requirements.txt
```

### Production (Render)
```bash
# Uses gunicorn automatically
gunicorn app:app --bind 0.0.0.0:8000
```

## Architecture

### Data Flow
1. **Facebook Lead Reception** → Webhook receives POST at `/facebook/webhook`
2. **Lead Storage** → Saves to `fb_leads` table with Facebook Marketing API enrichment
3. **Event Matching** → Two-step matching algorithm (45 chars, then colon split)
4. **Lead Consolidation** → Automatic consolidation to `expokossodo_registros`
5. **QR Generation** → Format: `{3_LETTERS}|{DNI}|{CARGO}|{EMPRESA}|{TIMESTAMP}`

### Key Components

**app.py**
- Main Flask application
- Webhook verification and lead reception
- Facebook Marketing API integration for campaign/adset/ad names
- Automatic lead consolidation after saving

**modules/events_matcher.py**
- Two-step event matching logic:
  1. 45-character normalization match
  2. Colon-based title match (text before ':')
- Maps day names to dates: `dia 1` → `2025-09-02`
- Maps sala codes: `S1` → `sala1`

**modules/lead_consolidator.py**
- Consolidates leads to `expokossodo_registros`
- Handles JSON array in `eventos_seleccionados` column
- Updates existing records or creates new ones
- Marks leads as processed to avoid duplication

**modules/qr_generator.py**
- Generates QR codes for event registration
- Cleans special characters and formats consistently

### Database Tables

**fb_leads**
- Raw lead storage with `procesado` flag
- Extracts: `job_title` → cargo, `company_name` → empresa
- Sala extraction from ad_name format: `S3 - Title` → sala: `S3`

**expokossodo_registros**
- Main registration table
- `eventos_seleccionados`: JSON array of event IDs
- QR code generated on first registration

### Environment Variables Required
- Database: `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_PORT`
- Facebook: `FB_APP_SECRET`, `FB_PAGE_ACCESS_TOKEN`, `WEBHOOK_VERIFY_TOKEN`
- Marketing API: `MKT_TOKEN`, `AD_ACCOUNT_ID`, `PAGE_ID`

### Critical Business Logic

**Event Date Mapping**
- `dia 1` → September 2, 2025
- `dia 2` → September 3, 2025
- `dia 3` → September 4, 2025

**Sala Mapping**
- Ad names contain sala prefix: `S1 - `, `S2 - `, `S3 - `, `S4 - `
- Maps to database: `sala1`, `sala2`, `sala3`, `sala4`

**Lead Processing Rules**
- If email exists in `expokossodo_registros`: add event to `eventos_seleccionados` if not present
- If email doesn't exist: create new registration with QR code
- Always mark lead as `procesado = 1` after consolidation

### Testing Considerations
- Webhook URL format: `https://domain.com/facebook/webhook`
- Verify token must match `WEBHOOK_VERIFY_TOKEN`
- All leads are processed automatically on reception
- No manual sync scripts needed - everything happens in real-time