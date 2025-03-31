# Client-Side API Endpoint Generation

This directory contains a script for generating client-side API endpoints from an OpenAPI schema.

## Overview

The `generate_api_client.py` script reads an OpenAPI schema JSON file and generates a JavaScript file with functions for
each API endpoint defined in the schema. The generated JavaScript file can be used in a browser extension or web
application to interact with the API.

## Usage

```bash
python generate_api_client.py <schema_path> <output_path>
```

### Arguments

- `schema_path`: Path to the OpenAPI schema JSON file
- `output_path`: Path to write the generated JavaScript file

### Example

```bash
python generate_api_client.py ../openapi_schema.json ../extension/api_client.js
```

## Generated API Client

The generated API client includes:

- A function for each API endpoint defined in the OpenAPI schema
- JSDoc comments for each function with parameter and return type information
- Error handling for API requests
- Cache invalidation for methods that modify data
- A helper function for cached community ratings

The API client is designed to work both as an ES module (for import in other JavaScript files) and as a content script (
for use in browser extensions).

## Function Names

The function names are generated from the operationId in the OpenAPI schema, with the following transformations:

- The operationId is split by underscores
- The method (get, put, post, delete, patch) is removed from the end
- The endpoint name is removed if it's redundant
- Special cases for `/ratings/my` and `/ratings/all` endpoints
- The remaining parts are converted to camelCase

For example:

- `get_credibility_rating_score_get` -> `getCredibilityRating`
- `get_community_rating_ratings_get` -> `getCommunityRating`
- `cast_user_vote_ratings_put` -> `castUserVote`
- `remove_user_vote_ratings_delete` -> `removeUserVote`
- `get_user_votes_ratings_my_get` -> `getUserVotes`
- `get_all_ratings_ratings_all_get` -> `getAllRatings`

## Integration with Browser Extension

To use the generated API client in a browser extension:

1. Include the api_client.js file in the extension's manifest.json as a content script
2. Make the api_client.js file web-accessible
3. Import the API client in your extension's JavaScript files
4. Use the API client functions to interact with the API

Example manifest.json:

```json
{
  "content_scripts": [
    {
      "matches": ["<all_urls>"],
      "js": ["api_client.js"]
    }
  ],
  "web_accessible_resources": [
    {
      "resources": ["api_client.js"],
      "matches": ["<all_urls>"]
    }
  ]
}
```

Example usage in JavaScript:

```javascript
import apiClient from './api_client.js';

// Get credibility rating for a page
const credibilityRating = await apiClient.getCredibilityRating(pageUrl);

// Get community rating for a page
const communityRating = await apiClient.getCommunityRating(pageUrl);

// Cast a vote on a page
const success = await apiClient.castUserVote(pageUrl, vote);

// Get all user votes
const userVotes = await apiClient.getUserVotes();
```