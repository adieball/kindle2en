This script is based on the work of Jamie Todd Rubin - http://www.jamierubin.net
Changes to the original script:
    - changed to Python 3.x
        - changed to work with Kindle Devices set to the German language (actually right now it only works when your
        Kindle is set to German)

This Python script will read and parse the "My Clippings.txt" file on Kindle device, organize them into title-based
notes for Evernote and then email the results to Evernote using the append option to append to existing notes.

Requires the following Python packages:
six-1.5.2
python-dateutil-2.2

NOTES ABOUT EVERNOTE EMAIL LIMITS.
This script uses the email-to-Evernote functionality to update your Kindle notes in Evernote. It sends one note per
title for which an update is required each time it runs. If you have a lot of highlights over a lot of different
titles, be aware of these daily limits for emailing to Evernote accounts:

Free: 50 daily
Premium: 250 daily
Business: 250 daily
More information about Evernote account limits can be found here: http://evernote.com/contact/support/kb/#!/article/23283158

TODO: make more universal (Kindle Language)
TODO: use Evernote API instead of email