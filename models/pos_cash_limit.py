# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from datetime import date
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
import logging
import pytz


class QuemenRetirosEfectivo(models.Model):
    _name = "pos_chash_limit.retiros_efectivo"
    _description = "Retiros de POS"

    def _denominacion_actual(self):
        denominacion_ids = self.env['pos.bill'].search([('id','>', 0)], order='value asc')
        lista_denominaciones = []
        if len(denominacion_ids) > 0:
            for denominacion in denominacion_ids:
                if denominacion.value >= 0.50:
                    valor = {'denominacion_id': denominacion.id, 'cantidad': 0.00}
                    lista_denominaciones.append((0,0,valor))
        return lista_denominaciones


    def _sesion_actual(self):
        sesion = False
        sesion_id = self.env['pos.session'].search([('user_id','=',self.env.user.id),('state','in',['opened','closing_control'])])
        if len(sesion_id) > 0:
            sesion = sesion_id
        # else:
        #     raise ValidationError(_('No puede retirar efectivo'))
        return sesion

    @api.depends('denominacion_ids')
    def _calcular_total(self):
        for retiro in self:
            total = 0
            for linea in retiro.denominacion_ids:
                total += (linea.cantidad * linea.denominacion_id.value)
            retiro.total = total

    name = fields.Char('Nombre', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    usuario_id = fields.Many2one('res.users','usuario',default=lambda self: self.env.user)
    fecha_hora = fields.Datetime('Hora',default=fields.Datetime.now)
    sesion_id = fields.Many2one('pos.session','Sesión', default=_sesion_actual, required=True, store=True)
    tienda_id = fields.Many2one('pos.config','tienda', related='sesion_id.config_id', store=True)
    motivo = fields.Char('Motivo', required=True, default = "Retiro de efectivo")
    total = fields.Float('Total', compute='_calcular_total')
    denominacion_ids = fields.One2many('quemen.retiro_denominacion','retiro_id',string="Denominaciones",default=_denominacion_actual)
    state = fields.Selection(
    [('borrador', 'Borrador'), ('confirmado', 'Confirmado')],
    'Estado', readonly=True, copy=False, default= "borrador")
    cajero = fields.Char('Cajero', required=True)
    entregado = fields.Boolean('Entregado', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        logging.warning('valores')
        logging.warning(vals_list)
        logging.warning(self)
        for vals in vals_list:
            secuencia_id = self.env['pos.session'].search([('id', '=', vals['sesion_id'])]).config_id.secuencia_id
            if vals.get('name', _('New')) == _('New'):
                seq_date = None
                if 'company_id' in vals:
                    vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                        'quemen.retiros', sequence_date=seq_date) or _('New')
                else:
                    vals['name'] = secuencia_id._next() or _('New')
        result = super(QuemenRetirosEfectivo, self).create(vals_list)
        return result

    def confirmar_retiro(self):
        for retiro in self:
            retiro.sesion_id.cash_register_id.write({'line_ids': [(0, 0,  { 'payment_ref': retiro.motivo, 'amount': retiro.total*-1})] })
            retiro.write({'state': 'confirmado'})


class QuemenRetiros(models.Model):
    _name = "pos_chash_limit.retiro_denominacion"

    retiro_id = fields.Many2one('quemen.retiros_efectivo','Retiro')
    denominacion_id = fields.Many2one('pos.bill','Denominacion')
    cantidad = fields.Integer('Cantidad')