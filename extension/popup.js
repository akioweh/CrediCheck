// Global variables
let currentUrl = null;
let currentUserVote = 0; // 0 = no vote, 1 = upvote, -1 = downvote
let upVotes = 0;
let downVotes = 0;
let credibilityScore = null;

// Get the current tab's URL
async function getCurrentTabUrl() {
    try {
        const tabs = await chrome.tabs.query({active: true, currentWindow: true});
        return tabs[0].url;
    } catch (error) {
        console.error("Error getting current tab:", error);
        return null;
    }
}

// Update the ratio bar based on upvotes and downvotes
function updateRatioBar(upVotesCount, downVotesCount) {
    // Store the votes in global variables for hover functionality
    upVotes = upVotesCount;
    downVotes = downVotesCount;

    const total = upVotes + downVotes;
    if (total === 0) {
        // If no votes, show 50/50
        document.getElementById('upvote-ratio').style.width = '50%';
        document.getElementById('downvote-ratio').style.width = '50%';
        document.getElementById('vote-bar').title = "No votes yet";
    } else {
        const upPercentage = (upVotes / total) * 100;
        const downPercentage = (downVotes / total) * 100;
        document.getElementById('upvote-ratio').style.width = `${upPercentage}%`;
        document.getElementById('upvote-ratio').setAttribute('aria-valuenow', upPercentage);
        document.getElementById('downvote-ratio').style.width = `${downPercentage}%`;
        document.getElementById('downvote-ratio').setAttribute('aria-valuenow', downPercentage);
        document.getElementById('vote-bar').title = `👍 ${upVotes} upvotes / 👎 ${downVotes} downvotes`;
    }
}

// Create and update star rating based on credibility score
function updateStarRating(score) {
    // Store the score in global variable for hover functionality
    credibilityScore = score;

    const starContainer = document.getElementById('star-rating');
    starContainer.innerHTML = ''; // Clear existing stars

    if (score === null) {
        starContainer.title = "No credibility score yet";
        // Display empty stars if no score
        for (let i = 0; i < 5; i++) {
            const star = document.createElement('span');
            star.innerHTML = '☆'; // Empty star
            star.style.color = '#ccc';
            star.style.fontSize = '1.2rem';
            star.style.margin = '0 2px';
            starContainer.appendChild(star);
        }
    } else {
        // Convert 0-10 score to 0-5 stars
        const starScore = Math.round((score / 10) * 5);
        starContainer.title = `Credibility Score: ${score.toFixed(1)}/10`;

        for (let i = 0; i < 5; i++) {
            const star = document.createElement('span');
            if (i < starScore) {
                star.innerHTML = '★'; // Filled star
                star.style.color = '#ffc107'; // Bootstrap warning color (yellow)
            } else {
                star.innerHTML = '☆'; // Empty star
                star.style.color = '#ccc';
            }
            star.style.fontSize = '1.2rem';
            star.style.margin = '0 2px';
            starContainer.appendChild(star);
        }
    }
}

// Update the vote buttons based on the user's current vote
function updateVoteButtons(vote) {
    const credibleBtn = document.getElementById('credible-btn');
    const notCredibleBtn = document.getElementById('not-credible-btn');

    // Reset both buttons
    credibleBtn.classList.remove('active');
    notCredibleBtn.classList.remove('active');

    // Highlight the appropriate button
    if (vote === 1) {
        credibleBtn.classList.add('active');
    } else if (vote === -1) {
        notCredibleBtn.classList.add('active');
    }

    // Store the current vote
    currentUserVote = vote;
}

// Update the UI with the URL information
async function updateUI(url) {
    currentUrl = url; // Store the URL in the global variable
    document.getElementById('domain-name').innerHTML = `<strong>${new URL(url).hostname}</strong>`;
    document.getElementById('status-message').textContent = ""; // Clear any status messages

    try {
        // Get credibility score
        const scoreData = await apiClient.getCredibilityRating(url);
        // Update star rating display
        updateStarRating(scoreData.score);

        // Get community ratings
        const ratingData = await apiClient.getCommunityRating(url);
        const totalRatings = ratingData.up_votes + ratingData.down_votes;
        document.getElementById('num-ratings').textContent = totalRatings.toString();

        // Update the ratio bar
        updateRatioBar(ratingData.up_votes, ratingData.down_votes);

        // Get user's vote for this site
        const userVote = await apiClient.getUserVoteFor(url);
        updateVoteButtons(userVote);
    } catch (error) {
        console.error("Error fetching data:", error);
        document.getElementById('status-message').textContent = "Error loading data. Please try again.";
    }
}

// Handle voting
async function handleVote(value) {
    if (!currentUrl) {
        document.getElementById('status-message').textContent = "Error: No URL available. Please refresh.";
        return;
    }

    try {
        // If user clicks the same button again, remove their vote
        const voteToSubmit = (currentUserVote === value) ? 0 : value;

        document.getElementById('status-message').textContent = "Submitting vote...";
        await apiClient.castUserVote(currentUrl, voteToSubmit);

        if (voteToSubmit === 0) {
            document.getElementById('status-message').textContent = "Vote removed successfully!";
        } else {
            document.getElementById('status-message').textContent = "Vote submitted successfully!";
        }

        // Refresh the UI to show updated ratings
        await updateUI(currentUrl);
    } catch (error) {
        console.error("Error casting vote:", error);
        document.getElementById('status-message').textContent = "Error submitting vote. Please try again.";
    }
}

// Initialize the popup
document.addEventListener('DOMContentLoaded', async () => {
    const url = await getCurrentTabUrl();
    if (url) {
        await updateUI(url);
    } else {
        document.getElementById('domain-name').innerHTML = "<strong>Error: Cannot access current tab</strong>";
        document.getElementById('status-message').textContent = "Please refresh and try again.";
    }

    // Add event listeners to buttons
    document.getElementById('credible-btn').addEventListener('click', () => handleVote(1));
    document.getElementById('not-credible-btn').addEventListener('click', () => handleVote(-1));
});
