#-*- coding: utf-8 -*-

from xvfbwrapper import Xvfb
import gspread
import time, datetime
import facebook
import mechanize
import urllib2
import json
import atexit
import sys
import Image

from selenium import webdriver

from email.MIMEImage import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage

from config import EMAIL, PASSWORD, SPREADSHEET_NAME, fb_email, fb_pass
from ban import ban

min_column = 83

vdisplay = Xvfb()
vdisplay.start()

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtWebKit import *

class Screenshot(QWebView):
    def __init__(self):
        self.app = QApplication(sys.argv)
        QWebView.__init__(self)
        self._loaded = False
        self.loadFinished.connect(self._loadFinished)

    def capture(self, url, output_file):
        self.load(QUrl(url))
        self.wait_load()
        # set to webpage size
        frame = self.page().mainFrame()
        self.page().setViewportSize(frame.contentsSize())
        # render image
        image = QImage(self.page().viewportSize(), QImage.Format_ARGB32)
        painter = QPainter(image)
        frame.render(painter)
        painter.end()
        print 'saving', output_file
        image.save(output_file)

    def wait_load(self, delay=0):
        # process app events until page loaded
        while not self._loaded:
            self.app.processEvents()
            time.sleep(delay)
        self._loaded = False

    def _loadFinished(self, result):
        self._loaded = True

def exit_handler():
    print "DEAD"
    vdisplay.stop()

atexit.register(exit_handler)

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

no_more_post = False

print "[*] START"

while True:
  try:
    #print "[#] Current column : " + str(min_column)
    cur_story = worksheet.cell(min_column, 2).value

    if cur_story == None:
        if no_more_post == False:
            print "No more post..."
            no_more_post = True
        else:
            pass
        continue
    else:
        no_more_post = False
        cur_story = cur_story.encode('utf-8')
        print "[*] current : %s" % min_column

    if any(word in cur_story for word in ban) is True:
        print "[ TRASH DETECTED ]"
        print "   >>> " + cur_story
        min_column += 1
        continue

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
        cur_tags = [x.strip().encode('utf-8').replace(' ','_').replace('@','') for x in cur_tag_string.split(',')]

        cur_tag_hash_string = "#unistfedex_" + " #unistfedex_".join(cur_tags)

        if any(word in cur_tag_hash_string for word in ban) is True:
            print "[ TRASH DETECTED ]"
            print "   >>> " + cur_story
            print "   >>> " + cur_tag_hash_string
            min_column += 1
            continue

    app_access = get_app_access()
    print " [%] APP_ACCESS : " + app_access

    #s = Screenshot()
    #s.capture('http://hexa2.iptime.org/~carpedm20/anonymous.php?message=' + cur_story, 'screenshot.png')

    file_name = 'screenshot.png'
    new_file_name = 'new.png'

    browser = webdriver.Firefox()
    browser.set_window_size(250,200)

    fb_message_url = 'http://hexa2.iptime.org/~carpedm20/anonymous.php?message=' + cur_story.replace('\n','<br/>')

    browser.get(fb_message_url)
    print "FB_MESSAGE_URL : " + fb_message_url

    browser.save_screenshot(file_name)

    img = Image.open(file_name)
    width, height = img.size

    new = img.crop((0, 0, 250, height))
    new.save(new_file_name)

    content = "사연 올리기 : http://goo.gl/8Epbui\r\n\r\n"
    content += cur_tag_hash_string

    print " >>> %s" % content
    print " >>>>>> %s" % cur_tag_hash_string

    graph = facebook.GraphAPI(app_access)
    #graph.put_wall_post(content)
    graph.put_photo(open(new_file_name), content)

    min_column += 1

  except:
    for e in sys.exc_info():
        print e
    continue
