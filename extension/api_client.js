// API client for CrediCheck service
const BASE_URL = "https://akioweh.com:4269";

// Default headers for API requests
const DEFAULT_HEADERS = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
};

function buildURL(endpoint, params = {}) {
    const url = new URL(BASE_URL + endpoint);
    Object.entries(params).forEach(([key, value]) => url.searchParams.append(key, value));
    return url;
}


// API client aligned with OpenAPI schema
const apiClient = {
    /**
     * Get Credibility Rating
     * Returns the central credibility rating for a given domain
     * @param {string} site - The URL of the site to get the credibility rating for
     * @returns {Promise<{site: string, score: number|null}>} - The credibility score
     */
    async getCredibilityRating(site) {
        const url = buildURL("/score", {site: site});
        const res = await fetch(url);
        if (!res.ok) throw new Error("Failed to Get Credibility Rating");
        return await res.json();
    },

    /**
     * Get Community Rating
     * Returns the aggregate community rating for a given domain.
     * @param {string} site - The URL of the site to get the community rating for
     * @returns {Promise<{site: string, up_votes: number, down_votes: number}>} - The community rating
     */
    async getCommunityRating(site) {
        const url = buildURL("/ratings", {site: site});
        const res = await fetch(url);
        if (!res.ok) throw new Error("Failed to Get Community Rating");
        return await res.json();
    },

    /**
     * Cast User Vote
     * Casts a personal vote on a given domain.
     * A value of 0 removes any existing vote.
     * @param {string} site - The URL of the site to vote on
     * @param {number} vote - The vote value (-1, 0, or 1)
     * @returns {Promise<boolean>} - True if successful
     */
    async castUserVote(site, vote) {
        const url = buildURL("/ratings", {site: site, vote: vote});
        const res = await fetch(url, {
            method: "PUT",
            headers: DEFAULT_HEADERS
        });
        if (!res.ok) throw new Error("Failed to Cast User Vote");
        return true;
    },

    /**
     * Remove User Vote
     * Removes a personal vote on a given domain.
     * @param {string} site - The URL of the site to remove the vote from
     * @returns {Promise<boolean>} - True if successful
     */
    async removeUserVote(site) {
        const url = buildURL("/ratings", {site: site});
        const res = await fetch(url, {
            method: "DELETE",
            headers: DEFAULT_HEADERS
        });
        if (!res.ok) throw new Error("Failed to Remove User Vote");
        return true;
    },

    /**
     * Get User Votes
     * Returns all votes cast by request sender.
     * @returns {Promise<Array<{site: string, value: number}>>} - Array of user votes
     */
    async getUserVotes() {
        const url = buildURL("/ratings/my/all");
        const res = await fetch(url);
        if (!res.ok) throw new Error("Failed to Get User Votes");
        return await res.json();
    },

    /**
     * Get User Vote For Site
     * Returns the vote cast by request sender for a given domain.
     * @param {string} site - The URL of the site to get the vote for
     * @returns {Promise<number>} - The vote value (-1, 0, or 1)
     */
    async getUserVoteFor(site) {
        const url = buildURL("/ratings/my", {site: site});
        const res = await fetch(url);
        if (!res.ok) throw new Error("Failed to Get User Vote");
        return await res.json();
    },
};

// Make the API client available as a global variable
window.apiClient = apiClient;
