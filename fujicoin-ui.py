#!/usr/bin/env python

import gi, os, subprocess, time, ConfigParser
gi.require_version('Gtk', '3.0')
gi.require_version('Vte', '2.91')
gi.require_version('GConf', '2.0')
from gi.repository import Gtk, Gdk, Vte, GLib, Pango, GConf, GdkPixbuf
from os.path import expanduser


##################################
# This set your home dir (/home/you)
HOME= expanduser("~")

# Change variable below according to your installation.
# Usually installation is in your home dir, so just change
# what is after '+', if not change all string after '='
FUJICOIND_DIR = '/usr/local/bin'
FUJICOINUI_DIR = HOME + '/Web/git/fujicoin-ui'
GLADE_DIR = FUJICOINUI_DIR +  '/glade'
CSS_DIR = FUJICOINUI_DIR + '/glade'
DEBUG_LOG = HOME + '/.fujicoin/debug.log'
DB_LOG = HOME + '/.fujicoin/db.log'
##################################

def get_conf():
    # Still not in use
    conf_file = HOME + '/.fujicoin/fujicoin-ui.conf'
    config = ConfigParser.ConfigParser()
    config.readfp(open(conf_file))
    glade = config.get('var', 'glade')
    css = config.get('var', 'css')
    debug_log = config.get('var', 'debug_log')
    return [glade, css, debug_log]

def display_error(data):
	dialogError = gtk.MessageDialog(None, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK)
	dialogError.set_markup(data)
	dialogError.run()
	dialogError.destroy()

def gladefile(x):
    f = os.path.join(GLADE_DIR, x)
    if not os.path.exists(f):
        raise IOError('No such file or directory: %s' % f)
    return os.path.abspath(f)

