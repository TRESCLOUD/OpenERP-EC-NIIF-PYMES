from osv import osv
from osv import fields
import decimal_precision as dp
from tools.translate import _

class res_partner(osv.osv):

    _inherit = 'res.partner'

    _columns = {
            'beneficiary':fields.char('Beneficiary', size=255, required=False),
        }
res_partner()