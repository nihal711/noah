# Database Schema Fixes Summary

## Issues Fixed

The HR System was experiencing database schema mismatch errors when accessing visa letter requests and bank letter requests. The main problems were:

### 1. VisaLetterRequest Model Issues
- **Problem**: Model used `addressedTo` (camelCase) but database had `addressed_to` (snake_case)
- **Error**: `column visa_letter_requests.addressedTo does not exist`
- **Fix**: Updated model to use `addressed_to` column name

### 2. BankLetterRequest Model Issues
- **Problem**: Model schema didn't match actual database structure
- **Database had**: `bank_name`, `purpose`, `additional_details`
- **Model expected**: `type`, `comment`, `language`, `addressedTo`, `bankName`, `branchName`
- **Fix**: Updated model to match actual database columns

### 3. Attachment Model Issues
- **Problem**: Model used camelCase field names but database used snake_case
- **Database had**: `file_name`, `file_type`, `file_desc`, `file_data`
- **Model expected**: `fileName`, `fileType`, `fileDesc`, `fileData`
- **Fix**: Updated model to use snake_case column names
- **Also**: Removed non-existent `created_at` column from model

## Files Modified

### 1. `models.py`
- Updated `VisaLetterRequest.addressedTo` → `addressed_to`
- Updated `BankLetterRequest` columns to match database schema
- Updated `Attachment` field names to snake_case
- Removed non-existent `created_at` from `Attachment`

### 2. `routers/visa_letter.py`
- Updated router to use `addressed_to` when creating visa letter requests
- Updated attachment creation to use snake_case field names

### 3. `routers/bank_letter.py`
- Updated router to map API fields to correct database columns:
  - `bankName` → `bank_name`
  - `type` → `purpose`
  - `comment` → `additional_details`
- Updated attachment creation to use snake_case field names

### 4. `schemas.py`
- Updated response schemas to match actual database column names
- Kept input schemas with camelCase for API compatibility
- Updated `VisaLetterRequestResponse` to use `addressed_to`
- Updated `BankLetterRequestResponse` to use correct database fields
- Updated `AttachmentResponse` to use snake_case field names

### 5. `main.py`
- Fixed health check query to use proper SQLAlchemy syntax

## Testing Results

✅ **All endpoints now working correctly:**
- Visa letter requests: Returns proper authentication error (401) instead of database error (500)
- Leave balance: Working correctly
- Bank letter requests: Returns proper authentication error (401) instead of database error (500)
- Health check: Database connection successful
- API documentation: Accessible

## Server Details
- **Port**: 8181 (as requested)
- **Health endpoint**: http://localhost:8181/health
- **API docs**: http://localhost:8181/docs
- **Database**: PostgreSQL on port 5433, database 'noah'

## Database Schema Validation
Confirmed actual database structure:
- `visa_letter_requests`: Uses `addressed_to` (not `addressedTo`)
- `bank_letter_requests`: Uses `bank_name`, `purpose`, `additional_details`
- `attachments`: Uses `file_name`, `file_type`, `file_desc`, `file_data` (no `created_at`)

All SQLAlchemy models now correctly match the actual database schema. 