# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 Ecuadorenlinea.net.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
import datetime
from dateutil.relativedelta import relativedelta
from os.path import join as opj
from operator import itemgetter

from tools.translate import _
from osv import fields, osv
import netsvc
import tools

class ecua_company_installer(osv.osv_memory):
    _name = 'ecua.company.installer'
    _inherit = 'res.config.installer'
    _columns={'name':fields.char('CEDULA/RUC', size=13, required=True),
              'company_id':fields.many2one('res.company', 'Company', readonly=True, required=True), 
             }
    
    def check_ref(self,cr,uid,ids):
        for data in self.browse(cr, uid, ids):
            ref = data.name
            if len(ref)==13:
                return True
            else:
                return False
    
    def _default_company(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        return user.company_id and user.company_id.id or False

    def execute(self, cr, uid, ids, context=None):
        partner_obj = self.pool.get('res.partner')
        for data in self.browse(cr, uid, ids, context=context):
            partner_ids=partner_obj.search(cr, uid, [('id','=',data.company_id.partner_id['id'])])
            vals_partner = {'ref':data['name'],
                             }
            partner_obj.write (cr, uid, partner_ids ,vals_partner, context=context)
            
    _defaults={'company_id':_default_company,
               }
    _constraints = [(check_ref,'The number of RUC is incorrect',['name'])]
ecua_company_installer()
