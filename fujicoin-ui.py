#!/usr/bin/env python

import gi, os, subprocess, time, ConfigParser
import simplejson as json
gi.require_version('Gtk', '3.0')
gi.require_version('Vte', '2.91')
gi.require_version('GConf', '2.0')
from gi.repository import Gtk, Gdk, Vte, GLib, Pango, GConf, GdkPixbuf
from os.path import expanduser


HOME = expanduser("~")
conf_file = HOME + '/.fujicoin/fujicoin-ui.conf'


def get_conf():
    config = ConfigParser.ConfigParser()
    config.readfp(open(conf_file))
    glade = config.get('var', 'glade')
    css = config.get('var', 'css')
    debug_log = config.get('var', 'debug_log')
    db_log = config.get('var', 'db_log')
    return { 'glade' : glade,
            'css' : css,
            'debug_log' : debug_log,
            'db_log' : db_log,
            }

conf = get_conf()
GLADE_DIR = conf['glade']
CSS_FILE = conf['css']
DEBUG_LOG = conf['debug_log']
DB_LOG = conf['db_log']

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

    def tail_debug_log(self, widget):
        self.term_debug_log.show()
        self.term_debug_log.feed_child('tail -f  ' + DEBUG_LOG + ' \n', -1)
        self.notebook.set_current_page(5)

    def get_service_status(self):
        status_service = subprocess.check_output('ps -A', shell=True)
        pid = subprocess.check_output("ps -A | grep fujicoind|awk '{print $1}' ; exit 0", stderr=subprocess.STDOUT, shell=True)
        if 'fujicoind' in status_service.decode():
            self.lbl_info_service.set_text('Fujicoind Server is running with pid ' + pid.decode())
            self.btn_service_start.set_sensitive(False)
            self.btn_service_stop.set_sensitive(True)
        elif 'fujicoind' not in status_service.decode():
            self.lbl_info_service.set_text('Fujicoind is Stopped')
            self.btn_service_stop.set_sensitive(False)
            self.btn_service_start.set_sensitive(True)
        else:
            self.lbl_info_service.set_text('Unable to get Fujicoind Server status')

    def start_service(self, widget):
        os.system('fujicoind &')
        time.sleep(1)
        status_service = subprocess.check_output('ps -A; exit 0', stderr=subprocess.STDOUT, shell=True)
        pid = subprocess.check_output("ps -A|grep fujicoind|awk '{print $1}'; exit 0 ", stderr=subprocess.STDOUT, shell=True)
        if 'fujicoind' in status_service.decode():
            self.lbl_info_service.set_text('Fujicoind Server is running with pid ' + pid.decode())
            self.btn_service_start.set_sensitive(False)
            self.btn_service_stop.set_sensitive(True)
            self.open_home(self)

    def stop_service(self, widget):
        os.system('fujicoind stop')
        time.sleep(1)
        status_service = subprocess.check_output('ps -A', shell=True)
        if  'fujicoind' not in status_service.decode():
            self.lbl_info_service.set_text('Fujicoind is Stopped')
            self.btn_service_stop.set_sensitive(False)
            self.btn_service_start.set_sensitive(True)

    def open_home(self, widget):
        self.get_service_status()
        get_info = subprocess.check_output("fujicoind getinfo; exit 0", stderr=subprocess.STDOUT, shell=True)
        try:
            j_info = json.loads(get_info)
            balance = j_info['balance']
            blocks = j_info['blocks']
            difficulty = j_info['difficulty']
            errors = j_info['errors']
            label_list = [self.lbl_balance, self.lbl_blocks, self.lbl_errors, self.lbl_difficulty]
            for i in label_list:
                i.set_text("")
            self.lbl_balance.set_text("Balance: " + str(balance))
            self.lbl_blocks.set_text("Blocks: " + str(blocks))
            self.lbl_difficulty.set_text("Difficulty: " + str(difficulty))
            self.lbl_errors.set_text("Errors: " + str(errors))
        except:
            pass
        self.notebook.set_current_page(0)

    def open_nodes(self, widget):
        self.listbox_nodes.destroy()
        self.listbox_nodes = Gtk.ListBox()
        self.vbox_cont_nodes.pack_start(self.listbox_nodes, False, False, 0)
        connected_node = subprocess.check_output("fujicoind getaddednodeinfo true; exit 0",  stderr=subprocess.STDOUT, shell=True)
        try:
            j_nodes = json.loads(connected_node)
            if len(j_nodes) > 0:
                for i in range(len(j_nodes)):
                    node_name = j_nodes[i]['addednode']
                    connected = str(j_nodes[i]['connected'])
                    self.hboxRowNode = Gtk.HBox()
                    self.listbox_nodes.add(self.hboxRowNode)
                    self.lbl_node_name = Gtk.Label()
                    self.hboxRowNode.pack_start(self.lbl_node_name, True, True, 5)
                    self.lbl_node_connected = Gtk.Label()
                    self.hboxRowNode.pack_start(self.lbl_node_connected, True, True, 5)
                    self.lbl_node_name.set_text(node_name)
                    self.lbl_node_connected.set_text(connected)
                    self.hboxRowNode.show()
                    self.lbl_node_name.show()
                    self.lbl_node_connected.show()
                    self.listbox_nodes.show()
            else:
                pass
                #self.hboxRowNode = Gtk.HBox()
                #self.listbox_nodes.add(self.hboxRowNode)
                #self.lbl_node_name = Gtk.Label()
                #self.hboxRowNode.pack_start(self.lbl_node_name, True, True, 5)
                #self.lbl_node_connected = Gtk.Label()
                #self.hboxRowNode.pack_start(self.lbl_node_connected, True, True, 5)
        except:
            pass

        self.notebook.set_current_page(4)

    def add_node(self, widget):
        node_name = self.txt_node_name.get_text()
        os.system('fujicoind addnode %s add' %(node_name))
        self.open_nodes(self)
        """connected_node = subprocess.check_output("fujicoind getaddednodeinfo true " + node_name, stderr=subprocess.STDOUT, shell=True)
        j_nodes = json.loads(connected_node)

        node_name = j_nodes[0]['addednode']
        connected = str(j_nodes[0]['connected'])

        self.hboxRowNode = Gtk.HBox()
        self.listbox_nodes.add(self.hboxRowNode)
        self.lbl_node_name = Gtk.Label()
        self.hboxRowNode.pack_start(self.lbl_node_name, True, True, 5)
        self.lbl_node_connected = Gtk.Label()
        self.hboxRowNode.pack_start(self.lbl_node_connected, True, True, 5)
        self.lbl_node_name.set_text(node_name)
        self.lbl_node_connected.set_text(connected)

        self.hboxRowNode.show()
        self.lbl_node_name.show()
        self.lbl_node_connected.show()"""

    def remove_node(self, widget):
        row = self.listbox_nodes.get_selected_rows()
        hbox = row[0].get_children()
        label = hbox[0].get_children()
        node_name = label[0].get_text()
        os.system('fujicoind addnode %s remove' %(node_name))
        self.open_nodes(self)

    def __init__(self):

        super(FujiCoin, self).__init__()


        self.builder = Gtk.Builder()
        self.builder.add_from_file(gladefile('fujicoin-ui.glade'))

        self.vbox_cont_nodes = self.builder.get_object('vbox_cont_nodes')
        self.lbl_info_service = self.builder.get_object('lbl_info_service')
        self.btn_service_start = self.builder.get_object('btn_service_start')
        self.btn_service_stop = self.builder.get_object('btn_service_stop')
        self.lbl_balance = self.builder.get_object('lbl_balance')
        self.lbl_blocks = self.builder.get_object('lbl_blocks')
        self.lbl_difficulty = self.builder.get_object('lbl_difficulty')
        self.lbl_errors = self.builder.get_object('lbl_errors')
        self.notebook = self.builder.get_object('notebook')
        self.btn_nodes_png = self.builder.get_object('btn_nodes_png')
        self.listbox_nodes = self.builder.get_object('listbox_nodes')
        self.txt_node_name = self.builder.get_object('txt_node_name')
        self.hbox_vte_debug_log = self.builder.get_object('hbox_vte_debug_log')

        w = self.builder.get_object('window-root')
        w.show_all()

        signals = {
            "on_window-root_destroy" : Gtk.main_quit,
            "on_menu_debug_log_activate": self.tail_debug_log,
            "on_btn_service_start_clicked" : self.start_service,
            "on_btn_service_stop_clicked" : self.stop_service,
            "on_btn_home_clicked": self.open_home,
            "on_btn_nodes_clicked": self.open_nodes,
            "on_btn_add_node_clicked" : self.add_node,
            "on_btn_remove_node_clicked": self.remove_node,
        }

        self.builder.connect_signals(signals)

        self.open_home(self)

        self.term_debug_log = self.create_terminal()
        self.hbox_vte_debug_log.add(self.term_debug_log)


         # CSS Style
        cssProvider = Gtk.CssProvider()
        cssProvider.load_from_path(CSS_FILE)
        screen = Gdk.Screen.get_default()
        styleContext = Gtk.StyleContext()
        styleContext.add_provider_for_screen(screen, cssProvider,
                                    Gtk.STYLE_PROVIDER_PRIORITY_USER)

    def main(self):
        Gtk.main()


if __name__ == "__main__":
    fujicoin = FujiCoin()
    fujicoin.main()
