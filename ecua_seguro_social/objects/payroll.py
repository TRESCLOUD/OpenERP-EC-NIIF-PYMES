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
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta

import netsvc
from osv import fields, osv
import tools
from tools.translate import _
import decimal_precision as dp

from tools.safe_eval import safe_eval as eval

class hr_payroll_structure(osv.osv):
    """
    Salary structure used to defined
    - Basic
    - Allowances
    - Deductions
    """

    _inherit = 'hr.payroll.structure'
    _description = 'Salary Structure'
    _columns = {
        'name':fields.char('Name', size=256, required=True),
        'code':fields.char('Reference', size=64, required=True),
        'company_id':fields.many2one('res.company', 'Company', required=True),
        'note': fields.text('Description'),
        'parent_id':fields.many2one('hr.payroll.structure', 'Parent'),
        'line_ids':fields.char('Salary Structure', size=256),
    }

    def _get_parent(self, cr, uid, context=None):
        obj_model = self.pool.get('ir.model.data')
        res = False
        data_id = obj_model.search(cr, uid, [('model', '=', 'hr.payroll.structure'), ('name', '=', 'structure_base')])
        if data_id:
            res = obj_model.browse(cr, uid, data_id[0], context=context).res_id
        return res

    _defaults = {
        'company_id': lambda self, cr, uid, context: \
                self.pool.get('res.users').browse(cr, uid, uid,
                    context=context).company_id.id,
        'parent_id': _get_parent,
    }

    def copy(self, cr, uid, id, default=None, context=None):
        """
        Create a new record in hr_payroll_structure model from existing one
        @param cr: cursor to database
        @param user: id of current user
        @param id: list of record ids on which copy method executes
        @param default: dict type contains the values to be override during copy of object
        @param context: context arguments, like lang, time zone

        @return: returns a id of newly created record
        """
        if not default:
            default = {}
        default.update({
            'code': self.browse(cr, uid, id, context=context).code + "(copy)",
            'company_id': self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        })
        return super(hr_payroll_structure, self).copy(cr, uid, id, default, context=context)

    def get_all_rules(self, cr, uid, structure_ids, context=None):
        """
        @param structure_ids: list of structure
        @return: returns a list of tuple (id, sequence) of rules that are maybe to apply
        """

        all_rules = []
        for struct in self.browse(cr, uid, structure_ids, context=context):
            all_rules += self.pool.get('hr.salary.rule')._recursive_search_of_rules(cr, uid, struct.rule_ids, context=context)
        return all_rules

    def _get_parent_structure(self, cr, uid, struct_ids, context=None):
        if not struct_ids:
            return []
        parent = []
        for struct in self.browse(cr, uid, struct_ids, context=context):
            if struct.parent_id:
                parent.append(struct.parent_id.id)
        if parent:
            parent = self._get_parent_structure(cr, uid, parent, context)
        return parent + struct_ids

hr_payroll_structure()


class contrib_register(osv.osv):
    '''
    Contribution Register
    '''

    _name = 'hr.contribution.register'
    _description = 'Contribution Register'

    _columns = {
        'company_id':fields.many2one('res.company', 'Company', required=False),
        'name':fields.char('Name', size=256, required=True, readonly=False),
        'register_line_ids':fields.one2many('hr.payslip.line2', 'register_id', 'Register Line', readonly=True),
        'note': fields.text('Description'),
    }
    _defaults = {
        'company_id': lambda self, cr, uid, context: \
                self.pool.get('res.users').browse(cr, uid, uid,
                    context=context).company_id.id,
    }

contrib_register()

class hr_salary_rule_category(osv.osv):
    """
    HR Salary Rule Category
    """

    _name = 'hr.salary.rule.category'
    _description = 'Salary Rule Category'
    _columns = {
        'name':fields.char('Name', size=64, required=True, readonly=False),
        'code':fields.char('Code', size=64, required=True, readonly=False),
        'parent_id':fields.many2one('hr.salary.rule.category', 'Parent', help="Linking a salary category to its parent is used only for the reporting purpose."),
        'note': fields.text('Description'),
        'company_id':fields.many2one('res.company', 'Company', required=False),
        'type':fields.selection([
            ('input','Input'),
            ('output','Output'),
            ('other','Other'),
             ],'Type', select=True,),
    }

    _defaults = {
        'company_id': lambda self, cr, uid, context: \
                self.pool.get('res.users').browse(cr, uid, uid,
                    context=context).company_id.id,
    }

hr_salary_rule_category()

class one2many_mod2(fields.one2many):

    def get(self, cr, obj, ids, name, user=None, offset=0, context=None, values=None):
        if context is None:
            context = {}
        if not values:
            values = {}
        res = {}
        for id in ids:
            res[id] = []
        ids2 = obj.pool.get(self._obj).search(cr, user, [(self._fields_id,'in',ids), ('appears_on_payslip', '=', True)], limit=self._limit)
        for r in obj.pool.get(self._obj)._read_flat(cr, user, ids2, [self._fields_id], context=context, load='_classic_write'):
            res[r[self._fields_id]].append( r['id'] )
        return res

class hr_payslip_run(osv.osv):

    _name = 'hr.payslip.run'
    _columns = {
        'name': fields.char('Name', size=64, required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'slip_ids': fields.one2many('hr.payslip', 'payslip_run_id', 'Payslips', required=False, readonly=True, states={'draft': [('readonly', False)]}),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('open', 'Open'),
            ('close', 'Close'),
        ], 'State', select=True, readonly=True),
        'date_start': fields.date('Date From', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'date_end': fields.date('Date To', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'credit_note': fields.boolean('Credit Note', readonly=True, states={'draft': [('readonly', False)]}, help="If its checked, indicates that all payslips generated from here are refund payslips."),
        'bank_statement_id':fields.many2one('account.bank.statement', 'Bank Statement', required=False),
    }
    _defaults = {
        'state': 'draft',
        'date_start': lambda *a: time.strftime('%Y-%m-01'),
        'date_end': lambda *a: str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
    }

    def draft_payslip_run(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'draft'}, context=context)

    def close_payslip_run(self, cr, uid, ids, context=None):
        payslip_run_obj = self.pool.get('hr.payslip.run')
        wf_service = netsvc.LocalService("workflow")
        for run in payslip_run_obj.browse(cr, uid, ids, context):
            for payslip in run.slip_ids:
                if payslip.state == 'draft' or payslip.state == 'verify':
                    wf_service.trg_validate(uid, 'hr.payslip', payslip.id, 'hr_verify_sheet', cr)
        return self.write(cr, uid, ids, {'state': 'close'}, context=context)

hr_payslip_run()

