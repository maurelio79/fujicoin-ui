#!/usr/bin/env python
try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser
import simplejson as json
import gi, os, subprocess, time, sys
gi.require_version('Gtk', '3.0')
gi.require_version('Vte', '2.91')
gi.require_version('GConf', '2.0')
from gi.repository import Gtk, Gdk, Vte, GLib, Pango, GConf, GdkPixbuf, GObject
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
        self.terminal.set_sensitive(True)
        return self.terminal

    def tail_debug_log(self, widget):
        self.term_debug_log.show()
        self.term_debug_log.feed_child('tail -f  ' + DEBUG_LOG + ' \n', -1)
        self.notebook.set_current_page(5)

    def open_home(self, widget):
        self.get_service_status()
        try:
            get_info = subprocess.check_output("fujicoind getinfo; exit 0", stderr=subprocess.STDOUT, shell=True)
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
            print ("Open_Home Unexpected error:", sys.exc_info())
        self.notebook.set_current_page(0)

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

    def open_transaction(self, widget):
        self.populate_drp_tran(self)
        self.listbox_transaction.destroy()
        self.listbox_transaction = Gtk.ListBox()
        self.vbox_cont_transaction.pack_start(self.listbox_transaction, False, False, 0)
        account_text = self.drp_tran_account.get_active_text()
        if (account_text == "ALL"):
            account_text = "*"
        count = str(int(self.spin_count_tran.get_value()))
        transactions = subprocess.check_output("fujicoind listtransactions \"" + account_text + "\" " + count + " 0; exit 0",  stderr=subprocess.STDOUT, shell=True)
        try:
            j_transactions = json.loads(transactions)
            if len(j_transactions) > 0:
                for i in range(len(j_transactions)):
                    account = j_transactions[i]['account']
                    category = j_transactions[i]['category']
                    amount = j_transactions[i]['amount']
                    self.hboxRowTransaction = Gtk.HBox()
                    self.hboxRowTransaction.set_margin_top(5)
                    self.listbox_transaction.add(self.hboxRowTransaction)
                    self.lbl_tran_account = Gtk.Label()
                    self.hboxRowTransaction.pack_start(self.lbl_tran_account, True, True, 5)
                    self.lbl_tran_category = Gtk.Label()
                    self.hboxRowTransaction.pack_start(self.lbl_tran_category, True, True, 5)
                    self.lbl_tran_amount = Gtk.Label()
                    self.hboxRowTransaction.pack_start(self.lbl_tran_amount, True, True, 5)
                    self.lbl_tran_account.set_text(account)
                    self.lbl_tran_category.set_text(category)
                    self.lbl_tran_amount.set_text(str(format(amount, '.8f')))
                    self.hboxRowTransaction.show()
                    self.lbl_tran_account.show()
                    self.lbl_tran_category.show()
                    self.lbl_tran_amount.show()
                    self.listbox_transaction.show()
            else:
                pass
        except:
            print ("Open Transaction Unexpected error:", sys.exc_info())

        self.notebook.set_current_page(1)

    def populate_drp_tran(self, widget):
        self.drp_tran_account.remove_all()
        self.drp_tran_account.append_text("ALL")
        list_account = subprocess.check_output("fujicoind listaccounts; exit 0",  stderr=subprocess.STDOUT, shell=True)
        j_accounts = json.loads(list_account)
        for key in j_accounts:
            if (key != ""):
                self.drp_tran_account.append_text(key)
            else:
                pass
        self.drp_tran_account.set_active(0)

    def set_filter_tran(self, widget):
        self.listbox_transaction.destroy()
        self.listbox_transaction = Gtk.ListBox()
        self.vbox_cont_transaction.pack_start(self.listbox_transaction, False, False, 0)
        account_text = self.drp_tran_account.get_active_text()
        category_text = self.drp_tran_category.get_active_text()
        if (account_text == "ALL" or account_text == None):
            account_text = "*"
        count = str(int(self.spin_count_tran.get_value()))
        try:
            transactions = subprocess.check_output("fujicoind listtransactions \"" + account_text + "\" " + count + " 0; exit 0",  stderr=subprocess.STDOUT, shell=True)
            j_transactions = json.loads(transactions)
            if len(j_transactions) > 0:
                for i in range(len(j_transactions)):
                    account = j_transactions[i]['account']
                    category = j_transactions[i]['category']
                    amount = j_transactions[i]['amount']
                    if ((account_text == "*" or account_text == account) and (category_text == "ALL" or category_text == category)):
                        self.hboxRowTransaction = Gtk.HBox()
                        self.hboxRowTransaction.set_margin_top(5)
                        self.listbox_transaction.add(self.hboxRowTransaction)
                        self.lbl_tran_account = Gtk.Label()
                        self.hboxRowTransaction.pack_start(self.lbl_tran_account, True, True, 5)
                        self.lbl_tran_category = Gtk.Label()
                        self.hboxRowTransaction.pack_start(self.lbl_tran_category, True, True, 5)
                        self.lbl_tran_amount = Gtk.Label()
                        self.hboxRowTransaction.pack_start(self.lbl_tran_amount, True, True, 5)
                        self.lbl_tran_account.set_text(account)
                        self.lbl_tran_category.set_text(category)
                        self.lbl_tran_amount.set_text(str(format(amount, '.8f')))
                        self.hboxRowTransaction.show()
                        self.lbl_tran_account.show()
                        self.lbl_tran_category.show()
                        self.lbl_tran_amount.show()
                        self.listbox_transaction.show()
                    else:
                        pass
            else:
                pass
        except:
            print ("Set_Filter Unexpected error:", sys.exc_info())

    def open_send(self, widget):
        self.populate_drp_send(self)
        self.lbl_result_move.set_text("")
        self.lbl_result_send.set_text("")
        self.notebook.set_current_page(3)

    def populate_drp_send(self, widget):
        try:
            self.drp_from_move.remove_all()
            self.drp_to_move.remove_all()
            self.drp_from_send.remove_all()
            list_account = subprocess.check_output("fujicoind listaccounts; exit 0",  stderr=subprocess.STDOUT, shell=True)
            j_accounts = json.loads(list_account)
            for key in j_accounts:
                if (key != ""):
                    self.drp_from_move.append_text(key)
                    self.drp_to_move.append_text(key)
                    self.drp_from_send.append_text(key)
                else:
                    pass
            self.drp_from_move.set_active(0)
            self.drp_to_move.set_active(0)
            self.drp_from_send.set_active(0)
        except:
            print ("Populate_Drp_Send Unexpected error:", sys.exc_info())

    def move_coin(self, widget):
        from_account = self.drp_from_move.get_active_text()
        to_account = self.drp_to_move.get_active_text()
        amount = self.spin_amount_move.get_value()
        amount = format(amount, '.8f')
        minconf = self.spin_minconf_move.get_value()
        minconf = int(minconf)
        comment = self.entry_comment_move.get_text()
        move_coin = subprocess.check_output("fujicoind move " + from_account + " " + to_account + " " + str(amount) + " " + str(minconf) + " " + comment + "; exit 0",  stderr=subprocess.STDOUT, shell=True)
        if (move_coin.strip() == "true"):
            move_message = "Correctly moved " + str(amount) + " fujicoin\nfrom account " + from_account + " to account " + to_account
            self.lbl_result_move.set_text(move_message)
        else:
            move_message = move_coin
            self.lbl_result_move.set_text(move_message)

    def send_coin(self, widget):
        from_account = self.drp_from_send.get_active_text()
        to_address = self.entry_send.get_text()
        amount = self.spin_amount_send.get_value()
        amount = format(amount, '.8f')
        minconf = self.spin_minconf_send.get_value()
        minconf = int(minconf)
        comment = self.entry_comment_send.get_text()
        comment_to = self.entry_comment_to_send.get_text()
        send_coin = subprocess.check_output("fujicoind sendfrom " + from_account + " " + to_address + " " + str(amount) + " " + str(minconf) + " " + comment + " " + comment_to + "; exit 0",  stderr=subprocess.STDOUT, shell=True)
        if (send_coin.strip() == "true"):
            send_message = "Correctly sent " + str(amount) + " fujicoin\nfrom account " + from_account + " to address " + to_address
            self.lbl_result_send.set_text(send_message)
        else:
            send_message = send_coin
            self.lbl_result_send.set_text(send_message)

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
                    self.hboxRowNode.set_margin_top(5)
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
        except:
            print ("Open_Nodes Unexpected error:", sys.exc_info())

        self.notebook.set_current_page(4)

    def add_node(self, widget):
        node_name = self.txt_node_name.get_text()
        os.system('fujicoind addnode %s add' %(node_name))
        self.open_nodes(self)

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

        self.btn_receive = self.builder.get_object('btn_receive')

        self.lbl_info_service = self.builder.get_object('lbl_info_service')
        # Notebbok
        self.notebook = self.builder.get_object('notebook')
        # Home Page
        self.btn_service_start = self.builder.get_object('btn_service_start')
        self.btn_service_stop = self.builder.get_object('btn_service_stop')
        self.lbl_balance = self.builder.get_object('lbl_balance')
        self.lbl_blocks = self.builder.get_object('lbl_blocks')
        self.lbl_difficulty = self.builder.get_object('lbl_difficulty')
        self.lbl_errors = self.builder.get_object('lbl_errors')
        # Transaction Page
        self.vbox_cont_transaction = self.builder.get_object('vbox_cont_transaction')
        self.listbox_transaction = self.builder.get_object('listbox_transaction')
        self.drp_tran_account = self.builder.get_object('drp_tran_account')
        self.drp_tran_category = self.builder.get_object('drp_tran_category')
        self.spin_count_tran = self.builder.get_object('spin_count_tran')
        # Send Page
        # Move section
        self.drp_from_move = self.builder.get_object('drp_from_move')
        self.drp_to_move = self.builder.get_object('drp_to_move')
        self.spin_amount_move = self.builder.get_object('spin_amount_move')
        self.spin_minconf_move = self.builder.get_object('spin_minconf_move')
        self.entry_comment_move = self.builder.get_object('entry_comment_move')
        self.lbl_result_move = self.builder.get_object('lbl_result_move')
        # Send section
        self.drp_from_send = self.builder.get_object('drp_from_send')
        self.entry_send = self.builder.get_object('entry_send')
        self.spin_amount_send = self.builder.get_object('spin_amount_send')
        self.spin_minconf_send = self.builder.get_object('spin_minconf_send')
        self.entry_comment_send = self.builder.get_object('entry_comment_send')
        self.entry_comment_to_send = self.builder.get_object('entry_comment_to_send')
        self.lbl_result_send = self.builder.get_object('lbl_result_send')

        # Receive Page
        self.vbox_cont_receive = self.builder.get_object('vbox_cont_receive')
        self.listbox_receive = self.builder.get_object('listbox_receive')
        # Nodes Page
        self.vbox_cont_nodes = self.builder.get_object('vbox_cont_nodes')
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
            "on_btn_transaction_clicked": self.open_transaction,
            "on_drp_tran_account_changed": self.set_filter_tran,
            "on_drp_tran_category_changed": self.set_filter_tran,
            "on_spin_count_tran_value_changed": self.set_filter_tran,
            "on_btn_send_clicked": self.open_send,
            "on_btn_move_clicked": self.move_coin,
            "on_btn_send_coin_clicked": self.send_coin,
            "on_btn_nodes_clicked": self.open_nodes,
            "on_btn_add_node_clicked" : self.add_node,
            "on_btn_remove_node_clicked": self.remove_node,
        }

        self.builder.connect_signals(signals)

        self.btn_receive.hide()

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
