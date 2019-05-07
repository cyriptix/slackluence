# slackluence
Takes a Slack export file and archives messages into Confluence pages

- Python 3
- dirty
- brittle
- cheaper than paying for unlimited Slack retention

### Preserves:
* Messages
* Attachments
* Avatars
* Channel/User mentions

### Doesn't Preserve:
* Emojis
* Reactions
* Edited message history

## Requirements:
* Python 3
* A Slack [User Token](https://api.slack.com/docs/token-types#user)
* A Confluence [Application Link and associated OAuth token/key](https://github.com/cyriptix/atlassian-oauth-helper)

## Instructions:
* Generate a Slack export and extract it somewhere
* Set up a new Python3 virtualenv and install modules from requirements.txt
* Fill in the vars at the top of the script
  * `slack_oauth_token`: your Slack user token
  * `channels_to_export`: comma separated list of channels you want to archive into Confluence
  * `working_dir`: the directory where you extracted your Slack export
  * `confluence_baseurl`: where your Confluence server lives (including context), eg: `https://confluence.example.com/confluence`
  * `confluence_space`: the Confluence space under which the new pages will live (expects the project key)
  * `confluence_token`: your Confluence OAuth token (not the secret)
  * `confluence_key`: the SSL private key that was used to set up the Confluence OAuth
  * `confluence_consumer`: the consumer key of your Application Link within Confluence
* Run the script

## TODO:
* Make configuring the script easier/nicer
* Add some exception handling
* Make the resulting pages a bit neater/look more like Slack