class FujiCoin(object):
    def create_terminal(self):
        self.terminal   = Vte.Terminal()
        self.terminal.spawn_sync(
            Vte.PtyFlags.DEFAULT,
            os.environ['HOME'],
            ["/bin/bash"],
            [],
            GLib.SpawnFlags.DO_NOT_REAP_CHILD,
            None,
            None,
        )
        self.terminal.set_scrollback_lines(5000)
        self.terminal.set_scroll_on_output(True)
        self.terminal.set_rewrap_on_resize(True)
        return self.terminal

    def get_service_status(self):

        status_service = subprocess.check_output('ps -A', shell=True)
        pid = subprocess.check_output("ps -A | grep fujicoind|awk '{print $1}' ; exit 0", stderr=subprocess.STDOUT, shell=True)
        if 'fujicoind' in status_service.decode():
            self.label_info_service.set_text('Fujicoind Server is running with pid ' + pid.decode())
            self.service_start.set_sensitive(False)
            self.service_stop.set_sensitive(True)
        elif 'fujicoind' not in status_service.decode():
            self.label_info_service.set_text('Fujicoind is Stopped')
            self.service_stop.set_sensitive(False)
            self.service_start.set_sensitive(True)
        else:
            self.label_info_service.set_text('Unable to get Fujicoind Server status')

    def start_service(self, widget):

        os.system('fujicoind &')
        time.sleep(1)
        status_service = subprocess.check_output('ps -A; exit 0', stderr=subprocess.STDOUT, shell=True)
        pid = subprocess.check_output("ps -A|grep fujicoind|awk '{print $1}'; exit 0 ", stderr=subprocess.STDOUT, shell=True)
        if 'fujicoind' in status_service.decode():
            self.label_info_service.set_text('Fujicoind Server is running with pid ' + pid.decode())
            self.service_start.set_sensitive(False)
            self.service_stop.set_sensitive(True)
            get_info = subprocess.check_output("fujicoind getinfo | grep -v } | grep -v {; exit 0", stderr=subprocess.STDOUT, shell=True)
            self.lbl_home.set_text(get_info.decode())

    def stop_service(self, widget):

        os.system('fujicoind stop')
        time.sleep(1)
        status_service = subprocess.check_output('ps -A', shell=True)
        if  'fujicoind' not in status_service.decode():
            self.label_info_service.set_text('Fujicoind is Stopped')
            self.service_stop.set_sensitive(False)
            self.service_start.set_sensitive(True)

    def btn_home_clicked(self, widget):
        self.get_service_status()
        get_info = subprocess.check_output("fujicoind getinfo | grep -v } | grep -v {; exit 0", stderr=subprocess.STDOUT, shell=True)
        self.lbl_home.set_text(get_info.decode())
        self.notebook.set_current_page(0)

    def btn_receive_clicked(self, widget):
        self.notebook.set_current_page(1)

    def btn_send_clicked(self, widget):
        self.notebook.set_current_page(2)

    def btn_transaction_clicked(self, widget):
        self.notebook.set_current_page(3)

    def btn_nodes_clicked(self, widget):
        connected_node = subprocess.check_output("fujicoind getaddednodeinfo true; exit 0",  stderr=subprocess.STDOUT, shell=True)
        self.lbl_nodes.set_text(connected_node.decode())
        self.notebook.set_current_page(4)

    def btn_add_clicked(self, widget):
        node_name = self.txt_node.get_text()
        os.system('fujicoind addnode %s add' %(node_name))
        connected_node = subprocess.check_output("fujicoind getaddednodeinfo true", stderr=subprocess.STDOUT, shell=True)
        self.lbl_nodes.set_text(connected_node.decode())

    def btn_remove_clicked(self, widget):
        node_name = self.txt_node.get_text()
        os.system('fujicoind addnode %s remove' %(node_name))
        connected_node = subprocess.check_output("fujicoind getaddednodeinfo true", stderr=subprocess.STDOUT, shell=True)
        self.lbl_nodes.set_text(connected_node.decode())

    def btn_term_clicked(self, widget):
        self.notebook.set_current_page(5)

    def btn_help_clicked(self, widget):
        self.notebook.set_current_page(6)

    def on_debug_log_activate(self, widget):
        self.term_debug.show()
        self.term_debug.feed_child('tail -f  ' + DEBUG_LOG + ' \n', -1)
        self.notebook.set_current_page(7)

    def on_db_log_activate(self, widget):
        self.term_db.show()
        self.term_db.feed_child('tail -f  ' + DB_LOG + ' \n', -1)
        self.notebook.set_current_page(8)


    def __init__(self):

        super(FujiCoin, self).__init__()


        self.builder = Gtk.Builder()
        self.builder.add_from_file(gladefile('fujicoin.glade'))

        self.label_info_service = self.builder.get_object('label_info_service')
        self.service_start = self.builder.get_object('service_start')
        self.service_stop = self.builder.get_object('service_stop')
        self.notebook = self.builder.get_object('notebook')
        self.lbl_home = self.builder.get_object('lbl_home')
        self.lbl_nodes = self.builder.get_object('lbl_nodes')
        self.lbl_help = self.builder.get_object('lbl_help')
        self.txt_node = self.builder.get_object('txt_node_name')
        self.hbox_vte_debug_log = self.builder.get_object('hbox_vte_debug_log')
        self.hbox_vte_db_log = self.builder.get_object('hbox_vte_db_log')


        w = self.builder.get_object('window-root')
        w.show_all()

        signals = {
            "on_window-root_destroy" : Gtk.main_quit,
            "on_service_start_clicked" : self.start_service,
            "on_service_stop_clicked" : self.stop_service,
            "on_btn_home_clicked" : self.btn_home_clicked,
            "on_btn_receive_clicked" : self.btn_receive_clicked,
            "on_btn_send_clicked" : self.btn_send_clicked,
            "on_btn_transaction_clicked" : self.btn_transaction_clicked,
            "on_btn_nodes_clicked" : self.btn_nodes_clicked,
            "on_btn_term_clicked" : self.btn_term_clicked,
            "on_btn_help_clicked" : self.btn_help_clicked,
            "on_btn_add_clicked": self.btn_add_clicked,
            "on_btn_remove_clicked": self.btn_remove_clicked,
            "on_debug_log_activate": self.on_debug_log_activate,
            "on_db_log_activate": self.on_db_log_activate,
        }

        self.builder.connect_signals(signals)

        self.get_service_status()
        get_info = subprocess.check_output("fujicoind getinfo | grep -v } | grep -v {; exit 0", stderr=subprocess.STDOUT, shell=True)
        self.lbl_home.set_text(get_info.decode())

        self.term_debug = self.create_terminal()
        self.hbox_vte_debug_log.add(self.terminal)

        self.term_db = self.create_terminal()
        self.hbox_vte_db_log.add(self.terminal)


         # CSS Style
        cssProvider = Gtk.CssProvider()
        cssProvider.load_from_path(CSS_DIR + '/style.css')
        screen = Gdk.Screen.get_default()
        styleContext = Gtk.StyleContext()
        styleContext.add_provider_for_screen(screen, cssProvider,
                                    Gtk.STYLE_PROVIDER_PRIORITY_USER)

    def main(self):
        Gtk.main()


if __name__ == "__main__":
    fujicoin = FujiCoin()
    fujicoin.main()