class hr_payslip(osv.osv):
    '''
    Pay Slip
    '''

    _inherit = 'hr.payslip'
    _description = 'Pay Slip'

    def _calculate(self, cr, uid, ids, field_names, arg, context=None):
        res={}
        for rs in self.browse(cr, uid, ids, context=context):
            inputs_ids = None
            outputs_ids = None
            other_inputs_ids = None
            company_contributions = None
            outputs= 0.0
            inputs= 0.0
            total_inputs= 0.0
            other_inputs= 0.0
            company_contributions= 0.0
            payslip_net= 0.0
            
            for line in rs.line_ids:
                if line.salary_rule_id:
                    #Se calcula todos los ingresos que recibe el empleado directo a su rol de pagos
                    if line.salary_rule_id.category_id.type == 'input' and not line.salary_rule_id.pay_to_other:
                        total_inputs += line.total
                    elif line.salary_rule_id.category_id.type == 'output':
                        outputs += line.total
                    if line.salary_rule_id.category_id.code == "INGR":
                        inputs += line.total
                    elif line.salary_rule_id.category_id.code == "OINGR":
                        other_inputs += line.total
                    elif line.salary_rule_id.category_id.code == "CONT" or line.salary_rule_id.company_contribution:
                        company_contributions += line.total
                elif line.extra_i_o_id:
                    #Se calcula todos los ingresos que recibe el empleado directo a su rol de pagos
                    if line.extra_i_o_id.category_id.type == 'input' and not line.extra_i_o_id.pay_to_other:
                        total_inputs += line.total
                    elif line.extra_i_o_id.category_id.type == 'output':
                        outputs += line.total
                    if line.extra_i_o_id.category_id.code == "INGR":
                        inputs += line.total
                    elif line.extra_i_o_id.category_id.code == "OINGR":
                        other_inputs += line.total
                    elif line.extra_i_o_id.category_id.code == "CONT" or line.extra_i_o_id.company_contribution:
                        company_contributions += line.total
                payslip_net = inputs + other_inputs + outputs
            
            record = {
            'outputs': outputs,
            'inputs': inputs,
            'other_inputs': other_inputs,
            'company_contributions': company_contributions,
            'payslip_net': payslip_net,
                      }
            res[rs.id] = record
        return res

    def _order_inputs_outputs(self, cr, uid, ids, field_names, arg, context=None):
        slip_line_obj = self.pool.get('hr.payslip.line2')
        res={}
        for rs in self.browse(cr, uid, ids, context=context):
            line_i_o_ids=[]
            for line in rs.line_ids:
                if line.salary_rule_id:
                    if line.salary_rule_id.category_id.code == "INGR":
                        line_i_o_ids.append(line.id)
                    elif line.salary_rule_id.category_id.code == "OINGR":
                        line_i_o_ids.append(line.id)
                elif line.extra_i_o_id:
                    if line.extra_i_o_id.category_id.code == "INGR":
                        line_i_o_ids.append(line.id)
                    elif line.extra_i_o_id.category_id.code == "OINGR":
                        line_i_o_ids.append(line.id)
            
            for line in rs.line_ids:
                if line.salary_rule_id:
                    if line.salary_rule_id.category_id.type == 'output':
                        line_i_o_ids.append(line.id)
                elif line.extra_i_o_id:
                    if line.extra_i_o_id.category_id.type == 'output':
                        line_i_o_ids.append(line.id)

            record = {
            'line_i_o_ids': line_i_o_ids,
                      }
            res[rs.id] = line_i_o_ids
        return res
    
    
    def _get_lines_salary_rule_category(self, cr, uid, ids, field_names, arg=None, context=None):
        result = {}
        if not ids: return result
        for id in ids:
            result.setdefault(id, [])
        cr.execute('''SELECT pl.slip_id, pl.id FROM hr_payslip_line2 AS pl \
                    LEFT JOIN hr_salary_rule_category AS sh on (pl.category_id = sh.id) \
                    WHERE pl.slip_id in %s \
                    GROUP BY pl.slip_id, pl.sequence, pl.id ORDER BY pl.sequence''',(tuple(ids),))
        res = cr.fetchall()
        for r in res:
            result[r[0]].append(r[1])
        return result

    def _amount_residual(self, cr, uid, ids, name, args, context=None):
        res = {}
        if not context:
            context = {}
        for payslip in self.browse(cr, uid, ids, context):
            total = payslip.payslip_net
            for vou in payslip.voucher_ids:
                if vou.state == 'posted':
                    total -= vou.amount
            res[payslip.id] = total
        return res
    
    def _get_payslip_from_voucher(self, cr, uid, ids, context=None):
        res = {}
        if not context:
            context = {}
        for vou in self.pool.get('account.voucher').browse(cr, uid, ids, context=None):
            if vou.payslip_id:
                res [vou.payslip_id.id] = True
        return res.keys()



    _columns = {
        'struct_id': fields.many2one('hr.payroll.structure', 'Structure', readonly=True, states={'draft': [('readonly', False)]}, help='Defines the rules that have to be applied to this payslip, accordingly to the contract chosen. If you let empty the field contract, this field isn\'t mandatory anymore and thus the rules applied will be all the rules set on the structure of all contracts of the employee valid for the chosen period'),
        'name': fields.char('Description', size=64, required=False, readonly=True, states={'draft': [('readonly', False)]}),
        'number': fields.char('Reference', size=64, required=False, readonly=True, states={'draft': [('readonly', False)]}),
        'employee_id': fields.many2one('hr.employee', 'Employee', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'date_from': fields.date('Date From', readonly=True, states={'draft': [('readonly', False)]}, required=True),
        'date_to': fields.date('Date To', readonly=True, states={'draft': [('readonly', False)]}, required=True),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('verify', 'Waiting'),
            ('open', 'Open'),
            ('done', 'Done'),
            ('cancel', 'Rejected'),
        ], 'State', select=True, readonly=True,
            help='* When the payslip is created the state is \'Draft\'.\
            \n* If the payslip is under verification, the state is \'Waiting\'. \
            \n* If the payslip is confirmed then state is set to \'Done\'.\
            \n* When user cancel payslip the state is \'Rejected\'.'),
        'line_ids': one2many_mod2('hr.payslip.line2', 'slip_id', 'Payslip Lines', readonly=True, states={'draft':[('readonly',False)]}),
        'company_id': fields.many2one('res.company', 'Company', required=False, readonly=True, states={'draft': [('readonly', False)]}),
        'worked_days_line_ids': fields.one2many('hr.payslip.worked_days', 'payslip_id', 'Payslip Worked Days', required=False, readonly=True, states={'draft': [('readonly', False)]}),
        'input_line_ids': fields.one2many('hr.payslip.input', 'payslip_id', 'Payslip Inputs', required=False, readonly=True, states={'draft': [('readonly', False)]}),
        'paid': fields.boolean('Made Payment Order ? ', required=False, readonly=True, states={'draft': [('readonly', False)]}),
        'note': fields.text('Description', readonly=True, states={'draft':[('readonly',False)]}),
        'contract_id': fields.many2one('hr.contract', 'Contract', required=False, readonly=True, states={'draft': [('readonly', False)]}),
        'details_by_salary_rule_category': fields.function(_get_lines_salary_rule_category, method=True, type='one2many', relation='hr.payslip.line2', string='Details by Salary Rule Category'),
        'credit_note': fields.boolean('Credit Note', help="Indicates this payslip has a refund of another", readonly=True, states={'draft': [('readonly', False)]}),
        'payslip_run_id': fields.many2one('hr.payslip.run', 'Payslip Run', readonly=True, states={'draft': [('readonly', False)]}),
        'grows': fields.function(_calculate, method=True, store=True, multi='dc', string='Gross Salary', digits_compute=dp.get_precision('Account')),
        'net': fields.function(_calculate, method=True, store=True, multi='dc', string='Net Salary', digits_compute=dp.get_precision('Account')),
        'allounce': fields.function(_calculate, method=True, store=True, multi='dc', string='Allowance', digits_compute=dp.get_precision('Account')),
        'deduction': fields.function(_calculate, method=True, store=True, multi='dc', string='Deduction', digits_compute=dp.get_precision('Account')),
        'other_pay': fields.function(_calculate, method=True, store=True, multi='dc', string='Others', digits_compute=dp.get_precision('Account')),
        'total_pay': fields.function(_calculate, method=True, store=True, multi='dc', string='Total Payment', digits_compute=dp.get_precision('Account')),
        'period_id': fields.many2one('account.period', 'Force Period',states={'draft': [('readonly', False)]}, readonly=True, domain=[('state','<>','done')], help="Keep empty to use the period of the validation(Payslip) date."),
        'journal_id': fields.many2one('account.journal', 'Expense Journal',states={'draft': [('readonly', False)]}, readonly=True, required=True),
        'move_id': fields.many2one('account.move', 'Accounting Entry', readonly=True),
        'outputs': fields.function(_calculate, method=True, store=True, multi='dc', string='Ouputs', digits_compute=dp.get_precision('Account')),
        'inputs': fields.function(_calculate, method=True, store=True, multi='dc', string='Inputs', digits_compute=dp.get_precision('Payroll')),
        'other_inputs': fields.function(_calculate, method=True, store=True, multi='dc', string='Other Inputs', digits_compute=dp.get_precision('Account')),
        'company_contributions': fields.function(_calculate, method=True, store=True, multi='dc', string='Company Contribution', digits_compute=dp.get_precision('Account')),
        'payslip_net': fields.function(_calculate, method=True, store=True, multi='dc', string='Net', digits_compute=dp.get_precision('Account')),
        'helper':fields.boolean('Helper',),
        'line_i_o_ids': fields.function(_order_inputs_outputs, method=True, string='Lines', type="many2many", relation="hr.payslip.line2"),
        'voucher_ids':fields.one2many('account.voucher', 'payslip_id', 'Vouchers', required=False, readonly=True),
        'residual': fields.function(_amount_residual, method=True, digits_compute=dp.get_precision('Account'), string='Residual',
            store={
                'hr.payslip': (lambda self, cr, uid, ids, c={}: ids, ['voucher_ids'], 50),
                'account.voucher': (_get_payslip_from_voucher, ['state'], 50),
            },
            help="Remaining amount due."),
        'newholidays_ids':fields.many2many('hr.newholidays', 'newholidays_payslip_rel', 'payslip_id', 'newholidyas_id', 'Ausencias'), 
        
    }
    
    _defaults = {
        'date_from': lambda *a: time.strftime('%Y-%m-01'),
        'date_to': lambda *a: str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
        'state': 'draft',
        'credit_note': False,
        'company_id': lambda self, cr, uid, context: \
                self.pool.get('res.users').browse(cr, uid, uid,
                    context=context).company_id.id,
    }

    def lista_sin_repeticiones(self, lista, elemento):
        existe = False
        for el in lista:
            if el == elemento:
                existe = True
                break
        if existe:
            return lista
        else:
            lista.append(elemento)
            return lista


    def _check_date_employee(self, cr, uid, ids, context=None):
        payslip_obj = self.pool.get('hr.payslip')
        for payslip in self.browse(cr, uid, ids, context):
            contract = payslip.contract_id and payslip.contract_id or None
            employee = payslip.employee_id and payslip.employee_id or None 
            date_from = payslip.date_from and payslip.date_from or None
            date_to = payslip.date_to and payslip.date_to or None
            #Verificar si existe otro contrato en el mismo periodo de tiempo de otro payslip
            #      |----|
            #      .
            #    |----|
            case1 = payslip_obj.search(cr, uid, [('id','!=', payslip.id),
                                                 ('employee_id','=', employee.id), 
                                                 ('contract_id','=', contract.id),
                                                 ('date_from','>=',date_from),
                                                 ('date_from','<=',date_to)])

            # |----|
            #      .
            #    |----|
            case2 = payslip_obj.search(cr, uid, [('id','!=', payslip.id),
                                                 ('employee_id','=', employee.id), 
                                                 ('contract_id','=', contract.id),
                                                 ('date_to','>=',date_from),
                                                 ('date_to','<=',date_to)])
            # |---------|
            #      
            #    |----|
            case3 = payslip_obj.search(cr, uid, [('id','!=', payslip.id),
                                                 ('employee_id','=', employee.id), 
                                                 ('contract_id','=', contract.id),
                                                 ('date_from','<=',date_from),
                                                 ('date_to','>=',date_to)])
            #    |----|
            #      
            #    |----|
            case4 = payslip_obj.search(cr, uid, [('id','!=', payslip.id),
                                                 ('employee_id','=', employee.id), 
                                                 ('contract_id','=', contract.id),
                                                 ('date_to','=',date_from),
                                                 ('date_to','=',date_to)])
            lista_payslip = []
            for c in case1:
                if lista_payslip.count(c) < 1:
                    lista_payslip = self.lista_sin_repeticiones(lista_payslip, c)
            for c in case2:
                if lista_payslip.count(c) < 1:
                    lista_payslip = self.lista_sin_repeticiones(lista_payslip, c)
            for c in case3:
                if lista_payslip.count(c) < 1:
                    lista_payslip = self.lista_sin_repeticiones(lista_payslip, c)
            for c in case4:
                if lista_payslip.count(c) < 1:
                    lista_payslip = self.lista_sin_repeticiones(lista_payslip, c)
            if int(len(lista_payslip)) > 0:
                if employee:
                    if contract:
                        raise osv.except_osv(_('Warning!'),
                                             _("There is another payslip between dates that you configurated for employee %s") % self.pool.get('hr.employee').name_get(cr, uid, [employee.id,]))
            else:
                return True
    
    def onchange_contract_id(self, cr, uid, ids, date_from, date_to, employee_id=False, contract_id=False, context=None):
        contract_obj = self.pool.get('hr.contract')
        if context is None:
            context = {}
        res = {'value':{
                 'line_ids': [],
                 'name': '',
                 }
              }
        context.update({'contract': True})
        if not contract_id:
            res['value'].update({'struct_id': False})
        journal_id = contract_id and contract_obj.browse(cr, uid, contract_id, context=context).journal_id.id or False
        res['value'].update({'journal_id': journal_id})
        return self.onchange_employee_id(cr, uid, ids, date_from=date_from, date_to=date_to, employee_id=employee_id, contract_id=contract_id, context=context)

    def set_draft(self, cr, uid, ids, context=None):
        if not context:
            context={}
        wf_service = netsvc.LocalService("workflow")
        line_obj = self.pool.get('hr.payslip.line2')
        work_days_obj = self.pool.get('hr.payslip.worked_days')
        for slip in self.browse(cr, uid, ids, context):
            for line in slip.line_ids:
                line_obj.unlink(cr, uid, [line.id])
            for line in slip.worked_days_line_ids:
                work_days_obj.unlink(cr, uid, [line.id])
        for id in ids:
            wf_service.trg_delete(uid, 'hr.payslip', id, cr)
            wf_service.trg_create(uid, 'hr.payslip', id, cr)
        self.write(cr, uid, ids, {'state':'draft'}, context=context)
        return True

    def cancel_sheet(self, cr, uid, ids, context=None):
        if not context:
            context = None
        move_pool = self.pool.get('account.move')
        voucher_obj = self.pool.get('account.voucher')
        extra_obj = self.pool.get('hr.extra.input.output')
        move_ids = []
        move_to_cancel = []
        for slip in self.browse(cr, uid, ids, context=context):
            move_ids.append(slip.move_id.id)
            if slip.move_id.state == 'posted':
                move_to_cancel.append(slip.move_id.id)
            for voucher in slip.voucher_ids:
                if voucher.state == 'posted':
                    raise osv.except_osv(_('Cancelation Error!'),_("You must cancel payment done for employee '%s' ") % (self.pool.get('hr.employee').name_get(cr, uid, [slip.employee_id.id,])[0][1]))
                else:
                    voucher_obj.cancel_voucher(cr, uid, [voucher.id], context)
                    voucher_obj.unlink(cr, uid, [voucher.id], context)
            for slip_line in slip.line_ids:
                if slip_line.extra_i_o_id:
                    extra_obj.write(cr, uid, [slip_line.extra_i_o_id.id], {'paid':False})
        move_pool.button_cancel(cr, uid, move_to_cancel, context=context)
        move_pool.unlink(cr, uid, move_ids, context=context)
        self.write(cr, uid, ids, {'state':'cancel'}, context=context)
        return True

    def process_sheet(self, cr, uid, ids, context=None):
        move_pool = self.pool.get('account.move')
        period_pool = self.pool.get('account.period')
        extra_pool = self.pool.get('hr.extra.input.output')
        timenow = time.strftime('%Y-%m-%d')
        if not context:
            context = {}
        for slip in self.browse(cr, uid, ids, context=context):
            timenow = slip.date_to
            self._check_date_employee(cr, uid, ids, context)
            if not slip.employee_id.partner_id:
                raise osv.except_osv(_('Configuration Error!'),_("You must configure correct Partner for employee '%s' ") % (self.pool.get('hr.employee').name_get(cr, uid, [slip.employee_id.id,])[0][1]))
            line_ids = []
            debit_sum = 0.0
            credit_sum = 0.0
            if not slip.period_id:
                search_periods = period_pool.find(cr, uid, slip.date_to, context=context)
                period_id = search_periods[0]
            else:
                period_id = slip.period_id.id

            name = _('Payslip of %s') % (slip.employee_id.name)
            move = {
                'narration': name,
                'date': timenow,
                'ref': slip.number,
                'journal_id': slip.journal_id.id,
                'period_id': period_id,
            }
            
            extra_ids = []
            for line in slip.line_ids:
                amt = slip.credit_note and -line.total or line.total
                #partner_id = False
                partner_id_debit = slip.employee_id.partner_id.id
                partner_id_credit = slip.employee_id.partner_id.id
                debit_account_id = None
                credit_account_id = None
                debit_line = None
                credit_line = None
                debit = 0.0
                credit = 0.0
                analytic_account_id = None 
                tax_code_id = None 
                tax_amount = None
                
                debit = amt > 0.0 and amt or 0.0
                credit = amt < 0.0 and -amt or 0.0

                if line.salary_rule_id:
                    if line.salary_rule_id.pay_to_other:
                        partner_id_debit = line.salary_rule_id.partner_id and line.salary_rule_id.partner_id.id or False
                        partner_id_credit = line.salary_rule_id.partner_id and line.salary_rule_id.partner_id.id or False
                    debit_account_id = line.salary_rule_id.account_debit.id or False
                    credit_account_id = line.salary_rule_id.account_credit.id or False
                    if line.salary_rule_id.category_id.type == 'input':
                        if line.salary_rule_id.use_partner_account:
                            debit_account_id =  slip.employee_id.partner_id.property_account_payable.id or False
                    elif line.salary_rule_id.category_id.type == 'output':
                        aux = debit
                        debit = credit
                        credit = aux
                        partner_id_debit = slip.employee_id.partner_id.id
                        if line.salary_rule_id.use_partner_account:
                            credit_account_id =  slip.employee_id.partner_id.property_account_receivable.id or False
                    analytic_account_id = line.salary_rule_id.analytic_account_id and line.salary_rule_id.analytic_account_id.id or False
                    tax_code_id = line.salary_rule_id.account_tax_id and line.salary_rule_id.account_tax_id.id or False
                    tax_amount = line.salary_rule_id.account_tax_id and amt or 0.0
                elif line.extra_i_o_id:
                    if line.extra_i_o_id.pay_to_other:
                        partner_id_debit = line.extra_i_o_id.partner_id and line.extra_i_o_id.partner_id.id or False
                        partner_id_credit = line.extra_i_o_id.partner_id and line.extra_i_o_id.partner_id.id or False
                    extra_ids.append(line.extra_i_o_id.id)
                    debit_account_id = line.extra_i_o_id.account_debit.id or False
                    credit_account_id = line.extra_i_o_id.account_credit.id or False
                    if line.extra_i_o_id.category_id.type == 'input':
                        if line.extra_i_o_id.use_partner_account:
                            debit_account_id =  slip.employee_id.partner_id.property_account_payable.id or False
                    elif line.extra_i_o_id.category_id.type == 'output':
                        aux = debit
                        debit = credit
                        credit = aux
                        partner_id_debit = slip.employee_id.partner_id.id
                        if line.extra_i_o_id.use_partner_account:
                            credit_account_id =  slip.employee_id.partner_id.property_account_receivable.id or False
                    analytic_account_id = line.extra_i_o_id.analytic_account_id and line.extra_i_o_id.analytic_account_id.id or False
                    tax_code_id = line.extra_i_o_id.account_tax_id and line.extra_i_o_id.account_tax_id.id or False
                    tax_amount = line.extra_i_o_id.account_tax_id and amt or 0.0
                if not debit_account_id or not credit_account_id:
                    raise osv.except_osv(_('Accounting Error!'),_("You have to configure debit and credit accounts for '%s' Payslip Line!") % (line.name))
                        
                debit_line = (0, 0, {
                    'name': line.name,
                    'date': timenow,
                    'partner_id': partner_id_debit,
                    'account_id': debit_account_id,
                    'journal_id': slip.journal_id.id,
                    'period_id': period_id,
                    'debit': debit,
                    'credit': credit,
                    'analytic_account_id': analytic_account_id,
                    'tax_code_id': tax_code_id,
                    'tax_amount': tax_amount,
                })
                credit_line = (0, 0, {
                    'name': line.name,
                    'date': timenow,
                    'partner_id': partner_id_credit,
                    'account_id': credit_account_id,
                    'journal_id': slip.journal_id.id,
                    'period_id': period_id,
                    'debit': credit,
                    'credit': debit,
                    'analytic_account_id': analytic_account_id,
                    'tax_code_id': tax_code_id,
                    'tax_amount': tax_amount,
                })
                if debit_account_id:
                    line_ids.append(debit_line)
                    debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
                if credit_account_id:
                    line_ids.append(credit_line)
                    credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']
                
            if debit_sum > credit_sum:
                adjust_credit = (0, 0, {
                    'name': _('Adjustment Entry'),
                    'date': timenow,
                    'partner_id': partner_id,
                    'account_id': slip.journal_id.default_credit_account_id.id,
                    'journal_id': slip.journal_id.id,
                    'period_id': period_id,
                    'debit': 0.0,
                    'credit': debit_sum - credit_sum,
                })
                line_ids.append(adjust_credit)
            elif debit_sum < credit_sum:
                adjust_debit = (0, 0, {
                    'name': _('Adjustment Entry'),
                    'date': timenow,
                    'partner_id': partner_id,
                    'account_id': slip.journal_id.default_debit_account_id.id,
                    'journal_id': slip.journal_id.id,
                    'period_id': period_id,
                    'debit': credit_sum - debit_sum,
                    'credit': 0.0,
                })
                line_ids.append(adjust_debit)
            
            extra_pool.write(cr, uid, extra_ids, {'paid':True}, context=context)
            move.update({'line_id': line_ids})
            move_id = move_pool.create(cr, uid, move, context=context)
            self.write(cr, uid, [slip.id], {'move_id': move_id}, context=context)
            if slip.journal_id.entry_posted:
                move_pool.post(cr, uid, [move_id], context=context)
        return self.write(cr, uid, ids, {'paid': True, 'state': 'done'}, context=context)

    def copy(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        default.update({
            'line_ids': [],
            'move_ids': [],
            'move_line_ids': [],
            'voucher_ids': [],
            'company_id': company_id,
            'period_id': False,
            'basic_before_leaves': 0.0,
            'basic_amount': 0.0
        })
        return super(hr_payslip, self).copy(cr, uid, id, default, context=context)

    def hr_verify_sheet(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'verify'}, context=context)

    def refund_sheet(self, cr, uid, ids, context=None):
        mod_obj = self.pool.get('ir.model.data')
        wf_service = netsvc.LocalService("workflow")
        for payslip in self.browse(cr, uid, ids, context=context):
            id_copy = self.copy(cr, uid, payslip.id, {'credit_note': True, 'name': _('Refund: ')+payslip.name}, context=context)
            self.compute_sheet(cr, uid, [id_copy], context=context)
            wf_service.trg_validate(uid, 'hr.payslip', id_copy, 'hr_verify_sheet', cr)
            wf_service.trg_validate(uid, 'hr.payslip', id_copy, 'process_sheet', cr)

        form_id = mod_obj.get_object_reference(cr, uid, 'hr_payroll', 'view_hr_payslip_form')
        form_res = form_id and form_id[1] or False
        tree_id = mod_obj.get_object_reference(cr, uid, 'hr_payroll', 'view_hr_payslip_tree')
        tree_res = tree_id and tree_id[1] or False
        return {
            'name':_("Refund Payslip"),
            'view_mode': 'tree, form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'hr.payslip',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': "[('id', 'in', %s)]" % [id_copy],
            'views': [(tree_res, 'tree'), (form_res, 'form')],
            'context': {}
        }

    def check_done(self, cr, uid, ids, context=None):
        return True

    #TODO move this function into hr_contract module, on hr.employee object
    def get_contract(self, cr, uid, employee, date_from, date_to, context=None):
        """
        @param employee: browse record of employee
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
        clause_final =  [('employee_id', '=', employee.id),'|','|'] + clause_1 + clause_2 + clause_3
        contract_ids = contract_obj.search(cr, uid, clause_final, context=context)
        return contract_ids

    def compute_sheet(self, cr, uid, ids, context=None):
        if not context:
            context={}
        slip_line_pool = self.pool.get('hr.payslip.line2')
        sequence_obj = self.pool.get('ir.sequence')
        for payslip in self.browse(cr, uid, ids, context=context):
            number = payslip.number or sequence_obj.get(cr, uid, 'salary.slip')
            #delete old payslip lines
            old_slipline_ids = slip_line_pool.search(cr, uid, [('slip_id', '=', payslip.id)], context=context)
#            old_slipline_ids
            if old_slipline_ids:
                slip_line_pool.unlink(cr, uid, old_slipline_ids, context=context)
            if payslip.contract_id:
                #set the list of contract for which the rules have to be applied
                contract_ids = [payslip.contract_id.id]
            else:
                #if we don't give the contract, then the rules to apply should be for all current contracts of the employee
                contract_ids = self.get_contract(cr, uid, payslip.employee_id, payslip.date_from, payslip.date_to, context=context)
            newholidays_obj = self.pool.get('hr.newholidays')
            newholidays_ids = newholidays_obj.search(cr, uid, [('employee_id','=',payslip.employee_id.id),('state','=','aproved'),('date_end','<=',payslip.date_to),('date_start','>=',payslip.date_from)])
            self.write(cr, uid, [payslip.id], {'newholidays_ids': [(6,0,newholidays_ids)]}, context=context)
            lines = [(0,0,line) for line in self.pool.get('hr.payslip').get_payslip_lines(cr, uid, contract_ids, payslip.id, context=context)]
            self.write(cr, uid, [payslip.id], {'line_ids': lines,'number': number}, context=context)
            #Linea agregada como artificio para campos calculado del payslip
            self.write(cr, uid, [payslip.id,], {}, context)
        return True

    def get_worked_day_lines(self, cr, uid, contract_ids, date_from, date_to, context=None):
        """
        @param contract_ids: list of contract id
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """
        def was_on_leave(employee_id, datetime_day, context=None):
            name = None
            code = None
            day = datetime_day.strftime("%Y-%m-%d")
            holiday_ids = self.pool.get('hr.holidays').search(cr, uid, [('state','=','validate'),('employee_id','=',employee_id),('type','=','remove'),('date_from','<=',day),('date_to','>=',day)])
            if holiday_ids:
                holiday = self.pool.get('hr.holidays').browse(cr, uid, holiday_ids, context=context)
                (name, code) = holiday[0].holiday_status_id.name, holiday[0].holiday_status_id.code
            return (name, code)

        res = []
        for contract in self.pool.get('hr.contract').browse(cr, uid, contract_ids, context=context):
            if not contract.working_hours:
                #fill only if the contract as a working schedule linked
                continue
            attendances = {
                 'name': _("Normal Working Days paid at 100%"),
                 'sequence': 1,
                 'code': 'WORK100',
                 'number_of_days': 0.0,
                 'number_of_hours': 0.0,
                 'contract_id': contract.id,
            }
            leaves = {}
            day_from = datetime.strptime(date_from,"%Y-%m-%d")
            day_to = datetime.strptime(date_to,"%Y-%m-%d")
            nb_of_days = (day_to - day_from).days + 1
            for day in range(0, nb_of_days):
                working_hours_on_day = self.pool.get('resource.calendar').working_hours_on_day(cr, uid, contract.working_hours, day_from + timedelta(days=day), context)
                if working_hours_on_day:
                    #the employee had to work
                    (leave_type, code) = was_on_leave(contract.employee_id.id, day_from + timedelta(days=day), context=context)
                    if leave_type:
                        #if he was on leave, fill the leaves dict
                        if leave_type in leaves:
                            leaves[leave_type]['number_of_days'] += 1.0
                            leaves[leave_type]['number_of_hours'] += working_hours_on_day
                        else:
                            leaves[leave_type] = {
                                'name': leave_type,
                                'sequence': 5,
                                'code': code,
                                'number_of_days': 1.0,
                                'number_of_hours': working_hours_on_day,
                                'contract_id': contract.id,
                            }
                    else:
                        #add the input vals to tmp (increment if existing)
                        attendances['number_of_days'] += 1.0
                        attendances['number_of_hours'] += working_hours_on_day
            leaves = [value for key,value in leaves.items()]
            res += [attendances] + leaves
        return res

    def get_inputs(self, cr, uid, contract_ids, date_from, date_to, context=None):
        res = []
        contract_obj = self.pool.get('hr.contract')
        rule_obj = self.pool.get('hr.salary.rule')

        structure_ids = contract_obj.get_all_structures(cr, uid, contract_ids, context=context)
        rule_ids = self.pool.get('hr.payroll.structure').get_all_rules(cr, uid, structure_ids, context=context)
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x:x[1])]

        for contract in contract_obj.browse(cr, uid, contract_ids, context=context):
            for rule in rule_obj.browse(cr, uid, sorted_rule_ids, context=context):
                if rule.input_ids:
                    for input in rule.input_ids:
                        inputs = {
                             'name': input.name,
                             'code': input.code,
                             'contract_id': contract.id,
                        }
                        res += [inputs]
        return res

    def get_payslip_lines(self, cr, uid, contract_ids, payslip_id, context=None):
        def _sum_salary_rule_category(localdict, category, amount):
            if category.parent_id:
                localdict = _sum_salary_rule_category(localdict, category.parent_id, amount)
            localdict['categories'].dict[category.code] = category.code in localdict['categories'].dict and localdict['categories'].dict[category.code] + amount or amount
            return localdict

        class BrowsableObject(object):
            def __init__(self, pool, cr, uid, employee_id, dict):
                self.pool = pool
                self.cr = cr
                self.uid = uid
                self.employee_id = employee_id
                self.dict = dict

            def __getattr__(self, attr):
                return attr in self.dict and self.dict.__getitem__(attr) or 0.0

        class InputLine(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""
            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = datetime.now().strftime('%Y-%m-%d')
                result = 0.0
                self.cr.execute("SELECT sum(amount) as sum\
                            FROM hr_payslip as hp, hr_payslip_input as pi \
                            WHERE hp.employee_id = %s AND hp.state = 'done' \
                            AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s",
                           (self.employee_id, from_date, to_date, code))
                res = self.cr.fetchone()[0]
                return res or 0.0

        class WorkedDays(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""
            def _sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = datetime.now().strftime('%Y-%m-%d')
                result = 0.0
                self.cr.execute("SELECT sum(number_of_days) as number_of_days, sum(number_of_hours) as number_of_hours\
                            FROM hr_payslip as hp, hr_payslip_worked_days as pi \
                            WHERE hp.employee_id = %s AND hp.state = 'done'\
                            AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s",
                           (self.employee_id, from_date, to_date, code))
                return self.cr.fetchone()

            def sum(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[0] or 0.0

            def sum_hours(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[1] or 0.0

        class Payslips(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""

            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = datetime.now().strftime('%Y-%m-%d')
                self.cr.execute("SELECT sum(case when hp.credit_note = False then (pl.total) else (-pl.total) end)\
                            FROM hr_payslip as hp, hr_payslip_line as pl \
                            WHERE hp.employee_id = %s AND hp.state = 'done' \
                            AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pl.slip_id AND pl.code = %s",
                            (self.employee_id, from_date, to_date, code))
                res = self.cr.fetchone()
                return res and res[0] or 0.0

        #we keep a dict with the result because a value can be overwritten by another rule with the same code
        if not context: context = {}
        result_dict = {}
        rules = {}
        categories_dict = {}
        blacklist = []
        payslip_obj = self.pool.get('hr.payslip')
        inputs_obj = self.pool.get('hr.payslip.worked_days')
        obj_rule = self.pool.get('hr.salary.rule')
        obj_extra = self.pool.get('hr.extra.input.output')
        payslip = payslip_obj.browse(cr, uid, payslip_id, context=context)
        worked_days = {}
        if payslip.worked_days_line_ids:
            for worked_days_line in payslip.worked_days_line_ids:
                worked_days[worked_days_line.code] = worked_days_line
        inputs = {}
        if payslip.input_line_ids:
            for input_line in payslip.input_line_ids:
                inputs[input_line.code] = input_line

        categories_obj = BrowsableObject(self.pool, cr, uid, payslip.employee_id.id, categories_dict)
        input_obj = InputLine(self.pool, cr, uid, payslip.employee_id.id, inputs)
        worked_days_obj = WorkedDays(self.pool, cr, uid, payslip.employee_id.id, worked_days)
        payslip_obj = Payslips(self.pool, cr, uid, payslip.employee_id.id, payslip)
        rules_obj = BrowsableObject(self.pool, cr, uid, payslip.employee_id.id, rules)
        
        total_ausencias = 0.0
        for holiday in payslip.newholidays_ids:
            if holiday.type_id.is_paid:
                total_ausencias += holiday.number_days
        localdict = {'categories': categories_obj,
                     'rules': rules_obj,
                     'payslip': payslip_obj,
                     'worked_days': worked_days_obj,
                     'inputs': input_obj,
                     'total_ausencia':total_ausencias
                     }
        #Agregado uso de contexto para paso valores desde otros modulos, para reglas salariales mas personalizadas
        if context.get('external_localdict'):
            localdict.update(
                             context.get('external_localdict')
                             )
        
        #get the ids of the structures on the contracts and their parent id as well
#        structure_ids = self.pool.get('hr.contract').get_all_structures(cr, uid, contract_ids, context=context)
        structure_ids = []
        for contract in self.pool.get('hr.contract').browse(cr, uid, contract_ids, context=context):
            if contract.struct_id:
                structure_ids.append(contract.struct_id.id)
        #get the rules of the structure and thier children
        rule_ids = self.pool.get('hr.payroll.structure').get_all_rules(cr, uid, structure_ids, context=context)
        #run the rules by sequence
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x:x[1])]

        for contract in self.pool.get('hr.contract').browse(cr, uid, contract_ids, context=context):
            employee = contract.employee_id
            localdict.update({'employee': employee, 'contract': contract})
            extra_i_o_ids = []
            #TODO:Para todos los extra pagos generar los respectivos payslip del rol
            extra_i_o_ids = obj_extra.search(cr, uid, [('paid','=',False),
                                                       ('employee_id','=', employee.id),
                                                       #Comprobar que este dentro de la fecha de calculo del payslip
                                                       #('date_to_pay','>', time.strftime('%Y-%m-%d')),
                                                       ])
            
            for extra in obj_extra.browse(cr, uid, extra_i_o_ids, context=context):
                if not (extra.date_to_pay >= payslip.date_from and extra.date_to_pay <= payslip.date_to):
                    extra_i_o_ids.remove(extra.id)
                
            for rule in obj_extra.browse(cr, uid, extra_i_o_ids, context=context):
                key = rule.code + '-' + str(contract.id)
                localdict['result'] = None
                localdict['result_qty'] = 1.0
                #check if the rule can be applied
                if obj_extra.satisfy_condition_extra(cr, uid, rule.id, localdict, context=context) and rule.id not in blacklist:
                    #compute the amount of the rule
                    amount, qty = obj_extra.compute_rule_extra(cr, uid, rule.id, localdict, context=context)
                    #check if there is already a rule computed with that code
                    previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
                    #set/overwrite the amount computed for this rule in the localdict
                    localdict[rule.code] = amount * qty
                    rules[rule.code] = rule
                    #sum the amount for its salary category
                    localdict = _sum_salary_rule_category(localdict, rule.category_id, (amount * qty) - previous_amount)
                    #create/overwrite the rule in the temporary results
                    result_dict[key] = {
                        #'salary_rule_id': rule.id,
                        'extra_i_o_id':rule.id,
                        'contract_id': contract.id,
                        'name': rule.name,
                        'code': rule.code,
                        'category_id': rule.category_id.id,
                        'sequence': rule.sequence,
                        'appears_on_payslip': rule.appears_on_payslip,
                        'condition_select': rule.condition_select,
                        'condition_python': rule.condition_python,
                        'condition_range': rule.condition_range,
                        'condition_range_min': rule.condition_range_min,
                        'condition_range_max': rule.condition_range_max,
                        'amount_select': rule.amount_select,
                        'amount_fix': rule.amount_fix,
                        'amount_python_compute': rule.amount_python_compute,
                        'amount_percentage': rule.amount_percentage,
                        'amount_percentage_base': rule.amount_percentage_base.id,
                        'register_id': rule.register_id.id,
                        'amount': amount,
                        'employee_id': contract.employee_id.id,
                        'quantity': qty,
                        'company_contribution':rule.company_contribution,
                    }
                else:
                    #blacklist this rule and its children
                    blacklist += [id for id, seq in self.pool.get('hr.salary.rule')._recursive_search_of_rules(cr, uid, [rule], context=context)]
            
            for rule in obj_rule.browse(cr, uid, sorted_rule_ids, context=context):
                key = rule.code + '-' + str(contract.id)
                localdict['result'] = None
                localdict['result_qty'] = 1.0
                #check if the rule can be applied
                if obj_rule.satisfy_condition(cr, uid, rule.id, localdict, context=context) and rule.id not in blacklist:
                    #compute the amount of the rule
                    amount, qty = obj_rule.compute_rule(cr, uid, rule.id, localdict, context=context)
                    #check if there is already a rule computed with that code
                    previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
                    #set/overwrite the amount computed for this rule in the localdict
                    localdict[rule.code] = amount * qty
                    rules[rule.code] = rule
                    #sum the amount for its salary category
                    localdict = _sum_salary_rule_category(localdict, rule.category_id, (amount * qty) - previous_amount)
                    #create/overwrite the rule in the temporary results
                    result_dict[key] = {
                        'salary_rule_id': rule.id,
                        'contract_id': contract.id,
                        'name': rule.name,
                        'code': rule.code,
                        'category_id': rule.category_id.id,
                        'sequence': rule.sequence,
                        'appears_on_payslip': rule.appears_on_payslip,
                        'condition_select': rule.condition_select,
                        'condition_python': rule.condition_python,
                        'condition_range': rule.condition_range,
                        'condition_range_min': rule.condition_range_min,
                        'condition_range_max': rule.condition_range_max,
                        'amount_select': rule.amount_select,
                        'amount_fix': rule.amount_fix,
                        'amount_python_compute': rule.amount_python_compute,
                        'amount_percentage': rule.amount_percentage,
                        'amount_percentage_base': rule.amount_percentage_base.id,
                        'register_id': rule.register_id.id,
                        'amount': amount,
                        'employee_id': contract.employee_id.id,
                        'quantity': qty,
                        'company_contribution':rule.company_contribution,
                        'use_partner_account': rule.use_partner_account
                    }
                else:
                    #blacklist this rule and its children
                    blacklist += [id for id, seq in self.pool.get('hr.salary.rule')._recursive_search_of_rules(cr, uid, [rule], context=context)]

        result = [value for code, value in result_dict.items()]
        return result

    def onchange_employee_id(self, cr, uid, ids, date_from, date_to, employee_id=False, contract_id=False, context=None):
        empolyee_obj = self.pool.get('hr.employee')
        contract_obj = self.pool.get('hr.contract')
        worked_days_obj = self.pool.get('hr.payslip.worked_days')
        input_obj = self.pool.get('hr.payslip.input')
        journal_obj = self.pool.get('account.journal')
        if context is None:
            context = {}
        #delete old worked days lines
        old_worked_days_ids = ids and worked_days_obj.search(cr, uid, [('payslip_id', '=', ids[0])], context=context) or False
        if old_worked_days_ids:
            worked_days_obj.unlink(cr, uid, old_worked_days_ids, context=context)

        #delete old input lines
        old_input_ids = ids and input_obj.search(cr, uid, [('payslip_id', '=', ids[0])], context=context) or False
        if old_input_ids:
            input_obj.unlink(cr, uid, old_input_ids, context=context)


        #defaults
        res = {'value':{
                      'line_ids':[],
                      'input_line_ids': [],
                      'worked_days_line_ids': [],
                      #'details_by_salary_head':[], TODO put me back
                      'name':'',
                      'contract_id': False,
                      'struct_id': False,
                      }
            }
        if not employee_id:
            return res
        ttyme = datetime.fromtimestamp(time.mktime(time.strptime(date_from, "%Y-%m-%d")))
        employee_id = empolyee_obj.browse(cr, uid, employee_id, context=context)
        res['value'].update({
                    'name': _('Salary Slip of %s for %s') % (employee_id.name, tools.ustr(ttyme.strftime('%B-%Y'))),
                    'company_id': employee_id.company_id.id
        })

        if not context.get('contract', False):
            #fill with the first contract of the employee
            contract_ids = self.get_contract(cr, uid, employee_id, date_from, date_to, context=context)                            
            res['value'].update({
                        'struct_id': contract_ids and contract_obj.read(cr, uid, contract_ids[0], ['struct_id'], context=context)['struct_id'][0] or False,
                        'contract_id': contract_ids and contract_ids[0] or False,
                        'journal_id': contract_ids and contract_obj.browse(cr, uid, contract_ids)[0].journal_id.id or False,
            })
        else:
            if contract_id:
                #set the list of contract for which the input have to be filled
                contract_ids = [contract_id]
                #fill the structure with the one on the selected contract
                contract_record = contract_obj.browse(cr, uid, contract_id, context=context)
                res['value'].update({
                            'struct_id': contract_record.struct_id.id,
                            'contract_id': contract_id,
                            'journal_id': contract_obj.browse(cr, uid, contract_id).journal_id.id or False,
                })
            else:
                #if we don't give the contract, then the input to fill should be for all current contracts of the employee
                contract_ids = self.get_contract(cr, uid, employee_id, date_from, date_to, context=context)
                if not contract_ids:
                    return res

        #computation of the salary input
        worked_days_line_ids = self.get_worked_day_lines(cr, uid, contract_ids, date_from, date_to, context=context)
        input_line_ids = self.get_inputs(cr, uid, contract_ids, date_from, date_to, context=context)
        res['value'].update({
                    'worked_days_line_ids': worked_days_line_ids,
                    'input_line_ids': input_line_ids,
        })
        return res

hr_payslip()

class hr_payslip_worked_days(osv.osv):
    '''
    Payslip Worked Days
    '''

    _name = 'hr.payslip.worked_days'
    _description = 'Payslip Worked Days'
    _columns = {
        'name': fields.char('Description', size=256, required=True),
        'payslip_id': fields.many2one('hr.payslip', 'Pay Slip', required=True, ondelete="cascade"),
        'sequence': fields.integer('Sequence', required=True,),
        'code': fields.char('Code', size=52, required=True, help="The code that can be used in the salary rules"),
        'number_of_days': fields.float('Number of Days'),
        'number_of_hours': fields.float('Number of Hours'),
        'contract_id': fields.many2one('hr.contract', 'Contract', required=True, help="The contract for which applied this input"),
    }
    _order = 'payslip_id, sequence'
    _defaults = {
        'sequence': 10,
    }
hr_payslip_worked_days()

class hr_payslip_worked_hours_interval(osv.osv):
    
    _name = "hr.payslip.worked.hours.interval"
    _columns = {
                    'name': fields.char('Description', size=256, required=True),
                    'code': fields.char('Code', size=52, required=True, help="The code that can be used in the salary rules"),
                    'number_of_hours': fields.float('Number of Hours'),
                    }
hr_payslip_worked_hours_interval()

class hr_payslip_input(osv.osv):
    '''
    Payslip Input
    '''

    _name = 'hr.payslip.input'
    _description = 'Payslip Input'
    _columns = {
        'name': fields.char('Description', size=256, required=True),
        'payslip_id': fields.many2one('hr.payslip', 'Pay Slip', required=True),
        'sequence': fields.integer('Sequence', required=True,),
        'code': fields.char('Code', size=52, required=True, help="The code that can be used in the salary rules"),
        'amount': fields.float('Amount', help="It is used in computation. For e.g. A rule for sales having 1% commission of basic salary for per product can defined in expression like result = inputs.SALEURO.amount * contract.wage*0.01."),
        'contract_id': fields.many2one('hr.contract', 'Contract', required=True, help="The contract for which applied this input"),
    }
    _order = 'payslip_id, sequence'
    _defaults = {
        'sequence': 10,
        'amount': 0.0,
    }

hr_payslip_input()

class hr_salary_rule_percentage_base(osv.osv):
    _name = "hr.salary.rule.percentage.base"
    _columns = {
                    'name':fields.char('Description', size=64, required=True,), 
                    'base':fields.char('Percentage based on',size=1024, required=True, help='result will be affected to a variable'),
                    }
hr_salary_rule_percentage_base()

class hr_salary_rule(osv.osv):

    _name = 'hr.salary.rule'
    _columns = {
        'name':fields.char('Name', size=256, required=True, readonly=False),
        'code':fields.char('Code', size=64, required=True, help="The code of salary rules can be used as reference in computation of other rules. In that case, it is case sensitive."),
        'sequence': fields.integer('Sequence', required=True, help='Use to arrange calculation sequence'),
        'quantity': fields.char('Quantity', size=256, help="It is used in computation for percentage and fixed amount.For e.g. A rule for Meal Voucher having fixed amount of 1€ per worked day can have its quantity defined in expression like worked_days.WORK100.number_of_days."),
        'category_id':fields.many2one('hr.salary.rule.category', 'Category', required=True),
        'active':fields.boolean('Active', help="If the active field is set to false, it will allow you to hide the salary rule without removing it."),
        'appears_on_payslip': fields.boolean('Appears on Payslip', help="Used for the display of rule on payslip"),
        'parent_rule_id':fields.many2one('hr.salary.rule', 'Parent Salary Rule', select=True),
        'company_id':fields.many2one('res.company', 'Company', required=False),
        'condition_select': fields.selection([('none', 'Always True'),('range', 'Range'), ('python', 'Python Expression')], "Condition Based on", required=True),
        'condition_range':fields.char('Range Based on',size=1024, readonly=False, help='This will use to computer the % fields values, in general its on basic, but You can use all categories code field in small letter as a variable name i.e. hra, ma, lta, etc...., also you can use, static varible basic'),
        'condition_python':fields.text('Python Condition', required=True, readonly=False, help='Applied this rule for calculation if condition is true. You can specify condition like basic > 1000.'),#old name = conditions
        'condition_range_min': fields.float('Minimum Range', required=False, help="The minimum amount, applied for this rule."),
        'condition_range_max': fields.float('Maximum Range', required=False, help="The maximum amount, applied for this rule."),
        'amount_select':fields.selection([
            ('percentage','Percentage (%)'),
            ('fix','Fixed Amount'),
            ('code','Python Code'),
        ],'Amount Type', select=True, required=True, help="The computation method for the rule amount."),
        'amount_fix': fields.float('Fixed Amount', digits_compute=dp.get_precision('Payroll'),),
        'amount_percentage': fields.float('Percentage (%)', digits_compute=dp.get_precision('Payroll'), help='For example, enter 50.0 to apply a percentage of 50%'),
        'amount_python_compute':fields.text('Python Code'),
        'amount_percentage_base':fields.many2one('hr.salary.rule.percentage.base','Percentage based on', required=False, readonly=False, help='result will be affected to a variable'),
        #'amount_percentage_base':fields.char('Percentage based on',size=1024, required=False, readonly=False, help='result will be affected to a variable'),
        'child_ids':fields.one2many('hr.salary.rule', 'parent_rule_id', 'Child Salary Rule'),
        'register_id':fields.many2one('hr.contribution.register', 'Contribution Register', help="Eventual third party involved in the salary payment of the employees."),
        'input_ids': fields.one2many('hr.rule.input', 'input_id', 'Inputs'),
        'note':fields.text('Description'),
        'analytic_account_id':fields.many2one('account.analytic.account', 'Analytic Account'),
        'account_tax_id':fields.many2one('account.tax.code', 'Tax Code'),
        'account_debit': fields.many2one('account.account', 'Debit Account'),
        'account_credit': fields.many2one('account.account', 'Credit Account'),
        'account_debit_partner':fields.boolean('Debit Account of Partner?', ),
        'account_credit_partner':fields.boolean('Credit Account of Partner?', ),
        'company_contribution':fields.boolean('Company Contribution?', required=False),
        'pay_to_other':fields.boolean('Pay to Other? / Provision?', required=False, help="If payment is made to another Partner and is part of the employee's salary, check this option, you must specify the beneficiary of the rule"), 
        'partner_id':fields.many2one('res.partner', 'Beneficiary', required=False, help="The accounting entries will be done with this Partner as data, to keep their accounts receivable or payable, Let in blank if you are using for provisions"),
        'use_partner_account':fields.boolean('Use partner account?', required=False, help="If you use this option if input or output will be used counterparties with the accounts configured on the employee, as the case output - Credit, or input - Debit"),         
     }
    _defaults = {
        'amount_python_compute': '''
# Available variables:
#----------------------
# payslip: object containing the payslips
# employee: hr.employee object
# contract: hr.contract object
# rules: object containing the rules code (previously computed)
# categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
# worked_days: object containing the computed worked days.
# inputs: object containing the computed inputs.

# Note: returned value have to be set in the variable 'result'

result = contract.wage * 0.10''',
        'condition_python':
'''
# Available variables:
#----------------------
# payslip: object containing the payslips
# employee: hr.employee object
# contract: hr.contract object
# rules: object containing the rules code (previously computed)
# categories: object containing the computed salary rule categories (sum of amount of all rules belonging to that category).
# worked_days: object containing the computed worked days
# inputs: object containing the computed inputs

# Note: returned value have to be set in the variable 'result'

result = rules.NET > categories.NET * 0.10''',
        'condition_range': 'contract.wage',
        'sequence': 5,
        'appears_on_payslip': True,
        'active': True,
        'company_id': lambda self, cr, uid, context: \
                self.pool.get('res.users').browse(cr, uid, uid,
                    context=context).company_id.id,
        'condition_select': 'none',
        'amount_select': 'fix',
        'amount_fix': 0.0,
        'amount_percentage': 0.0,
        'quantity': '1.0',
     }

    _sql_constraints = [('code_unique_salary_rule', 'unique(code)', _('Code of Salary rule must be unique!')),      ]

    def _recursive_search_of_rules(self, cr, uid, rule_ids, context=None):
        """
        @param rule_ids: list of browse record
        @return: returns a list of tuple (id, sequence) which are all the children of the passed rule_ids
        """
        children_rules = []
        for rule in rule_ids:
            if rule.child_ids:
                children_rules += self._recursive_search_of_rules(cr, uid, rule.child_ids, context=context)
        return [(r.id, r.sequence) for r in rule_ids] + children_rules

    #TODO should add some checks on the type of result (should be float)
    def compute_rule(self, cr, uid, rule_id, localdict, context=None):
        """
        @param rule_id: id of rule to compute
        @param localdict: dictionary containing the environement in which to compute the rule
        @return: returns the result of computation and the quantity as floats
        """
        rule = self.browse(cr, uid, rule_id, context=context)
        if rule.amount_select == 'fix':
            try:
                if rule.category_id.type == 'input':
                    return rule.amount_fix, eval(rule.quantity, localdict)
                elif rule.category_id.type == 'output':
                    return rule.amount_fix*-1, eval(rule.quantity, localdict)
            except:
                raise osv.except_osv(_('Error'), _('Wrong quantity defined for salary rule %s (%s)')% (rule.name, rule.code))
        elif rule.amount_select == 'percentage':
            try:
                amount = rule.amount_percentage * eval(rule.amount_percentage_base.base, localdict) / 100
                if rule.category_id.type == 'input':
                    return amount, eval(rule.quantity, localdict)
                elif rule.category_id.type == 'output':
                    return amount*-1, eval(rule.quantity, localdict)
            except:
                raise osv.except_osv(_('Error'), _('Wrong percentage base or quantity defined for salary rule %s (%s)')% (rule.name, rule.code))
        else:
            try:
                eval(rule.amount_python_compute, localdict, mode='exec', nocopy=True)
                result_rule=localdict['result']
                if rule.category_id.type == 'output':
                    result_rule =result_rule*-1
                return result_rule, 'result_qty' in localdict and localdict['result_qty'] or 1.0
            except:
                raise osv.except_osv(_('Error'), _('Wrong python code defined for salary rule %s (%s) ')% (rule.name, rule.code))

    def satisfy_condition(self, cr, uid, rule_id, localdict, context=None):
        """
        @param rule_id: id of hr.salary.rule to be tested
        @param contract_id: id of hr.contract to be tested
        @return: returns True if the given rule match the condition for the given contract. Return False otherwise.
        """
        rule = self.browse(cr, uid, rule_id, context=context)

        if rule.condition_select == 'none':
            return True
        elif rule.condition_select == 'range':
            try:
                result = eval(rule.condition_range, localdict)
                return rule.condition_range_min <=  result and result <= rule.condition_range_max or False
            except:
                raise osv.except_osv(_('Error'), _('Wrong range condition defined for salary rule %s (%s)')% (rule.name, rule.code))
        else: #python code
            try:
                eval(rule.condition_python, localdict, mode='exec', nocopy=True)
                return 'result' in localdict and localdict['result'] or False
            except:
                raise osv.except_osv(_('Error'), _('Wrong python condition defined for salary rule %s (%s)')% (rule.name, rule.code))

hr_salary_rule()

class hr_rule_input(osv.osv):
    '''
    Salary Rule Input
    '''

    _name = 'hr.rule.input'
    _description = 'Salary Rule Input'
    _columns = {
        'name': fields.char('Description', size=256, required=True),
        'code': fields.char('Code', size=52, required=True, help="The code that can be used in the salary rules"),
        'input_id': fields.many2one('hr.salary.rule', 'Salary Rule Input', required=True)
    }

hr_rule_input()

class extra_payment_deduction(osv.osv):

    _name = 'hr.extra.input.output'
    _inherit = 'hr.salary.rule'
    
    _columns = {
                'employee_id':fields.many2one('hr.employee', 'Employee', required=True, ondelete="restrict"),
                'date_to_pay': fields.date('Date', required=True),
                'paid':fields.boolean('Paid?',),
                'loan_id':fields.many2one('account.hr.third.loan', 'Loan', required=False, ondelete="restrict"), 
                'advance_id':fields.many2one('account.hr.advances', 'Advance', required=False, ondelete="restrict"), 
                'voucher_id':fields.many2one('account.voucher', 'Voucher', required=False, ondelete="restrict"), 
                    }

    #TODO should add some checks on the type of result (should be float)
    def compute_rule_extra(self, cr, uid, rule_id, localdict, context=None):
        """
        @param rule_id: id of rule to compute
        @param localdict: dictionary containing the environement in which to compute the rule
        @return: returns the result of computation and the quantity as floats
        """
        rule = self.browse(cr, uid, rule_id, context=context)
        if rule.amount_select == 'fix':
            try:
                if rule.category_id.type == 'input':
                    return rule.amount_fix, eval(rule.quantity, localdict)
                elif rule.category_id.type == 'output':
                    return rule.amount_fix*-1, eval(rule.quantity, localdict)
            except:
                raise osv.except_osv(_('Error'), _('Wrong quantity defined for salary rule %s (%s)')% (rule.name, rule.code))
        elif rule.amount_select == 'percentage':
            try:
                amount = rule.amount_percentage * eval(rule.amount_percentage_base.base, localdict) / 100
                if rule.category_id.type == 'input':
                    return amount, eval(rule.quantity, localdict)
                elif rule.category_id.type == 'output':
                    return amount*-1, eval(rule.quantity, localdict)
            except:
                raise osv.except_osv(_('Error'), _('Wrong percentage base or quantity defined for salary rule %s (%s)')% (rule.name, rule.code))
        else:
            try:
                eval(rule.amount_python_compute, localdict, mode='exec', nocopy=True)
                result_rule=localdict['result']
                if rule.category_id.type == 'output':
                    result_rule =result_rule*-1
                return result_rule, 'result_qty' in localdict and localdict['result_qty'] or 1.0
            except:
                raise osv.except_osv(_('Error'), _('Wrong python code defined for salary rule %s (%s) ')% (rule.name, rule.code))

    def satisfy_condition_extra(self, cr, uid, rule_id, localdict, context=None):
        """
        @param rule_id: id of hr.salary.rule to be tested
        @param contract_id: id of hr.contract to be tested
        @return: returns True if the given rule match the condition for the given contract. Return False otherwise.
        """
        rule = self.browse(cr, uid, rule_id, context=context)

        if rule.condition_select == 'none':
            return True
        elif rule.condition_select == 'range':
            try:
                result = eval(rule.condition_range, localdict)
                return rule.condition_range_min <=  result and result <= rule.condition_range_max or False
            except:
                raise osv.except_osv(_('Error'), _('Wrong range condition defined for salary rule %s (%s)')% (rule.name, rule.code))
        else: #python code
            try:
                eval(rule.condition_python, localdict, mode='exec', nocopy=True)
                return 'result' in localdict and localdict['result'] or False
            except:
                raise osv.except_osv(_('Error'), _('Wrong python condition defined for salary rule %s (%s)')% (rule.name, rule.code))

extra_payment_deduction()

class hr_payslip_line(osv.osv):
    '''
    Payslip Line
    '''

    _name = 'hr.payslip.line2'
    _inherit = 'hr.salary.rule'
    _description = 'Payslip Line'
    _order = 'contract_id, sequence'

    def _calculate_total(self, cr, uid, ids, name, args, context):
        if not ids: return {}
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = float(line.quantity) * line.amount
        return res

    _columns = {
        'slip_id':fields.many2one('hr.payslip', 'Pay Slip', required=True, ondelete="cascade"),
        'salary_rule_id':fields.many2one('hr.salary.rule', 'Rule',),
        'extra_i_o_id':fields.many2one('hr.extra.input.output', 'Extra Input/Output',),
        'employee_id':fields.many2one('hr.employee', 'Employee', required=True),
        'contract_id':fields.many2one('hr.contract', 'Contract', required=True),
        'amount': fields.float('Amount', digits_compute=dp.get_precision('Payroll')),
        'quantity': fields.float('Quantity', digits_compute=dp.get_precision('Payroll')),
        'total': fields.function(_calculate_total, method=True, type='float', string='Total', digits_compute=dp.get_precision('Payroll'),store=True ),
    }
    _sql_constraints = [
                        ('code_unique_salary_rule', '1=1', _('Code can duplicate')),     
                         ]

hr_payslip_line()

class hr_allounce_deduction_categoty(osv.osv):
    _inherit = 'hr.allounce.deduction.categoty' 
    _columns = {
                    'category_id':fields.many2one('hr.allounce.deduction.categoty', 'Category', required=False),
                    }
hr_allounce_deduction_categoty()

class hr_payroll_structure(osv.osv):

    _inherit = 'hr.payroll.structure'
    _columns = {
        'rule_ids':fields.many2many('hr.salary.rule', 'hr_structure_salary_rule_rel', 'struct_id', 'rule_id', 'Salary Rules'),
    }

hr_payroll_structure()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
