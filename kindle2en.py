#!/usr/bin/env python3
# encoding: utf-8
"""
kindle2en.py

Created by Andre Dieball - andre@dieball.net on 2016-06-12.
Copyright (c) 2016. All rights reserved.
Based on the work of Jamie Todd Rubin - http://www.jamierubin.net
Changes:
    - changed to Python 3.x
    - changed to work with Kindle Devices set to the German language
        (actually right now it only works when your Kindle is set to German)


//
// Dear maintainer:
//
// Once you are done trying to 'optimize' this routine,
// and have realized what a terrible mistake that was,
// please increment the following counter as a warning
// to the next guy:
//
// total_hours_wasted_here = 42
//

"""

from __future__ import print_function
import getopt
import os.path
import re
import codecs
import sys
from datetime import *
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from os.path import expanduser
import dateutil.parser as parser
import locale
import smtplib


class GermanParserInfo(parser.parserinfo):
    WEEKDAYS = [("Mo.", "Montag"),
                ("Di.", "Dienstag"),
                ("Mi.", "Mittwoch"),
                ("Do.", "Donnerstag"),
                ("Fr.", "Freitag"),
                ("Sa.", "Samstag"),
                ("So.", "Sonntag")]
    MONTHS = [('Jan', 'Januar'),
              ('Feb', 'Februar'),
              ('Mar', 'März'),
              ('Apr', 'April'),
              ('May', 'Mai'),
              ('Jun', 'Juni'),
              ('Jul', 'Juli'),
              ('Aug', 'August'),
              ('Sep', 'Sept', 'September'),
              ('Oct', 'Oktober'),
              ('Nov', 'November'),
              ('Dec', 'Dezember')]


def read_configuration(f):
    config_settings = {}
    if os.path.isfile(f) == False:
        sys.exit(2)

    lines = [line.strip() for line in open(f)]
    for line in lines:
        if (line == "" or line[0] == '#'):
            continue

        tokens = line.split('=')
        config_settings[tokens[0]] = tokens[1]

    return config_settings

def get_semaphore_date(f):
    if (os.path.isfile(f) == False):
        f = open(f, 'w')
        last_date = parser.parse('1/1/2000')
        print(last_date, file=f)
        f.close()

    lines = [line.strip() for line in open(f)]
    for line in lines:
        last_date = parser.parse(line)

    return last_date

