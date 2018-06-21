#!/usr/bin/env python3
import signal
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
gi.require_version('Notify', '0.7')
from gi.repository import Gtk, AppIndicator3, GObject, Notify
from time import sleep
from threading import Thread
import sys
from os import path, makedirs
from subprocess import call
from webbrowser import open as urlopen
from apiclient import discovery
from httplib2 import Http
from oauth2client import file, client, tools


# determine if application is a script file or frozen exe
if getattr(sys, 'frozen', False):
    current_path = path.dirname(sys.executable)
    APP_FROZEN = True
elif __file__:
    current_path = path.dirname(path.realpath(__file__))
    APP_FROZEN = False

CFG_PATH = path.expanduser('~') + "/.ujagagaGmailNotify"
CFG_NAME = "config.txt"
CFG_FULL_PATH = CFG_PATH + '/' + CFG_NAME
ICON_M_NEW_PATH = current_path + "/gmail_new.png"
ICON_M_NONE_PATH = current_path + "/gmail_none.png"
ICON_LOGO_PATH = current_path + "/logo.png"
SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
CREDENTIALS_NAME = "credentials_"
label_id_one = 'INBOX'
label_id_two = 'UNREAD'

IMG_ABOUT = ICON_LOGO_PATH
IMG_INFO = "dialog-information"


def open_cfg():
    global current_path
    global CFG_FULL_PATH
    global ICON_LOGO_PATH

    if APP_FROZEN:
        cmd = 'notify-send'
        cfg_msg = "The configuration file resides in:\n" + CFG_PATH
        cfg_msg += "\nYou can edit this file in any text editor."

        call([cmd, cfg_msg, '-i', ICON_LOGO_PATH])
    else:
        cmd = 'xdg-open'
        call([cmd, CFG_FULL_PATH])


def read_cfg():
    global CFG_FULL_PATH

    file = open(CFG_FULL_PATH, 'r')
    content = file.readlines()
    file.close()

    result_list = []

    for line in content:
        line = line.replace("\n", "")

        while " " in line:
            line = line.replace(" ", "")

        if not line.startswith("#") and len(line) > 2:
            result_list.append(line)

    return result_list


class Indicator:
    def __init__(self):
        global ICON_M_NEW_PATH
        global ICON_M_NONE_PATH

        self.app = 'ujagagaGmailNotify'

        self.indicator = AppIndicator3.Indicator.new(self.app, ICON_M_NONE_PATH, AppIndicator3.IndicatorCategory.OTHER)
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.indicator.set_menu(self.create_menu())

        # init baloon notifications
        Notify.init(self.app)

        # the thread:
        self.update = Thread(target=self.check_gmail)

        # daemonize the thread to make the indicator stoppable
        self.update.setDaemon(True)
        self.update.start()

    def create_menu(self):
        menu = Gtk.Menu()

        # Launch web browser
        item_open_gmail = Gtk.MenuItem('Open GMail')
        item_open_gmail.connect('activate', lambda unused_param: urlopen("https://mail.google.com"))
        menu.append(item_open_gmail)

        # separator
        menu_sep1 = Gtk.SeparatorMenuItem()
        menu.append(menu_sep1)

        # About
        item_about = Gtk.MenuItem('About')
        item_about.connect('activate', self.about)
        menu.append(item_about)

        # configure
        item_cfg = Gtk.MenuItem('Configure')
        item_cfg.connect('activate', self.configure)
        menu.append(item_cfg)

        # separator
        menu_sep2 = Gtk.SeparatorMenuItem()
        menu.append(menu_sep2)

        # quit
        item_quit = Gtk.MenuItem('Quit')
        item_quit.connect('activate', self.stop)
        menu.append(item_quit)

        menu.show_all()
        return menu

    def send_notification(self, msg_text, img=IMG_ABOUT):
        global ICON_LOGO_PATH
        global IMG_ABOUT
        Notify.Notification.new(self.app, msg_text, img).show()

    def configure(self, cmd):
        open_cfg()

    def check_gmail(self):
        global CREDENTIALS_NAME
        global CFG_PATH
        global ICON_M_NEW_PATH
        global ICON_M_NONE_PATH

        last_notification = None

        while True:
            total_msg_count = 0
            notification = ""

            mailbox_list = read_cfg()

            if len(mailbox_list) > 0:

                for mailbox in mailbox_list:

                    credentials_file_path = CFG_PATH + '/' + CREDENTIALS_NAME + mailbox

                    store = file.Storage(credentials_file_path)
                    creds = store.get()
                    if not creds or creds.invalid:
                        flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
                        creds = tools.run_flow(flow, store)

                    service = discovery.build('gmail', 'v1', http=creds.authorize(Http()))

                    unread_msgs = service.users().messages().list(userId='me',
                                                                  labelIds=[label_id_one, label_id_two]).execute()
                    msg_count = 0

                    try:
                        msg_count = len(unread_msgs['messages'])
                        total_msg_count += msg_count
                    except:
                        pass

                    print("Total unread messages in ", mailbox, ":", msg_count)

                    if msg_count > 0:
                        if len(notification) < 3:
                            notification = "New GMail in " + mailbox
                        else:
                            if mailbox == mailbox_list[-1]:
                                notification += ' and ' + mailbox
                            else:
                                notification += ", " + mailbox

                if total_msg_count == 0:

                    last_notification = ""
                    self.indicator.set_icon(ICON_M_NONE_PATH)

                else:

                    if notification != last_notification:
                        last_notification = notification
                        self.send_notification(notification)

                        self.indicator.set_icon(ICON_M_NEW_PATH)

                sleep(20)
            else:
                sleep(2)

    def about(self, event):
        global ICON_M_NEW_PATH
        global IMG_ABOUT

        self.send_notification('Indicator app to notify when new Gmail arrives', IMG_ABOUT)

    def stop(self, cmd):
        Notify.uninit()
        Gtk.main_quit()


# Create the configuration folder if it does not exist
if not path.exists(CFG_PATH):
    makedirs(CFG_PATH)

# Create configuration file if it does not exist
if not path.exists(CFG_FULL_PATH):
    cfg_file = open(CFG_FULL_PATH, 'w')
    cfg_file.write("# ujagaga GMail notifier configuration. Just list names of your mailboxes here.\n")
    cfg_file.write("# This configuration file is located in:" + CFG_PATH + "\n")
    cfg_file.close()

    # Show it to the user so it can be adjusted
    open_cfg()

Indicator()
# this is where we call GObject.threads_init()
GObject.threads_init()
signal.signal(signal.SIGINT, signal.SIG_DFL)
Gtk.main()
