#-*- coding:utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2011-2012 Christopher Ormaza - Ecuadorenlinea.net
#    Copyright (C) 2013- Carlos Lopez - Ecuadorenlinea.net 
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
from dateutil import relativedelta
from osv import fields, osv
from tools import config
from tools.translate import _
import decimal_precision as dp


class hr_employee(osv.osv):
    def get_date_last_contract_continuo(self, cr, uid, employee_id, days_free, context=None):
        """
        busca todos los contratos del empleado que esten en periodo de tiempo continuo
        @param employee_id: id del empleado
        @param days_free: maximo de dias que puede haber entre el fin de un contrato y el inicio otro y que se consideran periodos continuos.
        @return: La fecha de inicio del primer contrato que este en un periodo de tiempo ininterrumpido,
        False en caso de no haber contratos para el empleado
        """
        if not context: context={}
        contract_obj=self.pool.get('hr.contract')
        contract_ids=contract_obj.search(cr,uid,[('employee_id','=',employee_id)],order="date_start")
        #si no hay contratos
        if not contract_ids:
            return False
        total=len(contract_ids)
        #si hay un solo contrato retornar la fecha de inicio de ese contrato
        if total<=1:
                return contract_obj.read(cr,uid,[contract_ids[0]],['date_start'])[0]['date_start']
        #buscar en todos los contratos en order inverso del ultimo al primero
        date_contract1=None
        date_contract2=None
        while total > 1:
            date_contract1=contract_obj.read(cr,uid,[contract_ids[total-1]],['date_start','date_end'])[0]
            date_contract2=contract_obj.read(cr,uid,[contract_ids[total-2]],['date_start','date_end'])[0]
            date_start=datetime.strptime(date_contract1['date_start'],"%Y-%m-%d")
            date_end=datetime.strptime(date_contract2['date_end'],"%Y-%m-%d")
            #si hay un contrato que no tenga fecha fin
            if date_end:
                diff=date_start - date_end
                if diff.days > days_free :
                    return date_contract1['date_start']
            total-=1
        return date_contract2['date_start']
            
                
    
    def _calculate_working_time(self,cr,uid,ids,field_name,arg,context=None):
        """
        Calcula y devuelve en dias el tiempo que el empleado tiene trabajando en la empresa
        Se consideran todos los contratos en las fechas especificadas por contexto para el calculo
        """
        if not context: context={}
        res={}
        contratos_obj=self.pool.get('hr.contract')
        for employee in self.browse(cr,uid,ids,context):
            contratos_ids=[]
            total_time=0
            #si se especifican fecha se toman los contratos en esas fechas
            if context.has_key('date_from') and context.has_key('date_end'):
                contratos_ids=self.get_contract(cr, uid, employee.id, context.get('date_from'), context.get('date_end'), context)
            else:
                #tomar todos los contratos del empleado del ultimo periodo continuo
                date_start=self.get_date_last_contract_continuo(cr, uid, employee.id, 7, context)
                if date_start:
                    contratos_ids=contratos_obj.search(cr,uid,[('employee_id','=',employee.id),('date_start','>=',date_start)])
            for contrato in contratos_obj.browse(cr,uid,contratos_ids,context):
                total_time+=contrato.duration_contract
            res[employee.id]=total_time
        return res
    
    def get_contract(self, cr, uid, employee_id, date_from, date_to, context=None):
        """
        @param employee: id of employee
        @param date_from: date field
        @param date_to: date field
        @return: returns the ids of all the contracts for the given employee that need to be considered for the given dates
        """
        contract_obj = self.pool.get('hr.contract')
        clause = []
        #a contract is valid if it ends between the given dates
        clause_1 = ['&',('date_end', '<=', date_to),('date_end','>=', date_from)]
        #OR if it starts between the given dates
        clause_2 = ['&',('date_start', '<=', date_to),('date_start','>=', date_from)]
        #OR if it starts before the date_from and finish after the date_end (or never finish)
        clause_3 = [('date_start','<=', date_from),'|',('date_end', '=', False),('date_end','>=', date_to)]
        clause_final =  [('employee_id', '=', employee_id),'|','|'] + clause_1 + clause_2 + clause_3
        contract_ids = contract_obj.search(cr, uid, clause_final, context=context)
        return contract_ids
    
    
    def _current_employee_age(self,cr,uid,ids,field_name,arg,context):
        res = {}
        today = datetime.today()
        dob = today
        for employee in self.browse(cr, uid, ids):            
            if employee.birthday:
                dob = datetime.strptime(employee.birthday,'%Y-%m-%d')
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

    def _calculate_total_wage(self, cr, uid, ids, name, args, context):
        if not ids: return {}
        res = {}
        current_date = datetime.now().strftime('%Y-%m-%d')
        for employee in self.browse(cr, uid, ids, context=context):
            if not employee.contract_ids:
                res[employee.id] = {'basic': 0.0}
                continue
            cr.execute( 'SELECT SUM(wage) '\
                        'FROM hr_contract '\
                        'WHERE employee_id = %s '\
                        'AND date_start <= %s '\
                        'AND (date_end > %s OR date_end is NULL)',
                         (employee.id, current_date, current_date))
            result = dict(cr.dictfetchone())
            res[employee.id] = {'basic': result['sum']}
        return res

    
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
        'contract_id':fields.function(_get_latest_contract, string='Contract',method=True, type='many2one', relation="hr.contract", help='Latest contract of the employee'),
        'remaining_leaves': fields.function(_get_remaining_days, method=True, string='Remaining Legal Leaves', fnct_inv=_set_remaining_days, type="float", help='Total number of legal leaves allocated to this employee, change this value to create allocation/leave requests.', store=True),
        'account_debit': fields.many2one('account.account', 'Debit Account', domain=[('type','=','receivable')]),
        'account_credit': fields.many2one('account.account', 'Credit Account', domain=[('type','=','payable')]),
        'partner_id': fields.many2one('res.partner', 'Partner', ondelete="restrict"),
        'slip_ids':fields.one2many('hr.payslip', 'employee_id', 'Payslips', required=False, readonly=True),
        'total_wage': fields.function(_calculate_total_wage, method=True, type='float', string='Total Basic Salary', digits_compute=dp.get_precision('Payroll'), help="Sum of all current contract's wage of employee."),
        'working_time': fields.function(_calculate_working_time, method=True, type='float', string='Tiempo de trabajo', ),
