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


class hr_employee(osv.osv):

    def _current_employee_age(self,cr,uid,ids,field_name,arg,context):
        res = {}
        today = datetime.date.today()
        dob = today
        for employee in self.browse(cr, uid, ids):            
            if employee.birthday:
                dob = DateTime.strptime(employee.birthday,'%Y-%m-%d')            
            res[employee.id] = today.year - dob.year
        return res

    def _get_latest_contract(self, cr, uid, ids, field_name, args, context=None):
        res = {}
        obj_contract = self.pool.get('hr.contract')
        for emp in self.browse(cr, uid, ids, context=context):
            contract_ids = obj_contract.search(cr, uid, [('employee_id','=',emp.id),], order='date_start', context=context)
            if contract_ids:
                res[emp.id] = contract_ids[-1:][0]
            else:
                res[emp.id] = False
        return res
    
    def _set_remaining_days(self, cr, uid, empl_id, name, value, arg, context=None):
        employee = self.browse(cr, uid, empl_id, context=context)
        diff = value - employee.remaining_leaves
        type_obj = self.pool.get('hr.holidays.status')
        holiday_obj = self.pool.get('hr.holidays')
        # Find for holidays status
        status_ids = type_obj.search(cr, uid, [('limit', '=', False)], context=context)
        if len(status_ids) != 1 :
            raise osv.except_osv(_('Warning !'),_("To use this feature, you must have only one leave type without the option 'Allow to Override Limit' set. (%s Found).") % (len(status_ids)))
        status_id = status_ids and status_ids[0] or False
        if not status_id:
            return False
        if diff > 0:
            leave_id = holiday_obj.create(cr, uid, {'name': _('Allocation for %s') % employee.name, 'employee_id': employee.id, 'holiday_status_id': status_id, 'type': 'add', 'holiday_type': 'employee', 'number_of_days_temp': diff}, context=context)
        elif diff < 0:
            leave_id = holiday_obj.create(cr, uid, {'name': _('Leave Request for %s') % employee.name, 'employee_id': employee.id, 'holiday_status_id': status_id, 'type': 'remove', 'holiday_type': 'employee', 'number_of_days_temp': abs(diff)}, context=context)
        else:
            return False
        holiday_obj.holidays_confirm(cr, uid, [leave_id])
        holiday_obj.holidays_validate2(cr, uid, [leave_id])
        return True

    def _get_remaining_days(self, cr, uid, ids, name, args, context=None):
        cr.execute("SELECT sum(h.number_of_days_temp) as days, h.employee_id from hr_holidays h join hr_holidays_status s on (s.id=h.holiday_status_id) where h.type='add' and h.state='validate' and s.limit=False group by h.employee_id")
        res = cr.dictfetchall()
        remaining = {}
        for r in res:
            remaining[r['employee_id']] = r['days']
        for employee_id in ids:
            if not remaining.get(employee_id):
                remaining[employee_id] = 0.0
        return remaining

    _inherit = 'hr.employee'

    _columns = {
        'identification_id':fields.char('Identification No', size=10,),
        #Es necesario que se asigne una cuenta de tipo payable a la cuenta del empleado
        #para la generacion correcta de los asientos
        'employee_account':fields.property(
                            'account.account',
                            type='many2one',
                            relation='account.account',
                            string="Employee Account",
                            method=True,
                            domain="[('type', '=', 'payable')]",
                            view_load=True,
                            help="Employee Payable Account"),
        'child_ids':fields.one2many('hr.family.burden', 'employee_id', 'Childrens', ),
        'wife_id':fields.many2one('hr.family.burden', 'Wife / Husband', ),
        'education_ids':fields.one2many('hr.education.level', 'employee_id', 'Childrens', ),
        'extra_input_output_ids':fields.one2many('hr.extra.input.output', 'employee_id', 'Extra Payments/Deductions', ),
        'second_name':fields.char('Second Name', size=255,), 
        'last_name':fields.char('Last Name', size=255,), 
        'mother_last_name':fields.char('Mother Last Name', size=255,),
        'age' : fields.function(_current_employee_age,method=True,string='Age',type='integer',store=True),
        'manager': fields.boolean('Is a Manager'),
        'medic_exam': fields.date('Medical Examination Date'),
        'place_of_birth': fields.char('Place of Birth', size=30),
        'children': fields.integer('Number of Children'),
        'vehicle': fields.char('Company Vehicle', size=64),
        'vehicle_distance': fields.integer('Home-Work Distance', help="In kilometers"),
        'contract_ids': fields.one2many('hr.contract', 'employee_id', 'Contracts'),
        'contract_id':fields.function(_get_latest_contract, string='Contract', type='many2one', relation="hr.contract", help='Latest contract of the employee'),
        'remaining_leaves': fields.function(_get_remaining_days, method=True, string='Remaining Legal Leaves', fnct_inv=_set_remaining_days, type="float", help='Total number of legal leaves allocated to this employee, change this value to create allocation/leave requests.', store=True),
        'account_debit': fields.many2one('account.account', 'Debit Account', domain=[('type','=','receivable')]),
        'account_credit': fields.many2one('account.account', 'Credit Account', domain=[('type','=','payable')]),
        'partner_id': fields.many2one('res.partner', 'Partner', readonly=True),
        }
    
 #   def _get_account_debit(self, cr, uid, context=None):
 #       if not context:
 #           context={}
 #       user = self.pool.get('res.users').browse(cr, uid, uid, context)
 #       company = self.pool.get('res.company').browse(cr, uid, user.company_id.id, context)
 #       return company.default_account_debit_id.id or None

  #  def _get_account_credit(self, cr, uid, context=None):
  #      if not context:
  #          context={}
   #     user = self.pool.get('res.users').browse(cr, uid, uid, context)
 #       company = self.pool.get('res.company').browse(cr, uid, user.company_id.id, context)
  #      return company.default_account_credit_id.id or None
    
    _defaults = {  
   #     'account_debit': _get_account_debit,  
   #     'account_credit': _get_account_credit,  
        }

    def check_ced(self, ced):
        try:
            valores = [ int(ced[x]) * (2 - x % 2) for x in range(9) ]
            suma = sum(map(lambda x: x > 9 and x - 9 or x, valores))
            veri = 10 - (suma - (10*(suma/10)))
            if int(ced[9]) == int(str(veri)[-1:]):
                return True
            else:
                return False
        except:
            return False

    def _check_ced(self, cr, uid, ids):
        val = True 
        for employee in self.pool.get('hr.employee').browse(cr, uid, ids, None):
            if employee.identification_id:
                val = self.check_ced(employee.identification_id)
        return val
    
    def _check_employee_account(self, cr, uid, ids):
        #TODO: Debe validarse que la cuenta por pagar del partner
        #debe ser igual que la cuenta employee account, o podria
        #ser un onchange que asigne automaticamente el mismo campo
        return True

    def name_get(self,cr,uid,ids, context=None):
        res = []
        for r in self.read(cr,uid,ids,['name','second_name','last_name','mother_last_name'], context):
            name = r['name']
            if r['second_name']:
                name = name + " " +r['second_name'] 
            if r['last_name']:
                name = name + " " +r['last_name'] 
            if r['mother_last_name']:
                name = name + " " +r['mother_last_name'] 
            res.append((r['id'], name))
        return res

    def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        args = args[:]
        ids = []
        if name:
            ids = self.search(cr, user, [('identification_id', operator, name+"%")]+args, limit=limit)
            if not ids:
                ids = self.search(cr, user, [('name', operator, name+"%")]+args, limit=limit)
            if not ids:
                ids = self.search(cr, user, [('second_name', operator, name+"%")]+args, limit=limit)
            if not ids:
                ids = self.search(cr, user, [('last_name', operator, name+"%")]+args, limit=limit)
            if not ids:
                ids = self.search(cr, user, [('mother_last_name', operator, name+"%")]+args, limit=limit)
            if not ids:
                ids = self.search(cr, user, [('name', operator, name)]+ args, limit=limit)
            if not ids and len(name.split()) >= 2:
                #Separating code and name of account for searching
                operand1,operand2 = name.split(' ',1) #name can contain spaces e.g. OpenERP S.A.
                ids = self.search(cr, user, [('code', operator, operand1), ('name', operator, operand2)]+ args, limit=limit)
        else:
            ids = self.search(cr, user, args, context=context, limit=limit)
        return self.name_get(cr, user, ids, context=context)        
    
    def create(self, cr, uid, values, context=None):
        if context == None:
            context = {}
        partner_obj = self.pool.get('res.partner')
        employee_obj = self.pool.get('hr.employee')
        account_debit_id = None
        account_credit_id = None
        values_partner = {}
        name = values['name']
        if values.get('second_name', False):
            name = name + " " + values['second_name'] 
        if values.get('last_name', False):
            name = name + " " + values['last_name'] 
        if values.get('mother_last_name', False):
            name = name + " " + values['mother_last_name']
        values_partner = {
                          'name': name,
                          'ref': values.get('identification_id',False),
                          'customer':False,
                          'supplier':True,
                          'employee':True,
                          }
        if values.get('account_debit', False):
            account_debit_id = values['account_debit']
            values_partner['property_account_receivable']=account_debit_id
        if values.get('account_credit', False):
            account_credit_id = values['account_credit']
            values_partner['property_account_payable']=account_credit_id
        if values.get('user_id', False) != 1:
            partner_id = partner_obj.create(cr, uid, values_partner, context)
            values['partner_id'] = partner_id
        return super(hr_employee, self).create(cr, uid, values, context)
    
    def write(self, cr, uid, ids, values, context=None):
        employee_obj = self.pool.get('hr.employee')
        account_debit = None
        account_credit = None
        account_debit_n = values.get('account_debit', False)
        account_credit_n = values.get('account_credit', False)       
        for emp in employee_obj.browse(cr, uid, ids, context):
            account_debit = emp.account_debit
            account_credit = emp.account_credit
        if account_debit != account_debit_n:
            if account_debit_n:
                values['account_debit'] = account_debit_n
        if account_credit != account_credit_n:
            if account_credit_n:
                values['account_credit'] = account_credit_n
        return super(hr_employee, self).write(cr, uid, ids, values, context)
    
    
    
    _constraints = [(_check_ced, 'Validation Error: Invalid Identification No', ['identification_id']),
                    (_check_employee_account, 'Payable Account of Partner must be same employee_account!', ['employee_account']), 
                    ]
    
    _sql_constraints = [('identification_uniq', 'unique (identification_id)', _('The identification number must be unique !')),      ]
    
hr_employee()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: