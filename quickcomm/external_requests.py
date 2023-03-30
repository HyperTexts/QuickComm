

import requests_cache

# This caches the requests for 5 minutes, so we don't blow up the GitHub API
session = requests_cache.CachedSession('github_cache', expire_after=300)

def get_github_stream(github):
    """Get the stream of a user from GitHub"""
    # given the url, take the last section as the username
    
    username = github.split('/')[-1]
    url = f'https://api.github.com/users/{username}/events/public'
    response = session.get(url)
    return response.json()

def get_github_message(stream):
    """Get the message from the GitHub event"""


    type = stream['type']
    if type == 'CommitCommentEvent':
        return f"Commented on commit {stream['payload']['comment']['commit_id']}: {stream['payload']['comment']['body']}"
    elif type == 'CreateEvent':
        return f"Created {stream['payload']['ref_type']} {stream['payload']['ref']}"
    elif type == 'DeleteEvent':
        return f"Deleted {stream['payload']['ref_type']} {stream['payload']['ref']}"
    elif type == 'ForkEvent':
        return f"Forked {stream['repo']['name']} to {stream['payload']['forkee']['full_name']}"
    elif type == 'GollumEvent':
        return f"Updated {stream['repo']['name']} wiki"
    elif type == 'IssueCommentEvent':
        return f"Commented on issue {stream['payload']['issue']['number']}: {stream['payload']['comment']['body']}"
    elif type == 'IssuesEvent':
        return f"{stream['payload']['action']} issue {stream['payload']['issue']['number']}: {stream['payload']['issue']['title']}"
    elif type == 'MemberEvent':
        return f"Added {stream['payload']['member']['login']} as a collaborator to {stream['repo']['name']}"
    elif type == 'PublicEvent':
        return f"Made {stream['repo']['name']} public"
    elif type == 'PullRequestEvent':
        return f"{stream['payload']['action']} pull request {stream['payload']['number']}: {stream['payload']['pull_request']['title']}"
    elif type == 'PullRequestReviewEvent':
        return f"{stream['payload']['action']} pull request review {stream['payload']['review']['id']}"
    elif type == 'PullRequestReviewCommentEvent':
        return f"Commented on pull request {stream['payload']['pull_request']['number']}: {stream['payload']['comment']['body']}"
    elif type == 'PullRequestReviewThreadEvent':
        return f"Commented on pull request {stream['payload']['pull_request']['number']}: {stream['payload']['comment']['body']}"
    elif type == 'PushEvent':
        return f"Pushed {len(stream['payload']['commits'])} commit(s) to {stream['repo']['name']}"
    elif type == 'ReleaseEvent':
        return f"Published release {stream['payload']['release']['tag_name']}"
    elif type == 'SponsorshipEvent':
        return f"Received sponsorship from {stream['payload']['sponsor']['login']}"
    elif type == 'WatchEvent':
        return f"Starred {stream['repo']['name']}"
    else:
        return f"Unknown event type: {type}"

def get_github_url(stream):
    """Return the relevant URL for the GitHub event"""

    type = stream['type']

    if type == 'CommitCommentEvent':
        return stream['payload']['comment']['html_url']
    elif type == 'CreateEvent':
        return stream['repo']['url']
    elif type == 'DeleteEvent':
        return stream['repo']['url']
    elif type == 'ForkEvent':
        return stream['payload']['forkee']['html_url']
    elif type == 'GollumEvent':
        return stream['repo']['url']
    elif type == 'IssueCommentEvent':
        return stream['payload']['comment']['html_url']
    elif type == 'IssuesEvent':
        return stream['payload']['issue']['html_url']
    elif type == 'MemberEvent':
        return stream['repo']['url']
    elif type == 'PublicEvent':
        return stream['repo']['url']
    elif type == 'PullRequestEvent':
        return stream['payload']['pull_request']['html_url']
    elif type == 'PullRequestReviewEvent':
        return stream['payload']['review']['html_url']
    elif type == 'PullRequestReviewCommentEvent':
        return stream['payload']['comment']['html_url']
    elif type == 'PullRequestReviewThreadEvent':
        return stream['payload']['comment']['html_url']
    elif type == 'PushEvent':
        return stream['repo']['url']
    elif type == 'ReleaseEvent':
        return stream['payload']['release']['html_url']
    elif type == 'SponsorshipEvent':
        return stream['payload']['sponsor']['html_url']
    elif type == 'WatchEvent':
        return stream['repo']['url']
    else:
        return None