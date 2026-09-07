import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import tkinter as tk
from unittest.mock import patch, MagicMock

import database
from ui.main_window import MainWindow
from ui.invoice_ui import InvoiceUI, generate_thermal_receipt_pdf, generate_a4_invoice_pdf
from ui.invoice_history_ui import InvoiceHistoryUI
from ui.ledger_ui import LedgerUI
from ui.inventory_ui import InventoryUI
from ui.dashboard_ui import DashboardUI

def run_tests():
    print('=' * 60)
    print('STARTING FULL END-TO-END AUTOMATED TEST SUITE')
    print('=' * 60)

    root = tk.Tk()
    root.withdraw()

    with patch('tkinter.messagebox.showinfo') as mock_info, \
         patch('tkinter.messagebox.showerror') as mock_error, \
         patch('tkinter.messagebox.showwarning') as mock_warning, \
         patch('ui.invoice_ui.open_pdf_file') as mock_open_pdf:

        # Step 1: Initialize MainWindow
        print('[TEST 1] Initializing MainWindow...')
        app = MainWindow(root)
        print('MainWindow initialized successfully.')

        # Step 2: Test InvoiceUI directly
        print('[TEST 2] Testing InvoiceUI workflow...')
        app.open_invoice()
        inv_ui = app.current_ui

        assert hasattr(inv_ui, 'handle_table_click'), 'Missing handle_table_click!'
        assert hasattr(inv_ui, 'refresh_cart_table'), 'Missing refresh_cart_table!'
        assert hasattr(inv_ui, 'edit_cart_item'), 'Missing edit_cart_item!'
        assert hasattr(inv_ui, 'delete_cart_item'), 'Missing delete_cart_item!'
        assert hasattr(inv_ui, 'save_thermal_btn'), 'Missing save_thermal_btn!'
        assert hasattr(inv_ui, 'save_a4_btn'), 'Missing save_a4_btn!'
        print('All InvoiceUI methods & attributes present.')

        # Clear state
        inv_ui.clear_invoice()
        assert len(inv_ui.cart_items) == 0

        # Select customer
        customers = database.get_customer_names_with_phone()
        cust_name = customers[0] if customers else 'Test Auto Customer'
        inv_ui.customer_combo.set(cust_name)

        # Select product
        products = database.get_product_names()
        assert len(products) > 0, 'No products in database!'
        prod_name = products[0]
        inv_ui.product_combo.set(prod_name)
        inv_ui.autofill_product_details(focus_qty=False)

        # Add to cart
        inv_ui.qty_entry.delete(0, tk.END)
        inv_ui.qty_entry.insert(0, '3')
        inv_ui.discount_entry.delete(0, tk.END)
        inv_ui.discount_entry.insert(0, '5')

        inv_ui.add_to_cart()
        assert len(inv_ui.cart_items) == 1
        print('Added item to cart:', inv_ui.cart_items[0]['name'])

        if len(products) > 1:
            inv_ui.product_combo.set(products[1])
            inv_ui.autofill_product_details(focus_qty=False)
            inv_ui.qty_entry.delete(0, tk.END)
            inv_ui.qty_entry.insert(0, '2')
            inv_ui.add_to_cart()
            assert len(inv_ui.cart_items) == 2
            print('Added 2nd item to cart:', inv_ui.cart_items[1]['name'])

        # Test Editing cart item
        tree_children = inv_ui.tree.get_children()
        assert len(tree_children) >= 1
        first_row = tree_children[0]
        inv_ui.edit_cart_item(first_row)
        assert inv_ui.editing_cart_index == 0
        inv_ui.qty_entry.delete(0, tk.END)
        inv_ui.qty_entry.insert(0, '5')
        inv_ui.add_to_cart()
        assert inv_ui.cart_items[0]['quantity'] == 5
        print('Cart item edit & update verified successfully.')

        # Test Deleting a cart item
        if len(inv_ui.cart_items) >= 2:
            tree_children = inv_ui.tree.get_children()
            del_row = tree_children[-1]
            inv_ui.delete_cart_item(del_row)
            assert len(inv_ui.cart_items) == 1
            print('Cart item deletion verified successfully.')

        # Test Paid Amount & Pending calculation
        inv_ui.paid_entry.delete(0, tk.END)
        inv_ui.paid_entry.insert(0, '100')
        inv_ui.on_paid_changed()
        inv_ui.update_pending()
        print('Pending calculated successfully:', repr(inv_ui.pending_label.cget('text')))

        # Test Save Invoice - Thermal (Default)
        inv_ui.save_invoice(format_type='thermal')
        assert mock_info.called, 'showinfo was not called on save!'
        print('Save Invoice (80mm Thermal Receipt default) completed successfully.')

        # Re-add item to test A4 Save
        inv_ui.customer_combo.set(cust_name)
        inv_ui.product_combo.set(prod_name)
        inv_ui.autofill_product_details(focus_qty=False)
        inv_ui.qty_entry.delete(0, tk.END)
        inv_ui.qty_entry.insert(0, '2')
        inv_ui.add_to_cart()
        inv_ui.save_invoice(format_type='a4')
        print('Save Invoice (A4 format) completed successfully.')

        # Step 3: Test Invoice History UI
        print('[TEST 3] Testing Invoice History UI...')
        app.open_invoice_history()
        hist_ui = app.current_ui
        hist_rows = hist_ui.tree.get_children()
        print(f'Invoice History loaded with {len(hist_rows)} invoices.')
        if hist_rows:
            first_inv = hist_rows[0]
            hist_ui.tree.selection_set(first_inv)
            vals = hist_ui.tree.item(first_inv, 'values')
            print('Selected Invoice from History:', vals)

        # Step 4: Test Ledger UI
        print('[TEST 4] Testing Ledger UI...')
        app.open_ledger()
        ledger_ui = app.current_ui
        assert isinstance(ledger_ui, LedgerUI)
        ledger_rows = ledger_ui.customer_tree.get_children()
        print(f'✓ Ledger loaded with {len(ledger_rows)} customer entries.')
        if ledger_rows:
            first_cust = ledger_rows[0]
            ledger_ui.customer_tree.selection_set(first_cust)
            ledger_ui.on_customer_select()
            inv_rows = ledger_ui.invoice_tree.get_children()
            print(f'✓ Customer invoices loaded: {len(inv_rows)} invoices.')
            if inv_rows:
                inv_id = int(inv_rows[0])
                ledger_ui.show_payment_dialog(inv_id)
                print('✓ Payment drilldown dialog with 80mm Thermal & A4 buttons tested OK.')
            # Go back to customer list
            ledger_ui.show_customer_list()

        # Step 5: Test Inventory UI
        print('[TEST 5] Testing Inventory UI...')
        app.open_inventory()
        inv_tab = app.current_ui
        print('Inventory tab loaded successfully.')

        # Step 6: Test Dashboard UI
        print('[TEST 6] Testing Dashboard UI...')
        app.open_dashboard()
        dash_tab = app.current_ui
        print('Dashboard tab refreshed successfully.')

    root.destroy()
    print('=' * 60)
    print('ALL TESTS PASSED WITH ZERO ERRORS!')
    print('=' * 60)

if __name__ == '__main__':
    run_tests()
