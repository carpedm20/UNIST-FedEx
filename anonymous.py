#-*- coding: utf-8 -*-
import gspread
import time, datetime
import facebook
import mechanize
import urllib2
import json
import sys

from email.MIMEImage import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage

from config import EMAIL, PASSWORD, SPREADSHEET_NAME, fb_email, fb_pass

facebook_app_link='https://www.facebook.com/dialog/oauth?scope=manage_pages,publish_stream&redirect_uri=http://carpedm20.blogspot.kr&response_type=token&client_id=641444019231608'

def get_second_from_timestamp(v):
    return time.mktime(datetime.datetime.strptime(v, "%d/%m/%Y %H:%M:%S").timetuple())

def get_app_access():
    link='https://www.facebook.com/dialog/oauth?scope=manage_pages,publish_stream&redirect_uri=http://carpedm20.blogspot.kr&response_type=token&client_id=641444019231608'

    br_mech = mechanize.Browser()
    br_mech.set_handle_robots(False)

    #print '[1] open link'
    br_mech.open(link)

    #print '[2] current url : ' + br_mech.geturl()

    br_mech.form = list(br_mech.forms())[0]
    control = br_mech.form.find_control("email")
    control.value=fb_email
    control = br_mech.form.find_control("pass")
    control.value=fb_pass

    #print '[3] submit'
    br_mech.submit()

    #print '[4] current url : ' + br_mech.geturl()

    app_access = br_mech.geturl().split('token=')[1].split('&expires')[0]
    page_app_access_url = "https://graph.facebook.com/me/accounts?access_token=" + app_access

    j = urllib2.urlopen(page_app_access_url)
    j = json.loads(j.read())

    for d in j['data']:
        if d['id'] == '1384519248463574':
            app_access = d['access_token']
            break

    return app_access

gc = gspread.login(EMAIL, PASSWORD)

worksheet = gc.open(SPREADSHEET_NAME).sheet1

min_column = 20

while True:
    try:
        cur_story = worksheet.cell(min_column, 2).value

        if cur_story == None:
            continue
        else:
            cur_story = cur_story.encode('utf-8')
            print "[*] current : %s" % min_column

        if worksheet.cell(min_column, 4).value:
            if worksheet.cell(min_column, 4).value.encode('utf-8') != "잔디":
                min_column += 1
                continue
        else:
            min_column += 1
            continue

        cur_tag_hash_string = ""

        if worksheet.cell(min_column, 3).value:
            cur_tag_string = worksheet.cell(min_column, 3).value
            cur_tags = [x.strip().encode('utf-8').replace(' ','_') for x in cur_tag_string.split(',')]
            cur_tag_hash_string = "#unistfedex_" + " #unistfedex_".join(cur_tags)

        app_access = get_app_access()
        print " [%] APP_ACCESS : " + app_access

        content = "사연 올리기 : http://goo.gl/8Epbui\r\n\r\n" + cur_story + "\r\n\r\n"
        content += cur_tag_hash_string

        print " >>> %s" % content
        print " >>>>>> %s" % cur_tag_hash_string

        graph = facebook.GraphAPI(app_access)
        graph.put_wall_post(content)

        min_column += 1

    except:
        for e in sys.exc_info():
            print e
        continue
