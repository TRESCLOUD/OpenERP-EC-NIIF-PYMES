#-*- coding:utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2011-2012 Christopher Ormaza - Ecuadorenlinea.net 
#    (<http://www.ecuadorenlinea.net>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
import netsvc
from datetime import date, datetime, timedelta

from mx import DateTime
import datetime

from osv import fields, osv
from tools import config
from tools.translate import _

class hr_family_burden(osv.osv):
    
    def _current_age(self,cr,uid,ids,field_name,arg,context):
        res = {}
        today = datetime.date.today()
        dob = today
        for family_burden in self.browse(cr, uid, ids):            
            if family_burden.birth_date:
                dob = DateTime.strptime(family_burden.birth_date,'%Y-%m-%d')            
            res[family_burden.id] = today.year - dob.year
        return res

    _name = 'hr.family.burden' 
    _columns = {    
                    'employee_id':fields.many2one('hr.employee', 'Employee', required=False), 
                    'name':fields.char('Name', size=255, required=True,),
                    'last_name':fields.char('Last Name', size=200, required=True,),
                    'birth_date': fields.date('Birth Date'),
                    'relationship':fields.selection([
                        ('child', 'Child'),
                        ('wife_husband', 'Wife/Husband'),
                        ], 'Relationship', select=True,),
                    'age' : fields.function(_current_age,method=True,string='Age',type='integer',store=True),
                    }

    def name_get(self,cr,uid,ids, context=None):
        res = []
        for r in self.read(cr , uid, ids, ['name','last_name'], context):
            name = r['name']
            if r['last_name']:
                name = name + " " +r['last_name'] 
            res.append((r['id'], name))
        return res
    
hr_family_burden()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: