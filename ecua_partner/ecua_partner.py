# -*- coding: utf-8 -*-
from osv import osv, fields
from datetime import datetime

class partner(osv.osv):
    _inherit='res.partner'
    _name = 'res.partner'
    
    def _get_user_id(self, cr, uid, ids, context={}):
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr,uid,uid) 
        return user.id
    
    _defaults = {
         'user_id': _get_user_id,
         'date': datetime.now()
         }
    
partner()

class partner_address(osv.osv):
    _inherit='res.partner.address'
    _name = 'res.partner.address'
    
    def _get_user_location_id(self, cr, uid, ids, context={}):
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr,uid,uid)
        partner_address = user.company_id.partner_id.address

        for loc in partner_address:
            loc.location.id

        return loc.location.id
    
    _defaults = {
         'location': _get_user_location_id,
         }
    
partner_address()

class res_country(osv.osv):
    _inherit='res.country'
    _name = 'res.country'
    
    _columns = {'ec_tax_code': fields.char('Country tax code', size=3, help='The SRI country code in three chars.', ),
                'ec_double_taxation': fields.boolean('Double taxation', help='Indicates that the country has a double taxation agreement.',),
     }
    
res_country()