#        'days_vacation': fields.function(_calculate_days_vacation, method=True, type='float', string='Dias de Vacaciones'),   
        }
    
    def _get_account_debit(self, cr, uid, context=None):
        if not context:
            context={}
        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        company = self.pool.get('res.company').browse(cr, uid, user.company_id.id, context)
        return company.default_account_debit_id.id or None

    def _get_account_credit(self, cr, uid, context=None):
        if not context:
            context={}
        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        company = self.pool.get('res.company').browse(cr, uid, user.company_id.id, context)
        return company.default_account_credit_id.id or None
    
    _defaults = {  
        'account_debit': _get_account_debit,  
        'account_credit': _get_account_credit,  
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
                          'customer':True,
                          'supplier':True,
                          'employee':True,
                          'property_account_receivable' : values.get('account_debit',None),
                          'property_account_payable' : values.get('account_credit',None),
                          }
        if values.get('user_id', False) != 1:
            partner_ids = partner_obj.search(cr, uid, [('ref','=', values.get('identification_id',False))])
            if partner_ids:
                partner_id = partner_ids[0]
                partner_obj.write(cr, uid, [partner_id], {
                                                          'customer':True,
                                                          'supplier':True,
                                                          'employee':True,
                                                          'property_account_receivable' : values.get('account_debit',None),
                                                          'property_account_payable' : values.get('account_credit',None),
                                                          })
                
            else:
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
    
    
    
    _constraints = [(_check_ced, _('Validation Error: Invalid Identification No'), ['identification_id']),
                    (_check_employee_account, _('Payable Account of Partner must be same employee_account!'), ['account_debit','account_credit']), 
                    ]
    
    _sql_constraints = [('identification_uniq', 'unique (identification_id,company_id)', _('The identification number must be unique !')),]
    
hr_employee()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: