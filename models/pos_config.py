# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _

class PosConfig(models.Model):
    _inherit = 'pos.config'

    efectivo_maximo = fields.Float(string="Efectivo máxmio")
    secuencia_id = fields.Many2one('ir.sequence', 'Secuencia')
    diario_efectivo_id = fields.Many2one('account.journal','Diario efectivo')
