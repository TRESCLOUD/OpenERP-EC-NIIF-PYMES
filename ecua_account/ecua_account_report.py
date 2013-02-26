from osv import osv,fields


class report_account_receivable(osv.osv):
    _inherit = "report.account.receivable"
    
    def _ecua_init(self, cr):
        tools.drop_view_if_exists(cr, 'report_account_type_sales')
        
    return super(report.account.receivable, self).__init__(pool, cr)

report_account_receivable()