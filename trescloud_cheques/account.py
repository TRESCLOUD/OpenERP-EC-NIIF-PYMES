from osv import osv, fields

class account_journal(osv.osv):
    """
        Add fields Allow Check writing, Use Preprinted Check and Check Sequence on journal
    """
    _inherit = "account.journal"
    _columns = {
        'allow_check_writing': fields.boolean('Allow Check writing', help='Fill this if the journal is to be used for writing checks.'),
        'use_preprint_check': fields.boolean('Use Preprinted Check'),
        'check_sequence': fields.many2one('ir.sequence', 'Check Sequence', 
                                          help="This field contains the information related to the numbering of the check number."),
        }

account_journal()

#class check_log(osv.osv):
#    """
#        Check Log model
#    """
#    _name = 'check.log'
#    _description = 'Check Log'
#    _columns = {
#        'name': fields.many2one('account.voucher', 'Reference payment'),
#        'status': fields.selection([('active', 'Active'), ('voided', 'Voided'), ('stop_pay', 'Stop Pay Placed'), ('lost', 'Lost'), ('unk', 'Unknown')],
#                                    "Check Status"),
#        'check_no': fields.char('Check Number', size=64),
#        'cleared': fields.boolean('Cleared', help="Check this if the check is cleared (aka Paid) by the Bank")
#        }
#    
#    _defaults = {
#        'status': 'blank',
#        }
#check_log()
#
#
#class account_invoice(osv.osv):
#    """Update inv_reference field.
#    This field will update only if the stock_assigned_picker module is installed."""
#    _inherit = "account.invoice"
#
#    def _calc_inv_ref(self, cr, uid, ids, name, args, context=None):
#        """
#        @param cr: current row of the database
#        @param uid: id of user currently logged
#        @param ids: ids of selected records
#        @param name: 
#        @param args: 
#        @param context: context
#        @return: 
#        """
#        res = {}
#        picking_obj = self.pool.get('stock.picking')
#        for inv in self.browse(cr, uid, ids, context=context):
#            cr.execute("SELECT purchase_id FROM purchase_invoice_rel WHERE invoice_id = %s", (inv.id,))
#            pur_ids = cr.fetchall() or None
#            if pur_ids and pur_ids[0]:
#                pick_ids = picking_obj.search(cr, uid, [('purchase_id', '=', pur_ids[0][0])], context=context)
#                if pick_ids:
#                    pici_id = picking_obj.browse(cr, uid, pick_ids[0], context=context)
#                    if hasattr(pici_id, 'ref_inv_no'):
#                        res[inv.id] = pici_id.ref_inv_no
#        return res
#    
#    def _get_invoice_pur(self, cr, uid, ids, context=None):
#        """
#        @param cr: current row of database
#        @param uid: id of user currently logged in
#        @param ids: ids of selected records
#        @param context: context
#        @return: list of ids
#        """
#        result = {}
#        for purchase_id in self.pool.get('purchase.order').browse(cr, uid, ids, context=context):
#            for invoice_id in purchase_id.invoice_ids:
#                result[invoice_id.id] = True
#        return result.keys() 
#    
#    def _get_invoice_pick(self, cr, uid, ids, context=None):
#        """
#        @param cr: current row of database
#        @param uid: id of user currently logged in
#        @param ids: ids of selected records
#        @param context: context
#        @return: list of ids
#        """
#        result = {}
#        for pick in self.pool.get('stock.picking').browse(cr, uid, ids, context=context):
#            if pick.purchase_id:
#                for invoice_id in pick.purchase_id.invoice_ids:
#                    result[invoice_id.id] = True
#        return result.keys()
#
#    _columns = {
#        'inv_ref': fields.function(_calc_inv_ref, method=True, string='Reference Invoice', type='char', size=32,
#            store = {
#                'account.invoice': (lambda self, cr, uid, ids, c={}: ids, ['state'], 10),
#                'purchase.order': (_get_invoice_pur, ['order_line'], 10),
#                'stock.picking': (_get_invoice_pick, ['ref_inv_no', 'purchase_id'], 10),
#                }, multi=False),
#        }
#    
#account_invoice()
#
## vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
