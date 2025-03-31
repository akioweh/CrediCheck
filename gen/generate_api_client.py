import json
import sys


def generate_api_client(schema_path, output_path):
    """
    Generate a JavaScript API client from an OpenAPI schema.

    Args:
        schema_path (str): Path to the OpenAPI schema JSON file
        output_path (str): Path to write the generated JavaScript file
    """
    # Load the OpenAPI schema
    with open(schema_path, 'r') as f:
        schema = json.load(f)

    # Dictionary to store function names for each path and method
    function_names = {}

    # Start building the JavaScript file
    js_code = [
        "// Generated from OpenAPI schema",
        "const BASE_URL = \"http://localhost:8000\";  // Replace with actual server URL",
        "",
        "function buildURL(endpoint, params = {}) {",
        "    const url = new URL(BASE_URL + endpoint);",
        "    Object.entries(params).forEach(([key, value]) => url.searchParams.append(key, value));",
        "    return url;",
        "}",
        "",
        "// Simple cache using localStorage",
        "const cacheKey = (url) => `credicheck::${url}`;",
        "",
        "// API client generated from OpenAPI schema",
        "const apiClient = {",
    ]

    # Generate a function for each operation in the schema
    for path, path_item in schema.get('paths', {}).items():
        for method, operation in path_item.items():
            if method not in ['get', 'put', 'post', 'delete', 'patch']:
                continue

            operation_id = operation.get('operationId')
            if not operation_id:
                continue

            # Extract the base function name from the operationId
            # Format: operation_name_endpoint_method
            # Example: get_credibility_rating_score_get -> getCredibilityRating
            parts = operation_id.split('_')

            # Remove the endpoint and method from the end
            if len(parts) > 2 and parts[-1] in ['get', 'put', 'post', 'delete', 'patch']:
                parts = parts[:-1]  # Remove method

                # Check if the second-to-last part is the endpoint name
                endpoint_name = path.strip('/').split('/')[-1]
                if parts[-1].lower() == endpoint_name.lower():
                    parts = parts[:-1]  # Remove endpoint name

                # Special case for ratings/my and ratings/all
                if path == '/ratings/my':
                    # For this endpoint, we want to use getUserVotes
                    parts = ['get', 'user', 'votes']
                elif path == '/ratings/all':
                    # For this endpoint, we want to use getAllRatings
                    parts = ['get', 'all', 'ratings']

            # Convert to camelCase
            function_name = parts[0]
            for part in parts[1:]:
                function_name += part.capitalize()

            # Get parameters
            parameters = operation.get('parameters', [])
            required_params = [p for p in parameters if p.get('required', False)]

            # Build function signature
            param_names = [p['name'] for p in required_params]
            function_signature = ", ".join(param_names)

            # Build JSDoc comment
            js_doc = [
                "    /**",
                f"     * {operation.get('summary', '')}",
                f"     * {operation.get('description', '')}",
            ]

            for param in required_params:
                param_type = "string"
                if param.get('schema', {}).get('type') == 'integer':
                    param_type = "number"
                js_doc.append(f"     * @param {{{param_type}}} {param['name']} - {param.get('description', '')}")

            js_doc.append("     * @returns {Promise<Object>} - The response data")
            js_doc.append("     */")

            # Build function body
            function_body = []

            # URL construction
            if param_names:
                params_obj = ", ".join([f"{p}: {p}" for p in param_names])
                function_body.append(f"        const url = buildURL(\"{path}\", {{{params_obj}}});")
            else:
                function_body.append(f"        const url = buildURL(\"{path}\");")

            # Fetch call
            if method == 'get':
                function_body.append("        const res = await fetch(url);")
            else:
                function_body.append(f"        const res = await fetch(url, {{")
                function_body.append(f"            method: \"{method.upper()}\",")
                function_body.append("        });")

            # Handle response
            if method == 'get':
                function_body.append(
                    f"        if (!res.ok) throw new Error(\"Failed to {operation.get('summary', '')}\");")
                function_body.append("        return await res.json();")
            else:
                # For non-GET methods, check for specific status codes
                success_codes = [r for r in operation.get('responses', {}).keys() if r.startswith('2')]
                if success_codes:
                    success_codes_str = ", ".join([str(code) for code in success_codes])
                    function_body.append(
                        f"        if (!res.ok) throw new Error(\"Failed to {operation.get('summary', '')}\");")

                    # For methods that return data
                    if '200' in success_codes:
                        function_body.append("        return res.status === 200 ? await res.json() : true;")
                    else:
                        function_body.append("        return true;")
                else:
                    function_body.append(
                        f"        if (!res.ok) throw new Error(\"Failed to {operation.get('summary', '')}\");")
                    function_body.append("        return true;")

            # Add cache invalidation for methods that modify data
            if method in ['put', 'post', 'delete', 'patch'] and 'ratings' in path:
                # Find the page parameter
                page_param = next((p for p in required_params if p['name'] == 'page'), None)
                if page_param:
                    function_body.insert(-1, "        // Invalidate cache")
                    function_body.insert(-1, "        localStorage.removeItem(cacheKey(`ratings::${page}`));")

            # Store the function name for this path and method
            function_names[(path, method)] = function_name

            # Combine everything
            function_code = js_doc + [
                f"    async {function_name}({function_signature}) {{",
                *function_body,
                "    },",
                ""
            ]

            js_code.extend(function_code)

    # Add helper function for cached community rating
    # Get the function name for getting community ratings
    community_rating_function = function_names.get(('/ratings', 'get'), 'getCommunityRating')

    js_code.extend([
        "    /**",
        "     * Get Cached Community Rating",
        "     * Returns the cached community rating for a given page, or fetches it if not cached.",
        "     * @param {string} pageURL - The URL of the page to get the community rating for",
        "     * @returns {Promise<Object>} - The community rating",
        "     */",
        "    async getCachedCommunityRating(pageURL) {",
        "        const cached = localStorage.getItem(cacheKey(`ratings::${pageURL}`));",
        "        if (cached) return JSON.parse(cached);",
        f"        return await apiClient.{community_rating_function}(pageURL);",
        "    },",
    ])

    # Close the object and add export
    js_code.extend([
        "};",
        "",
        "// Make the API client available both as a module export and as a global variable",
        "try {",
        "    // For ES modules",
        "    export default apiClient;",
        "} catch (e) {",
        "    // For content scripts",
        "    window.apiClient = apiClient;",
        "}",
    ])

    # Write the JavaScript file
    with open(output_path, 'w') as f:
        f.write('\n'.join(js_code))

    print(f"Generated API client at {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python generate_api_client.py <schema_path> <output_path>")
        sys.exit(1)

    schema_path = sys.argv[1]
    output_path = sys.argv[2]

    generate_api_client(schema_path, output_path)
