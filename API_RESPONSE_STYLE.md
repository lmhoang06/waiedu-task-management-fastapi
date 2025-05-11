# API Response Style Guide

All API endpoints in this project must follow a consistent response structure. This ensures predictable, easy-to-parse responses for clients and simplifies error handling.

## Standard Response Envelope

Every API response should be wrapped in a JSON object with the following fields:

- `success` (bool): Indicates if the request was successful.
- `data` (object or array, nullable, optional): The main payload of the response. Should be included only if the request was successful (`success: true`).
- `error` (object or null, optional): Error details if the request failed. Should be included only if the request failed (`success: false`).
- `message` (string): A human-readable message describing the result.

## Success Response Example
```json
{
  "success": true,
  "data": {
    "id": 123,
    "username": "johndoe"
  },
  "message": "User retrieved successfully."
}
```

## Error Response Example
```json
{
  "success": false,
  "error": {
    "code": "USER_NOT_FOUND",
    "details": "No user exists with the given ID."
  },
  "message": "User not found."
}
```

## Notes
- If `success` is `true`, the `error` field should be omitted.
- If `success` is `false`, the `data` field should be omitted.
- The `error` object should include at least a `code` and optionally a `details` field.
- The `message` field should always be present and provide a clear, human-readable summary.
- For paginated endpoints, include pagination info inside the `data` object.

---

**All new and existing endpoints must adhere to this response style.** 