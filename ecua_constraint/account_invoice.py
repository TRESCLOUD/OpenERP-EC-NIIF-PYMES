from osv import osv
from osv import fields
from tools.translate import _
import time
import psycopg2
import re
from lxml import etree
import decimal_precision as dp

class account_invoice(osv.osv):

    _inherit = "account.invoice"
    
    _sql_constraints = [
                        ('invoice_number_out_not_uniq','unique(invoice_number_out)', _("There's another credit note with this number!")),
                                                
                        ]
account_invoice()