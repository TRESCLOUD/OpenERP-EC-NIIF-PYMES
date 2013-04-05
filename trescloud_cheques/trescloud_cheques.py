# -*- coding: utf-8 -*-
from osv import osv, fields
from datetime import datetime
from amount_to_words import amount_to_words_es
from tools.translate import _
import netsvc
import pooler
import time

class check(osv.osv):
    
    """ Cheque """
    _name = 'check.check'
    
    def get_id(self, cr, uid, sequence_id, test='id', context=None):
        """
        Function to find next sequence number
        """
        seq_pool = self.pool.get('ir.sequence')
        assert test in ('code', 'id')
        company_id = self.pool.get('res.users').read(cr, uid, uid, ['company_id'], context=context)['company_id'][0] or None
        cr.execute('''SELECT id, number_next, prefix, suffix, padding
                      FROM ir_sequence
                      WHERE %s=%%s
                      AND active=true
                      AND (company_id = %%s or company_id is NULL)
                      ORDER BY company_id, id
                      FOR UPDATE NOWAIT''' % test,
                      (sequence_id, company_id))
        res = cr.dictfetchone()
        if res:
            if res['number_next']:
                return (seq_pool._process(res['prefix']) + '%%0%sd' % res['padding'] % res['number_next'] + seq_pool._process(res['suffix']),
                        res['number_next'])
            else:
                return (seq_pool._process(res['prefix']) + seq_pool._process(res['suffix']), 0)
        return False

    def _get_nxt_no(self, cr, uid, context=None):
        """
        Function to find next sequence number and update sequence
        """
        if context is None:
            context = {}
        if 'active_id' in context:
            voucher_id = self.pool.get('account.voucher').browse(cr, uid, context['active_id'], context=context)
            if not voucher_id.journal_id.check_sequence:
                raise osv.except_osv(_('Warning!'), _('Please add "Check Sequence" for journal %s.'%str(voucher_id.journal_id.name)))
            res = self.get_id(cr, uid, voucher_id.journal_id.check_sequence.id, test='id', context=context)
            return res and res[0]
        else:
            return False
        
    def _get_new_no(self, cr, uid, context=None):
        """
        Function to get the next number used to generate sequence
        """
        if context is None:
            context = {}
        res = []
        if 'active_id' in context:
            voucher_id = self.pool.get('account.voucher').browse(cr, uid, context['active_id'], context=context)
            res = self.get_id(cr, uid, voucher_id.journal_id.check_sequence.id , test='id', context=context)
            #print res
        return res and res[1]
    
    def onchange_check_number(self, cr, uid, ids, journal, context=None):
        journal_id = self.pool.get('account.journal').browse(cr, uid, journal, context=context)
        result={}
        res={}
        context={}
        warning = {}
        if not journal_id.check_sequence:
            warning = {
                        'title': _('Warning!'),
                        'message': _('Please add "Check Sequence" for journal %s.'%str(journal_id.name))
                        }
            return {'warning':warning}
        result=self.get_id(cr, uid, journal_id.check_sequence.id , test='id', context=context)
        res['check_number']=result[0]
        res['new_no']=result[0]
        journal_id = self.pool.get('account.journal').browse(cr, uid, journal, context=context)
        context.update({'journal_id':journal})
        return {'value': res}
    
    def default_get(self, cr, uid, fields_list, context=None):
        """
        Returns default values for fields
        @param fields_list: list of fields, for which default values are required to be read
        @param context: context arguments, like lang, time zone

        @return: Returns a dict that contains default values for fields
        """
        if context is None:
            context = {}
        journal_id=context.get('journal_id', False)
        values={}
        if journal_id:
            partner_obj = self.pool.get('res.partner')
            partner = partner_obj.browse(cr, uid, context['partner_id'])
            values = super(check, self).default_get(cr, uid, fields_list, context=context)  
            values.update({
                'amount':context['amount'],
                'journal_id':context['journal_id'],
                'supplier':context['partner_id'],
                'payee_name':partner.name,
                'amount_in_words':amount_to_words_es(context['amount']),
                'check_number':self._get_nxt_no(cr, uid, context),
                'new_no': self._get_new_no(cr, uid, context),
                'state':'draft',
                'ver_p':True,
                
            })
        else:
            #journalo_id = self.pool.get('account.journal').browse(cr, uid, journal_id, context=context)
            #nxt_no = self.pool.get('ir.sequence').read(cr, uid, journalo_id.check_sequence.id, ['number_next'], context=context)['number_next']
            #new_no=nxt_no+1
            #self.pool.get('ir.sequence').write(cr, uid, [journalo_id.check_sequence.id], {'number_next': new_no}, context=context)
            values.update({
                'amount_in_words': 'Cero con 00/100',
                'current_date': datetime.now(),
                'state': 'draft',
                'ver_p':False,
           #     'new_no':nxt_no,
                
            })           
        return values
    
    def onchange_partner(self,cr,uid,ids,partner_id,context=None):
        result={}
        partner_obj = self.pool.get('res.partner')
        partner = partner_obj.browse(cr, uid, partner_id)
        result['payee_name'] = partner.name
        return {'value': result}
    
    def onchange_amount(self, cr, uid, ids, amount, context=None):
        """
        Function to convert amount to words
        """
        result = {}
        
        amount_in_words = amount_to_words_es(amount)

        result['amount_in_words'] = amount_in_words
        
        return {'value': result}
    
    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        checks = self.read(cr, uid, ids, ['state'], context=context)
        unlink_ids = []
        for t in checks:
            if t['state'] in ('draft'):
                unlink_ids.append(t['id'])
            else:
                raise osv.except_osv(_('Invalid action !'), _('Cannot delete check(s) that are already printed!'))
        osv.osv.unlink(self, cr, uid, unlink_ids, context=context)
        return True
    
    _columns = {
        'supplier':fields.many2one('res.partner', 'Partner', change_default=1, required=True ),
        'journal_id': fields.many2one('account.journal', 'Journal',required=True),
        'check_number': fields.char('Check Number', size=32, help='check number',required=True),
        'payee_name': fields.char('Payee name', size=45, help='Used to indicate the payee name of check.', required=True),
        'current_date': fields.date('Current date', required=True),
        'amount': fields.float('Amount', digits=(2,2), required=True),
        'amount_in_words': fields.char(' ', size=70),
        'check_id': fields.many2one('account.voucher', 'Check Reference'),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('printed', 'Printed'),
            ('canceled', 'Canceled'),
            ('charged', 'Charged'),
            ('lost', 'Lost'),
            ('rejected', 'Rejected'),
            ],"State", readonly=True,),
        'new_no': fields.integer('Update Check Number', help= 'Enter new check number here if you wish to update'),
        'ver_p':fields.boolean('Verificacion'),
    }
    _sql_constraints = [
        ('check_number_uniq', 'unique (check_number)','The check number must be unique !'),
    ]
    _defaults = {
        'amount_in_words': 'Cero con 00/100',
        'current_date': datetime.now(),
        'state': 'draft',
        'check_number':_get_nxt_no,
        'new_no': _get_new_no,
     }
   
    def action_canceled(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if not len(ids):
            return False
        self.write(cr, uid, ids, {'state': 'canceled'})
        wf_service = netsvc.LocalService("workflow")
        for i in ids:     
            wf_service.trg_write(uid,'check.check', i, cr)
        return True
    
    def action_charged(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if not len(ids):
            return False
        self.write(cr, uid, ids, {'state': 'charged'})
        wf_service = netsvc.LocalService("workflow")
        for i in ids:     
            wf_service.trg_write(uid,'check.check', i, cr)
        return True
    
    def action_lost(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if not len(ids):
            return False
        self.write(cr, uid, ids, {'state': 'lost'})
        wf_service = netsvc.LocalService("workflow")
        for i in ids:     
            wf_service.trg_write(uid,'check.check', i, cr)
        return True
    
    def action_rejected(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if not len(ids):
            return False
        self.write(cr, uid, ids, {'state': 'rejected'})
        wf_service = netsvc.LocalService("workflow")
        for i in ids:     
            wf_service.trg_write(uid,'check.check', i, cr)
        return True
    
    def action_printed(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        self.write(cr, uid, ids, {'state': 'printed', 'date': time.strftime('%Y-%m-%d %H:%M:%S')}, context=context)
#        self.write(cr, uid, ids, {})
#        self.write(cr, uid, ids, { 'state' : 'printed' })
#######################################################################################################       
        #funciona cuando es sobre modulos base.
#######################################################################################################
        
#        for obj_inv in self.browse(cr, uid, ids, context=context):
#            if obj_inv.ver_p == False:
#                nxt_no = self.pool.get('ir.sequence').read(cr, uid,  obj_inv.journal_id.check_sequence.id, ['number_next'], context=context)['number_next']
#                new_no=nxt_no+1
#                self.pool.get('ir.sequence').write(cr, uid, [ obj_inv.journal_id.check_sequence.id], {'number_next': new_no}, context=context)

########################################################################################################       
        ## funcion especifica para ecua_account
########################################################################################################        
        for obj_inv in self.browse(cr, uid, ids, context=context):
            nxt_no = self.pool.get('ir.sequence').read(cr, uid,  obj_inv.journal_id.check_sequence.id, ['number_next'], context=context)['number_next']
            new_no=nxt_no+1
            self.pool.get('ir.sequence').write(cr, uid, [ obj_inv.journal_id.check_sequence.id], {'number_next': new_no}, context=context)
        
        return True
        
    def imprimir(self, cr, uid, ids, context=None):
        self.action_printed(cr, uid, ids, context=context)
        return {
             'type': 'ir.actions.report.xml',
             'report_name': 'check_report',    # the 'Service Name' from the report
             'datas' : {
             'model' : 'check.check',    # Report Model
             'res_ids' : ids
             }
         }

check()