def main(argv):
    update_time = datetime.now()
    locale.setlocale(locale.LC_TIME, ('de', 'UTF-8'))
    verbose = 1
    CONFIG_FILE = ""
    HOME_DIR = expanduser("~")

    try:
        opts, args = getopt.getopt(argv, "hvVf:", ["file="])
    except:
        print('kindle2en.py -h -v -V -f <configfile>')
        sys.exit(2)
    for opt, arg in opts:
        if (opt == '-h'):
            usage = """Usage: kindle2en.py [options]
                    Options:
                    -f       specific location of configuration file other than home dir
                    -h       display help
                    -v       verbose output
                    -V       output version information and exit
                    """
            print(usage)
            sys.exit(0)
        elif (opt == '-f'):
            CONFIG_FILE = arg
        elif (opt == '-v'):
            verbose = 1
        elif (opt == '-V'):
            print('kindle2en.py (0.9.0)')

    if (CONFIG_FILE == ""):
        CONFIG_FILE = HOME_DIR + '/kindle2en.cfg'

    if (verbose == 1):
        print('Using config file at ' + CONFIG_FILE)

    # Read configuration file
    config = read_configuration(CONFIG_FILE)

    # Other settings
    SEMAPHORE = HOME_DIR + '/kindle2en.sem'
    RECORD_DELIM = '=========='

    if (os.path.isfile(config['CLIPPINGS_FILE']) == False):
        # ASSERT: error! Can't find the clippings file; exit cleanly
        print('Cannot locate "My Clippings.txt" at ' + config['CLIPPINGS_FILE'] + '.')
        sys.exit(1)

    # Process semaphore file for last_date value
    last_date = get_semaphore_date(SEMAPHORE)
    if (verbose == 1):
        print('Looking for updates since ' + last_date.strftime("%Y-%m-%d %H:%M:%S"))

    line_count = 0
    title_notes = {}
    is_title = prev_date = notenote = highlight = 0

    if (verbose == 1):
        print('Parsing the clippings file at ' + config['CLIPPINGS_FILE'])

    # Parse the clippings.txt file
    lines = [line.strip() for line in codecs.open(config['CLIPPINGS_FILE'], 'r', 'utf-8-sig')]
    for line in lines:
        line_count = line_count + 1
        if (line_count == 1 or is_title == 1):
            title = line
            prev_title = 1
            is_title = 0
            note_type_result = note_type = l = l_result = location = ""
            continue
        else:
            # ASSERT: not the first line
            if (prev_title == 1):
                # ASSERT: this is the date line
                # print(line)
                result = re.search(r'(.*)Hinzugefügt am (.*)', line, re.M | re.I)
                if (result is not None):
                    note_type_result = result.group(1)
                    # print(note_type_result)
                    if (note_type_result.find("Markierung") > 0):
                        note_type = "Markierung"
                    else:
                        note_type = "Notiz"

                    l = note_type_result
                    l_result = re.search(r'(\d+)', l, re.M | re.I)
                    location = l_result.group(1)
                    note_date = parser.parse(result.group(2), parserinfo=GermanParserInfo())

                if (note_date >= last_date):
                    # ASSERT: We haven't collected this note yet, so do it now.
                    str_date = note_date.strftime("%Y-%m-%d %H:%M:%S")
                    if title in title_notes:
                        title_notes[
                            title] += note_type + ' am ' + str_date + ', ' + ' beginnend bei Position ' + location + '\n'
                    else:
                        title_notes[
                            title] = note_type + ' am ' + str_date + ', ' + ' bei Position ' + location + '\n'

                    prev_title = 0
                    collect = 1
                continue
            elif (line == RECORD_DELIM):
                # ASSERT: end of record
                if (note_type == "Markierung" and highlight == 1):
                    title_notes[title] += '</i></div></blockquote><i><br/></i>\n'

                if (note_type == "Notiz" and notenote == 1):
                    title_notes[title] += '</div></blockquote><br/>\n';

                collect = 0
                is_title = 1
                highlight = 0
                notenote = 0
                continue
            else:
                # ASSERT: collecting lines for the current title/date
                if (collect == 1):
                    if (note_type == "Markierung" and highlight == 0):
                        title_notes[
                            title] += '<div><br/></div><blockquote style="margin: 0 0 0 40px; border: none; padding: 0px;"><div><i style="background-color:rgb(255, 250, 165);-evernote-highlight:true;">' + line + '\n'
                        highlight = 1
                    elif (note_type == "Notiz" and notenote == 0):
                        title_notes[
                            title] += '<div><br/></div><blockquote style="margin: 0 0 0 40px; border: none; padding: 0px;"><div>' + line + '\n'
                        notenote = 1
                    else:
                        title_notes[title] += line + '\n'

    # Email to Evernote

    msg_count = 0
    for title, note in title_notes.items():
        # INV: Do this for each title update we have


        # Package as an HTML email message so that we get the formatting in the note
        msg = MIMEMultipart('alternative')
        part1 = MIMEText(note, 'html')
        #part1 = MIMEText(note.encode('ascii', 'ignore'), 'html')
        msg.attach(part1)

        subject = str(title)
        #subject = title.encode('ascii', 'ignore')

        # Add notebook from config file, if it exists and is set
        notebook = config.get('NOTEBOOK', '')
        if notebook != '':
            subject += " @" + notebook

        # The space-+ at the end of the subject tells Evernote to append this to the most
        # recent note with the same title, or create a new note if the title does not exist
        subject += ' +'
        msg['Subject'] = subject

        # Address the message
        msg['From'] = config['GMAIL_USERNAME']
        msg['To'] = config['EN_ADDRESS']
        msg = msg.as_string()

        # Send the message
        try:
            smtplib.SMTP.set_debuglevel=1
            session = smtplib.SMTP(config['GMAIL_SERVER'], 587)
            #session.ehlo()
            session.starttls()
            session.login(config['GMAIL_USERNAME'], config['GMAIL_PASS'])
            session.sendmail(config['GMAIL_USERNAME'], config['EN_ADDRESS'], msg)
        except:
            pass
        else:
            if (verbose == 1):
                print('    Notes updated for ' + str(title))
            msg_count = msg_count + 1
            session.quit()

    # Update semaphore file
    f = open(SEMAPHORE, 'w')
    print(update_time.strftime("%Y-%m-%d %H:%M:%S"), file=f)
    f.close()

    if (verbose == 1):
        print('Finished parsing clippings file. Updated ' + str(msg_count) + ' notes in Evernote.')
        print('Be sure to sync Evernote with the server to see your updates.')


if __name__ == "__main__":
    main(sys.argv[1:])
