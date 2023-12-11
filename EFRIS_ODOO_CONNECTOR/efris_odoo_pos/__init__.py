# -*- coding: utf-8 -*-
from . import models
from . import wizard

from odoo.exceptions import UserError
from odoo import api, SUPERUSER_ID


def pre_init_hook(cr):
    env = api.Environment(cr, SUPERUSER_ID, {})
    queue_job = env['ir.model.data'].search(
            [('module', '=', 'queue_job')])
    queue_job_cron_jobrunner = env['ir.model.data'].search(
            [('module', '=', 'queue_job_cron_jobrunner')])
    if not queue_job_cron_jobrunner or not queue_job:
        raise UserError("Please make sure you have added and installed Queue Job and Queue Job Cron Jobrunner in your system")