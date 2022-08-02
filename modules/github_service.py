from github import Github


def create_issue(detection_name, config):
    title = f"{detection_name} needs testing"

    g = Github(config["github_token"])
    repo = g.get_repo(config["github_repo"])


    open_issues = repo.get_issues(state='open')
    create_issue = all(issue.title != title for issue in open_issues)
    if create_issue:
        repo.create_issue(title=title, body="This detection failed automated testing. Please review.")
