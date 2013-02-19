# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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
from tools.translate import _
from osv import fields, osv
from datetime import datetime
class hr_contract_type(osv.osv):
    _name = 'hr.contract.type'
    _description = 'Contract Type'
    _columns = {
        'name': fields.char('Contract Type', size=32, required=True),
    }
hr_contract_type()

class hr_contract(osv.osv):
    def _calculate_duration_contract(self,cr,uid,ids,field_name,arg,context=None):
        """
        Calcula y devuelve en dias la duracion del contrato, restando la fecha de inicio y la fecha final.
        En caso de no haber fecha final en el contrato se toma la fecha actual del sistema y de esta manera se actualiza dinamicamente
        """
        if not context: context={}
        res={}
        #se suma un dia al resultado porque las fechas son excluidas del calculo
        for contrato in self.browse(cr,uid,ids):
            if contrato.date_end:
                date_start=datetime.strptime(contrato.date_start, '%Y-%m-%d')
                date_end=datetime.strptime(contrato.date_end, '%Y-%m-%d')
                duracion_contrato=date_end -date_start
                res[contrato.id]=duracion_contrato.days + 1
            else:
                date_start=datetime.strptime(contrato.date_start, '%Y-%m-%d')
                date_end=datetime.now()
                duracion_contrato=date_end -date_start
                res[contrato.id]=duracion_contrato.days + 1
        return res
    
    def _calculate_salary(self, cr, uid, ids, field_names, arg, context=None):
        return {}
    
    def compute_basic(self, cr, uid, ids, context=None):
        return {}

    _inherit = 'hr.contract'
    _description = 'Contract'
    _columns = {
        'name': fields.char('Contract Reference', size=32, required=True),
        'employee_id': fields.many2one('hr.employee', "Employee", required=True),
        'department_id': fields.related('employee_id', 'department_id', type='many2one', relation='hr.department', string="Department", readonly=True),
        'type_id': fields.many2one('hr.contract.type', "Contract Type", required=True),
        'job_id': fields.many2one('hr.job', 'Job Title'),
        'date_start': fields.date('Start Date', required=True),
        'date_end': fields.date('End Date'),
        'trial_date_start': fields.date('Trial Start Date'),
        'trial_date_end': fields.date('Trial End Date'),
        'working_hours': fields.many2one('resource.calendar', 'Working Schedule'),
        'wage': fields.float('Wage', digits=(16, 2), required=True, help="Basic Salary of the employee"),
        'advantages': fields.text('Advantages'),
        'notes': fields.text('Notes'),
        'permit_no': fields.char('Work Permit No', size=256, required=False, readonly=False),
        'visa_no': fields.char('Visa No', size=64, required=False, readonly=False),
        'visa_expire': fields.date('Visa Expire Date'),
        #reescritura de campos de antiguo modulo
        'wage_type_id': fields.many2one('hr.contract.wage.type', 'Wage Type', required=False),
        'basic': fields.function(_calculate_salary, method=True, store=True, multi='dc', type='float', string='Basic Salary', digits=(14, 2)),
        'gross': fields.function(_calculate_salary, method=True, store=True, multi='dc', type='float', string='Gross Salary', digits=(14, 2)),
        'net': fields.function(_calculate_salary, method=True, store=True, multi='dc', type='float', string='Net Salary', digits=(14, 2)),
        'advantages_net': fields.function(_calculate_salary, method=True, store=True, multi='dc', type='float', string='Deductions', digits=(14, 2)),
        'advantages_gross': fields.function(_calculate_salary, method=True, store=True, multi='dc', type='float', string='Allowances', digits=(14, 2)),
        'analytic_account_id':fields.many2one('account.analytic.account', 'Analytic Account'),
        'journal_id': fields.many2one('account.journal', 'Salary Journal'),
        'struct_id': fields.many2one('hr.payroll.structure', 'Salary Structure'),
        'schedule_pay': fields.selection([
            ('monthly', 'Monthly'),
#            ('quarterly', 'Quarterly'),
#            ('semi-annually', 'Semi-annually'),
#            ('annually', 'Annually'),
#            ('weekly', 'Weekly'),
#            ('bi-weekly', 'Bi-weekly'),
#            ('bi-monthly', 'Bi-monthly'),
            ],'Scheduled Pay', select=True),
        'method_payment':fields.selection([
                ('payment_employee', 'Pago al Empleado'),
                ('accumulated', 'Acumulado'),
                ], 'Forma de Pago-Fondos de Reserva', select=True),
        'duration_contract': fields.function(_calculate_duration_contract, method=True, type='float', string='Duración del contrato en dias'),
        }
    
    
    def _get_journal(self, cr, uid, context=None):
        if not context:
            context = {}
        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        company = self.pool.get('res.company').browse(cr, uid, user.company_id.id, context)
        return company.default_salary_journal_id.id or None

    def _get_struct(self, cr, uid, context=None):
        if not context:
            context = {}
        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        company = self.pool.get('res.company').browse(cr, uid, user.company_id.id, context)
        return company.default_struct_id.id or None

    def _get_working_hours(self, cr, uid, context=None):
        if not context:
            context = {}
        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        company = self.pool.get('res.company').browse(cr, uid, user.company_id.id, context)
        return company.default_working_hours_id.id or None

    
    def get_all_structures(self, cr, uid, contract_ids, context=None):
        """
        @param contract_ids: list of contracts
        @return: the structures linked to the given contracts, ordered by hierachy (parent=False first, then first level children and so on) and without duplicata
        """
        all_structures = []
        structure_ids = [contract.struct_id.id for contract in self.browse(cr, uid, contract_ids, context=context)]
        return list(set(self.pool.get('hr.payroll.structure')._get_parent_structure(cr, uid, structure_ids, context=context)))

    def _get_type(self, cr, uid, context=None):
        type_ids = self.pool.get('hr.contract.type').search(cr, uid, [('name', '=', 'Employee')])
        return type_ids and type_ids[0] or False

    _defaults = {
        'date_start': lambda *a: time.strftime("%Y-%m-%d"),
        'type_id': _get_type,
        'working_hours':_get_working_hours,
        'journal_id':_get_journal,
        'struct_id':_get_struct,
    }

    def _check_dates(self, cr, uid, ids, context=None):
        for contract in self.read(cr, uid, ids, ['date_start', 'date_end'], context=context):
             if contract['date_start'] and contract['date_end'] and contract['date_start'] > contract['date_end']:
                 return False
        return True

    _constraints = [
        (_check_dates, _('Error! contract start-date must be lower then contract end-date.'), ['date_start', 'date_end'])
    ]
hr_contract()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
